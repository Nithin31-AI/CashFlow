import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.session import engine, Base, check_database_health, dispose_engine
import app.models  # Ensure all models are registered
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cashflow")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s backend services...", settings.PROJECT_NAME)
    safe_db_url = engine.url.render_as_string(hide_password=True)
    logger.info("Database connection target: %s", safe_db_url)
    
    try:
        # Perform health check query (SELECT NOW()) during startup
        health = check_database_health()
        if health.get("status") == "healthy":
            logger.info("Database connectivity verified successfully (server time: %s).", health.get("server_time"))
        else:
            logger.warning("Database connectivity degraded during startup: %s", health.get("error"))
        
        # Ensure database schema exists
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified.")
    except Exception as exc:
        logger.error("Database connection initialization failure: %s", type(exc).__name__)
        logger.warning("Application starting in degraded mode; database operations may fail until connectivity is restored.")

    yield

    logger.info("Shutting down %s backend services...", settings.PROJECT_NAME)
    dispose_engine()

app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    description=f"{settings.PROJECT_NAME} - {settings.TAGLINE}. Production-oriented financial intelligence SaaS platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """
    Database and application health-check endpoint.
    Executes 'SELECT NOW();' to confirm active PostgreSQL database connectivity.
    """
    db_health = check_database_health()
    is_db_healthy = db_health.get("status") == "healthy"
    
    payload = {
        "status": "healthy" if is_db_healthy else "degraded",
        "app": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "environment": settings.ENVIRONMENT,
        "database": db_health,
    }
    status_code = 200 if is_db_healthy else 503
    return JSONResponse(status_code=status_code, content=payload)

# Include v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
