import io
import uuid
import pytest
from tests.conftest import auth_headers

def setup_business(client):
    email = f"batch_uploader_{uuid.uuid4().hex[:8]}@test.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Batch Tester"}
    )
    user_id = reg.json()["id"]
    headers = auth_headers(user_id)

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": "Batch Biz", "currency": "INR"},
        headers=headers
    )
    return biz_res.json()["id"], headers

def test_multi_file_batch_upload_with_isolation(client):
    business_id, headers = setup_business(client)

    csv_content_1 = b"Date,Description,Amount\n2026-01-01,Test Row 1,1000\n"
    csv_content_2 = b"Date,Description,Amount\n2026-01-02,Test Row 2,2000\n"

    # Send 2 valid files simultaneously in batch
    files = [
        ("files", ("statement_a.csv", io.BytesIO(csv_content_1), "text/csv")),
        ("files", ("statement_b.csv", io.BytesIO(csv_content_2), "text/csv")),
    ]

    response = client.post(
        f"/api/v1/businesses/{business_id}/uploads/batch",
        files=files,
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 2
    assert data["successful_count"] == 2
    assert data["failed_count"] == 0
    assert len(data["results"]) == 2
    assert data["results"][0]["status"] == "SUCCESS"
    assert data["results"][0]["import_job_id"] is not None

    # Now attempt a batch with 1 duplicate file and 1 fresh file
    csv_content_3 = b"Date,Description,Amount\n2026-01-03,Test Row 3,3000\n"
    mixed_files = [
        ("files", ("statement_a_duplicate.csv", io.BytesIO(csv_content_1), "text/csv")),  # Duplicate content
        ("files", ("statement_c_fresh.csv", io.BytesIO(csv_content_3), "text/csv")),       # Fresh content
    ]

    response_mixed = client.post(
        f"/api/v1/businesses/{business_id}/uploads/batch",
        files=mixed_files,
        headers=headers
    )
    assert response_mixed.status_code == 200
    mixed_data = response_mixed.json()
    assert mixed_data["total_files"] == 2
    assert mixed_data["successful_count"] == 1
    assert mixed_data["failed_count"] == 1
    # Check that duplicate failed gracefully without crashing the fresh file
    assert mixed_data["results"][0]["status"] == "FAILED"
    assert "Duplicate file" in mixed_data["results"][0]["error_message"]
    assert mixed_data["results"][1]["status"] == "SUCCESS"
