import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False, default=30)
    num_paths = Column(Integer, nullable=False, default=1000)
    seed = Column(Integer, nullable=True)
    starting_cash = Column(Numeric(15, 2), nullable=False)
    min_projected_cash = Column(Numeric(15, 2), nullable=False)
    max_projected_cash = Column(Numeric(15, 2), nullable=False)
    p10_ending_cash = Column(Numeric(15, 2), nullable=False)
    p50_ending_cash = Column(Numeric(15, 2), nullable=False)
    p90_ending_cash = Column(Numeric(15, 2), nullable=False)
    reserve_breach_probability = Column(Numeric(5, 4), nullable=False, default=0.0)
    expected_shortfall = Column(Numeric(15, 2), nullable=False, default=0.0)
    potential_shortage_day = Column(Integer, nullable=True)
    assumptions = Column(JSON, nullable=False)
    percentile_paths = Column(JSON, nullable=False)
    model_version = Column(String(50), default="monte-carlo-v1.0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", backref="simulation_runs")
