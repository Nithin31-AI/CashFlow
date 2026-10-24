import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Date, Numeric, ForeignKey, Enum as SAEnum, Integer, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class GoalType(str, enum.Enum):
    MINIMUM_RESERVE = "MINIMUM_RESERVE"
    DEBT_REDUCTION = "DEBT_REDUCTION"
    GROWTH_CAPEX = "GROWTH_CAPEX"
    COLLECTION_ACCELERATION = "COLLECTION_ACCELERATION"
    EXPENSE_CAP = "EXPENSE_CAP"

class GoalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACHIEVED = "ACHIEVED"
    AT_RISK = "AT_RISK"
    INACTIVE = "INACTIVE"

class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    goal_type = Column(SAEnum(GoalType), nullable=False, default=GoalType.MINIMUM_RESERVE)
    target_amount = Column(Numeric(15, 2), nullable=False)
    target_date = Column(Date, nullable=True)
    is_hard_constraint = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    status = Column(SAEnum(GoalStatus), default=GoalStatus.ACTIVE, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", backref="financial_goals")
