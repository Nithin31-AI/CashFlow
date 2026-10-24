# cashFlow — System Architecture

## 1. System Overview & Architecture Diagram

cashFlow is structured as a decoupled full-stack SaaS application with a Next.js 15 App Router frontend and a Python FastAPI RESTful backend backed by an SQL database.

```
+-------------------------------------------------------------------------+
|                              CLIENT LAYER                               |
|                                                                         |
|   Next.js 15 App Router (React 19, TypeScript, Tailwind CSS, Lucide)     |
|   - Spatial UI & Theme Engine: Dark Mode (#0B0D0B) & Cream Mode (#F7F4EA)|
|   - Dynamic Theme-Aware Logo Switching (cashflow-logo-dark/light.png)   |
|   - Workspaces: /dashboard, /invoices, /transactions, /reconciliation,  |
|                 /forecast, /imports/new (Batch Queue), /settings        |
+------------------------------------+------------------------------------+
                                     │ HTTP / REST / JSON
                                     ▼
+-------------------------------------------------------------------------+
|                              API GATEWAY                                |
|                                                                         |
|   FastAPI Application (Port 8000)                                       |
|   - CORS Middleware: Configurable origins (localhost:3000 default)      |
|   - Security Headers: X-Content-Type-Options, X-Frame-Options, X-XSS     |
|   - Authentication Dependency: JWT bearer token validation               |
|   - Tenant Dependency: RequireBusinessRole (OWNER/FINANCE/ACCOUNTANT/VIEW)
+------------------------------------+------------------------------------+
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
+──────────────────────────+               +──────────────────────────────+
|     DOMAIN SERVICES      |               |      STORAGE & LEDGER        |
|                          |               |                              |
| - financial_service.py   |               | - Secure Uploads Directory   |
| - currency_service.py    |               |   (/backend/uploads, UUID)   |
| - reconciliation_service |               | - SQLite / PostgreSQL 16     |
| - forecasting_service.py |               |   SQLAlchemy 2.0 ORM         |
| - risk_service.py        |               |   Alembic 1.20 Migrations    |
| - csv/excel/validator    |               |   (9c2481321bb2, a1b2c3d4e5f6)
| - audit.py (Redaction)   |               |                              |
+──────────────────────────+               +──────────────────────────────+
```

---

## 2. Technology Stack Breakdown

### Frontend (Actual Implemented Dependencies)
- **Framework**: Next.js 15.1.7 (React 19.0.0, React DOM 19.0.0)
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 3.4.1 + PostCSS 8 + Autoprefixer
- **Icons**: Lucide React 0.468.0
- **Theme Architecture**: Custom `ThemeProvider` with system preference detection and `localStorage` persistence.
- **Branding Assets**: Theme-aware `cashflow-logo-dark.png` and `cashflow-logo-light.png`.
- **State & Session**: React Context (`AuthProvider`) persisting JWT tokens and active business ID in `localStorage`.

### Backend (Actual Implemented Dependencies)
- **Language**: Python 3.12.9
- **Framework**: FastAPI 0.124.4 (ASGI)
- **ASGI Server**: Uvicorn 0.33.0
- **Data Validation & Settings**: Pydantic 2.12.5, Pydantic-Settings 2.14.0
- **ORM**: SQLAlchemy 2.0.52
- **Database Migrations**: Alembic 1.20.1
- **Database Drivers**: `sqlite3` (built-in standard), `psycopg2-binary` 2.9.12 (PostgreSQL)
- **Security & Cryptography**: `python-jose` (3.5.0), `passlib` (1.7.4), `bcrypt` (4.3.0)
- **File Ingestion & Parsing**: `pandas` (3.0.3), `openpyxl` (3.1.5), `pdfplumber` (0.11.10), `pillow` (12.2.0)
- **Testing**: `pytest` (9.1.1), `pytest-asyncio` (1.4.0), `httpx` (0.28.1)

---

## 3. Directory Responsibilities

### `backend/`
- `app/api/`: API route controllers and dependency injection.
  - `deps.py`: `get_db`, `get_current_user`, and `RequireBusinessRole` multi-tenant access validator.
  - `v1/`: Versioned endpoints (`auth.py`, `businesses.py`, `members.py`, `accounts.py`, `uploads.py`, `imports.py`, `financial.py`, `transactions.py`, `invoices.py`, `reconciliation.py`, `forecasting.py`, `currencies.py`, `audit.py`).
- `app/core/`: Central configurations and security primitives.
  - `config.py`: Environment-driven settings with validation.
  - `security.py`: Password hashing, JWT token creation/decoding, SHA-256 token hashing.
  - `storage.py`: Safe file writing, extension verification, MIME magic byte validation, SHA-256 hashing.
  - `audit.py`: Credential-sanitized audit logging service.
- `app/db/`: Database session management and engine configuration.
- `app/models/`: SQLAlchemy 2.0 ORM declarative models.
- `app/schemas/`: Pydantic request and response schemas.
- `app/services/`: Financial engine, reconciliation, forecasting, risk detection, currency, CSV/Excel parsers.
- `alembic/`: Database migration environment and revision scripts (`9c2481321bb2`, `a1b2c3d4e5f6`).
- `tests/`: Automated pytest test suite (19 tests).

### `frontend/`
- `src/app/`: Next.js 15 App Router pages and layouts.
  - `(auth)/`: Authentication pages (`/login`, `/register`, `/forgot-password`, `/reset-password`).
  - `(dashboard)/`: Workspace pages (`/dashboard`, `/invoices`, `/transactions`, `/reconciliation`, `/forecast`, `/imports/new`, `/imports`, `/settings/*`).
- `src/components/`: Reusable Spatial UI components (`Logo.tsx`, `ThemeToggle.tsx`, `Sidebar.tsx`, `EmptyState.tsx`, `StatusBadge.tsx`).
- `src/lib/`: Unified API client (`api.ts`), Auth Context (`auth.tsx`), Theme Context (`theme.tsx`), and formatting utilities (`utils.ts`).
- `public/images/`: Static image assets including theme-aware `cashflow-logo-dark.png` and `cashflow-logo-light.png`.

---

## 4. Key Architectural Constraints & Invariants

1. **Strict Multi-Tenancy**: The client passes `business_id` in path parameters. The backend explicitly verifies user membership and RBAC role on every query.
2. **Deterministic Financial Math**: Exact `Decimal` arithmetic. `Ending Balance = Opening Balance + Inflows - Outflows`. Unpaid invoices strictly isolated in `outstanding_receivables` and never added to cash.
3. **Internal Transfer Pairing**: Transfers between accounts paired and excluded from revenue/expense metrics.
4. **Explainable AI Matching**: Automated reconciliation candidate scoring with human review gates.
5. **Private File Storage & Magic Bytes**: Non-public storage with UUID names and MIME inspection.
6. **Zero FOUC Spatial Theme Engine**: CSS custom properties with SSR mounted guard.
7. **Server-Side Identity Validation**: Client identity or verification claims are never trusted; Google OAuth tokens are verified server-side via Google's public certs.

---

## 5. Google OAuth Authentication Flow

```
+----------+             +--------------------------+             +-------------------------+
|  Client  |             | Google Identity Services |             | cashFlow Backend API    |
+----+-----+             +------------+-------------+             +------------+------------+
     |                                |                                        |
     | 1. Click "Continue with Google"|                                        |
     |------------------------------->|                                        |
     | 2. User selects account        |                                        |
     |<-------------------------------|                                        |
     | 3. Returns signed ID Token     |                                        |
     |--------------------------------+                                        |
     |                                                                         |
     | 4. POST /api/v1/auth/google {"credential": "<id_token>"}                |
     |------------------------------------------------------------------------>|
     |                                                 5. verify_oauth2_token()|
     |                                                    - audience check     |
     |                                                    - issuer check       |
     |                                                    - email_verified check
     |                                                 6. Lookup / Create User |
     |                                                    & default workspace  |
     |                                                 7. Issue JWT token      |
     | 8. 200 OK {"access_token": "...", "user": {...}}                        |
     |<------------------------------------------------------------------------|
     | 9. Save session & redirect to /dashboard                                |
```

---

## 6. Docker & Containerization Topology

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
                                                        cashflow_postgres_data
```
