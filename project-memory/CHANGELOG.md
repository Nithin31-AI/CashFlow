# cashFlow — Project Changelog

This document maintains a chronological development history of the **cashFlow** application.

---

## [2026-10-24] — Stage 1: Foundation, Database, Security & Financial Data Import

### Objective
Establish the production-grade foundation, database models, multi-tenant RBAC security, financial account tracking, and end-to-end 8-step statement import workflow with automated validation and ledger commits for small service businesses.

### Development Stage
**Stage 1 of 4** (Completed & Verified)

### Files Created
- **Backend Architecture & Config**:
  - `backend/app/main.py`: FastAPI application entrypoint with CORS, error handlers, and router inclusions.
  - `backend/app/core/config.py`: Pydantic settings loading JWT secret, DB URL, upload limits, and token expiry.
  - `backend/app/core/security.py`: Password hashing via `passlib[bcrypt]` and JWT HS256 encoder/decoder.
  - `backend/app/db/session.py`: SQLAlchemy 2.0 engine, scoped session factory, and base declarative class.
  - `backend/alembic/`: Database migration environment and initial schema migration `9c2481321bb2`.
- **Database Models (`backend/app/models/`)**:
  - `user.py`, `business.py`, `account.py`, `upload.py`, `audit.py`.
- **API Schemas & Endpoints (`backend/app/schemas/`, `backend/app/api/v1/`)**:
  - `auth.py`, `businesses.py`, `accounts.py`, `uploads.py`, `audit.py`, `deps.py`.
- **Financial Import Processing Engine (`backend/app/services/`)**:
  - `file_service.py`: Magic-byte MIME detection, SHA-256 deduplication, directory containment storage.
  - `import_service.py`: Chunked CSV parser, date normalizer, decimal conversion, heuristic column mapper.
  - `validation_service.py`: Row-level checks (missing date/amount, unrecognized format, duplicate transaction IDs).
- **Automated Test Suite (`backend/tests/`)**:
  - `conftest.py`: StaticPool SQLite in-memory test fixture with dependency overrides.
  - `test_auth.py`, `test_multitenancy.py`, `test_accounts.py`, `test_uploads.py`.
- **Frontend Application (`frontend/`)**:
  - `app/layout.tsx`, `app/page.tsx`, `app/login/page.tsx`, `app/register/page.tsx`.
  - `app/dashboard/layout.tsx`, `app/dashboard/page.tsx`, `app/dashboard/accounts/page.tsx`.
  - `app/dashboard/import/page.tsx`, `app/dashboard/audit/page.tsx`.
  - `components/Navbar.tsx`, `components/Sidebar.tsx`, `components/Logo.tsx`.
  - `lib/api.ts`: Typed fetch client with JWT bearer interceptors and 401 redirection.
  - `public/images/cashflow-logo.png`, `public/cashflow-logo.png`: Official cashFlow logo asset.

### Features Implemented
- User authentication with bcrypt hashing and JWT bearer tokens.
- Tenant isolation ensuring users only access businesses where they hold verified membership.
- Financial account management (checking, savings, credit, cash-on-hand) with currency tracking.
- 8-step statement import workflow:
  1. Upload CSV with magic byte validation & SHA-256 deduplication.
  2. Background metadata extraction.
  3. Heuristic column mapping (date, description, amount/debit/credit, balance, reference).
  4. Manual column mapping review & adjustment.
  5. Row-by-row validation with pass/warning/error categorization.
  6. Financial statement preview.
  7. Human approval gate prior to ledger modification.
  8. Atomic batch commit to `imported_records` and account balance update.
- Tamper-evident audit logging for auth, memberships, account modifications, uploads, and imports.

### Database Changes
- Generated and executed initial Alembic migration `9c2481321bb2` creating 11 core tables:
  `users`, `password_reset_tokens`, `businesses`, `business_memberships`, `financial_accounts`, `uploaded_files`, `import_jobs`, `import_mappings`, `import_validation_results`, `imported_records`, and `audit_logs`.

### API Changes
- Implemented 23 REST endpoints under `/api/v1/` covering Auth, Businesses, Memberships, Accounts, Uploads, Imports, Audit Logs, and System Health.

### Tests Executed & Results
- **Command**: `pytest backend/tests -v`
- **Result**: `11 passed in 14.03s` (100% pass rate).
- **End-to-End Verification**: Executed browser automation session verifying registration, workspace setup, statement upload (`sample_bank_statement.csv`), column mapping, validation, approval, and live dashboard rendering (Net Cash: ₹2,94,000).

### Bugs Discovered & Fixed
1. *PowerShell `mkdir -p` syntax failure*: Resolved by using PowerShell `New-Item -ItemType Directory -Force`.
2. *Next.js 16 installation lock & hang*: Pinned package dependencies to Next.js 15.1.7, React 19, and Tailwind CSS 3.4.1.
3. *Missing `autoprefixer` build error*: Added `autoprefixer` to dev dependencies to complete Next.js compilation.
4. *Pytest duplicate email conflict*: Updated `tests/test_uploads.py` to generate unique test emails (`uploader_<uuid>@test.com`).
5. *SQLite `:memory:` session disconnect*: Configured `StaticPool` in `conftest.py` so in-memory test connections share identical schema.
6. *FastAPI `get_db` generator override mismatch*: Unified `get_db` import paths across `deps.py`, `conftest.py`, and `app.db.session`.

### Important Decisions
- Recorded `DEC-001` through `DEC-007` in `project-memory/DECISIONS_LOG.md`.

---

## [2026-10-24] — Persistent Project Memory & Continuity System

### Objective
Establish a persistent, verified project memory system inside the repository to ensure context continuity across AI development sessions without loss of requirements, architecture, schema, or testing status.

### Files Created
- `project-memory/PROJECT_CONTEXT.md`
- `project-memory/CURRENT_STATE.md`
- `project-memory/ARCHITECTURE.md`
- `project-memory/REQUIREMENTS.md`
- `project-memory/DATABASE_SCHEMA.md`
- `project-memory/API_DOCUMENTATION.md`
- `project-memory/UI_DESIGN_SYSTEM.md`
- `project-memory/AI_ML_DOCUMENTATION.md`
- `project-memory/SECURITY_RULES.md`
- `project-memory/TESTING_STATUS.md`
- `project-memory/DECISIONS_LOG.md`
- `project-memory/CHANGELOG.md`
- `project-memory/NEXT_STEPS.md`
- `AGENTS.md` (Repository root session protocol)

### Documentation Updated
- All 13 memory files synchronized with real repository code, database schema, and test results.

---

## [2026-10-24] — Stage 2: Financial Engine, Reconciliation, Forecasting, Risk Prediction, Spatial UI, Theme Support & Multi-File Uploads

### Objective
Implement Stage 2 financial intelligence architecture: authoritative decimal balance calculations, invoice-payment allocation, internal transfer isolation, intelligent transaction-to-invoice reconciliation matching with Explainable AI confidence scores and review gates, multi-horizon forecasting (7d, 30d, 90d, 180d, 365d), cash-shortage risk prediction, 2.5σ statistical expense anomaly detection, multi-file batch uploads, Spatial UI design system with dual themes (Dark Mode & Light Cream Mode), theme-aware logo assets, and natural vertical window scrolling.

### Development Stage
**Stage 2 of 4** (Completed & Verified)

### Files Created / Modified
- **Database Schema & Migrations**:
  - `backend/alembic/versions/a1b2c3d4e5f6_stage2_financial_engine.py`: Alembic migration adding 8 new tables and extending businesses and financial accounts.
  - `backend/app/models/exchange_rate.py`, `backend/app/models/invoice.py`, `backend/app/models/transaction.py`, `backend/app/models/reconciliation.py`, `backend/app/models/forecast.py`.
- **Financial & AI Services**:
  - `backend/app/services/financial_service.py`: Exact `Decimal` cash arithmetic, internal transfer pairing/exclusion, liquid vs receivables separation.
  - `backend/app/services/currency_service.py`: Multi-currency conversion with provenance tracking.
  - `backend/app/services/reconciliation_service.py`: Candidate matching, confidence scoring, approval and rejection actions.
  - `backend/app/services/forecasting_service.py`: Multi-horizon cash projections with daily points and confidence intervals.
  - `backend/app/services/risk_service.py`: Minimum cash reserve shortfall calculation, invoice payment delay prediction, and 2.5σ statistical expense anomaly detector.
- **API Routers**:
  - `backend/app/api/v1/financial.py`, `transactions.py`, `invoices.py`, `reconciliation.py`, `forecasting.py`, `currencies.py`.
  - Updated `backend/app/api/v1/uploads.py`: Batch multi-file endpoint (`POST /{business_id}/uploads/batch`).
  - Mounted all routers in `backend/app/api/v1/router.py`.
- **Branding & Assets**:
  - `frontend/public/images/cashflow-logo-dark.png`, `frontend/public/cashflow-logo-dark.png`: Light cream logo for dark mode.
  - `frontend/public/images/cashflow-logo-light.png`, `frontend/public/cashflow-logo-light.png`: Dark charcoal logo for light cream mode.
  - `frontend/src/components/Logo.tsx`: Dynamic theme-aware logo selection based on active theme.
- **Frontend Architecture & Pages**:
  - `frontend/src/lib/theme.tsx`: ThemeProvider with system preference and `localStorage` persistence.
  - `frontend/src/components/ThemeToggle.tsx`: Light/Dark/System mode switcher.
  - `frontend/tailwind.config.ts` & `globals.css`: Spatial UI utilities and CSS variables for near-black and warm cream themes.
  - `frontend/src/app/(dashboard)/layout.tsx`: Natural vertical window scrolling with sticky sidebar.
  - `frontend/src/app/(dashboard)/dashboard/page.tsx`: Spatial UI command center with cash position, reserve headroom, and 30-day forecast graph.
  - `frontend/src/app/(dashboard)/invoices/page.tsx`: Invoices list, payment delay warnings, and payment modal.
  - `frontend/src/app/(dashboard)/transactions/page.tsx`: Ledger table, category filtering, and internal transfer modal.
  - `frontend/src/app/(dashboard)/reconciliation/page.tsx`: Explainable AI matching candidates and review actions.
  - `frontend/src/app/(dashboard)/forecast/page.tsx`: Runway forecasting with confidence intervals and expense anomaly reviews.
  - `frontend/src/app/(dashboard)/imports/new/page.tsx`: Multi-file drag-and-drop batch queue with individual file progress and retry.
- **Automated Tests**:
  - `backend/tests/test_financial_engine.py`, `test_batch_uploads.py`, `test_reconciliation.py`, `test_forecasting_and_risk.py`.
  - `backend/tests/conftest.py`: Added `db_session` alias and `test_user` fixture.

### Test Results
- **Automated Tests**: **19 passed out of 19 tests** (`python -m pytest tests -v` in 22.03s).
- **TypeScript Type Validation**: **`npx tsc --noEmit` exited with code 0 (zero errors)** across all Next.js routes.
- **Runtime Verification**: Interactive browser subagent recorded session (`stage2_verification_1792861824162.webp`) verifying full user flows across all 6 core dashboard pages, theme switching, and logo updating.

---

## [2026-10-24] — Stage 3: Advanced AI, Monte Carlo Simulation, Decision Optimisation, Conversational AI, Alerts & Branding Consistency

### Objective
Implement Stage 3 advanced financial intelligence: Monte Carlo stochastic cash-flow simulation engine, business financial goals and constraints, constrained decision optimisation solver, interactive scenario creation and comparison, explainable financial recommendations, grounded tool-calling conversational assistant, configurable automated sentinel alerts with duplicate suppression, model evaluation tracking, single canonical sage-green color (`#8A9A78`), and official CF monogram favicon.

### Development Stage
**Stage 3 of 4** (Completed & Verified)

### Files Created / Modified
- **Branding & Assets**:
  - `frontend/src/app/globals.css`: Standardized single canonical sage-green accent `#8A9A78` across BOTH dark and light themes.
  - `frontend/public/favicon.ico`, `frontend/public/images/cashflow-favicon.png`, `frontend/src/app/favicon.ico`: High-resolution official CF monogram favicon with transparent background.
  - `frontend/src/app/layout.tsx`: Configured metadata icons with official favicon.
- **Database Schema & Migrations**:
  - `backend/alembic/versions/b2c3d4e5f6a7_stage3_advanced_ai_simulation.py`: Alembic migration adding 8 new tables: `financial_goals`, `simulation_runs`, `saved_scenarios`, `optimisation_plans`, `financial_recommendations`, `alert_rules`, `alert_events`, `model_evaluations`.
  - `backend/app/models/goal.py`, `simulation.py`, `scenario.py`, `recommendation.py`, `alert.py`, `model_evaluation.py`.
  - `backend/app/models/invoice.py`: Added `paid_amount` alias property.
  - `backend/app/models/__init__.py`: Exported all Stage 3 models.
- **Backend Services**:
  - `backend/app/services/simulation_service.py`: 1000-path stochastic Monte Carlo simulation, daily percentile envelopes (P10/P50/P90), reserve breach probability, expected shortfall, seed reproducibility.
  - `backend/app/services/decision_service.py`: Goals and constraints, scenario modeling and comparison, linear constrained solver, explainable recommendations.
  - `backend/app/services/alert_service.py`: Rule evaluation, 24h/48h duplicate suppression, acknowledge/resolve workflows.
  - `backend/app/services/assistant_service.py`: Tool-calling grounded dispatcher (`get_actual_cash_balance`, `get_overdue_invoices`, `get_forecast_summary`, `get_simulation_summary`, `get_recommendations`), prompt injection sanitization, citations.
  - `backend/app/services/financial_service.py`: Added `calculate_cash_position` wrapper with attribute and dict access.
- **API Routers**:
  - `backend/app/api/v1/simulations.py`, `decisions.py`, `alerts.py`, `assistant.py`.
  - Mounted all routers in `backend/app/api/v1/router.py`.
  - `backend/app/api/deps.py`: Added `require_finance_or_higher` alias.
- **Frontend Views & API Client**:
  - `frontend/src/lib/api.ts`: Added Stage 3 TypeScript interfaces and API methods.
  - `frontend/src/components/Sidebar.tsx`: Added navigation links for `/simulation`, `/decisions`, `/assistant`, `/alerts`.
  - `frontend/src/app/(dashboard)/simulation/page.tsx`: Monte Carlo simulation interface with parameter sliders, P10/P50/P90 cards, breach risk %, and daily percentile envelope.
  - `frontend/src/app/(dashboard)/decisions/page.tsx`: Goals & constraints, custom scenario simulator, side-by-side comparison, constrained optimisation plan with user confirmation, and explainable recommendations.
  - `frontend/src/app/(dashboard)/assistant/page.tsx`: Grounded conversational AI assistant with suggested prompt pills, verified data citations badges, and assumptions notes.
  - `frontend/src/app/(dashboard)/alerts/page.tsx`: Sentinel alerts activity stream, acknowledge/resolve actions, "Evaluate Alerts Now" trigger, and configurable rule management.
- **Automated Tests**:
  - `backend/tests/test_simulations.py`: Tests Monte Carlo simulation reproducibility, percentiles, payment delays, and invoice integration.
  - `backend/tests/test_decisions_and_scenarios.py`: Tests goal creation, constrained optimisation solver, and scenario comparisons.
  - `backend/tests/test_alerts_and_assistant.py`: Tests alert rules, 24h duplicate suppression, and conversational assistant tool calling.

### Test Results
- **Automated Tests**: **25 passed out of 25 tests** (`python -m pytest tests -v` in 14.24s).
- **TypeScript Type Validation**: **`npx tsc --noEmit` exited with code 0 (zero errors)** across all Next.js routes.
- **Runtime Verification**: Interactive browser subagent recorded session (`stage3_verification_1792867272444.webp`) verifying full user flows across all 4 new views, favicon rendering, and canonical sage-green `#8A9A78` styling.

---

## [2026-10-25] — Stage 4: Production Readiness, Authentication Enhancements, Dockerization, Security Validation & Product Cleanup

### Objective
Implement Stage 4: Google authentication with server-side ID token validation and safe account linking, show/hide password visibility toggle across authentication forms, updated official product tagline ("Turn financial data into confident business decisions."), removal of internal stage references from customer-facing UI, production-grade multi-stage Docker containerization with non-root security, Docker Compose with PostgreSQL 16 Alpine and named volumes, production security validation, and complete test verification.

### Development Stage
**Stage 4 of 4** (Completed & Verified)

### Files Created / Modified
- **Authentication & Backend Security**:
  - `backend/app/core/config.py`: Added `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` settings.
  - `backend/app/schemas/auth.py`: Added `GoogleAuthRequest` and `GoogleConfigResponse` models.
  - `backend/app/services/google_auth.py`: Created Google OAuth service with server-side ID token verification via `google.oauth2.id_token`, audience checks, issuer validation, and email verification assertion.
  - `backend/app/api/v1/auth.py`: Implemented `GET /api/v1/auth/google/config` and `POST /api/v1/auth/google` with automatic workspace creation for new users and safe account linking for existing users.
  - `backend/app/main.py`: Added `/api/v1/health` route alias alongside `/health`.
  - `backend/requirements.txt`: Added `google-auth>=2.28.0` and `psycopg2-binary>=2.9.9`.
- **Frontend Authentication & UI**:
  - `frontend/src/components/GoogleSignInButton.tsx`: Created reusable Google sign-in button using official Google Identity Services (GIS), multi-color Google SVG icon, loading states, and configuration error handling.
  - `frontend/src/app/(auth)/login/page.tsx`: Added Google Sign-In button, show/hide password visibility toggle (Eye/EyeOff, accessible `aria-label`, `type="button"`), updated official product tagline.
  - `frontend/src/app/(auth)/register/page.tsx`: Added Google Sign-In button, independent show/hide toggles for both Password and Confirm Password fields, password match validation, updated official product tagline.
  - `frontend/src/lib/api.ts`: Added `googleAuth` and `getGoogleConfig` methods; cleaned internal stage comments.
- **Customer UI Cleanup (Stage Text Removal)**:
  - `frontend/src/app/page.tsx`: Replaced "Stage 2: Financial Engine..." badge with "Financial Intelligence Platform".
  - `frontend/src/app/(dashboard)/dashboard/page.tsx`: Replaced "STAGE 2 FINANCIAL INTELLIGENCE" badge with "FINANCIAL INTELLIGENCE ENGINE".
  - `frontend/src/app/(dashboard)/decisions/page.tsx`: Replaced "Stage 3 Production" badge with "Autonomous Solver".
- **Dockerization & Deployment Preparation**:
  - `backend/Dockerfile`: Multi-stage build with unprivileged non-root user `appuser` (UID 1000), `libpq-dev`, `curl` healthcheck, and optimized dependencies.
  - `frontend/Dockerfile`: Multi-stage build with unprivileged non-root user `nextjs` (UID 1001), Next.js production bundle, and `wget` healthcheck.
  - `docker-compose.yml`: Configured PostgreSQL 16 Alpine, unexposed db port to host, service dependencies with healthchecks, persistent volumes `postgres_data` and `backend_uploads`, and custom bridge network `cashflow_network`.
  - `backend/.dockerignore` & `frontend/.dockerignore`: Excluded `.env`, `.git`, local databases, caches, and test artifacts.
  - `.gitignore`: Created comprehensive root `.gitignore` and untracked previously committed compiled `.pyc` and `.db` files from the repository index.
  - `.env.example`: Updated with Google OAuth configuration, PostgreSQL variables, and instructions.
- **Automated Tests**:
  - `backend/tests/test_auth.py`: Added 4 new tests (`test_google_config_endpoint`, `test_google_auth_new_user_and_auto_workspace`, `test_google_auth_existing_user_linking`, `test_google_auth_empty_token_fails`).
  - `backend/tests/test_alerts_and_assistant.py`: Added resilience test for null/undefined alert categories.

### Test Results
- **Automated Tests**: **30 passed out of 30 tests** (`python -m pytest tests -v` in 20.32s).
- **TypeScript Type Validation**: **`npx tsc --noEmit` exited with code 0 (zero errors)** across all Next.js routes.
- **Frontend Production Build**: **`npm run build` compiled all 23 static and dynamic routes with code 0**.
- **Runtime Verification**: Interactive browser subagent recorded session (`stage4_auth_and_ui_verification_1792878142330.webp`) verifying login page, register page, password visibility toggles, Google button, and stage text removal across dashboard and decisions pages.
