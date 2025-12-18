from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime



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
    enrichment_status: str = "pending"
    enrichment_retry_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_enriched_at: Optional[datetime] = None
