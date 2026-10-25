import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("cashflow.db")

def normalize_database_url(url: str) -> str:
    """Normalize database connection URL to ensure compatibility with SQLAlchemy 2.0 & psycopg2."""
    if not url:
        return url
    trimmed = url.strip()
    if trimmed.startswith("postgres://"):
        return trimmed.replace("postgres://", "postgresql+psycopg2://", 1)
    elif trimmed.startswith("postgresql://") and not trimmed.startswith("postgresql+"):
        return trimmed.replace("postgresql://", "postgresql+psycopg2://", 1)
    return trimmed

database_url = normalize_database_url(settings.DATABASE_URL)

# Configure connection arguments and connection pool based on dialect
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if "sqlite" in database_url:
    connect_args["check_same_thread"] = False
else:
    # PostgreSQL configuration
    # Enable connection pooling and recycling to prevent stale connections
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
    })
    # If sslmode is not explicitly specified in the query parameters and host is not local,
    # default to sslmode=require while preserving proper certificate validation.
    if "sslmode" not in database_url.lower() and not any(h in database_url for h in ["localhost", "127.0.0.1", "@db:"]):
        connect_args["sslmode"] = "require"

engine = create_engine(
    database_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_health(db: Optional[Session] = None) -> dict:
    """
    Executes 'SELECT NOW();' (or dialect equivalent) to verify database connectivity.
    Returns health status, database dialect, and server timestamp without exposing sensitive credentials.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        bind = db.get_bind() if hasattr(db, "get_bind") else engine
        dialect_name = bind.dialect.name
        query = text("SELECT datetime('now')") if dialect_name == "sqlite" else text("SELECT NOW()")
        server_time = db.execute(query).scalar()
        return {
            "status": "healthy",
            "database": dialect_name,
            "server_time": str(server_time),
        }
    except Exception as exc:
        logger.error("Database health-check query failed: %s", type(exc).__name__)
        backend_name = "unknown"
        try:
            backend_name = engine.url.get_backend_name()
        except Exception:
            pass
        return {
            "status": "unhealthy",
            "database": backend_name,
            "error": "Database connection unavailable",
        }
    finally:
        if close_db:
            db.close()

def dispose_engine():
    """Cleanly disposes connection pool on application shutdown."""
    logger.info("Closing database connection pool...")
    engine.dispose()
    logger.info("Database connection pool closed successfully.")
