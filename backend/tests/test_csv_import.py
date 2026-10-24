from tests.conftest import auth_headers

def setup_business_with_account(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "importer@agency.com",
        "password": "Password123!",
        "full_name": "Agency Accountant"
    })
    headers = auth_headers(r.json()["id"])
    b = client.post("/api/v1/businesses/", json={"name": "Creative Agency"}, headers=headers)
    biz_id = b.json()["id"]

    acc = client.post(f"/api/v1/businesses/{biz_id}/accounts", json={
        "name": "HDFC Business Current Account",
        "account_type": "BANK",
        "account_number_mask": "•••• 9102"
    }, headers=headers)
    acc_id = acc.json()["id"]

    return biz_id, acc_id, headers

def test_full_csv_import_workflow_with_validation(client):
    biz_id, acc_id, headers = setup_business_with_account(client)

    # Synthetic bank statement CSV with both valid and invalid rows
    csv_content = """Date,Particulars,Cheque No,Withdrawal,Deposit
01/03/2026,Client Project Advance,REF-1001,,150000.00
05/03/2026,AWS Cloud Hosting,,12450.00,
10/03/2026,Office Stationery,CHQ-445,3200.00,
32/13/2026,Invalid Date Row,,1000.00,
15/03/2026,,REF-1002,500.00,
20/03/2026,Software License,,abc_invalid,
25/03/2026,Consulting Retainer,REF-1003,,85000.00
"""

    # Step 1: Upload file
    upload_res = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("march_statement.csv", csv_content.encode("utf-8"), "text/csv")},
        headers=headers
    )
    assert upload_res.status_code == 201
    upload_id = upload_res.json()["id"]

    # Step 2: Start import and auto-detect columns
    start_res = client.post(
        f"/api/v1/businesses/{biz_id}/imports/start?upload_id={upload_id}",
        headers=headers
    )
    assert start_res.status_code == 200
    start_data = start_res.json()
    job_id = start_data["job_id"]
    assert start_data["file_type"] == "CSV"
    assert "Date" in start_data["headers"]
    assert start_data["suggested_mappings"]["date"] == "Date"
    assert start_data["suggested_mappings"]["description"] == "Particulars"
    assert start_data["suggested_mappings"]["debit"] == "Withdrawal"
    assert start_data["suggested_mappings"]["credit"] == "Deposit"

    # Step 3, 4 & 5: Adjust mapping and run validation
    mapping_payload = {
        "account_id": acc_id,
        "column_mappings": {
            "date": "Date",
            "description": "Particulars",
            "reference": "Cheque No",
            "debit": "Withdrawal",
            "credit": "Deposit",
        },
        "date_format": "%d/%m/%Y"
    }
    map_res = client.post(
        f"/api/v1/businesses/{biz_id}/imports/{job_id}/mapping",
        json=mapping_payload,
        headers=headers
    )
    assert map_res.status_code == 200
    summary = map_res.json()
    assert summary["total_rows"] == 7
    assert summary["valid_rows"] == 4   # Rows 1, 2, 3, 7
    assert summary["invalid_rows"] == 3 # Rows 4 (bad date), 5 (missing desc), 6 (bad amount)

    # Step 6: Preview results
    preview_res = client.get(f"/api/v1/businesses/{biz_id}/imports/{job_id}/preview", headers=headers)
    assert preview_res.status_code == 200
    preview = preview_res.json()
    assert preview["total_rows"] == 7

    # Find the invalid rows in preview
    invalid_items = [r for r in preview["preview_rows"] if not r["is_valid"]]
    assert len(invalid_items) == 3
    # Check that error messages are informative
    error_texts = " ".join([" ".join(i["errors"]) for i in invalid_items])
    assert "Date" in error_texts
    assert "Description cannot be empty" in error_texts
    assert "Invalid debit amount" in error_texts

    # Step 7 & 8: Explicitly confirm import
    confirm_res = client.post(f"/api/v1/businesses/{biz_id}/imports/{job_id}/confirm", headers=headers)
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["success"] is True
    assert confirm_data["imported_count"] == 4

    # Verify records stored with full provenance
    records_res = client.get(f"/api/v1/businesses/{biz_id}/records", headers=headers)
    assert records_res.status_code == 200
    records = records_res.json()
    assert len(records) == 4
    for rec in records:
        assert rec["import_job_id"] == job_id
        assert rec["account_id"] == acc_id
        assert rec["currency"] == "INR"
        assert rec["amount"] != 0
