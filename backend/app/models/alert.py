import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Integer, Text, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class AlertCategory(str, enum.Enum):
    RESERVE_BREACH = "RESERVE_BREACH"
    MAJOR_OBLIGATION = "MAJOR_OBLIGATION"
    OVERDUE_INVOICE = "OVERDUE_INVOICE"
    UNUSUAL_EXPENSE = "UNUSUAL_EXPENSE"
    FORECAST_DROP = "FORECAST_DROP"
    STALE_DATA = "STALE_DATA"

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(SAEnum(AlertCategory), nullable=False)
    threshold_value = Column(Numeric(15, 2), nullable=False, default=0.0)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    suppression_window_hours = Column(Integer, default=24, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", backref="alert_rules")

class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(36), ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="GENERAL")
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False, index=True)
    financial_evidence = Column(JSON, nullable=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    business = relationship("Business", backref="alert_events")
    rule = relationship("AlertRule", backref="triggered_events")
