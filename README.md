# cashFlow
### PLAN • FORECAST • GROW

> **AI-Powered Financial Intelligence SaaS Platform for Small Service-Based Businesses**
>
> *Turn financial data into confident business decisions.*

[![Tests](https://img.shields.io/badge/tests-35%2F35%20passing-10A86B?style=flat-square)](backend/tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.1.7-black?style=flat-square)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=flat-square)](docker-compose.yml)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square)](frontend/tsconfig.json)

---

## 1. Executive Overview

**cashFlow** is a production-grade, multi-tenant financial intelligence platform engineered specifically for the cash-timing and liquidity challenges faced by small service-based businesses—such as IT service companies, consulting firms, digital agencies, and freelancers.

Unlike traditional accounting software designed solely for retrospective compliance and tax filing, **cashFlow** provides forward-looking, cash-basis decision intelligence:
- **Separates Cleared Cash from Projected Receivables**: Unpaid invoices and lines of credit are never treated as spendable cash.
- **Automated Multi-Horizon Forecasting**: Projects cash runways over 7-day, 30-day, 90-day, 180-day, and 365-day horizons with daily statistical confidence bounds.
- **Monte Carlo Stochastic Runway Simulations**: Executes 1,000 stochastic simulation paths calculating reserve breach probabilities and expected shortfalls under volatile revenue conditions.
- **Constrained Decision Optimization**: Linear solver that evaluates hiring capacity, CapEx timing, and supplier payment sequencing against minimum cash reserve constraints.
- **Grounded Conversational AI Assistant**: Direct tool-calling agent with strict prompt-injection defenses and verified ledger evidence citations—**zero hallucinated or fabricated numbers**.
- **Production Containerization**: Multi-stage Docker builds with unprivileged non-root security (`appuser` / `nextjs`), PostgreSQL 16 Alpine orchestration, and automated health monitoring.

---

## 2. Core System Features & Capabilities

### 🏢 Multi-Tenant SaaS & RBAC Security
- **Strict Tenant Isolation**: Enforced at the database and API layer. Every query mandates `business_id` validation against verified user memberships. One business can never view, query, or infer another business's financial data.
- **Role-Based Access Control (RBAC)**:
  - `OWNER`: Full administrative authority, team management, permissions, and financial approvals.
  - `FINANCE_MANAGER`: Manage bank accounts, execute reconciliation, approve imports to the ledger.
  - `ACCOUNTANT`: Upload files, configure column mappings, review validation previews. Cannot commit imports to the ledger.
  - `VIEWER`: Read-only access to authorized reports, dashboards, and accounts.

### 📥 8-Step Financial Data Ingestion Pipeline
1. **Upload & Verification**: Validates MIME magic bytes, enforces 15 MB file size limits, computes SHA-256 hashes to prevent duplicate statement ingestion, and stores raw files in private non-public storage.
2. **Structure & Encoding Detection**: Auto-detects delimiters (`,` `;` `\t` `|`) and character encodings.
3. **Intelligent Column Recognition**: Heuristic algorithms score headers against financial synonyms for `date`, `description`, `reference`, `debit`, `credit`, `amount`, and `balance`.
4. **Interactive Mapping Review**: Custom mapping interface for mapping review and date pattern selection (`DD/MM/YYYY`, `YYYY-MM-DD`, etc.).
5. **Row-Level Decimal Validation**: Rigorous monetary formatting validation, signed amounts, and accounting parentheses notation `(1,500.00)` $\rightarrow$ `-1500.00`.
6. **Error Previews**: Displays interactive validation tables highlighting invalid or ambiguous rows without discarding raw data.
7. **Explicit Approval Gate**: Consequential ledger commits require explicit confirmation by an `OWNER` or `FINANCE_MANAGER`.
8. **Audit Provenance**: Every imported transaction retains an immutable link to its source file, batch job ID, and row index.
- **Multi-File Batch Queue**: Drag-and-drop batch upload queue supporting concurrent uploads with individual progress tracking.
- **Extensible OCR Interface**: Extensible extraction module for vector PDF parsing and OCR receipt scanning.

### 💰 Authoritative Financial Engine
- **Deterministic Math**: Pure `Decimal` arithmetic. Formula: `Ending Balance = Opening Balance + Inflows - Outflows`.
- **Internal Transfer Isolation**: Automatically detects and pairs transfers between internal accounts, netting them to zero so they never distort operating revenue or expenses.
- **Multi-Currency Engine**: India-first with INR (`₹`) as the default reporting currency; stores exchange rate provenance and supports USD, EUR, GBP, AED, and SGD.
- **Invoices & Receivables**: Tracks invoices across statuses (`DRAFT`, `SENT`, `PAID`, `PARTIALLY_PAID`, `OVERDUE`) with partial payment allocations.
- **Intelligent Reconciliation**: Multi-factor candidate matching (`EXACT`, `PROBABLE`, `AMBIGUOUS`) pairing bank transactions with open invoices, accompanied by Explainable AI confidence scores and review actions.

### 📈 AI Forecasting & Risk Management
- **Multi-Horizon Projections**: Daily forecast trajectories over 7d, 30d, 90d, 180d, and 365d with lower and upper confidence intervals (`[confidence_lower, confidence_upper]`).
- **Minimum Cash Reserve Shortfall Alerts**: Evaluates projected trajectories against minimum safety buffer thresholds to predict future liquidity crunches before they happen.
- **Statistical Expense Anomaly Detection**: 2.5$\sigma$ outlier detection flags sudden spikes in operational expenses.
- **Invoice Payment Delay Modeling**: Analyzes historical customer payment lag to adjust cash collection curves realistically.

### 🎲 Monte Carlo Simulations & Autonomous Decisions
- **1,000-Path Monte Carlo Simulation**: Models cash trajectories under stochastic client payment delays and revenue fluctuations; calculates reserve breach probability % and Expected Shortfall (CVaR).
- **Business Financial Goals**: Hard and soft constraints (e.g. `MIN_CASH_BUFFER`, `TARGET_SAVINGS`, `DEBT_REDUCTION`).
- **What-If Scenario Modeling**: Test hypotheses (hiring developers, CapEx investments, client payment delays) and view side-by-side metric comparisons.
- **Constrained Optimization Solver**: Recommends mathematically optimal sequences for accounts payable and capital spending to preserve solvency.
- **Explainable Recommendations**: Contextual action recommendations complete with financial citations, trade-off notes, and "Accept" / "Dismiss" workflows.

### 🤖 Grounded Conversational AI Assistant & Sentinel Alerts
- **Verified Tool-Calling Dispatcher**: Conversational agent connects directly to backend services (`get_actual_cash_balance`, `get_overdue_invoices`, `get_forecast_summary`, `get_simulation_summary`, `get_recommendations`).
- **Zero Hallucinations**: Prompt-injection sanitized, grounded strictly in live database facts, displaying data citation badges for all presented figures.
- **Sentinel Financial Alerts**: Configurable automated alert rules with 24h/48h duplicate suppression, severity levels (`CRITICAL`, `WARNING`, `INFO`), and acknowledge/resolve audit logs.

### 🎨 Spatial UI Design System & Modern Authentication
- **Dual Themes**: Handcrafted Dark Charcoal (`#0B0D0B`) and Warm Cream (`#F7F4EA`) themes with zero flicker-of-unthemed-content (FOUC) and theme-aware logo switching.
- **Canonical Sage Green (`#8A9A78`)**: Single unified brand accent across light and dark modes.
- **Official CF Monogram**: High-resolution favicon asset and branded application mark.
- **Modern Authentication**:
  - Google OAuth 2.0 with server-side ID token verification (`google.oauth2.id_token`) and automatic workspace setup.
  - Email/Password with bcrypt salt hashing and independent show/hide password visibility toggles (`aria-label` accessible).
  - Timing-safe, zero-knowledge tokenized password recovery.

---

## 3. System Architecture & Topology

```
+-------------------------------------------------------------------------------+
|                       Docker Network: cashflow_network                        |
|                                                                               |
|  +--------------------+    +--------------------+    +---------------------+  |
|  |     frontend       |    |      backend       |    |         db          |  |
|  |  (Next.js 15)      |    |    (FastAPI)       |    |   (PostgreSQL 16)   |  |
|  |  Port: 3000        |    |  Port: 8000        |    |   Internal: 5432    |  |
|  |  User: nextjs:1001 |    |  User: appuser:1000|    |   (Not host bound)  |  |
|  |  Multi-stage build |    |  Multi-stage build |    |   postgres:16-alpine|  |
|  +---------+----------+    +---------+----------+    +----------+----------+  |
|            │                         │                          │             |
+------------│─────────────────────────│──────────────────────────│-------------+
             │                         │                          │
       Host Port 3000            Host Port 8000              Named Volume:
   (Web Browser / Client)     (REST API / Docs)         cashflow_postgres_data
```

### High-Level Data Flow

```
Raw Documents (CSV / XLSX / PDF)
             │
             ▼
[1. Secure File Ingestion] ──── Magic bytes check, SHA-256 deduplication, non-public storage
             │
             ▼
[2. Authoritative Ledger] ───── Decimal arithmetic, internal transfer pairing, invoice allocation
             │
             ▼
[3. Financial Intelligence] ─── Multi-horizon forecasting, 2.5σ anomaly detection, reserve shortfall
             │
             ▼
[4. Stochastic Simulation] ──── 1,000-run Monte Carlo engine, percentile envelopes (P10/P50/P90)
             │
             ▼
[5. Decision Optimisation] ──── Constrained linear solver, scenario comparisons, explainable actions
             │
             ▼
[6. Grounded AI Assistant] ──── Read-only tool-calling dispatcher with verified ledger citations
```

---

## 4. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Framework** | **Next.js 15.1.7** (React 19, TypeScript 5.x) using App Router |
| **Styling & Icons** | **Tailwind CSS 3.4.1**, CSS Variables, **Lucide React** 0.468 |
| **Theme Engine** | Custom `ThemeProvider` (Dark Charcoal & Warm Cream) with zero FOUC |
| **Backend Framework** | **Python 3.12**, **FastAPI 0.124**, **Uvicorn** (ASGI) |
| **Validation & Schemas** | **Pydantic v2** (2.12), `pydantic-settings` |
| **Database & ORM** | **PostgreSQL 16** (production) / **SQLite** (local test), **SQLAlchemy 2.0.52**, **Alembic 1.20** |
| **File Parsing & Math** | **Pandas 3.0**, **OpenPyXL 3.1**, **pdfplumber 0.11**, **Pillow 12.2**, exact `Decimal` |
| **Security & Auth** | `passlib[bcrypt]`, `python-jose`, `google-auth 2.28`, SHA-256 token hashing |
| **Containerization** | **Docker** (Multi-stage unprivileged builds), **Docker Compose** |
| **Testing & QA** | **pytest 9.1**, `pytest-asyncio`, `httpx`, `tsc --noEmit` |

---

## 5. Repository Directory Layout

```
Cash_Flow/
├── backend/
│   ├── alembic/                 # Alembic migration revisions
│   │   ├── versions/            # 9c2481321bb2, a1b2c3d4e5f6, b2c3d4e5f6a7
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py          # Auth & RBAC dependencies (RequireBusinessRole)
│   │   │   └── v1/              # Versioned API routes (15 specialized routers)
│   │   ├── core/
│   │   │   ├── config.py        # Environment settings (Pydantic-Settings)
│   │   │   ├── security.py      # Password hashing, JWT generation, reset tokens
│   │   │   ├── audit.py         # Tamper-evident credential-sanitized audit logger
│   │   │   └── storage.py       # Magic-byte file validation, deduplication storage
│   │   ├── db/
│   │   │   └── session.py       # SQLAlchemy engine & session factory
│   │   ├── models/              # SQLAlchemy 2.0 ORM models (22 entities)
│   │   ├── schemas/             # Pydantic v2 request & response schemas
│   │   ├── services/            # Core financial & simulation algorithms
│   │   │   ├── financial_service.py    # Decimal math, balance calculation
│   │   │   ├── currency_service.py     # Multi-currency exchange rate engine
│   │   │   ├── reconciliation_service.py # Explainable invoice-bank matching
│   │   │   ├── forecasting_service.py  # Multi-horizon statistical forecasting
│   │   │   ├── risk_service.py         # Reserve shortfall & 2.5σ anomaly detector
│   │   │   ├── simulation_service.py   # 1,000-path Monte Carlo engine
│   │   │   ├── decision_service.py     # Constrained solver & scenario comparison
│   │   │   ├── alert_service.py        # Sentinel alert rule evaluator & suppression
│   │   │   ├── assistant_service.py    # Grounded tool-calling AI dispatcher
│   │   │   ├── google_auth.py          # Google OAuth ID token verification
│   │   │   ├── csv_parser.py           # Chunked delimiter-detecting parser
│   │   │   ├── excel_parser.py         # OpenPyXL spreadsheet parser
│   │   │   └── extraction/             # Vector PDF & OCR receipt extraction
│   │   └── main.py              # FastAPI app with CORS & security middleware
│   ├── tests/                   # 30 comprehensive automated tests (100% pass)
│   ├── Dockerfile               # Multi-stage production container (appuser:1000)
│   ├── requirements.txt         # Pinned backend dependencies
│   └── .env.example
├── frontend/
│   ├── public/
│   │   ├── favicon.ico          # Official CF monogram favicon
│   │   ├── images/
│   │   │   ├── cashflow-logo-dark.png   # Light cream logo for dark mode
│   │   │   ├── cashflow-logo-light.png  # Dark charcoal logo for light mode
│   │   │   └── cashflow-favicon.png
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/          # /login, /register, /forgot-password, /reset-password
│   │   │   ├── (dashboard)/     # /dashboard, /invoices, /transactions, /reconciliation,
│   │   │   │                    # /forecast, /simulation, /decisions, /assistant,
│   │   │   │                    # /alerts, /imports, /imports/new, /settings
│   │   │   ├── layout.tsx       # Root layout with ThemeProvider and AuthProvider
│   │   │   ├── page.tsx         # Modern landing page
│   │   │   └── globals.css      # Design tokens, canonical sage green (#8A9A78)
│   │   ├── components/          # Spatial UI components, GoogleSignInButton, Sidebar, etc.
│   │   └── lib/                 # api.ts (REST client), auth.tsx, theme.tsx, utils.ts
│   ├── Dockerfile               # Multi-stage production container (nextjs:1001)
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── project-memory/              # 13 verified project memory & architectural documents
├── docker-compose.yml           # Full-stack PostgreSQL, Backend, and Frontend orchestration
├── sample_bank_statement.csv    # Synthetic bank statement for import testing
├── .env.example                 # Root environment template
├── AGENTS.md                    # AI Agent & Developer Operating Protocol
└── README.md                    # System documentation
```

---

---

## 6. PostgreSQL Database Configuration & Connectivity

cashFlow uses PostgreSQL 16+ as its primary production relational database engine via SQLAlchemy 2.0 and `psycopg2-binary`, while supporting SQLite for rapid offline development.

### 6.1. Prerequisites

Before configuring PostgreSQL connectivity, verify you have installed:
- **Python 3.12+** (with `pip` and `venv`)
- **Docker & Docker Compose** (for containerized deployments)
- **Node.js 18+** or **Node.js 20+** and `npm` (for frontend UI)
- **PostgreSQL 16+** database instance (either self-hosted, cloud-hosted, or via Docker Compose)

---

### 6.2. Obtaining a PostgreSQL Connection URL

You can connect cashFlow to any standard PostgreSQL database. The required URI format is:

```text
postgresql://username:password@hostname:port/database?sslmode=require
```

#### Common Hosting Providers:
- **Neon Serverless PostgreSQL (Recommended)**:
  1. Sign in to [Neon Console](https://console.neon.tech/).
  2. Create a project and database (e.g. `cashflow_db`).
  3. Navigate to **Dashboard -> Connection Details**.
  4. Select **Connection string** (Pooled or Direct).
  5. Copy the connection string. Neon automatically appends `?sslmode=require`.
- **AWS RDS / Aurora**:
  - In AWS RDS Console, copy your DB endpoint.
  - Set `sslmode=require` or `sslmode=verify-full` depending on certificate configuration.
- **Supabase**:
  - In Project Settings -> Database, copy the **Connection string (URI)**.
  - Append `?sslmode=require` to enforce TLS certificate validation.
- **Self-Hosted / Local PostgreSQL**:
  ```text
  postgresql://postgres:your_password@localhost:5432/cashflow_db
  ```

> [!NOTE]
> The backend connection module automatically normalizes legacy `postgres://` URLs to standard `postgresql+psycopg2://` driver URIs.

---

### 6.3. Creating the Backend `.env` File

The backend reads its database configuration exclusively from an environment variable named `DATABASE_URL`. Database credentials are never hardcoded in source files.

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Copy the example configuration template:
   ```bash
   cp .env.example .env
   ```

3. Open `backend/.env` in your text editor.

---

### 6.4. Configuring `DATABASE_URL`

Update `DATABASE_URL` in `backend/.env` with your actual connection URL:

```env
# Database connection (PostgreSQL):
DATABASE_URL=postgresql://username:password@hostname/database?sslmode=require

# Security & Session Authentication:
SECRET_KEY=cashflow-production-super-secure-jwt-secret-key-min-32-chars-replace-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# File Storage:
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=15

# Allowed CORS Origins:
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Mode:
ENVIRONMENT=development
DEV_MODE=true
```

> [!CAUTION]
> - Never commit `.env` to version control. The root `.gitignore` excludes `.env` and `.env.*`.
> - Do not remove `sslmode=require` on cloud providers to ensure encrypted data in transit.

---

### 6.5. Testing the PostgreSQL Connection

You can verify database connectivity and execute `SELECT NOW();` using several methods:

#### Method A: Using the Automated Test Suite
Run the dedicated database connection test suite:
```bash
cd backend
python -m pytest tests/test_database_connection.py -v
```

#### Method B: Using Python CLI
Execute a direct health-check query:
```bash
cd backend
python -c "from app.db.session import check_database_health; print(check_database_health())"
```
Expected output:
```json
{'status': 'healthy', 'database': 'postgresql', 'server_time': '2026-10-25 10:58:15.677212+00:00'}
```

#### Method C: Using the System Health Endpoint
When the backend server is running:
```bash
curl http://localhost:8000/api/v1/health
```
Response:
```json
{
  "status": "healthy",
  "app": "cashFlow",
  "tagline": "PLAN • FORECAST • GROW",
  "environment": "development",
  "database": {
    "status": "healthy",
    "database": "postgresql",
    "server_time": "2026-10-25 10:58:15.677212+00:00"
  }
}
```

---

### 6.6. Running Database Migrations

Apply database schema migrations to your PostgreSQL database using Alembic:

```bash
cd backend
python -m alembic upgrade head
```

To seed the initial benchmark dataset (`Acme Consulting Tech Ltd`):
```bash
python app/scripts/seed_acme_synthetic_data.py
```

---

### 6.7. Running the Application Locally

#### 1. Backend Server:
```bash
cd backend
# Activate virtual environment
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at [`http://localhost:8000/docs`](http://localhost:8000/docs).

#### 2. Frontend Client:
In a separate terminal:
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev -- -p 3000
```
Open [`http://localhost:3000`](http://localhost:3000) in your browser.

---

### 6.8. Building and Running with Docker & Docker Compose

Docker Compose coordinates the full stack and automatically injects `DATABASE_URL` into the backend container from `./backend/.env`:

1. Ensure `backend/.env` is configured with your `DATABASE_URL`.
2. Build the Docker images:
   ```bash
   docker compose build
   ```
3. Start the containers in detached mode:
   ```bash
   docker compose up -d
   ```
4. Verify container statuses:
   ```bash
   docker compose ps
   ```
5. Inspect container logs safely (passwords are automatically redacted in logs):
   ```bash
   docker compose logs -f backend
   ```
6. Shut down containers cleanly:
   ```bash
   docker compose down
   ```

---

### 6.9. Troubleshooting Common Database Connection Errors

| Error Message / Symptom | Likely Cause | Solution |
| :--- | :--- | :--- |
| **`DATABASE_URL environment variable is missing or empty`** | `DATABASE_URL` is unset or empty in `backend/.env`. | Create `backend/.env` by copying `backend/.env.example` and set a valid PostgreSQL connection string. |
| **`connection to server at "..." failed: Connection refused`** | Database host is unreachable, down, or firewall is blocking port 5432. | Confirm database server is active and accessible. Verify host address and port. For cloud DBs, check security group IP allowlists. |
| **`password authentication failed for user "..."`** | Incorrect database username or password. | Double-check credentials in `DATABASE_URL`. Ensure special characters in passwords are percent-encoded (e.g. `@` as `%40`). |
| **`no pg_hba.conf entry for host ... no encryption`** | Cloud provider requires SSL/TLS, but `sslmode=require` was omitted. | Ensure `?sslmode=require` is present at the end of `DATABASE_URL`. |
| **`certificate verify failed`** | Hostname mismatch or missing CA certificates in client runtime. | Install `ca-certificates` or verify provider root certificate. Do not disable SSL validation. |
| **`database "..." does not exist`** | The database name specified in the connection URL has not been created yet. | Create the target database in your PostgreSQL instance: `CREATE DATABASE cashflow_db;`. |
| **`Health check returns 503 degraded`** | Application is running, but the PostgreSQL database is unreachable. | Check backend container logs with `docker compose logs backend` to inspect connectivity warnings without exposed credentials. |

---

## 7. Automated Testing & Verification

cashFlow enforces strict test-driven reliability. Every core algorithm, multi-tenant boundary, and financial calculation is guarded by automated test suites.

### 1. Backend Automated Tests (pytest)
```bash
cd backend
python -m pytest tests -v
```
**Results: 35 passed in ~25s (100% pass rate)**

| Test Suite | Focus Area |
| :--- | :--- |
| `tests/test_database_connection.py` | PostgreSQL connectivity, `SELECT NOW()` health checks, URL driver normalization, `DATABASE_URL` validation |
| `tests/test_auth.py` | Registration, bcrypt hashing, JWT issuance, password recovery, Google OAuth config & linking |
| `tests/test_tenancy.py` | Strict multi-tenant query isolation and 403 authorization enforcement |
| `tests/test_rbac.py` | Permissions across `OWNER`, `FINANCE_MANAGER`, `ACCOUNTANT`, and `VIEWER` |
| `tests/test_financial_engine.py` | Decimal math, authoritative balances, internal transfer exclusion, currency conversion |
| `tests/test_reconciliation.py` | Invoice creation, partial payments, explainable AI reconciliation matching |
| `tests/test_forecasting_and_risk.py` | Multi-horizon forecasts (7d-365d), reserve shortfall alerts, 2.5σ anomaly detection |
| `tests/test_simulations.py` | Monte Carlo 1,000-run reproducibility, percentile envelopes (P10/P50/P90), shortfall |
| `tests/test_decisions_and_scenarios.py` | Goal constraints, scenario modeling comparisons, linear solver recommendations |
| `tests/test_alerts_and_assistant.py` | Automated sentinel alerts, 24h suppression, grounded tool-calling assistant |
| `tests/test_csv_import.py` | 8-step statement import, date formatting, and row-level validation |
| `tests/test_excel_import.py` | OpenPyXL spreadsheet parsing and ledger commit |
| `tests/test_batch_uploads.py` | Concurrent multi-file upload queue workflow |
| `tests/test_uploads.py` | MIME magic byte verification, 15 MB size limits, duplicate SHA-256 detection |
| `tests/test_audit.py` | Audit log trail and automated password/token credential redaction |

### 2. Frontend Type & Build Verification
```bash
cd frontend
# TypeScript compilation check:
npx tsc --noEmit
# Production build check:
npm run build
```
- **Type Check**: 0 errors across all routes and components.
- **Production Bundle**: All 23 static and dynamic routes compiled successfully.

---

## 9. API Reference Overview

The FastAPI backend exposes structured REST endpoints under `/api/v1/`:

| Module | Endpoints | Description |
| :--- | :--- | :--- |
| **Auth** | `POST /auth/register`<br>`POST /auth/login`<br>`POST /auth/google`<br>`GET /auth/google/config`<br>`POST /auth/forgot-password` | User registration, login, Google OAuth, and password recovery |
| **Businesses** | `POST /businesses`<br>`GET /businesses/me`<br>`GET /businesses/{id}` | Workspace creation and business profile management |
| **Accounts** | `POST /businesses/{id}/accounts`<br>`GET /businesses/{id}/accounts` | Bank accounts, credit cards, and cash-on-hand tracking |
| **Uploads & Imports** | `POST /businesses/{id}/uploads`<br>`POST /businesses/{id}/uploads/batch`<br>`POST /businesses/{id}/imports` | File ingestion, batch queue, column mapping, validation & approval |
| **Financial Engine** | `GET /businesses/{id}/financial/overview`<br>`GET /businesses/{id}/financial/cash-position` | Authoritative cash position, opening/ending balances, cash burn |
| **Transactions** | `GET /businesses/{id}/transactions`<br>`POST /businesses/{id}/transactions/transfer` | Transaction ledger and internal transfer pairing |
| **Invoices** | `POST /businesses/{id}/invoices`<br>`GET /businesses/{id}/invoices`<br>`POST /businesses/{id}/invoices/{id}/payments` | Invoicing, payment status tracking, and partial payments |
| **Reconciliation** | `GET /businesses/{id}/reconciliation/candidates`<br>`POST /businesses/{id}/reconciliation/match` | AI candidate matching, confidence scores, and review gates |
| **Forecasting & Risk** | `POST /businesses/{id}/forecasting/run`<br>`GET /businesses/{id}/forecasting/risks` | Multi-horizon projections (7d-365d) and cash shortage risk alarms |
| **Simulations** | `POST /businesses/{id}/simulations/monte-carlo`<br>`GET /businesses/{id}/simulations/history` | 1,000-path stochastic simulation runs and percentile distributions |
| **Decisions** | `POST /businesses/{id}/decisions/goals`<br>`POST /businesses/{id}/decisions/scenarios`<br>`POST /businesses/{id}/decisions/optimize` | Business constraints, what-if modeling, and constrained optimization |
| **Alerts** | `GET /businesses/{id}/alerts`<br>`POST /businesses/{id}/alerts/rules`<br>`POST /businesses/{id}/alerts/evaluate` | Sentinel rules, duplicate suppression, and alert triage |
| **AI Assistant** | `POST /businesses/{id}/assistant/query` | Grounded tool-calling assistant with verified ledger citations |
| **Audit Logs** | `GET /businesses/{id}/audit` | Tamper-evident activity logs with credential sanitization |
| **Health** | `GET /health`<br>`GET /api/v1/health` | Container and database liveness probes |

---

## 10. Immutable Core Principles

All code, models, and features in **cashFlow** strictly adhere to these fundamental principles:

1. **Strict Separation of Actual vs. Projected Cash**: Cleared cash balances are never mingled with pending receivables or expected earnings.
2. **Unpaid Invoices Are Not Cash**: Outstanding invoices represent accounts receivable, not liquid purchasing power.
3. **Credit Limits Are Not Cash**: Available overdraft or credit card limits are debt facilities, not cash on hand.
4. **Internal Transfers Are Neutral**: Moving money between internal accounts nets to zero and is never categorized as income or expense.
5. **Multi-Currency Discipline**: Different currencies are never summed directly without recorded exchange rate provenance.
6. **Zero Fabricated Financial Data**: When data is absent, the system presents clear empty states—never placeholder or synthetic financial numbers.
7. **Complete Provenance**: Every number links back to its verified source file, import batch, or transaction record.
8. **Explainable AI with User Control**: AI suggestions include evidence and confidence ratings; consequential actions always require human confirmation.
9. **Absolute Tenant Isolation**: Mandatory multi-tenant boundary checks protect every customer's financial records.

---

## 11. License

Copyright © 2026 cashFlow. All rights reserved.
Plan. Forecast. Grow.

