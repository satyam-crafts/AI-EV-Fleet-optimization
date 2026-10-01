"""Test health check endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_health_check():
    """Verify that root /health returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_v1_health_check():
    """Verify that /api/v1/health returns 200 and version info."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "v1"
