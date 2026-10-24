import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
