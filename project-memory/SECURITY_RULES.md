# cashFlow — Security & Privacy Architecture

## 1. Authentication & Credential Security

- **Password Storage**: Passwords are never stored in plaintext. Hashing is performed using `passlib` with `bcrypt` (12 rounds) in `backend/app/core/security.py`.
- **JWT Access Tokens**: Stateless Bearer tokens signed with `HS256` using `SECRET_KEY`. Standard token lifespan is 24 hours (`ACCESS_TOKEN_EXPIRE_MINUTES=1440`).
- **Timing-Safe Password Recovery**:
  - Endpoint: `POST /api/v1/auth/forgot-password`.
  - Privacy Preservation: Always returns a generic confirmation message regardless of whether the submitted email exists in the database.
  - Token Storage: Plaintext recovery tokens are never stored in the database. The database stores a SHA-256 hash (`PasswordResetToken.token_hash`) with a 60-minute expiration.
  - Development Fallback: In non-production environments (`DEV_MODE=true`), a `dev_reset_token` is provided in the development response to enable local automated testing without configuring an external SMTP relay.

---

## 2. Multi-Tenant Authorization & RBAC

- **Database-Enforced Tenant Isolation**:
  - Every tenant-owned table stores foreign key `business_id` referencing `businesses.id`.
  - All foreign key relationships use `ondelete="CASCADE"`.
- **API Authorization Dependency (`RequireBusinessRole`)**:
  - Implemented in `backend/app/api/deps.py`.
  - Client-supplied `business_id` in URL route parameters is **never trusted blindly**.
  - The dependency explicitly queries `business_memberships` for `business_id == req_business_id` and `user_id == current_user.id`. If no membership exists, an immediate `HTTP 403 Forbidden ("Access denied")` is returned.
- **Granular Role Hierarchy**:
  - `OWNER`: Full administrative, member governance, and financial management authority.
  - `FINANCE_MANAGER`: Manage financial accounts, upload documents, and approve imports into the ledger.
  - `ACCOUNTANT`: Upload documents, adjust column mappings, review validation previews. Cannot approve imports.
  - `VIEWER`: Read-only access to authorized records and audit logs.
- **Owner Demotion/Deletion Guard**:
  - Business logic in `backend/app/api/v1/members.py` verifies that an organization always has at least one active `OWNER`. Attempts to demote or delete the sole owner return `HTTP 400 Bad Request`.

---

## 3. File Ingestion & Storage Security

- **Non-Public Storage Directory**:
  - Uploaded financial files are stored in `backend/uploads/` outside the web root or public static directories (`backend/app/core/storage.py`).
  - Files are given UUID-prefixed randomized filenames to prevent directory traversal and name collision.
- **MIME Magic Byte Verification**:
  - File extensions are validated against an allowlist (`.csv`, `.xls`, `.xlsx`, `.pdf`, `.png`, `.jpg`, `.jpeg`).
  - The first 64 bytes of file content are inspected for true magic numbers (`%PDF-`, `\x89PNG`, `\xff\xd8\xff`, `PK\x03\x04`). Binary null bytes in CSV files are blocked.
- **Upload Size Limit**:
  - Files exceeding `MAX_UPLOAD_SIZE_MB` (default 15 MB) are rejected with `HTTP 413 Request Entity Too Large`. Empty files (0 bytes) are rejected with `HTTP 400`.
- **Duplicate Upload Prevention**:
  - During upload, a SHA-256 hash of the byte stream is computed and checked against `uploaded_files.file_hash` within the tenant. Duplicate uploads return `HTTP 409 Conflict`.

---

## 4. API & Network Security

- **Security Headers Middleware**:
  - Implemented in `backend/app/main.py`:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `X-XSS-Protection: 1; mode=block`
- **CORS Restrictions**:
  - Configured via `CORS_ORIGINS` in `Settings`. Default development origins restricted to `http://localhost:3000` and `http://127.0.0.1:3000`.
- **Credential Sanitization in Audit Logs**:
  - All audit events passing through `backend/app/core/audit.py` are filtered through `sanitize_details`.
  - Keys matching `password`, `hashed_password`, `token`, `access_token`, `secret`, `authorization`, and `raw_token` are automatically replaced with `[REDACTED]`.

---

## 5. Secret Management & Environment Hygiene

- All credentials, secrets, and connection strings are managed strictly through environment variables (`.env`).
- Safe templates (`.env.example` in root and `backend/.env.example`) are committed to version control with placeholder values.
- Real production secrets, private keys, database passwords, or customer documents must never be committed to the repository or stored in project-memory files.
