import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "cashFlow"
    TAGLINE: str = "PLAN • FORECAST • GROW"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Dev
    ENVIRONMENT: str = "development"
    DEV_MODE: bool = True
    
    # Database
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Union[str, None]) -> str:
        val = str(v).strip() if v else ""
        if not val:
            raise ValueError(
                "DATABASE_URL environment variable is missing or empty. "
                "Please configure DATABASE_URL in your backend/.env file "
                "(format: postgresql://username:password@hostname/database?sslmode=require)."
            )
        return val
    
    # Security & Tokens
    SECRET_KEY: str = "cashflow-stage1-super-secure-jwt-secret-key-change-in-production-min32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Union[str, None] = None
    GOOGLE_CLIENT_SECRET: Union[str, None] = None
    
    # Upload storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xls", ".xlsx", ".pdf", ".png", ".jpg", ".jpeg"]
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://[::1]:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                return ["*"]
        return v

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
