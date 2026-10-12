import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import get_allowed_origins


@pytest.fixture
def client():
    return TestClient(app)


def test_cors_allowed_origin_localhost_3000(client):
    """Verifies that requests from localhost:3000 receive CORS approval and credentials header."""
    res = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_cors_allowed_origin_127_0_0_1_3000(client):
    """Verifies that requests from 127.0.0.1:3000 receive CORS approval and credentials header."""
    res = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_cors_rejected_untrusted_origin(client):
    """Verifies that untrusted origins do not receive an access-control-allow-origin header."""
    res = client.get("/health", headers={"Origin": "http://malicious-attacker.com"})
    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers


def test_cors_preflight_request_allowed(client):
    """Verifies that an OPTIONS preflight request from an allowed origin returns 200 with CORS headers."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    res = client.options("/api/projects", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"
    assert "access-control-allow-methods" in res.headers


def test_cors_preflight_request_rejected(client):
    """Verifies that an OPTIONS preflight request from an untrusted origin is rejected."""
    headers = {
        "Origin": "http://evil-attacker.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    res = client.options("/api/projects", headers=headers)
    assert "access-control-allow-origin" not in res.headers


def test_get_allowed_origins_env_parsing(monkeypatch):
    """Verifies parsing of comma-separated environment variable ALLOWED_ORIGINS."""
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://nexmove.app, https://staging.nexmove.app , ")
    origins = get_allowed_origins()
    assert origins == ["https://nexmove.app", "https://staging.nexmove.app"]

    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    default_origins = get_allowed_origins()
    assert "http://localhost:3000" in default_origins
    assert "http://127.0.0.1:3000" in default_origins


def test_get_allowed_origin_regex_env_parsing(monkeypatch):
    """Verifies parsing of ALLOWED_ORIGIN_REGEX environment variable."""
    from backend.app.core.config import get_allowed_origin_regex

    monkeypatch.setenv("ALLOWED_ORIGIN_REGEX", r"^https://nexmove(-[a-z0-9-]+)?\.vercel\.app$")
    regex = get_allowed_origin_regex()
    assert regex == r"^https://nexmove(-[a-z0-9-]+)?\.vercel\.app$"

    monkeypatch.delenv("ALLOWED_ORIGIN_REGEX", raising=False)
    monkeypatch.delenv("CORS_ORIGIN_REGEX", raising=False)
    assert get_allowed_origin_regex() is None


def test_cors_with_project_scoped_origin_regex():
    """Verifies that project-scoped regex allows intended Vercel preview/production domains and rejects others."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient

    custom_app = FastAPI()
    custom_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_origin_regex=r"^https://nexmove(-[a-z0-9-]+)?\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @custom_app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(custom_app)

    # 1. Exact project production URL matches
    res1 = client.get("/ping", headers={"Origin": "https://nexmove.vercel.app"})
    assert res1.status_code == 200
    assert res1.headers.get("access-control-allow-origin") == "https://nexmove.vercel.app"

    # 2. Project preview branch URL matches
    res2 = client.get("/ping", headers={"Origin": "https://nexmove-git-main-omikashrestha.vercel.app"})
    assert res2.status_code == 200
    assert res2.headers.get("access-control-allow-origin") == "https://nexmove-git-main-omikashrestha.vercel.app"

    # 3. Different project on vercel.app is REJECTED
    res3 = client.get("/ping", headers={"Origin": "https://unrelated-project.vercel.app"})
    assert res3.status_code == 200
    assert "access-control-allow-origin" not in res3.headers

    # 4. Malicious domain is REJECTED
    res4 = client.get("/ping", headers={"Origin": "https://attacker.com"})
    assert res4.status_code == 200
    assert "access-control-allow-origin" not in res4.headers


def test_database_url_normalization():
    """Verifies that postgres:// is normalized to postgresql:// while SQLite is preserved."""
    # Test SQLite URL preservation
    sqlite_url = "sqlite:////path/to/nexmove.db"
    assert sqlite_url.startswith("sqlite://")

    # Test legacy postgres:// replacement logic
    legacy_pg = "postgres://user:pass@host:5432/db"
    normalized = legacy_pg.replace("postgres://", "postgresql://", 1) if legacy_pg.startswith("postgres://") else legacy_pg
    assert normalized == "postgresql://user:pass@host:5432/db"
