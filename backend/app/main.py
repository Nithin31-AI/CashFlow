import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.session import engine, Base
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
    # Ensure database schema exists
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down %s backend services...", settings.PROJECT_NAME)

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
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "environment": settings.ENVIRONMENT,
    }

# Include v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
