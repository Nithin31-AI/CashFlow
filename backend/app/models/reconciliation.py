import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class ReconciliationStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class MatchType(str, enum.Enum):
    EXACT = "EXACT"
    PROBABLE = "PROBABLE"
    AMBIGUOUS = "AMBIGUOUS"
    MANUAL = "MANUAL"

class MatchedEntityType(str, enum.Enum):
    INVOICE = "INVOICE"
    PAYMENT = "PAYMENT"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"

class ReconciliationRecord(Base):
    """
    Intelligent reconciliation records linking ledger transactions to invoices or payments.
    Includes explainable matching signals, confidence scores, and mandatory human review gates.
    """
    __tablename__ = "reconciliations"
    __table_args__ = (
        UniqueConstraint("transaction_id", "matched_entity_type", "matched_entity_id", name="uq_reconciliation_match"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    matched_entity_type = Column(SQLEnum(MatchedEntityType), default=MatchedEntityType.INVOICE, nullable=False, index=True)
    matched_entity_id = Column(String(36), nullable=False, index=True)
    
    confidence_score = Column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    match_type = Column(SQLEnum(MatchType), default=MatchType.PROBABLE, nullable=False)
    status = Column(SQLEnum(ReconciliationStatus), default=ReconciliationStatus.PENDING_REVIEW, nullable=False, index=True)
    
    matched_amount = Column(Numeric(15, 2), nullable=False)
    explanation = Column(Text, nullable=False)
    
    reviewed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="reconciliations")
    transaction = relationship("Transaction", back_populates="reconciliation")
    reviewer = relationship("User")
