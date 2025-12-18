from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from config import settings

class PracticeAreaInput(BaseModel):
    area: str = Field(..., max_length=100)
    proficiency: str = Field(default="Intermediate")
    years_in_practice: int = Field(default=0, ge=0, le=60)
    
    @validator('proficiency')
    def validate_proficiency(cls, v):
        if v not in settings.PROFICIENCY_LEVELS:
            return "Intermediate"  # Default if invalid
        return v

class PracticeAreaStored(PracticeAreaInput):
    linked_legal_documents: List[str] = Field(default_factory=list)
    linked_knowledge_docs: List[str] = Field(default_factory=list)

class AttorneyCreate(BaseModel):
    name: str = Field(..., max_length=settings.MAX_NAME_LENGTH)
    email: EmailStr
    seniority: str
    years_of_experience: int = Field(..., ge=0, le=settings.MAX_YEARS_EXPERIENCE)
    practice_areas: List[PracticeAreaInput] = Field(default_factory=list)  # OPTIONAL - can be empty
    
    @validator('seniority')
    def validate_seniority(cls, v):
        # Case-insensitive matching
        v_lower = v.lower()
        seniority_map = {
            'associate': 'Associate',
            'senior associate': 'Senior Associate',
            'partner': 'Partner',
            'senior partner': 'Senior Partner'
        }
        
        if v_lower in seniority_map:
            return seniority_map[v_lower]
        
        if v not in settings.SENIORITY_LEVELS:
            raise ValueError(f"Seniority must be one of {settings.SENIORITY_LEVELS}")
        return v
    
    @validator('practice_areas')
    def validate_practice_areas(cls, v, values):
        # Allow empty practice areas
        if not v:
            return []
        
        if len(v) > settings.MAX_PRACTICE_AREAS:
            raise ValueError(f"Maximum {settings.MAX_PRACTICE_AREAS} practice areas allowed")
        
        years_exp = values.get('years_of_experience', 0)
        for pa in v:
            if pa.years_in_practice > years_exp:
                pa.years_in_practice = years_exp  # Cap at total experience
        return v

class AttorneyStored(BaseModel):
    attorney_id: str
    name: str
    email: str
    seniority: str
    years_of_experience: int
    practice_areas: List[PracticeAreaStored] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
