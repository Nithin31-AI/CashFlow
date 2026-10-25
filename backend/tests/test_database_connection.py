import pytest
from app.db.session import normalize_database_url, check_database_health
from app.core.config import Settings

def test_health_check_endpoint(client):
    """Verify that /api/v1/health executes SELECT NOW() and returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"]["status"] == "healthy"
    assert "server_time" in data["database"]
    assert data["database"]["server_time"] is not None

def test_root_health_check_endpoint(client):
    """Verify that root /health alias functions identically."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "healthy"

def test_database_health_check_function(db):
    """Verify check_database_health returns expected metadata with active session."""
    health = check_database_health(db)
    assert health["status"] == "healthy"
    assert "database" in health
    assert "server_time" in health
    assert health["server_time"] is not None

def test_normalize_database_url():
    """Verify URL normalization handles legacy postgres and explicit psycopg2 dialect."""
    # postgres:// scheme
    legacy_url = "postgres://usr:pwd@dbhost:5432/cashflow_db"
    normalized = normalize_database_url(legacy_url)
    assert normalized.startswith("postgresql+psycopg2://usr:pwd@dbhost:5432/cashflow_db")

    # postgresql:// scheme
    standard_url = "postgresql://usr:pwd@dbhost:5432/cashflow_db?sslmode=require"
    normalized = normalize_database_url(standard_url)
    assert normalized.startswith("postgresql+psycopg2://usr:pwd@dbhost:5432/cashflow_db?sslmode=require")

    # sqlite scheme preserved
    sqlite_url = "sqlite:///./cashflow.db"
    assert normalize_database_url(sqlite_url) == sqlite_url

def test_database_url_validation_error_on_empty():
    """Verify that missing/empty DATABASE_URL raises informative configuration error."""
    with pytest.raises(ValueError) as exc_info:
        Settings(DATABASE_URL="")
    err_msg = str(exc_info.value)
    assert "DATABASE_URL environment variable is missing or empty" in err_msg
    assert "postgresql://username:password@hostname/database?sslmode=require" in err_msg
