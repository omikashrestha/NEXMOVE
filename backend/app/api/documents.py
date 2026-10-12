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
        ),
        SampleDocumentInfo(
            filename="lease_ambiguous_inr.txt",
            title="Draft Lease with Missing Key Terms",
            description="Lacks explicit monthly rent and deposit figures, requiring manual clarification with landlord."
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


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
import io

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
CHUNK_SIZE = 64 * 1024  # 64 KB
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


@router.post("/upload", response_model=DocumentAnalysisResponse)
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Parses an uploaded text (.txt, .md) or PDF (.pdf) document and flags contractual risks.
    Enforces a strict 5 MB streaming read limit, validates signatures, and parses text-based PDFs.
    """
    filename = file.filename or "uploaded_lease.txt"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Please upload a plain text (.txt, .md) or PDF (.pdf) agreement."
        )

    # 1. Stream file in chunks to enforce 5 MB cap without trusting client Content-Length
    content_chunks = []
    total_bytes = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds maximum allowed limit of 5 MB."
            )
        content_chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please provide a valid lease agreement document."
        )

    content_bytes = b"".join(content_chunks)

    # 2. Extract Text based on format
    if ext == ".pdf":
        if not content_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file. Header signature does not match PDF specification."
            )
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    pass
                if reader.is_encrypted:
                    raise HTTPException(
                        status_code=422,
                        detail="The uploaded PDF is password-protected or encrypted. Please provide an unencrypted agreement."
                    )

            pages_text = []
            for page in reader.pages:
                try:
                    t = page.extract_text()
                    if t and t.strip():
                        pages_text.append(t.strip())
                except Exception:
                    continue
            raw_text = "\n\n".join(pages_text).strip()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse PDF document structure: {str(exc)}"
            )

        if not raw_text:
            raise HTTPException(
                status_code=422,
                detail="No readable text found in the uploaded PDF. Scanned images or image-only PDFs are not supported. Please upload a text-based document."
            )
    else:
        # Plain text or Markdown
        try:
            raw_text = content_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            raw_text = content_bytes.decode("latin-1", errors="ignore").strip()

        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded document contains no readable text."
            )

    # 3. Analyze document text through DocumentIntelligenceAgent
    agent = DocumentIntelligenceAgent()
    audit = agent.analyze_document(raw_text_content=raw_text)
    audit.document_filename = filename

    # 4. Attach to project if requested
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
                    "notice_period_days": audit.extracted_notice_period_days,
                    "lock_in_months": audit.extracted_lock_in_months
                },
                flagged_clauses=[c.model_dump() for c in audit.flagged_clauses_for_review],
                disclaimer=audit.disclaimer
            )
            db.add(record)
            if project.plan_cache:
                cache = dict(project.plan_cache)
                cache["document_audit"] = audit.model_dump()
                project.plan_cache = cache
            db.commit()
            db.refresh(record)
            record_id = record.id

    return DocumentAnalysisResponse(record_id=record_id, audit=audit)
