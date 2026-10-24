import io
import openpyxl
from tests.conftest import auth_headers

def create_synthetic_excel_bytes():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"
    
    # Headers
    ws.append(["Txn Date", "Narration", "Ref ID", "Amount"])
    
    # Rows (using signed amount)
    ws.append(["2026-04-01", "Client Project Retainer", "TXN-901", 125000.00])
    ws.append(["2026-04-05", "Server Infrastructure", "TXN-902", -18500.00])
    ws.append(["2026-04-10", "Design Contractor Payment", "TXN-903", -35000.00])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def test_excel_import_workflow(client):
    # Register & setup business
    r = client.post("/api/v1/auth/register", json={
        "email": "excel_user@firm.com",
        "password": "Password123!",
        "full_name": "Excel Auditor"
    })
    headers = auth_headers(r.json()["id"])
    b = client.post("/api/v1/businesses/", json={"name": "Audit Firm"}, headers=headers)
    biz_id = b.json()["id"]

    excel_bytes = create_synthetic_excel_bytes()

    # Upload Excel file
    upload_res = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("ledger.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers
    )
    assert upload_res.status_code == 201
    upload_id = upload_res.json()["id"]

    # Start import
    start_res = client.post(
        f"/api/v1/businesses/{biz_id}/imports/start?upload_id={upload_id}",
        headers=headers
    )
    assert start_res.status_code == 200
    job_id = start_res.json()["job_id"]
    assert start_res.json()["file_type"] == "EXCEL"

    # Map and validate
    map_res = client.post(
        f"/api/v1/businesses/{biz_id}/imports/{job_id}/mapping",
        json={
            "column_mappings": {
                "date": "Txn Date",
                "description": "Narration",
                "reference": "Ref ID",
                "amount": "Amount",
            },
            "date_format": "%Y-%m-%d"
        },
        headers=headers
    )
    assert map_res.status_code == 200
    summary = map_res.json()
    assert summary["total_rows"] == 3
    assert summary["valid_rows"] == 3
    assert summary["invalid_rows"] == 0

    # Confirm import
    confirm_res = client.post(f"/api/v1/businesses/{biz_id}/imports/{job_id}/confirm", headers=headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["imported_count"] == 3
