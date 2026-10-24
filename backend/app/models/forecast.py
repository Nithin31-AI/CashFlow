import uuid
import enum
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Date, Text, Numeric, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class RiskType(str, enum.Enum):
    CASH_SHORTAGE = "CASH_SHORTAGE"
    PAYMENT_DELAY = "PAYMENT_DELAY"
    EXPENSE_SPIKE = "EXPENSE_SPIKE"

class RiskSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class ForecastRun(Base):
    """
    Historical record of cash-flow forecasts across supported horizons (7d, 30d, 90d, 6m, 12m).
    Strictly records model version, assumptions, and daily projection data.
    """
    __tablename__ = "forecast_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    run_date = Column(Date, nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False)  # 7, 30, 90, 180, 365
    starting_cash = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    
    projected_inflows = Column(Numeric(15, 2), nullable=False)
    projected_outflows = Column(Numeric(15, 2), nullable=False)
    net_change = Column(Numeric(15, 2), nullable=False)
    ending_cash = Column(Numeric(15, 2), nullable=False)
    confidence_lower = Column(Numeric(15, 2), nullable=False)
    confidence_upper = Column(Numeric(15, 2), nullable=False)
    
    model_version = Column(String(50), default="v2.0-baseline-exponential", nullable=False)
    assumptions = Column(JSON, nullable=True)
    daily_projections = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="forecasts")


class RiskAssessment(Base):
    """
    Explainable cash-shortage risks and late payment predictions with contributing factors.
    """
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    risk_type = Column(SQLEnum(RiskType), nullable=False, index=True)
    severity = Column(SQLEnum(RiskSeverity), default=RiskSeverity.MEDIUM, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    potential_date = Column(Date, nullable=True, index=True)
    estimated_shortfall = Column(Numeric(15, 2), nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    recommended_action = Column(Text, nullable=False)
    
    status = Column(SQLEnum(RiskStatus), default=RiskStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="risks")


class ExpenseAnomaly(Base):
    """
    Expense analysis anomaly indicators for human review.
    Clear distinction: flagged for review, not assumed fraudulent.
    """
    __tablename__ = "expense_anomalies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    anomaly_score = Column(Numeric(5, 2), nullable=False)  # 0 to 100
    category = Column(String(100), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    expected_amount_range = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    reviewed = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="anomalies")
