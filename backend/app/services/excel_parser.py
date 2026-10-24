import os
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException, status
import openpyxl

def parse_excel_file(file_path: str, max_rows: int = 10000) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parses an Excel file (.xlsx or .xls) safely.
    Returns: (headers, rows_as_dicts)
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".xlsx":
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
            sheet = wb.active
            if not sheet:
                raise HTTPException(status_code=400, detail="Excel workbook has no active sheet.")

            rows_iter = sheet.iter_rows(values_only=True)
            headers = None
            data_rows: List[Dict[str, Any]] = []

            for row in rows_iter:
                # Skip leading completely empty rows before headers
                if headers is None:
                    if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                        continue
                    headers = [str(c).strip() if c is not None else f"Column_{i+1}" for i, c in enumerate(row)]
                    continue

                # Skip completely empty rows
                if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                    continue

                row_dict = {}
                for idx, h in enumerate(headers):
                    val = row[idx] if idx < len(row) else None
                    if isinstance(val, (datetime, date)):
                        row_dict[h] = val.strftime("%Y-%m-%d")
                    elif val is not None:
                        row_dict[h] = str(val).strip()
                    else:
                        row_dict[h] = ""
                data_rows.append(row_dict)

                if len(data_rows) >= max_rows:
                    break

            wb.close()

            if not headers:
                raise HTTPException(status_code=400, detail="Excel file does not contain a valid header row.")

            return headers, data_rows

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading Excel (.xlsx) file: {str(e)}"
            )

    elif ext == ".xls":
        try:
            import pandas as pd
            df = pd.read_excel(file_path, nrows=max_rows)
            if df.empty:
                raise HTTPException(status_code=400, detail="The .xls file is empty.")
            headers = [str(c).strip() for c in df.columns]
            # Replace NaNs with empty string
            df = df.fillna("")
            data_rows = df.to_dict(orient="records")
            # Convert values to strings
            clean_rows = []
            for r in data_rows:
                clean_r = {}
                for k, v in r.items():
                    if isinstance(v, (datetime, date)):
                        clean_r[str(k).strip()] = v.strftime("%Y-%m-%d")
                    else:
                        clean_r[str(k).strip()] = str(v).strip()
                clean_rows.append(clean_r)
            return headers, clean_rows
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading Excel (.xls) file: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format for Excel parsing: {ext}"
        )
