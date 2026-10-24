from tests.conftest import auth_headers

def test_strict_tenant_isolation(client):
    # Register User A
    r_a = client.post("/api/v1/auth/register", json={
        "email": "owner_a@company-a.com",
        "password": "Password123!",
        "full_name": "Alice Corp"
    })
    user_a = r_a.json()
    headers_a = auth_headers(user_a["id"])

    # Register User B
    r_b = client.post("/api/v1/auth/register", json={
        "email": "owner_b@company-b.com",
        "password": "Password123!",
        "full_name": "Bob Services"
    })
    user_b = r_b.json()
    headers_b = auth_headers(user_b["id"])

    # User A creates Business A
    r_biz_a = client.post("/api/v1/businesses/", json={
        "name": "Acme IT Solutions",
        "currency": "INR",
    }, headers=headers_a)
    assert r_biz_a.status_code == 201
    biz_a_id = r_biz_a.json()["id"]

    # User B creates Business B
    r_biz_b = client.post("/api/v1/businesses/", json={
        "name": "Blue Ocean Consulting",
        "currency": "INR",
    }, headers=headers_b)
    assert r_biz_b.status_code == 201
    biz_b_id = r_biz_b.json()["id"]

    # PROVE: User B CANNOT access Business A
    # 1. Get Business A details
    res = client.get(f"/api/v1/businesses/{biz_a_id}", headers=headers_b)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # 2. Update Business A
    res = client.patch(f"/api/v1/businesses/{biz_a_id}", json={"name": "Hacked Name"}, headers=headers_b)
    assert res.status_code == 403

    # 3. List Business A accounts
    res = client.get(f"/api/v1/businesses/{biz_a_id}/accounts", headers=headers_b)
    assert res.status_code == 403

    # 4. List Business A uploads
    res = client.get(f"/api/v1/businesses/{biz_a_id}/uploads", headers=headers_b)
    assert res.status_code == 403

    # 5. List Business A imports
    res = client.get(f"/api/v1/businesses/{biz_a_id}/imports", headers=headers_b)
    assert res.status_code == 403

    # 6. List Business A records
    res = client.get(f"/api/v1/businesses/{biz_a_id}/records", headers=headers_b)
    assert res.status_code == 403

    # 7. List Business A audit logs
    res = client.get(f"/api/v1/businesses/{biz_a_id}/audit-logs", headers=headers_b)
    assert res.status_code == 403

    # PROVE: Unauthenticated request is rejected
    res_unauth = client.get(f"/api/v1/businesses/{biz_a_id}")
    assert res_unauth.status_code == 401
