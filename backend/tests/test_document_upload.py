import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.session import Base, get_db
from backend.app.db.models import User, RelocationProject


_doc_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
_DocTestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_doc_test_engine)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=_doc_test_engine)

    def _override():
        db = _DocTestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    prev_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override
    yield
    if prev_override is not None:
        app.dependency_overrides[get_db] = prev_override
    else:
        app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=_doc_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# Sample valid PDF with extractable text
VALID_TEXT_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 125 >>
stream
BT
/F1 12 Tf
72 712 Td
(Monthly rent is Rs 35000. Security deposit amount is Rs 70000. No pets allowed on premises.) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000227 00000 n 
0000000302 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
477
%%EOF
"""

# Blank PDF with no extractable text
BLANK_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
185
%%EOF
"""


def test_upload_valid_text_lease(client):
    """Verifies that a valid plain text lease is processed and terms are extracted."""
    text_content = (
        "Residential Lease Agreement.\n"
        "The tenant agrees to pay monthly rent of Rs. 32000.\n"
        "Security deposit amount is Rs. 64000.\n"
        "No pets of any species allowed on the premises under penalty of forfeiture.\n"
    )
    files = {"file": ("my_lease.txt", io.BytesIO(text_content.encode("utf-8")), "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 200
    data = res.json()["audit"]
    assert data["extracted_monthly_rent_inr"] == 32000.0
    assert data["extracted_security_deposit_inr"] == 64000.0
    assert len(data["flagged_clauses_for_review"]) > 0


def test_upload_valid_markdown_lease(client):
    """Verifies that a markdown (.md) lease is accepted and analyzed."""
    md_content = "# Rental Agreement\nMonthly base rent is Rs. 28000. Security deposit Rs. 56000."
    files = {"file": ("lease.md", io.BytesIO(md_content.encode("utf-8")), "text/markdown")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 200
    data = res.json()["audit"]
    assert data["extracted_monthly_rent_inr"] == 28000.0


def test_upload_oversized_file_returns_413(client):
    """Verifies that an upload exceeding 5 MB is aborted with 413 Payload Too Large."""
    # 5.2 MB of dummy data
    oversized_data = b"A" * (5 * 1024 * 1024 + 200 * 1024)
    files = {"file": ("huge_lease.txt", io.BytesIO(oversized_data), "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 413
    assert "5 MB" in res.json()["detail"]


def test_upload_empty_file_returns_400(client):
    """Verifies that a 0-byte file returns a 400 Bad Request."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_upload_unsupported_extension_returns_400(client):
    """Verifies that an unsupported file extension returns 400."""
    files = {"file": ("malicious.exe", io.BytesIO(b"binary executable data"), "application/octet-stream")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_upload_invalid_pdf_header_returns_400(client):
    """Verifies that a file named .pdf without %PDF signature returns 400."""
    files = {"file": ("fake.pdf", io.BytesIO(b"This is not a real PDF file!"), "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    assert "Header signature does not match" in res.json()["detail"]


def test_upload_valid_pdf_extracts_text_and_clauses(client):
    """Verifies genuine PDF text extraction using pypdf."""
    files = {"file": ("signed_agreement.pdf", io.BytesIO(VALID_TEXT_PDF_BYTES), "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 200
    data = res.json()["audit"]
    assert data["extracted_monthly_rent_inr"] == 35000.0
    assert data["extracted_security_deposit_inr"] == 70000.0
    assert any(c["risk_level"] == "HIGH" for c in data["flagged_clauses_for_review"])


def test_upload_blank_pdf_returns_422(client):
    """Verifies that a textless or scanned PDF without extractable text returns 422."""
    files = {"file": ("scanned_blank.pdf", io.BytesIO(BLANK_PDF_BYTES), "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 422
    assert "No readable text found" in res.json()["detail"]
