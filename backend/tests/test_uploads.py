import uuid
from tests.conftest import auth_headers

def setup_business(client):
    unique_email = f"uploader_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Uploader User"
    })
    user_id = r.json()["id"]
    headers = auth_headers(user_id)

    b = client.post("/api/v1/businesses/", json={"name": "Upload Test Corp"}, headers=headers)
    return b.json()["id"], headers

def test_file_type_and_extension_validation(client):
    biz_id, headers = setup_business(client)

    # 1. Disallowed extension (.sh / .exe)
    res_bad_ext = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("script.sh", b"echo 'hack'", "text/x-sh")},
        headers=headers
    )
    assert res_bad_ext.status_code == 400
    assert "not permitted" in res_bad_ext.json()["detail"]

    # 2. Empty file (0 bytes)
    res_empty = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("empty.csv", b"", "text/csv")},
        headers=headers
    )
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["detail"]

    # 3. Spoofed content: claims to be PNG but has random text bytes
    res_spoof = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("fake.png", b"not a real png image at all", "image/png")},
        headers=headers
    )
    assert res_spoof.status_code == 400
    assert "Invalid PNG file content signature" in res_spoof.json()["detail"]

    # 4. Binary null bytes in CSV
    res_binary_csv = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("corrupt.csv", b"col1,col2\x00corrupt", "text/csv")},
        headers=headers
    )
    assert res_binary_csv.status_code == 400
    assert "Binary content detected" in res_binary_csv.json()["detail"]

    # 5. Valid CSV succeeds
    valid_csv = b"date,narration,amount\n2026-03-01,Client Retainer,75000.00"
    res_valid_csv = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("statement.csv", valid_csv, "text/csv")},
        headers=headers
    )
    assert res_valid_csv.status_code == 201
    assert res_valid_csv.json()["original_filename"] == "statement.csv"

def test_duplicate_upload_detection(client):
    biz_id, headers = setup_business(client)

    csv_data = b"date,description,amount\n2026-02-15,Office Rent,-45000"
    
    # First upload succeeds
    r1 = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("feb_rent.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert r1.status_code == 201

    # Second identical upload triggers 409 Conflict
    r2 = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("feb_rent.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert r2.status_code == 409
    assert "Duplicate upload detected" in r2.json()["detail"]

def test_upload_history_listing(client):
    biz_id, headers = setup_business(client)

    csv1 = b"date,desc,amount\n2026-01-01,One,10"
    csv2 = b"date,desc,amount\n2026-01-02,Two,20"

    client.post(f"/api/v1/businesses/{biz_id}/uploads", files={"file": ("file1.csv", csv1, "text/csv")}, headers=headers)
    client.post(f"/api/v1/businesses/{biz_id}/uploads", files={"file": ("file2.csv", csv2, "text/csv")}, headers=headers)

    res = client.get(f"/api/v1/businesses/{biz_id}/uploads", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    filenames = [i["original_filename"] for i in items]
    assert "file1.csv" in filenames
    assert "file2.csv" in filenames
