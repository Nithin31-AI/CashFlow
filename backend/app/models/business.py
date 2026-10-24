import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class Business(Base):
    __tablename__ = "businesses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)  # India-first default INR
    country = Column(String(10), default="IN", nullable=False)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    minimum_cash_reserve = Column(Numeric(15, 2), default=100000.00, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    memberships = relationship("BusinessMembership", back_populates="business", cascade="all, delete-orphan")
    accounts = relationship("FinancialAccount", back_populates="business", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="business", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="business", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="business", cascade="all, delete-orphan")
    records = relationship("ImportedRecord", back_populates="business", cascade="all, delete-orphan")
    
    # Stage 2 relationships
    transactions = relationship("Transaction", back_populates="business", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="business", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="business", cascade="all, delete-orphan")
    reconciliations = relationship("ReconciliationRecord", back_populates="business", cascade="all, delete-orphan")
    forecasts = relationship("ForecastRun", back_populates="business", cascade="all, delete-orphan")
    risks = relationship("RiskAssessment", back_populates="business", cascade="all, delete-orphan")
    anomalies = relationship("ExpenseAnomaly", back_populates="business", cascade="all, delete-orphan")
