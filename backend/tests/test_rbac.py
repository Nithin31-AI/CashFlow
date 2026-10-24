from tests.conftest import auth_headers

def setup_org_with_roles(client):
    """Sets up an organization with OWNER, FINANCE_MANAGER, ACCOUNTANT, and VIEWER."""
    users = {}
    roles = ["owner", "finance_manager", "accountant", "viewer"]
    
    for r in roles:
        res = client.post("/api/v1/auth/register", json={
            "email": f"{r}@company.com",
            "password": "Password123!",
            "full_name": f"User {r.capitalize()}"
        })
        users[r] = res.json()
        users[f"{r}_headers"] = auth_headers(users[r]["id"])

    # Owner creates business
    biz_res = client.post("/api/v1/businesses/", json={
        "name": "Role Test Services",
        "currency": "INR",
    }, headers=users["owner_headers"])
    biz_id = biz_res.json()["id"]

    # Owner invites finance_manager, accountant, viewer
    client.post(f"/api/v1/businesses/{biz_id}/members", json={
        "email": users["finance_manager"]["email"],
        "role": "FINANCE_MANAGER"
    }, headers=users["owner_headers"])

    client.post(f"/api/v1/businesses/{biz_id}/members", json={
        "email": users["accountant"]["email"],
        "role": "ACCOUNTANT"
    }, headers=users["owner_headers"])

    client.post(f"/api/v1/businesses/{biz_id}/members", json={
        "email": users["viewer"]["email"],
        "role": "VIEWER"
    }, headers=users["owner_headers"])

    return biz_id, users

def test_rbac_permissions(client):
    biz_id, users = setup_org_with_roles(client)

    # 1. VIEWER can view accounts, but cannot create account
    res_view = client.get(f"/api/v1/businesses/{biz_id}/accounts", headers=users["viewer_headers"])
    assert res_view.status_code == 200

    res_create_fail = client.post(f"/api/v1/businesses/{biz_id}/accounts", json={
        "name": "Hacked Account",
        "account_type": "BANK"
    }, headers=users["viewer_headers"])
    assert res_create_fail.status_code == 403
    assert "Insufficient permissions" in res_create_fail.json()["detail"]

    # 2. FINANCE_MANAGER can create account
    res_create_ok = client.post(f"/api/v1/businesses/{biz_id}/accounts", json={
        "name": "Reserve Bank Account",
        "account_type": "BANK"
    }, headers=users["finance_manager_headers"])
    assert res_create_ok.status_code == 201

    # 3. VIEWER cannot upload files
    dummy_csv = b"date,description,amount\n2026-01-01,Test,100"
    res_upload_fail = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("test.csv", dummy_csv, "text/csv")},
        headers=users["viewer_headers"]
    )
    assert res_upload_fail.status_code == 403

    # 4. ACCOUNTANT can upload files
    res_upload_ok = client.post(
        f"/api/v1/businesses/{biz_id}/uploads",
        files={"file": ("test.csv", dummy_csv, "text/csv")},
        headers=users["accountant_headers"]
    )
    assert res_upload_ok.status_code == 201
    upload_id = res_upload_ok.json()["id"]

    # 5. ACCOUNTANT can start import job and apply mapping
    res_start = client.post(
        f"/api/v1/businesses/{biz_id}/imports/start?upload_id={upload_id}",
        headers=users["accountant_headers"]
    )
    assert res_start.status_code == 200
    job_id = res_start.json()["job_id"]

    res_map = client.post(
        f"/api/v1/businesses/{biz_id}/imports/{job_id}/mapping",
        json={
            "column_mappings": {"date": "date", "description": "description", "amount": "amount"},
            "date_format": "%Y-%m-%d"
        },
        headers=users["accountant_headers"]
    )
    assert res_map.status_code == 200

    # 6. ACCOUNTANT CANNOT confirm import (only FINANCE_MANAGER or OWNER can approve)
    res_confirm_fail = client.post(
        f"/api/v1/businesses/{biz_id}/imports/{job_id}/confirm",
        headers=users["accountant_headers"]
    )
    assert res_confirm_fail.status_code == 403

    # 7. FINANCE_MANAGER CAN confirm import
    res_confirm_ok = client.post(
        f"/api/v1/businesses/{biz_id}/imports/{job_id}/confirm",
        headers=users["finance_manager_headers"]
    )
    assert res_confirm_ok.status_code == 200
    assert res_confirm_ok.json()["success"] is True

    # 8. FINANCE_MANAGER CANNOT manage business members (only OWNER can)
    res_member_fail = client.post(
        f"/api/v1/businesses/{biz_id}/members",
        json={"email": "extra@company.com", "role": "VIEWER"},
        headers=users["finance_manager_headers"]
    )
    assert res_member_fail.status_code == 403
