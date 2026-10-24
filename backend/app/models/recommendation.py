import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum as SAEnum, Text, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.forecast import RiskSeverity

class RecommendationActionType(str, enum.Enum):
    INVOICE_FOLLOWUP = "INVOICE_FOLLOWUP"
    EXPENSE_DEFERRAL = "EXPENSE_DEFERRAL"
    RESERVE_REPLENISHMENT = "RESERVE_REPLENISHMENT"
    FINANCING_ASSESSMENT = "FINANCING_ASSESSMENT"
    DISCRETIONARY_REDUCTION = "DISCRETIONARY_REDUCTION"

class RecommendationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"

class FinancialRecommendation(Base):
    __tablename__ = "financial_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    action_type = Column(SAEnum(RecommendationActionType), nullable=False)
    severity = Column(SAEnum(RiskSeverity), default=RiskSeverity.MEDIUM, nullable=False)
    estimated_impact = Column(Numeric(15, 2), nullable=False, default=0.0)
    reasoning = Column(Text, nullable=False)
    supporting_records = Column(JSON, nullable=True)  # List of relevant IDs (invoices, expenses, etc.)
    assumptions = Column(Text, nullable=True)
    disadvantages = Column(Text, nullable=True)
    status = Column(SAEnum(RecommendationStatus), default=RecommendationStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", backref="financial_recommendations")
