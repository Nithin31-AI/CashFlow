from app.core.security import verify_password, get_password_hash

def test_password_hashing():
    pwd = "MySecurePassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_registration_and_login(client):
    # Register
    reg_payload = {
        "email": "consultant@example.com",
        "password": "Password123!",
        "full_name": "Rohan Sharma"
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "consultant@example.com"
    assert data["full_name"] == "Rohan Sharma"
    assert "id" in data

    # Duplicate registration fails
    r_dup = client.post("/api/v1/auth/register", json=reg_payload)
    assert r_dup.status_code == 400

    # Login
    login_payload = {
        "email": "consultant@example.com",
        "password": "Password123!"
    }
    r_login = client.post("/api/v1/auth/login", json=login_payload)
    assert r_login.status_code == 200
    token_data = r_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Get /me with token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == "consultant@example.com"

    # Invalid login fails
    r_bad = client.post("/api/v1/auth/login", json={"email": "consultant@example.com", "password": "WrongPassword"})
    assert r_bad.status_code == 401

def test_password_recovery_workflow(client):
    # Register user
    reg_payload = {
        "email": "recovery_user@example.com",
        "password": "InitialPassword123!",
        "full_name": "Anita Verma"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Forgot password for non-existent email - does not reveal existence
    r_fake = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r_fake.status_code == 200
    assert "If this email is registered" in r_fake.json()["message"]

    # Forgot password for real user
    r_real = client.post("/api/v1/auth/forgot-password", json={"email": "recovery_user@example.com"})
    assert r_real.status_code == 200
    token = r_real.json().get("dev_reset_token")
    assert token is not None

    # Reset password with token
    reset_payload = {
        "token": token,
        "new_password": "NewSecretPassword456!"
    }
    r_reset = client.post("/api/v1/auth/reset-password", json=reset_payload)
    assert r_reset.status_code == 200

    # Old password fails
    r_old = client.post("/api/v1/auth/login", json={"email": "recovery_user@example.com", "password": "InitialPassword123!"})
    assert r_old.status_code == 401

    # New password succeeds
    r_new = client.post("/api/v1/auth/login", json={"email": "recovery_user@example.com", "password": "NewSecretPassword456!"})
    assert r_new.status_code == 200

def test_google_config_endpoint(client):
    r = client.get("/api/v1/auth/google/config")
    assert r.status_code == 200
    data = r.json()
    assert "enabled" in data
    assert "client_id" in data

def test_google_auth_new_user_and_auto_workspace(client):
    # Simulated Google authentication for new user
    token_str = "mock_google_token_new_googlenew@enterprise.com"
    r = client.post("/api/v1/auth/google", json={"credential": token_str})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "googlenew@enterprise.com"

    # Verify user can access protected endpoint with returned token
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == "googlenew@enterprise.com"

    # Verify auto-created business workspace exists
    r_biz = client.get("/api/v1/businesses/", headers=headers)
    assert r_biz.status_code == 200
    biz_list = r_biz.json()
    assert len(biz_list) >= 1
    assert "Workspace" in biz_list[0]["name"]

def test_google_auth_existing_user_linking(client):
    # Register user with password first
    email = "googlelink@company.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "Link User"
    })

    # Sign in using Google with identical verified email
    token_str = f"mock_google_token_existing_{email}"
    r = client.post("/api/v1/auth/google", json={"credential": token_str})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["email"] == email

    # Verify token works
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == email

def test_google_auth_empty_token_fails(client):
    r = client.post("/api/v1/auth/google", json={"credential": ""})
    assert r.status_code in [400, 422]
