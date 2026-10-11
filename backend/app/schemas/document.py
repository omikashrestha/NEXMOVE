from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator


class FlaggedClause(BaseModel):
    clause_title: str = Field(..., description="Short category title for the flagged clause")
    raw_text: str = Field(..., description="Exact or near-exact excerpt from the document")
    risk_level: str = Field("MEDIUM", description="Advisory severity: LOW, MEDIUM, or HIGH")
    advisory_note: str = Field(..., description="Contextual explanation for why this term is flagged for review")
    suggested_action: Optional[str] = Field(None, description="Suggested question to ask the landlord")
    why_it_matters: Optional[str] = Field(None, description="Why this clause matters to the tenant")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "severity" in data and "risk_level" not in data:
                data["risk_level"] = data["severity"]
            if "clause_text" in data and "raw_text" not in data:
                data["raw_text"] = data["clause_text"]
            if "issue_rationale" in data and "advisory_note" not in data:
                data["advisory_note"] = data["issue_rationale"]
        return data


class DocumentAudit(BaseModel):
    document_filename: str = Field(..., description="Original name of the uploaded document")
    parse_status: str = Field("SUCCESS", description="SUCCESS, PARTIAL, FAILED, or NEEDS_MANUAL_REVIEW")
    extracted_monthly_rent_inr: Optional[float] = Field(None, description="Monthly rent extracted from lease")
    extracted_security_deposit_inr: Optional[float] = Field(None, description="Security deposit extracted from lease")
    extracted_notice_period_days: Optional[int] = Field(None, description="Notice period in days")
    extracted_lock_in_months: Optional[int] = Field(None, description="Lock-in duration in months")
    extracted_maintenance_inr: Optional[float] = Field(None, description="Monthly maintenance fee extracted from lease")
    flagged_clauses_for_review: List[FlaggedClause] = Field(default_factory=list, description="Clauses requiring human inspection")
    disclaimer: str = Field(
        "Automated extraction for informational user review only. Does not constitute formal legal counsel or legal advice.",
        description="Mandatory legal safety disclaimer"
    )
    is_sample_document: bool = Field(True, description="Indicates whether this is an example benchmark document")
