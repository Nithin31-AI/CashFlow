import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Date, DateTime, JSON, Text
from app.db.session import Base

class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    evaluation_date = Column(Date, default=lambda: date.today(), nullable=False)
    metrics = Column(JSON, nullable=False)  # e.g., {"mape": 0.082, "rmse": 4500.0, "shortage_recall": 0.94}
    baseline_comparison = Column(JSON, nullable=True)  # vs naive moving average
    status = Column(String(50), default="ACTIVE", nullable=False)
    limitations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
