# cashFlow — Next Steps & Continuation Plan

This document defines the prioritized continuation roadmap for developers and AI agents working on **cashFlow**.

---

## A. Current Stage
- **Development Stage**: **Stage 4: Production Readiness, Authentication Enhancements, Dockerization, Deployment Preparation, Security Validation, and Product Cleanup (COMPLETED & VERIFIED)**
  - **Stage 1 Status**: Complete and Verified (Foundation, Database, Security, Financial Data Import).
  - **Stage 2 Status**: Complete and Verified (Financial Engine, Reconciliation, Multi-Horizon Forecasting, Risk Prediction, Spatial UI, Dual Theme Support, Theme-Aware Logos, and Multiple-File Uploads).
  - **Stage 3 Status**: Complete and Verified (Advanced AI, Monte Carlo Simulation, Financial Decision Optimisation, Conversational AI Assistant, Configurable Alerts, and Canonical Sage Green Branding).
  - **Stage 4 Status**: Complete and Verified (Google Authentication with official GIS flow and server-side validation, Password Visibility Toggles on Sign-In & Sign-Up, Official Tagline update, Removal of internal stage references from customer-facing UI, Production Multi-stage Dockerization for backend and frontend, Docker Compose with PostgreSQL 16 & persistent volumes, Security Validation, and Full Test Suite passes).

---

## B. Completed Stage 4 Deliverables
- [x] **Google Authentication**:
  - Implemented `POST /api/v1/auth/google` and `GET /api/v1/auth/google/config`.
  - Server-side ID token verification using `google.oauth2.id_token` validating audience, issuer, and email verification claims.
  - Automatic business workspace creation for newly registered Google users.
  - Safe account linking for existing email/password accounts with matching verified email.
  - Reusable frontend `GoogleSignInButton.tsx` with official Google multi-color SVG and informative error states.
- [x] **Password Visibility Toggle**:
  - Added Eye/EyeOff show/hide password buttons to sign-in and sign-up pages.
  - Independent visibility toggle on both Password and Confirm Password inputs.
  - Keyboard accessible, screen-reader friendly (`aria-label`), `type="button"` preventing accidental form submission.
- [x] **Official Tagline & Customer UI Cleanup**:
  - Replaced stage promotional text on login and sign-up pages with official tagline: *"Turn financial data into confident business decisions."*
  - Removed all user-facing references to "Stage 1", "Stage 2", "Stage 3", "Stage 4" from landing page, dashboard, and decisions pages.
- [x] **Production Dockerization & Container Startup Verification**:
  - `backend/Dockerfile`: Multi-stage build with standard `/opt/venv` virtual environment, unprivileged `appuser` (non-root, UID 1000), `libpq-dev`, `curl` healthcheck, `requests`, `google-auth`, `email-validator`, and `psycopg2-binary`.
  - `frontend/Dockerfile`: Multi-stage build with unprivileged `nextjs` user (non-root), production optimization, and container healthcheck.
  - `docker-compose.yml`: PostgreSQL 16 Alpine, unexposed db port to host, healthcheck dependencies, service-to-service networking, named persistent volumes (`postgres_data`, `backend_uploads`), clean modern schema without obsolete top-level `version`.
  - `.dockerignore` for both frontend and backend excluding `.env`, `.git`, caches, and uploads.
  - Verified live runtime orchestration: `cashflow_postgres`, `cashflow_backend`, and `cashflow_frontend` running healthy simultaneously.
- [x] **Production Security Validation**:
  - Zero hardcoded secrets; documented `.env.example`.
  - Cleaned repository index by untracking compiled `.pyc` and local `.db` files; created root `.gitignore`.
  - Tenant isolation verified on all queries; password hashing via Bcrypt; tokenized timing-safe password recovery.
- [x] **Full Automated & Runtime Testing**:
  - Pytest: **35 passed out of 35 tests in 71.08s**.
  - TypeScript: `npx tsc --noEmit` exited with **code 0 (zero errors)**.
  - Production Build: `npm run build` compiled all 23 routes with **code 0**.
  - Browser subagent verified login, register, password visibility, tagline, and dashboard.
- [x] **PostgreSQL Database Connectivity & Health Monitoring**:
  - Normalized `DATABASE_URL` parsing (`postgresql+psycopg2://`) with TLS/SSL encryption (`sslmode=require`).
  - Implemented dynamic database health checks (`SELECT NOW();` / `SELECT 1;`) exposed at `/health` and `/api/v1/health`.
  - Configured Docker Compose `env_file: - ./backend/.env` without leaking credentials.
  - Added unit and integration tests in `backend/tests/test_database_connection.py`.
- [x] **Decisions Screen Client-Side Resilience & Schema Contract**:
  - Eliminated `TypeError: Cannot read properties of undefined (reading 'toFixed')` at `/decisions`.
  - Added finite numeric checks and currency formatting guards for null/undefined/string values.
  - Added explicit Pydantic response models (`GoalOut`, `ScenarioOut`, `OptimisationPlanOut`, `RecommendationOut`) and fixed baseline attribute expiration.
- [x] **Synthetic Benchmark Dataset (Acme Consulting Tech Ltd)**:
  - Adapted excerpt to cashFlow multi-tenant schema in `backend/app/db/seeds/acme_synthetic_dataset.sql`.
  - Automated seeding and analytical processing script in `backend/app/scripts/seed_acme_synthetic_data.py`.
  - Seeded both PostgreSQL 16 (Docker) and SQLite (`cashflow.db`).
- [x] **Critical System-Wide Bug Investigation & Integration Repairs**:
  - **BUG 1 Fixed & Verified**: Added Alembic migration `c3d4e5f6a7b8` linking payments and transactions; statement import confirmation generates authoritative `Transaction` ledger records with rule-based categorization, links `imported_record_id`, and immediately updates account balance; updated `ForecastingService` and `SimulationService` to account for both `Transaction` and unlinked `ImportedRecord` outflows.
  - **BUG 2 Fixed & Verified**: Invoice payment creation creates exactly one `Transaction` linked by `payment_id`, prevents double cash counting by linking matching unreconciled bank transactions, validates `amount > 0` and `amount <= unpaid`, enforces idempotency, updates deposit account balance; added `PATCH /invoices/{id}/status` blocking direct transition to `PAID` without payment; updated frontend invoice payment modal with account selection and remaining balance helper.
  - **BUG 3 Fixed & Verified**: Fixed `AttributeError: 'dict' object has no attribute 'horizon_days'` by implementing dual dict/object safe attribute access in `AssistantService`; implemented 5 missing grounded tools (`get_expenses_summary`, `get_recorded_payments`, `get_cash_flow_risks`, `get_scenario_summary`, `get_historical_cash_flow`); expanded query routing with out-of-scope non-financial guardrails; updated frontend assistant error handler to diagnostically display backend errors instead of generic disconnect notices.
  - **Automated Regression Suite**: Authored `backend/tests/test_system_integration_repairs.py` (4/4 passing), elevating total test count to **39 PASSED, 0 FAILED** (100% pass rate).

---

## C. Recommended Next Priorities (Post-Bug Fixes)
1. **Live Staging Deployment & Domain Provisioning**:
   - Deploy Docker Compose or Kubernetes manifests to staging server with automated SSL provisioning (Let's Encrypt / Caddy reverse proxy).
2. **Automated End-to-End Browser Playwright/Cypress Suite**:
   - Run end-to-end browser tests in CI/CD pipeline simulating CSV file upload, invoice creation, payment recording, and AI assistant questioning.
3. **Plaid / Banking Open Banking Connector**:
   - Implement live bank feed aggregation for real-time automated statement syncing.


---

## C. Remaining Manual Deployment Steps (User Machine)
1. **Google Cloud Console Setup**:
   - Create OAuth 2.0 Client ID (Web Application) at https://console.cloud.google.com/apis/credentials.
   - Set Authorized JavaScript Origins: `http://localhost:3000` (and your production domain).
   - Set Authorized Redirect URIs: `http://localhost:3000/api/auth/callback/google` (and your production domain).
   - Copy Client ID and Secret to `.env` (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`).
2. **Container Registry Image Build & Push**:
   - Log in to Docker registry: `docker login`
   - Build, tag, and push images using documented commands.
