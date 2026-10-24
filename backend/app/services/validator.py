import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple

COMMON_DATE_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d-%b-%Y",
    "%d %B %Y",
]

def clean_amount_str(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "-"):
        return None

    # Check for parentheses indicating negative: (100.50) -> -100.50
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1].strip()

    # Remove currency symbols and formatting commas
    s = re.sub(r"[₹$,€£A-Za-z\s]", "", s)
    if not s:
        return None

    try:
        dec = Decimal(s)
        return -dec if is_negative else dec
    except InvalidOperation:
        raise ValueError(f"Invalid monetary amount: '{val}'")

def parse_date_with_formats(val: Any, preferred_format: Optional[str]) -> date:
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val

    s = str(val).strip()
    if not s:
        raise ValueError("Date value is missing or empty")

    formats_to_try = []
    if preferred_format:
        formats_to_try.append(preferred_format)
    for fmt in COMMON_DATE_FORMATS:
        if fmt not in formats_to_try:
            formats_to_try.append(fmt)

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date()
        except ValueError:
            continue

    raise ValueError(f"Date '{s}' does not match expected format {preferred_format or 'standard date formats'}")

def validate_and_parse_row(
    row_index: int,
    raw_row: Dict[str, Any],
    mappings: Dict[str, Optional[str]],
    preferred_date_format: Optional[str] = "%d/%m/%Y",
    default_currency: str = "INR"
) -> Tuple[bool, List[str], List[str], Optional[Dict[str, Any]]]:
    """
    Validates a single row against mapped columns.
    Returns: (is_valid, errors_list, warnings_list, parsed_dict)
    """
    errors: List[str] = []
    warnings: List[str] = []

    date_col = mappings.get("date")
    desc_col = mappings.get("description")
    ref_col = mappings.get("reference")
    debit_col = mappings.get("debit")
    credit_col = mappings.get("credit")
    amount_col = mappings.get("amount")
    curr_col = mappings.get("currency")

    # 1. Date Validation
    parsed_date = None
    if not date_col or date_col not in raw_row:
        errors.append("Transaction date column is not mapped or missing.")
    else:
        raw_date = raw_row[date_col]
        try:
            parsed_date = parse_date_with_formats(raw_date, preferred_date_format)
        except ValueError as e:
            errors.append(str(e))

    # 2. Description Validation
    parsed_desc = ""
    if not desc_col or desc_col not in raw_row:
        errors.append("Description column is not mapped or missing.")
    else:
        parsed_desc = str(raw_row[desc_col]).strip()
        if not parsed_desc:
            errors.append("Description cannot be empty.")

    # 3. Amount / Debit / Credit Validation
    net_amount: Optional[Decimal] = None
    parsed_debit: Optional[Decimal] = None
    parsed_credit: Optional[Decimal] = None

    if debit_col and credit_col:
        raw_debit = raw_row.get(debit_col)
        raw_credit = raw_row.get(credit_col)

        try:
            parsed_debit = clean_amount_str(raw_debit)
        except ValueError as e:
            errors.append(f"Invalid debit amount in column '{debit_col}': {str(e)}")

        try:
            parsed_credit = clean_amount_str(raw_credit)
        except ValueError as e:
            errors.append(f"Invalid credit amount in column '{credit_col}': {str(e)}")

        if parsed_debit is None and parsed_credit is None:
            errors.append("Both debit and credit amounts are blank or zero.")
        else:
            dr = parsed_debit or Decimal("0.00")
            cr = parsed_credit or Decimal("0.00")
            net_amount = cr - dr
    elif amount_col:
        raw_amt = raw_row.get(amount_col)
        try:
            net_amount = clean_amount_str(raw_amt)
            if net_amount is None:
                errors.append(f"Amount in column '{amount_col}' is missing.")
            else:
                if net_amount < 0:
                    parsed_debit = abs(net_amount)
                else:
                    parsed_credit = net_amount
        except ValueError as e:
            errors.append(f"Invalid amount in column '{amount_col}': {str(e)}")
    else:
        errors.append("Neither an amount column nor debit/credit columns are mapped.")

    # 4. Reference Number
    parsed_ref = None
    if ref_col and ref_col in raw_row:
        ref_val = str(raw_row[ref_col]).strip()
        if ref_val and ref_val.lower() not in ("nan", "none", "null", "-"):
            parsed_ref = ref_val

    # 5. Currency
    currency = default_currency
    if curr_col and curr_col in raw_row:
        c_val = str(raw_row[curr_col]).strip().upper()
        if c_val and len(c_val) == 3:
            currency = c_val

    is_valid = len(errors) == 0

    parsed_record = None
    if is_valid and parsed_date and net_amount is not None:
        parsed_record = {
            "row_index": row_index,
            "transaction_date": parsed_date.isoformat(),
            "description": parsed_desc,
            "reference_number": parsed_ref,
            "debit": float(parsed_debit) if parsed_debit is not None else None,
            "credit": float(parsed_credit) if parsed_credit is not None else None,
            "amount": float(net_amount),
            "currency": currency,
        }

    return is_valid, errors, warnings, parsed_record

def validate_all_rows(
    rows: List[Dict[str, Any]],
    mappings: Dict[str, Optional[str]],
    preferred_date_format: Optional[str] = "%d/%m/%Y",
    default_currency: str = "INR"
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Validates an entire dataset against mappings.
    Returns: (valid_count, invalid_count, validation_results)
    """
    valid_count = 0
    invalid_count = 0
    results = []

    for idx, raw_row in enumerate(rows, start=1):
        is_valid, errors, warnings, parsed = validate_and_parse_row(
            row_index=idx,
            raw_row=raw_row,
            mappings=mappings,
            preferred_date_format=preferred_date_format,
            default_currency=default_currency
        )
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

        results.append({
            "row_index": idx,
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "parsed_data": parsed,
            "raw_data": raw_row,
        })

    return valid_count, invalid_count, results
