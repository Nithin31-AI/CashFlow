import csv
import io
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException, status

def detect_encoding(file_bytes: bytes) -> str:
    """Detects encoding between utf-8-sig (with BOM), utf-8, and latin-1."""
    if file_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        file_bytes.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"

def parse_csv_file(file_path: str, max_rows: int = 10000) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parses a CSV file with automatic delimiter and encoding detection.
    Returns: (headers, rows_as_dicts)
    """
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        encoding = detect_encoding(raw_bytes)
        text_content = raw_bytes.decode(encoding)
        
        # Sniff delimiter from first few lines
        sample = "\n".join(text_content.splitlines()[:10])
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)
        
        rows: List[List[str]] = []
        for line in reader:
            # Skip empty lines
            if not line or all(cell.strip() == "" for cell in line):
                continue
            rows.append([cell.strip() for cell in line])

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded CSV file is empty or contains no readable rows."
            )

        headers = rows[0]
        # Clean headers: remove BOM or empty strings
        cleaned_headers = []
        for idx, h in enumerate(headers):
            h_clean = h.strip()
            if not h_clean:
                h_clean = f"Column_{idx + 1}"
            cleaned_headers.append(h_clean)

        data_rows: List[Dict[str, Any]] = []
        for r_idx, row in enumerate(rows[1:], start=2):
            if r_idx > max_rows:
                break
            # Skip empty rows
            if not row or all(c.strip() == "" for c in row):
                continue
            row_dict = {}
            for col_idx, h in enumerate(cleaned_headers):
                val = row[col_idx] if col_idx < len(row) else ""
                row_dict[h] = val
            data_rows.append(row_dict)

        return cleaned_headers, data_rows

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(e)}"
        )
