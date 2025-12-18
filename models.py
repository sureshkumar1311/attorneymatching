from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from config import settings

# ---- Attorney Models ----
class PracticeAreaInput(BaseModel):
    area: str = Field(..., max_length=100)
    proficiency: str
    years_in_practice: int = Field(..., ge=0, le=60)
    
    @validator('proficiency')
    def validate_proficiency(cls, v):
        if v not in settings.PROFICIENCY_LEVELS:
            raise ValueError(f"Proficiency must be one of {settings.PROFICIENCY_LEVELS}")
        return v

class PracticeAreaStored(PracticeAreaInput):
    linked_legal_documents: List[str] = Field(default_factory=list)
    linked_knowledge_docs: List[str] = Field(default_factory=list)

class AttorneyCreate(BaseModel):
    name: str = Field(..., max_length=settings.MAX_NAME_LENGTH)
    email: EmailStr
    seniority: str
    years_of_experience: int = Field(..., ge=0, le=settings.MAX_YEARS_EXPERIENCE)
    practice_areas: List[PracticeAreaInput]
    
    @validator('seniority')
    def validate_seniority(cls, v):
        if v not in settings.SENIORITY_LEVELS:
            raise ValueError(f"Seniority must be one of {settings.SENIORITY_LEVELS}")
        return v
    
    @validator('practice_areas')
    def validate_practice_areas(cls, v, values):
        if len(v) > settings.MAX_PRACTICE_AREAS:
            raise ValueError(f"Maximum {settings.MAX_PRACTICE_AREAS} practice areas allowed")
        
        years_exp = values.get('years_of_experience', 0)
        for pa in v:
            if pa.years_in_practice > years_exp:
                raise ValueError(f"Years in practice cannot exceed total experience")
        return v

class AttorneyStored(BaseModel):
    attorney_id: str
    name: str
    email: str
    seniority: str
    years_of_experience: int
    practice_areas: List[PracticeAreaStored]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

# ---- Public Data Models ----
class PublicSourceCreate(BaseModel):
    title: str = Field(..., max_length=500)
    url: str = Field(..., pattern=r'^https?://.+')

class ReferenceData(BaseModel):
    source: Optional[str] = None
    url: str
    published_date: Optional[str] = None

class PublicSourceStored(BaseModel):
    news_id: str
    title: str
    risk_area: Optional[str] = None
    summary: Optional[str] = None
    reference: ReferenceData
    relevant_topics: List[str] = Field(default_factory=list)
    jurisdiction: Optional[str] = None
    impact_level: Optional[str] = None
    enrichment_status: str = "pending"  # pending, processing, completed, failed
    enrichment_retry_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_enriched_at: Optional[datetime] = None

