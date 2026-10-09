from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.config import DATA_DIR
from backend.app.db.session import get_db
from backend.app.db.models import RelocationProject, DocumentRecord
from backend.app.schemas.document import DocumentAudit
from backend.app.agents.document import DocumentIntelligenceAgent

router = APIRouter(prefix="/api/documents", tags=["Documents"])


class SampleDocumentInfo(BaseModel):
    filename: str
    title: str
    description: str


class DocumentAnalysisResponse(BaseModel):
    record_id: Optional[str] = None
    audit: DocumentAudit


@router.get("/samples", response_model=List[SampleDocumentInfo])
def list_sample_leases():
    """Lists available synthetic lease documents for testing and demonstrations."""
    return [
        SampleDocumentInfo(
            filename="lease_standard_inr.txt",
            title="Standard Bengaluru 2BHK Lease (HSR Layout)",
            description="Clean 11-month lease with ₹30,000 rent and standard 2-month deposit. No hidden penalty fees."
        ),
        SampleDocumentInfo(
            filename="lease_redflag_inr.txt",
            title="Strict Non-Standard Lease (Indiranagar)",
            description="Contains non-refundable 1-month painting deduction, strict pet prohibition, and restricted move-in hours."
        )
    ]


@router.post("/analyze-sample", response_model=DocumentAnalysisResponse)
def analyze_sample_lease(
    sample_filename: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Analyzes a bundled sample lease and optionally attaches findings to a project."""
    lease_path = DATA_DIR / "sample_leases" / sample_filename
    if not lease_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample lease '{sample_filename}' not found.")

    agent = DocumentIntelligenceAgent()
    audit = agent.analyze_document(file_path=lease_path)

    record_id = None
    if project_id:
        project = db.query(RelocationProject).filter_by(id=project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        record = DocumentRecord(
            project_id=project.id,
            file_name=sample_filename,
            file_type="LEASE",
            extracted_terms={
                "monthly_rent_inr": audit.extracted_monthly_rent_inr,
                "security_deposit_inr": audit.extracted_security_deposit_inr,
                "notice_period_days": audit.extracted_notice_period_days,
                "lock_in_months": audit.extracted_lock_in_months
            },
            flagged_clauses=[c.model_dump() for c in audit.flagged_clauses_for_review],
            disclaimer=audit.disclaimer
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id

    return DocumentAnalysisResponse(record_id=record_id, audit=audit)


@router.post("/upload", response_model=DocumentAnalysisResponse)
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Parses an uploaded text or PDF document and flags contractual risks for user review."""
    content_bytes = await file.read()
    try:
        raw_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = content_bytes.decode("latin-1", errors="ignore")

    agent = DocumentIntelligenceAgent()
    audit = agent.analyze_document(raw_text_content=raw_text)
    audit.document_filename = file.filename or "uploaded_lease.txt"

    record_id = None
    if project_id:
        project = db.query(RelocationProject).filter_by(id=project_id).first()
        if project:
            record = DocumentRecord(
                project_id=project.id,
                file_name=audit.document_filename,
                file_type="LEASE",
                extracted_terms={
                    "monthly_rent_inr": audit.extracted_monthly_rent_inr,
                    "security_deposit_inr": audit.extracted_security_deposit_inr,
                    "notice_period_days": audit.extracted_notice_period_days
                },
                flagged_clauses=[c.model_dump() for c in audit.flagged_clauses_for_review],
                disclaimer=audit.disclaimer
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            record_id = record.id

    return DocumentAnalysisResponse(record_id=record_id, audit=audit)
