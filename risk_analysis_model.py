from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class RiskAnalysisRequest(BaseModel):
    companyName: str = Field(..., max_length=200)
    companyemail: EmailStr
    companyphonenumber: str = Field(..., max_length=20)
    practicearea: str = Field(..., max_length=100)

class ReferenceItem(BaseModel):
    label: str
    url: str

class RecommendedAttorney(BaseModel):
    name: str
    role: str
    reason: str
    attorney_id: Optional[str] = None
    email: Optional[str] = None

class RiskAnalysisResponse(BaseModel):
    company: str
    practice_area: str
    risks: List[str]
    references: List[ReferenceItem]
    recommended_attorney: RecommendedAttorney
    email_template: str
    confidence_score: float = Field(..., ge=1.0, le=100.0)