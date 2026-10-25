# cashFlow — API Documentation

This document describes the actual FastAPI REST endpoints implemented in the application.

- **Base URL Prefix**: `/api/v1`
- **Interactive Documentation**: Swagger UI at `http://localhost:8000/docs`, ReDoc at `http://localhost:8000/redoc`.
- **Authentication**: Bearer Token in `Authorization` header (`Authorization: Bearer <jwt_access_token>`).

---

## 1. Authentication Endpoints (`/api/v1/auth`)

### 1.1 `POST /api/v1/auth/register`
- **Purpose**: Register a new user account.
- **Auth**: Public.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!",
    "full_name": "Full Name"
  }
  ```
- **Response**: `201 Created` -> `UserOut` (`id`, `email`, `full_name`, `is_active`, `created_at`).
- **Errors**: `400 Bad Request` if email already registered.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

### 1.2 `POST /api/v1/auth/login`
- **Purpose**: Authenticate user and issue JWT token.
- **Auth**: Public.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!"
  }
  ```
- **Response**: `200 OK` -> `Token` (`access_token`, `token_type`, `user`).
- **Errors**: `401 Unauthorized` on invalid credentials or inactive account.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

### 1.3 `GET /api/v1/auth/me`
- **Purpose**: Retrieve authenticated user profile.
- **Auth**: Bearer JWT token required.
- **Response**: `200 OK` -> `UserOut`.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

### 1.4 `POST /api/v1/auth/forgot-password`
- **Purpose**: Initiate secure password recovery without leaking registration status.
- **Auth**: Public.
- **Request Body**: `{"email": "user@example.com"}`.
- **Response**: `200 OK` -> `{"message": "If this email is registered...", "dev_reset_token": "..."}`.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

### 1.5 `POST /api/v1/auth/reset-password`
- **Purpose**: Reset password using token.
- **Auth**: Public (token-authorized).
- **Request Body**: `{"token": "raw_token", "new_password": "NewPassword123!"}`.
- **Response**: `200 OK` -> `{"message": "Password reset successful."}`.
- **Errors**: `400 Bad Request` if token is invalid, expired, or already used.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

### 1.6 `GET /api/v1/auth/google/config`
- **Purpose**: Retrieve public Google OAuth client ID and enabled status for frontend Google Identity Services initialization.
- **Auth**: Public.
- **Response**: `200 OK` -> `{"client_id": "...", "enabled": true}`.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

### 1.7 `POST /api/v1/auth/google`
- **Purpose**: Authenticate user via Google ID Token (JWT) issued by Google Identity Services. Validates signature, audience, and email verification claims on the server. If user is new, automatically registers them and generates their initial workspace. If user exists, links and authenticates them securely.
- **Auth**: Public.
- **Request Body**: `{"credential": "<google_id_token>"}`.
- **Response**: `200 OK` -> `Token` (`access_token`, `token_type`, `user`).
- **Errors**: `400 Bad Request` on unverified email or invalid token; `401 Unauthorized` on signature failure.
- **Source**: `backend/app/api/v1/auth.py`
- **Test Status**: `VERIFIED` (`tests/test_auth.py`).

---

## 2. Business Management (`/api/v1/businesses`)

### 2.1 `POST /api/v1/businesses/`
- **Purpose**: Create a new business workspace. Grants creator `OWNER` role and creates default bank account.
- **Auth**: Authenticated User.
- **Request Body**: `{"name": "Company Name", "currency": "INR", "country": "IN", "timezone": "Asia/Kolkata"}`.
- **Response**: `201 Created` -> `BusinessOut` (`id`, `name`, `slug`, `currency`, `country`, `timezone`, `role: "OWNER"`).
- **Source**: `backend/app/api/v1/businesses.py`
- **Test Status**: `VERIFIED` (`tests/test_tenancy.py`).

### 2.2 `GET /api/v1/businesses/`
- **Purpose**: List all businesses the current user belongs to.
- **Auth**: Authenticated User.
- **Response**: `200 OK` -> `List[BusinessOut]`.
- **Source**: `backend/app/api/v1/businesses.py`
- **Test Status**: `VERIFIED` (`tests/test_tenancy.py`).

### 2.3 `GET /api/v1/businesses/{business_id}`
- **Purpose**: Get business workspace details.
- **Auth**: Authenticated User with membership in `business_id` (`VIEWER` or higher).
- **Response**: `200 OK` -> `BusinessOut`.
- **Errors**: `403 Forbidden` if user is not a member.
- **Source**: `backend/app/api/v1/businesses.py`
- **Test Status**: `VERIFIED` (`tests/test_tenancy.py`).

### 2.4 `PATCH /api/v1/businesses/{business_id}`
- **Purpose**: Update business settings.
- **Auth**: Requires `OWNER` role in `business_id`.
- **Request Body**: Partial `{"name": "...", "currency": "...", "country": "...", "timezone": "..."}`.
- **Response**: `200 OK` -> `BusinessOut`.
- **Errors**: `403 Forbidden` if role is less than `OWNER`.
- **Source**: `backend/app/api/v1/businesses.py`
- **Test Status**: `VERIFIED` (`tests/test_tenancy.py`).

---

## 3. Team & Memberships (`/api/v1/businesses/{business_id}/members`)

### 3.1 `GET /api/v1/businesses/{business_id}/members`
- **Purpose**: List members of the business.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `List[MembershipOut]`.
- **Source**: `backend/app/api/v1/members.py`
- **Test Status**: `VERIFIED` (`tests/test_rbac.py`).

### 3.2 `POST /api/v1/businesses/{business_id}/members`
- **Purpose**: Add or invite a user by email with specific role.
- **Auth**: `OWNER` only.
- **Request Body**: `{"email": "colleague@example.com", "role": "FINANCE_MANAGER"}`.
- **Response**: `201 Created` -> `MembershipOut`.
- **Errors**: `404 Not Found` if user not registered; `400 Bad Request` if already member.
- **Source**: `backend/app/api/v1/members.py`
- **Test Status**: `VERIFIED` (`tests/test_rbac.py`).

### 3.3 `PATCH /api/v1/businesses/{business_id}/members/{membership_id}`
- **Purpose**: Update a member's role. Prevents demoting the last owner.
- **Auth**: `OWNER` only.
- **Request Body**: `{"role": "ACCOUNTANT"}`.
- **Response**: `200 OK` -> `MembershipOut`.
- **Source**: `backend/app/api/v1/members.py`
- **Test Status**: `VERIFIED` (`tests/test_rbac.py`).

### 3.4 `DELETE /api/v1/businesses/{business_id}/members/{membership_id}`
- **Purpose**: Remove a member from the workspace. Prevents removing the last owner.
- **Auth**: `OWNER` only.
- **Response**: `204 No Content`.
- **Source**: `backend/app/api/v1/members.py`
- **Test Status**: `VERIFIED` (`tests/test_rbac.py`).

---

## 4. Financial Accounts (`/api/v1/businesses/{business_id}/accounts`)

### 4.1 `GET /api/v1/businesses/{business_id}/accounts`
- **Purpose**: List bank accounts, cards, and wallets.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `List[AccountOut]`.
- **Source**: `backend/app/api/v1/accounts.py`
- **Test Status**: `VERIFIED` (`tests/test_rbac.py`).

### 4.2 `POST /api/v1/businesses/{business_id}/accounts`
- **Purpose**: Create a financial account.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Request Body**: `{"name": "...", "account_type": "BANK", "currency": "INR", "account_number_mask": "•••• 1234"}`.
- **Response**: `201 Created` -> `AccountOut`.
- **Source**: `backend/app/api/v1/accounts.py`
- **Test Status**: `VERIFIED` (`tests/test_rbac.py`).

---

## 5. File Uploads (`/api/v1/businesses/{business_id}/uploads`)

### 5.1 `POST /api/v1/businesses/{business_id}/uploads`
- **Purpose**: Upload financial file (CSV, XLSX, XLS, PDF, PNG, JPG). Magic number validated, duplicate SHA-256 checked.
- **Auth**: `ACCOUNTANT` or higher.
- **Body**: `multipart/form-data` with `file`.
- **Response**: `201 Created` -> `UploadedFileOut`.
- **Errors**: `400 Bad Request` on invalid signature/empty file; `409 Conflict` on duplicate upload; `413` on size > 15MB.
- **Source**: `backend/app/api/v1/uploads.py`
- **Test Status**: `VERIFIED` (`tests/test_uploads.py`).

### 5.2 `GET /api/v1/businesses/{business_id}/uploads`
- **Purpose**: List upload history for the business.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `List[UploadedFileOut]`.
- **Source**: `backend/app/api/v1/uploads.py`
- **Test Status**: `VERIFIED` (`tests/test_uploads.py`).

---

## 6. Financial Import Pipeline (`/api/v1/businesses/{business_id}/imports`)

### 6.1 `POST /api/v1/businesses/{business_id}/imports/start?upload_id={upload_id}`
- **Purpose**: Step 1 & 2: Inspect file structure, detect columns, create `ImportJob` (`PENDING_MAPPING`).
- **Auth**: `ACCOUNTANT` or higher.
- **Response**: `200 OK` -> `{"job_id": "...", "headers": [...], "suggested_mappings": {...}, "suggested_date_format": "..."}`.
- **Source**: `backend/app/api/v1/imports.py`
- **Test Status**: `VERIFIED` (`tests/test_csv_import.py`).

### 6.2 `POST /api/v1/businesses/{business_id}/imports/{job_id}/mapping`
- **Purpose**: Step 3, 4 & 5: Save column mapping and date format, run validation on all rows, store validation results.
- **Auth**: `ACCOUNTANT` or higher.
- **Request Body**:
  ```json
  {
    "account_id": "optional_account_id",
    "column_mappings": {
      "date": "Date",
      "description": "Particulars",
      "reference": "Cheque No",
      "debit": "Withdrawal",
      "credit": "Deposit"
    },
    "date_format": "%d/%m/%Y"
  }
  ```
- **Response**: `200 OK` -> `ImportValidationSummary` (`total_rows`, `valid_rows`, `invalid_rows`, `preview_rows`).
- **Source**: `backend/app/api/v1/imports.py`
- **Test Status**: `VERIFIED` (`tests/test_csv_import.py`).

### 6.3 `GET /api/v1/businesses/{business_id}/imports/{job_id}/preview`
- **Purpose**: Step 6: Fetch preview rows and row-level validation errors.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `ImportValidationSummary`.
- **Source**: `backend/app/api/v1/imports.py`
- **Test Status**: `VERIFIED` (`tests/test_csv_import.py`).

### 6.4 `POST /api/v1/businesses/{business_id}/imports/{job_id}/confirm`
- **Purpose**: Step 7 & 8: Explicitly approve import. Commits only valid rows to `imported_records` with full provenance.
- **Auth**: `FINANCE_MANAGER` or `OWNER` only.
- **Response**: `200 OK` -> `{"success": true, "imported_count": 4, "message": "..."}`.
- **Errors**: `403 Forbidden` if role is Accountant or Viewer; `400 Bad Request` if job already approved or 0 valid rows.
- **Source**: `backend/app/api/v1/imports.py`
- **Test Status**: `VERIFIED` (`tests/test_csv_import.py`, `tests/test_rbac.py`).

### 6.5 `GET /api/v1/businesses/{business_id}/imports`
- **Purpose**: List all import jobs and batch statuses.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `List[ImportJobOut]`.
- **Source**: `backend/app/api/v1/imports.py`
- **Test Status**: `VERIFIED`.

### 6.6 `GET /api/v1/businesses/{business_id}/records`
- **Purpose**: List approved financial records in the ledger.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `List[ImportedRecordOut]`.
- **Source**: `backend/app/api/v1/imports.py`
- **Test Status**: `VERIFIED`.

---

## 7. Audit Trail (`/api/v1/businesses/{business_id}/audit-logs`)

### 7.1 `GET /api/v1/businesses/{business_id}/audit-logs`
- **Purpose**: Retrieve immutable audit events for the business.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Response**: `200 OK` -> `List[AuditLogOut]`.
- **Source**: `backend/app/api/v1/audit.py`
- **Test Status**: `VERIFIED` (`tests/test_audit.py`).

---

## 8. Multi-File Batch Uploads (`/api/v1/businesses/{business_id}/uploads/batch`)

### 8.1 `POST /api/v1/businesses/{business_id}/uploads/batch`
- **Purpose**: Upload multiple statements concurrently with per-file status badges and retry ability.
- **Auth**: `ACCOUNTANT` or higher.
- **Payload**: `multipart/form-data` with `files` list.
- **Response**: `200 OK` -> `BatchUploadResponse` (`total_files`, `successful_count`, `failed_count`, `results`).
- **Source**: `backend/app/api/v1/uploads.py`
- **Test Status**: `VERIFIED` (`tests/test_batch_uploads.py`).

---

## 9. Financial Engine & Ledger (`/api/v1/businesses/{business_id}/financial`)

### 9.1 `GET /api/v1/businesses/{business_id}/financial/overview`
- **Purpose**: Authoritative decimal balance calculations, liquid cash vs receivables separation, and reserve headroom.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `FinancialOverview` (`actual_cash_balance`, `minimum_cash_reserve`, `reserve_headroom`, `outstanding_receivables`, `overdue_receivables`, `total_revenue`, `total_expenses`, `net_income`, `accounts`).
- **Source**: `backend/app/api/v1/financial.py`
- **Test Status**: `VERIFIED` (`tests/test_financial_engine.py`).

### 9.2 `PATCH /api/v1/businesses/{business_id}/financial/settings/reserve`
- **Purpose**: Configure business minimum cash reserve threshold.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/financial.py`
- **Test Status**: `VERIFIED`.

### 9.3 `GET /api/v1/businesses/{business_id}/transactions`
- **Purpose**: Classified financial ledger list with filtering by category, status, and internal transfers.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/transactions.py`
- **Test Status**: `VERIFIED`.

### 9.4 `POST /api/v1/businesses/{business_id}/transactions`
- **Purpose**: Record manual transaction or internal transfer between two accounts with automatic pairing.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/transactions.py`
- **Test Status**: `VERIFIED` (`tests/test_financial_engine.py`).

---

## 10. Invoices & Payments (`/api/v1/businesses/{business_id}/invoices` & `/payments`)

### 10.1 `GET /api/v1/businesses/{business_id}/invoices`
- **Purpose**: List customer invoices with payment delay prediction indicators.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/invoices.py`
- **Test Status**: `VERIFIED`.

### 10.2 `POST /api/v1/businesses/{business_id}/invoices`
- **Purpose**: Create customer billing invoice.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/invoices.py`
- **Test Status**: `VERIFIED`.

### 10.3 `PATCH /api/v1/businesses/{business_id}/invoices/{invoice_id}/status`
- **Purpose**: Update invoice lifecycle status (`DRAFT`, `SENT`, `CANCELLED`, `PAID`).
- **Enforcement**: Direct transition to `PAID` is strictly prohibited if `unpaid > 0`. Moving to `PAID` requires actual settlement via `POST /payments`.
- **Request Body**: `{"status": "PAID"}` (`InvoiceStatusUpdate`).
- **Auth**: `ACCOUNTANT` or higher.
- **Source**: `backend/app/api/v1/invoices.py`
- **Test Status**: `VERIFIED` (`tests/test_system_integration_repairs.py`).

### 10.4 `POST /api/v1/businesses/{business_id}/payments`
- **Purpose**: Record customer payment settlement and synchronize ledger.
- **Enforcement**:
  1. Validates `amount > 0` and `amount <= unpaid`.
  2. Enforces idempotency via `(reference_number, amount)` check against duplicate submissions.
  3. Reconciles with existing unreconciled bank transaction if matched, avoiding duplicate cash inflows. Otherwise, creates exactly one authoritative `Transaction` ledger entry linked via `payment_id`.
  4. Automatically recalculates deposit account `current_balance` and transitions invoice status (`PARTIALLY_PAID` or `PAID`).
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/invoices.py`
- **Test Status**: `VERIFIED` (`tests/test_system_integration_repairs.py`).

---

## 11. Reconciliation Engine (`/api/v1/businesses/{business_id}/reconciliation`)

### 11.1 `GET /api/v1/businesses/{business_id}/reconciliation/candidates`
- **Purpose**: Fetch Explainable AI match candidates between unallocated bank transactions and customer invoices.
- **Auth**: `VIEWER` or higher.
- **Response**: `200 OK` -> `List[ReconciliationCandidate]` (`confidence_score`, `match_type`, `explanation`, `matched_amount`).
- **Source**: `backend/app/api/v1/reconciliation.py`
- **Test Status**: `VERIFIED` (`tests/test_reconciliation.py`).

### 11.2 `POST /api/v1/businesses/{business_id}/reconciliation/approve`
- **Purpose**: Explicit human approval gate committing reconciliation link.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/reconciliation.py`
- **Test Status**: `VERIFIED` (`tests/test_reconciliation.py`).

### 11.3 `POST /api/v1/businesses/{business_id}/reconciliation/reject`
- **Purpose**: Explicit human rejection gate dismissing false candidate match.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/reconciliation.py`
- **Test Status**: `VERIFIED` (`tests/test_reconciliation.py`).

---

## 12. Forecasting & Risk Models (`/api/v1/businesses/{business_id}/forecasts`)

### 12.1 `GET /api/v1/businesses/{business_id}/forecasts`
- **Purpose**: Multi-horizon cash projections (7d, 30d, 90d, 180d, 365d) with confidence intervals and daily paths.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/forecasting.py`
- **Test Status**: `VERIFIED` (`tests/test_forecasting_and_risk.py`).

### 12.2 `GET /api/v1/businesses/{business_id}/forecasts/risks`
- **Purpose**: Cash-shortage risk predictions and shortfall amounts against minimum reserve.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/forecasting.py`
- **Test Status**: `VERIFIED` (`tests/test_forecasting_and_risk.py`).

### 12.3 `GET /api/v1/businesses/{business_id}/forecasts/anomalies`
- **Purpose**: 2.5σ statistical expense anomalies flagged against historical category baselines.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/forecasting.py`
- **Test Status**: `VERIFIED` (`tests/test_forecasting_and_risk.py`).

### 12.4 `POST /api/v1/businesses/{business_id}/forecasts/anomalies/{anomaly_id}/review`
- **Purpose**: Mark expense anomaly as reviewed by human operator.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/forecasting.py`
- **Test Status**: `VERIFIED`.

---

## 13. Monte Carlo Simulation Engine (`/api/v1/businesses/{business_id}/simulations`)

### 13.1 `POST /api/v1/businesses/{business_id}/simulations/run`
- **Purpose**: Execute 1000-path stochastic Monte Carlo simulation with payment delays, collection probabilities, and expense multipliers.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/simulations.py`
- **Test Status**: `VERIFIED` (`tests/test_simulations.py`).

### 13.2 `GET /api/v1/businesses/{business_id}/simulations/latest`
- **Purpose**: Retrieve the most recent simulation run and daily percentile envelope.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/simulations.py`
- **Test Status**: `VERIFIED`.

---

## 14. Decision Optimisation & Scenarios (`/api/v1/businesses/{business_id}/...`)

### 14.1 `GET` & `POST /api/v1/businesses/{business_id}/goals`
- **Purpose**: List and create business financial goals with hard vs soft constraint flags.
- **Auth**: `VIEWER` for GET; `FINANCE_MANAGER` or `OWNER` for POST.
- **Source**: `backend/app/api/v1/decisions.py`
- **Test Status**: `VERIFIED` (`tests/test_decisions_and_scenarios.py`).

### 14.2 `GET` & `POST /api/v1/businesses/{business_id}/scenarios`
- **Purpose**: List and create custom financial scenarios and calculate comparative metrics against baseline.
- **Auth**: `VIEWER` for GET; `FINANCE_MANAGER` or `OWNER` for POST.
- **Source**: `backend/app/api/v1/decisions.py`
- **Test Status**: `VERIFIED` (`tests/test_decisions_and_scenarios.py`).

### 14.3 `POST /api/v1/businesses/{business_id}/optimisation/run`
- **Purpose**: Solve linear constrained financial optimisation model balancing cash preservation against goals.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/decisions.py`
- **Test Status**: `VERIFIED` (`tests/test_decisions_and_scenarios.py`).

### 14.4 `GET /api/v1/businesses/{business_id}/recommendations`
- **Purpose**: List active explainable financial recommendations with severity, estimated impact, and reasoning.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/decisions.py`
- **Test Status**: `VERIFIED`.

### 14.5 `POST /api/v1/businesses/{business_id}/recommendations/{id}/status`
- **Purpose**: Update recommendation status to `ACCEPTED` or `DISMISSED`.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/decisions.py`
- **Test Status**: `VERIFIED`.

---

## 15. Financial Alerts (`/api/v1/businesses/{business_id}/alerts`)

### 15.1 `GET` & `POST /api/v1/businesses/{business_id}/alerts/rules`
- **Purpose**: List and configure automated sentinel alert rules (thresholds, suppression windows).
- **Auth**: `VIEWER` for GET; `FINANCE_MANAGER` or `OWNER` for POST.
- **Source**: `backend/app/api/v1/alerts.py`
- **Test Status**: `VERIFIED` (`tests/test_alerts_and_assistant.py`).

### 15.2 `GET /api/v1/businesses/{business_id}/alerts/events`
- **Purpose**: Stream active and historical alert events.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/alerts.py`
- **Test Status**: `VERIFIED`.

### 15.3 `POST /api/v1/businesses/{business_id}/alerts/evaluate`
- **Purpose**: Evaluate all active alert rules against live financial ledgers and suppress duplicate alerts within 24h.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/alerts.py`
- **Test Status**: `VERIFIED` (`tests/test_alerts_and_assistant.py`).

### 15.4 `POST /api/v1/businesses/{business_id}/alerts/events/{id}/acknowledge` & `/resolve`
- **Purpose**: Human acknowledgment and resolution actions for alert events.
- **Auth**: `FINANCE_MANAGER` or `OWNER`.
- **Source**: `backend/app/api/v1/alerts.py`
- **Test Status**: `VERIFIED`.

---

## 16. Conversational AI Financial Assistant (`/api/v1/businesses/{business_id}/assistant`)

### 16.1 `POST /api/v1/businesses/{business_id}/assistant/query`
- **Purpose**: Ask natural language financial questions answered via 10 verified deterministic backend tools with strict grounded citations and zero hallucination.
- **Request Body**: `{"query": "What is our 30-day forecast and cash runway?"}`
- **Response**: `200 OK` -> `AssistantResponse` (`query`, `answer`, `citations`, `tool_data`, `assumptions_note`).
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/assistant.py`, `backend/app/services/assistant_service.py`
- **Test Status**: `VERIFIED` (`tests/test_alerts_and_assistant.py`, `tests/test_system_integration_repairs.py`).

### 16.2 `GET /api/v1/businesses/{business_id}/assistant/tools`
- **Purpose**: Introspect verified financial tools available to the assistant.
- **Available Tools**:
  1. `get_actual_cash_balance`: Cleared liquid bank balances and reserve headroom.
  2. `get_overdue_invoices`: Unpaid receivables and predicted collection delays.
  3. `get_forecast_summary`: Multi-horizon deterministic forecast projections.
  4. `get_simulation_summary`: Monte Carlo stochastic risk metrics and breach probabilities.
  5. `get_recommendations`: Active constrained prescriptive actions and impact.
  6. `get_expenses_summary`: Category-wise expense breakdown from posted outflows.
  7. `get_recorded_payments`: Historical customer payment settlements.
  8. `get_cash_flow_risks`: Sentinel alert rules and active breach events.
  9. `get_scenario_summary`: Custom comparative decision scenarios.
  10. `get_historical_cash_flow`: Aggregated revenue, expenses, and net cash flow.
- **Auth**: `VIEWER` or higher.
- **Source**: `backend/app/api/v1/assistant.py`
- **Test Status**: `VERIFIED`.
