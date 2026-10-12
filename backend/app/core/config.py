from pathlib import Path
from typing import List
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "sample_benchmarks"

_raw_db_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/nexmove.db")
# Safely normalize legacy postgres:// prefix to postgresql:// if an external PostgreSQL URL is provided
if _raw_db_url.startswith("postgres://"):
    _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
DATABASE_URL = _raw_db_url

DEFAULT_CURRENCY = "INR"
DEFAULT_CURRENCY_SYMBOL = "₹"


def get_allowed_origins() -> List[str]:
    """Resolves CORS origins from ALLOWED_ORIGINS/CORS_ORIGINS or safe development defaults."""
    raw = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5678",
        "http://127.0.0.1:5678",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://testserver",
    ]
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        return origins if origins else default_origins
    return default_origins


def get_allowed_origin_regex() -> str | None:
    """
    Resolves an optional origin regex for project-scoped preview deployments.
    Defaults to None unless ALLOWED_ORIGIN_REGEX is explicitly configured.
    """
    raw = os.getenv("ALLOWED_ORIGIN_REGEX") or os.getenv("CORS_ORIGIN_REGEX")
    if raw and raw.strip():
        return raw.strip()
    return None


ALLOWED_ORIGINS: List[str] = get_allowed_origins()
ALLOWED_ORIGIN_REGEX: str | None = get_allowed_origin_regex()
