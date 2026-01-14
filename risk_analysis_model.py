from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class RiskAnalysisRequest(BaseModel):
    companyName: str = Field(..., max_length=200)
    companyemail: Optional[EmailStr] = None  # Made optional
    companyphonenumber: Optional[str] = None  # Made optional
    practicearea: str = Field(..., max_length=100)

class ReferenceItem(BaseModel):
    label: str
    url: str

class RecommendedAttorney(BaseModel):
    name: str
    role: str
    reason: str
    match_score: int 
    attorney_id: Optional[str] = None
    email: Optional[str] = None

class RiskAnalysisResponse(BaseModel):
    company: str
    practice_area: str
    risks: List[str]
    references: List[ReferenceItem]
    recommended_attorneys: List[RecommendedAttorney]  # Changed from recommended_attorney (singular) to list
    email_template: str
    confidence_score: float = Field(..., ge=1.0, le=100.0)