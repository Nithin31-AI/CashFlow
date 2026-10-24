from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.membership import MembershipRole
from app.schemas.auth import UserOut

class MembershipInvite(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.VIEWER

class MembershipUpdate(BaseModel):
    role: MembershipRole

class MembershipOut(BaseModel):
    id: str
    business_id: str
    user_id: str
    role: MembershipRole
    created_at: datetime
    user: UserOut

    class Config:
        from_attributes = True
