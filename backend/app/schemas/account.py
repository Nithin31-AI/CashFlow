from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.account import AccountType

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    account_type: AccountType = AccountType.BANK
    account_number_mask: Optional[str] = Field(None, max_length=50)
    currency: str = Field(default="INR", max_length=10)
    institution_name: Optional[str] = Field(None, max_length=100)

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    account_number_mask: Optional[str] = None
    currency: Optional[str] = None
    institution_name: Optional[str] = None
    is_active: Optional[bool] = None

class AccountOut(BaseModel):
    id: str
    business_id: str
    name: str
    account_type: AccountType
    account_number_mask: Optional[str] = None
    currency: str
    institution_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
