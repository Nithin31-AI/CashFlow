import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Integer, Text, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class OptimisationStatus(str, enum.Enum):
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    PARTIALLY_FEASIBLE = "PARTIALLY_FEASIBLE"

class SavedScenario(Base):
    __tablename__ = "saved_scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_baseline = Column(Boolean, default=False, nullable=False)
    parameters = Column(JSON, nullable=False)  # delay_days, collection_rate, expense_adjustment, capex_amount, etc.
    projected_ending_cash = Column(Numeric(15, 2), nullable=False)
    min_cash = Column(Numeric(15, 2), nullable=False)
    shortage_risk_percent = Column(Numeric(5, 2), nullable=False, default=0.0)
    runway_days = Column(Integer, nullable=False, default=90)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", backref="saved_scenarios")
    created_by = relationship("User")

class OptimisationPlan(Base):
    __tablename__ = "optimisation_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id = Column(String(36), ForeignKey("saved_scenarios.id", ondelete="SET NULL"), nullable=True)
    status = Column(SAEnum(OptimisationStatus), nullable=False, default=OptimisationStatus.FEASIBLE)
    objective_value = Column(Numeric(15, 2), nullable=False, default=0.0)
    recommended_actions = Column(JSON, nullable=False)
    trade_offs = Column(Text, nullable=True)
    hard_constraints_satisfied = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", backref="optimisation_plans")
    scenario = relationship("SavedScenario", backref="optimisation_plans")
