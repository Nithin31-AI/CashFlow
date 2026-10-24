import re
from typing import List, Dict, Any, Optional, Tuple

FIELD_SYNONYMS = {
    "date": [
        "date", "transaction_date", "txn_date", "value_date", "posting_date", 
        "trans_date", "booking_date", "trade_date"
    ],
    "description": [
        "description", "narration", "particulars", "memo", "details", 
        "remarks", "payee", "transaction_details", "summary", "notes"
    ],
    "reference": [
        "reference", "ref_no", "ref", "cheque_no", "chq_no", "utr", 
        "transaction_id", "txn_id", "reference_number", "trans_id", "doc_no"
    ],
    "debit": [
        "debit", "dr", "withdrawal", "withdrawals", "outflow", "spent", 
        "paid_out", "debit_amount", "dr_amount"
    ],
    "credit": [
        "credit", "cr", "deposit", "deposits", "inflow", "received", 
        "paid_in", "credit_amount", "cr_amount"
    ],
    "amount": [
        "amount", "net_amount", "transaction_amount", "txn_amount", 
        "total", "total_amount", "sum"
    ],
    "currency": [
        "currency", "curr", "ccy", "iso_currency"
    ],
}

def normalize_header(header: str) -> str:
    """Normalizes header string for comparison: removes punctuation, lowercases."""
    return re.sub(r"[^a-z0-9]", "_", header.lower()).strip("_")

def detect_column_mappings(
    headers: List[str], 
    sample_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, Optional[str]], Optional[str]]:
    """
    Intelligently maps raw file headers to standardized cashFlow fields.
    Returns: (suggested_mappings, suggested_date_format)
    """
    mappings: Dict[str, Optional[str]] = {
        "date": None,
        "description": None,
        "reference": None,
        "debit": None,
        "credit": None,
        "amount": None,
        "currency": None,
    }

    normalized_headers = [(h, normalize_header(h)) for h in headers]

    # Find matches based on synonyms
    used_headers = set()
    for field, synonyms in FIELD_SYNONYMS.items():
        best_match = None
        for orig, norm in normalized_headers:
            if orig in used_headers:
                continue
            # Exact match
            if norm in synonyms:
                best_match = orig
                break
            # Partial substring match
            if any(syn in norm for syn in synonyms):
                best_match = orig
                break

        if best_match:
            mappings[field] = best_match
            used_headers.add(best_match)

    # Detect date format from sample rows
    suggested_date_format = "%d/%m/%Y"  # Default India-first
    if mappings["date"] and sample_rows:
        date_col = mappings["date"]
        sample_values = [str(r.get(date_col, "")).strip() for r in sample_rows if r.get(date_col)]
        for val in sample_values:
            if re.match(r"^\d{4}-\d{2}-\d{2}", val):
                suggested_date_format = "%Y-%m-%d"
                break
            elif re.match(r"^\d{2}/\d{2}/\d{4}", val):
                parts = val.split("/")
                try:
                    if int(parts[0]) > 12:
                        suggested_date_format = "%d/%m/%Y"
                    elif int(parts[1]) > 12:
                        suggested_date_format = "%m/%d/%Y"
                    else:
                        suggested_date_format = "%d/%m/%Y"
                except Exception:
                    suggested_date_format = "%d/%m/%Y"
                break
            elif re.match(r"^\d{2}-\d{2}-\d{4}", val):
                suggested_date_format = "%d-%m-%Y"
                break
            elif re.match(r"^\d{2}\.\d{2}\.\d{4}", val):
                suggested_date_format = "%d.%m.%Y"
                break

    return mappings, suggested_date_format
