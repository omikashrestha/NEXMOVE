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
