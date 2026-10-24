from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    currency: str = Field(default="INR", max_length=10)
    country: str = Field(default="IN", max_length=10)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)

class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    currency: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)

class BusinessOut(BaseModel):
    id: str
    name: str
    slug: str
    currency: str
    country: str
    timezone: str
    created_at: datetime
    role: Optional[str] = None  # Role of current authenticated user

    class Config:
        from_attributes = True
