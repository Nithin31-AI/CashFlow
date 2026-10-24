from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db,
    require_viewer_or_higher,
)
from app.models.membership import BusinessMembership
from app.services.currency_service import CurrencyService, DEFAULT_BENCHMARK_RATES

router = APIRouter()

class ConversionRequest(BaseModel):
    amount: Decimal
    from_currency: str
    to_currency: str = "INR"
    transaction_date: Optional[date] = None

@router.get("/{business_id}/currencies/rates")
def list_exchange_rates(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    rates = {}
    for (base, target), rate in DEFAULT_BENCHMARK_RATES.items():
        if base != target:
            rates[f"{base}_{target}"] = float(rate)
    return {
        "reporting_currency": "INR",
        "benchmark_rates": rates,
        "source": "RBI_REFERENCE"
    }

@router.post("/{business_id}/currencies/convert")
def convert_currency(
    business_id: str,
    payload: ConversionRequest,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    res = CurrencyService.convert_amount(
        db=db,
        amount=payload.amount,
        from_currency=payload.from_currency,
        to_currency=payload.to_currency,
        transaction_date=payload.transaction_date
    )
    if not res["is_converted"]:
        raise HTTPException(status_code=400, detail=res.get("error", "Currency conversion failed."))
    
    return {
        "original_amount": float(res["original_amount"]),
        "original_currency": res["original_currency"],
        "converted_amount": float(res["converted_amount"]),
        "reporting_currency": res["reporting_currency"],
        "exchange_rate": float(res["exchange_rate"]),
        "rate_date": res["rate_date"].isoformat() if res["rate_date"] else None,
        "rate_source": res["rate_source"],
    }
