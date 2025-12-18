from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from services.database_service import DatabaseService
from models.public_source import PublicSourceCreate
from config import settings

class PublicSourceService:
    def __init__(self):
        self.db = DatabaseService()
    
    def create_public_source(self, source_data: PublicSourceCreate) -> Dict[str, Any]:
        """Create a public data source with minimal info (title + URL)"""
        
        news_id = f"NEWS-{str(uuid.uuid4())[:8].upper()}"
        
        public_source_doc = {
            "id": news_id,
            "news_id": news_id,
            "title": source_data.title,
            "risk_area": None,
            "summary": None,
            "reference": {
                "source": None,
                "url": source_data.url,
                "published_date": None
            },
            "relevant_topics": [],
            "jurisdiction": "Unknown",
            "impact_level": None,
            "enrichment_status": "pending",
            "enrichment_retry_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_enriched_at": None
        }
        
        result = self.db.insert_item(settings.PUBLIC_DATA_CONTAINER, public_source_doc)
        return result
    
    def get_public_sources(
        self,
        risk_area: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        enrichment_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all public sources with optional filters"""
        
        query_parts = ["SELECT * FROM c"]
        conditions = []
        
        if risk_area:
            conditions.append(f"c.risk_area = '{risk_area}'")
        
        if jurisdiction:
            conditions.append(f"c.jurisdiction = '{jurisdiction}'")
        
        if enrichment_status:
            conditions.append(f"c.enrichment_status = '{enrichment_status}'")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query = " ".join(query_parts)
        return self.db.query_items(settings.PUBLIC_DATA_CONTAINER, query)
    
    def get_public_source_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific public source by ID"""
        query = f"SELECT * FROM c WHERE c.news_id = '{news_id}'"
        results = self.db.query_items(settings.PUBLIC_DATA_CONTAINER, query)
        return results[0] if results else None
    
    def update_enrichment_status(
        self,
        news_id: str,
        status: str,
        enriched_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update enrichment status and data"""
        
        item = self.get_public_source_by_id(news_id)
        if not item:
            return False
        
        item['enrichment_status'] = status
        item['updated_at'] = datetime.utcnow().isoformat()
        
        if enriched_data:
            item.update(enriched_data)
            item['last_enriched_at'] = datetime.utcnow().isoformat()
        
        if status == 'failed':
            item['enrichment_retry_count'] = item.get('enrichment_retry_count', 0) + 1
        
        self.db.update_item(
            settings.PUBLIC_DATA_CONTAINER,
            news_id,
            item['jurisdiction'],
            item
        )
        return True
    
    def delete_public_source(self, news_id: str) -> bool:
        """Delete a public source"""
        source = self.get_public_source_by_id(news_id)
        if not source:
            return False
        
        self.db.delete_item(
            settings.PUBLIC_DATA_CONTAINER,
            news_id,
            source['jurisdiction']
        )
        return True
    
    def bulk_create_public_sources(self, sources_data: List[Dict[str, Any]]) -> List[str]:
        """Bulk create public sources from parsed data"""
        created_ids = []
        
        for source_data in sources_data:
            news_id = f"NEWS-{str(uuid.uuid4())[:8].upper()}"
            
            public_source_doc = {
                "id": news_id,
                "news_id": news_id,
                "title": source_data['title'],
                "risk_area": source_data.get('risk_area'),
                "summary": source_data.get('summary'),
                "reference": {
                    "source": source_data.get('source'),
                    "url": source_data['url'],
                    "published_date": source_data.get('published_date')
                },
                "relevant_topics": [],
                "jurisdiction": source_data.get('jurisdiction', 'Unknown'),
                "impact_level": source_data.get('impact_level'),
                "enrichment_status": "completed" if source_data.get('summary') else "pending",
                "enrichment_retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_enriched_at": None
            }
            
            self.db.insert_item(settings.PUBLIC_DATA_CONTAINER, public_source_doc)
            created_ids.append(news_id)
        
        return created_ids
