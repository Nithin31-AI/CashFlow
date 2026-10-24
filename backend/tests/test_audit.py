from tests.conftest import auth_headers

def test_audit_logs_and_security_redaction(client):
    # Register
    r = client.post("/api/v1/auth/register", json={
        "email": "audit_tester@example.com",
        "password": "SecretPassword123!",
        "full_name": "Audit Tester"
    })
    headers = auth_headers(r.json()["id"])

    # Create business
    b = client.post("/api/v1/businesses/", json={"name": "Audit Safety Corp"}, headers=headers)
    biz_id = b.json()["id"]

    # Upload file
    csv = b"date,desc,amount\n2026-05-01,Service Fee,50000"
    client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("test.csv", csv, "text/csv")},
        headers=headers
    )

    # Fetch audit logs
    audit_res = client.get(f"/api/v1/businesses/{biz_id}/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 2  # BUSINESS_CREATED, FILE_UPLOADED

    # Ensure no passwords or raw credentials exist in logs
    log_dump = str(logs).lower()
    assert "secretpassword123!" not in log_dump
    assert "token" not in [v for l in logs if l.get("details") for k, v in l["details"].items() if k == "password"]
