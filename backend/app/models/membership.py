import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class MembershipRole(str, enum.Enum):
    OWNER = "OWNER"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    VIEWER = "VIEWER"

class BusinessMembership(Base):
    __tablename__ = "business_memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(MembershipRole), nullable=False, default=MembershipRole.VIEWER)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("business_id", "user_id", name="uq_business_user_membership"),
    )
