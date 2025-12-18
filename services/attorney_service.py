from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from services.database_service import DatabaseService
from models.attorney import AttorneyCreate, PracticeAreaStored
from config import settings

class AttorneyService:
    def __init__(self):
        self.db = DatabaseService()
    
    def create_attorney(self, attorney_data: AttorneyCreate) -> Dict[str, Any]:
        """Create a single attorney profile"""
        
        # Check for duplicate email
        if self.email_exists(attorney_data.email):
            raise ValueError(f"Email already exists: {attorney_data.email}")
        
        # Generate attorney_id
        attorney_id = f"ATT-{str(uuid.uuid4())[:8].upper()}"
        
        # Convert practice areas to stored format
        practice_areas_stored = [
            PracticeAreaStored(
                **pa.dict(),
                linked_legal_documents=[],
                linked_knowledge_docs=[]
            ).dict() for pa in attorney_data.practice_areas
        ]
        
        # Create stored document
        attorney_doc = {
            "id": attorney_id,
            "attorney_id": attorney_id,
            "name": attorney_data.name,
            "email": attorney_data.email,
            "seniority": attorney_data.seniority,
            "years_of_experience": attorney_data.years_of_experience,
            "practice_areas": practice_areas_stored,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into Cosmos DB
        result = self.db.insert_item(settings.ATTORNEY_CONTAINER, attorney_doc)
        return result
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        query = f"SELECT * FROM c WHERE c.email = '{email}'"
        results = self.db.query_items(settings.ATTORNEY_CONTAINER, query)
        return len(results) > 0
    
    def get_attorneys(
        self,
        practice_area: Optional[str] = None,
        seniority: Optional[str] = None,
        min_experience: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all attorneys with optional filters"""
        
        query_parts = ["SELECT * FROM c"]
        conditions = []
        
        if practice_area:
            conditions.append(f"ARRAY_CONTAINS(c.practice_areas, {{'area': '{practice_area}'}}, true)")
        
        if seniority:
            conditions.append(f"c.seniority = '{seniority}'")
        
        if min_experience:
            conditions.append(f"c.years_of_experience >= {min_experience}")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query = " ".join(query_parts)
        return self.db.query_items(settings.ATTORNEY_CONTAINER, query)
    
    def get_attorney_by_id(self, attorney_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific attorney by ID"""
        query = f"SELECT * FROM c WHERE c.attorney_id = '{attorney_id}'"
        results = self.db.query_items(settings.ATTORNEY_CONTAINER, query)
        return results[0] if results else None
    
    def delete_attorney(self, attorney_id: str) -> bool:
        """Delete an attorney profile"""
        attorney = self.get_attorney_by_id(attorney_id)
        if not attorney:
            return False
        
        self.db.delete_item(
            settings.ATTORNEY_CONTAINER,
            attorney_id,
            attorney['seniority']
        )
        return True
    
    def bulk_create_attorneys(self, attorneys_data: List[Dict[str, Any]]) -> List[str]:
        """
        Bulk create attorneys from parsed data
        Returns list of created attorney IDs
        Provides detailed feedback on skipped attorneys
        """
        created_ids = []
        skipped = []
        
        print(f"\n Starting bulk creation of {len(attorneys_data)} attorneys...")
        
        for idx, attorney_data in enumerate(attorneys_data, 1):
            email = attorney_data['email']
            name = attorney_data['name']
            
            # Skip if email exists
            if self.email_exists(email):
                skip_msg = f"  Attorney {idx}/{len(attorneys_data)}: Skipped - Duplicate email: {email} ({name})"
                print(skip_msg)
                skipped.append({
                    "email": email,
                    "name": name,
                    "reason": "Duplicate email"
                })
                continue
            
            try:
                attorney_id = f"ATT-{str(uuid.uuid4())[:8].upper()}"
                
                practice_areas_stored = [
                    {
                        **pa,
                        "linked_legal_documents": [],
                        "linked_knowledge_docs": []
                    } for pa in attorney_data['practice_areas']
                ]
                
                attorney_doc = {
                    "id": attorney_id,
                    "attorney_id": attorney_id,
                    **attorney_data,
                    "practice_areas": practice_areas_stored,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                self.db.insert_item(settings.ATTORNEY_CONTAINER, attorney_doc)
                created_ids.append(attorney_id)
                print(f"Attorney {idx}/{len(attorneys_data)}: Created - {name} ({email}) - ID: {attorney_id}")
                
            except Exception as e:
                skip_msg = f" Attorney {idx}/{len(attorneys_data)}: Failed - {name} ({email}) - Error: {str(e)}"
                print(skip_msg)
                skipped.append({
                    "email": email,
                    "name": name,
                    "reason": str(e)
                })
        
        # Final summary
        print(f"\n" + "=" * 60)
        print(f" BULK CREATION SUMMARY")
        print(f"=" * 60)
        print(f" Successfully created: {len(created_ids)}")
        print(f"  Skipped (duplicates): {len(skipped)}")
        print(f"=" * 60)
        
        if skipped:
            print(f"\n  SKIPPED ATTORNEYS:")
            for skip in skipped:
                print(f"   • {skip['name']} ({skip['email']}) - {skip['reason']}")
        
        return created_ids
