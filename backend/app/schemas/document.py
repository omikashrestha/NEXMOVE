from typing import List, Optional
from pydantic import BaseModel, Field


class FlaggedClause(BaseModel):
    clause_title: str = Field(..., description="Short category title for the flagged clause")
    raw_text: str = Field(..., description="Exact or near-exact excerpt from the document")
    risk_level: str = Field("MEDIUM", description="Advisory severity: LOW, MEDIUM, or HIGH")
    advisory_note: str = Field(..., description="Contextual explanation for why this term is flagged for review")


class DocumentAudit(BaseModel):
    document_filename: str = Field(..., description="Original name of the uploaded document")
    parse_status: str = Field("SUCCESS", description="SUCCESS, PARTIAL, or FAILED")
    extracted_monthly_rent_inr: Optional[float] = Field(None, description="Monthly rent extracted from lease")
    extracted_security_deposit_inr: Optional[float] = Field(None, description="Security deposit extracted from lease")
    extracted_notice_period_days: Optional[int] = Field(None, description="Notice period in days")
    extracted_lock_in_months: Optional[int] = Field(None, description="Lock-in duration in months")
    flagged_clauses_for_review: List[FlaggedClause] = Field(default_factory=list, description="Clauses requiring human inspection")
    disclaimer: str = Field(
        "Automated extraction for informational user review only. Does not constitute formal legal counsel.",
        description="Mandatory legal safety disclaimer"
    )
