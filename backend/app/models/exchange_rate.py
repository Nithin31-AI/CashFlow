import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Numeric, Date, DateTime, UniqueConstraint
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class ExchangeRate(Base):
    """
    Exchange rate lookup table for authoritative multi-currency conversions.
    Preserves original currency, target reporting currency, exchange rate,
    effective date, and reference source.
    """
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint("base_currency", "target_currency", "rate_date", name="uq_exchange_rate_date"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    base_currency = Column(String(10), nullable=False, index=True)   # e.g., 'USD'
    target_currency = Column(String(10), nullable=False, index=True) # e.g., 'INR'
    rate = Column(Numeric(18, 6), nullable=False)                    # e.g., 86.500000
    rate_date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False, index=True)
    source = Column(String(100), default="RBI_REFERENCE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
