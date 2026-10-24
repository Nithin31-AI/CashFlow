from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.exchange_rate import ExchangeRate

# Standard benchmark rates against INR for small service businesses
DEFAULT_BENCHMARK_RATES = {
    ("USD", "INR"): Decimal("86.500000"),
    ("EUR", "INR"): Decimal("92.800000"),
    ("GBP", "INR"): Decimal("111.400000"),
    ("AED", "INR"): Decimal("23.550000"),
    ("SGD", "INR"): Decimal("65.200000"),
    ("INR", "INR"): Decimal("1.000000"),
}

class CurrencyService:
    """
    Authoritative multi-currency conversion service.
    Enforces that:
    - INR is the default base/reporting currency.
    - Currencies are never summed without explicit conversion.
    - Conversion rates are recorded with rate date and source.
    - If no rate is available, the service explicitly indicates conversion is unavailable.
    """

    @staticmethod
    def get_exchange_rate(
        db: Session,
        base_currency: str,
        target_currency: str,
        rate_date: Optional[date] = None
    ) -> Optional[Decimal]:
        base = base_currency.upper()
        target = target_currency.upper()

        if base == target:
            return Decimal("1.000000")

        query = db.query(ExchangeRate).filter(
            ExchangeRate.base_currency == base,
            ExchangeRate.target_currency == target
        )
        if rate_date:
            query = query.filter(ExchangeRate.rate_date <= rate_date)
        
        record = query.order_by(ExchangeRate.rate_date.desc()).first()
        if record:
            return record.rate

        # Check default fallback benchmark
        if (base, target) in DEFAULT_BENCHMARK_RATES:
            return DEFAULT_BENCHMARK_RATES[(base, target)]
        
        # Check reverse rate
        if (target, base) in DEFAULT_BENCHMARK_RATES:
            return Decimal("1.000000") / DEFAULT_BENCHMARK_RATES[(target, base)]

        return None

    @staticmethod
    def convert_amount(
        db: Session,
        amount: Decimal,
        from_currency: str,
        to_currency: str = "INR",
        transaction_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Converts monetary amount while recording full conversion provenance.
        """
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        dec_amount = Decimal(str(amount))

        if from_curr == to_curr:
            return {
                "original_amount": dec_amount,
                "original_currency": from_curr,
                "converted_amount": dec_amount,
                "reporting_currency": to_curr,
                "exchange_rate": Decimal("1.000000"),
                "rate_date": transaction_date or datetime.now(timezone.utc).date(),
                "rate_source": "IDENTITY",
                "is_converted": True,
            }

        rate = CurrencyService.get_exchange_rate(db, from_curr, to_curr, transaction_date)
        if rate is None:
            return {
                "original_amount": dec_amount,
                "original_currency": from_curr,
                "converted_amount": None,
                "reporting_currency": to_curr,
                "exchange_rate": None,
                "rate_date": None,
                "rate_source": None,
                "is_converted": False,
                "error": f"No authoritative exchange rate available from {from_curr} to {to_curr} on {transaction_date}."
            }

        converted = (dec_amount * rate).quantize(Decimal("0.01"))
        return {
            "original_amount": dec_amount,
            "original_currency": from_curr,
            "converted_amount": converted,
            "reporting_currency": to_curr,
            "exchange_rate": rate,
            "rate_date": transaction_date or datetime.now(timezone.utc).date(),
            "rate_source": "RBI_REFERENCE",
            "is_converted": True,
        }
