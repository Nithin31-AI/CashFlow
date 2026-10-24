# cashFlow
### PLAN • FORECAST • GROW

> **Stage 1 of 4: Foundation, Database, Security, and Financial Data Import**

cashFlow is a production-oriented financial intelligence SaaS platform designed for small service-based businesses (IT service companies, consulting firms, digital agencies, freelancers). It empowers business leaders to consolidate financial records, understand their true cash position, forecast future cash flows, identify liquidity risks, and make informed financial decisions.

---

## 1. Stage 1 Architecture & Highlights

- **Multi-Tenant SaaS Foundation**: Strict tenant isolation enforced at the database and API layer. Every financial record is associated with a specific `business_id` and verified against authenticated business memberships. One business can never access another business's data.
- **Role-Based Access Control (RBAC)**:
  - `OWNER`: Full administrative authority, team management, permission updates, and financial operations.
  - `FINANCE_MANAGER`: Manage permitted financial accounts, review and approve imported records into the ledger.
  - `ACCOUNTANT`: Upload files, configure column mappings, review validation previews. Cannot approve imports into the ledger.
  - `VIEWER`: Read-only access to authorized financial records, accounts, and reports.
- **Database & Migrations**: PostgreSQL & SQLite support with SQLAlchemy 2.0 ORM and Alembic schema migrations.
- **Financial Data Import Pipeline**: An 8-step ingestion workflow with automatic delimiter/encoding detection, heuristic column mapping, date format recognition, and row-level validation.
- **Zero Fabricated Financial Data**: Real calculations strictly derived from verified source documents; informative empty states when data is absent.
- **Security & Auditability**:
  - Bcrypt password hashing
  - Secure JWT access tokens
  - Tokenized password recovery workflow (timing-safe, zero email existence leakage)
  - SHA-256 file hashing for duplicate upload prevention
  - Non-public secure file storage
  - Structured audit trail with automated credential redaction.

---

## 2. Technology Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons.
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **File Processing**: Pandas, OpenPyXL, pdfplumber, Pillow.
- **Testing**: pytest, pytest-asyncio, FastAPI TestClient.
- **Containers**: Docker, Docker Compose (PostgreSQL 16).

---

## 3. Brand Identity & Design System

- **Official Product Name**: `cashFlow`
- **Official Tagline**: `PLAN • FORECAST • GROW`
- **Official Logo**: Stored at `frontend/public/images/cashflow-logo.png`
- **Brand Palette**:
  - Dark Charcoal: `#111820`
  - Deep Charcoal Accent: `#1A2533`
  - Vivid Emerald Green: `#10A86B`
  - Emerald Green Dark: `#0D8554`
  - Light Mint Tint: `#E8F8F1`
  - Pure White: `#FFFFFF`
- **Currency**: India-first with INR (`₹`) as the default currency formatting, fully ready for multi-currency operations (USD, EUR, GBP, AED, SGD).

---

## 4. End-to-End Financial Import Pipeline

cashFlow implements a structured 8-step data import workflow:

1. **Step 1 (Upload)**: Authorized user uploads CSV, XLSX, XLS, PDF, or image files. Backend validates MIME magic bytes, enforces 15 MB size limits, computes a SHA-256 hash, checks for duplicate uploads in the business, and stores the file in non-public storage.
2. **Step 2 (Structure Detection)**: The parser inspects headers, delimiters, character encodings, and extracts sample data rows.
3. **Step 3 (Intelligent Suggestions)**: Column detection algorithms score headers against financial synonyms for `date`, `description`, `reference`, `debit`, `credit`, `amount`, and `currency`.
4. **Step 4 (Mapping Review)**: The user reviews and customizes the column mappings, selects target financial accounts, and confirms the date format (e.g. `DD/MM/YYYY`, `YYYY-MM-DD`).
5. **Step 5 (Validation Engine)**: The engine validates every row against monetary decimal rules, date structures, missing values, and negative parentheses notation `(1,500.00)` -> `-1500.00`.
6. **Step 6 (Interactive Preview)**: Displays a preview showing total rows, valid rows, invalid rows, and detailed error messages for any problematic rows without discarding them.
7. **Step 7 (Explicit Approval)**: An `OWNER` or `FINANCE_MANAGER` explicitly confirms the import.
8. **Step 8 (Ledger Commitment & Provenance)**: Validated records are stored in `imported_records` linked directly to `import_job_id` and the source file for complete auditability.

---

## 5. Extensible PDF & Image OCR Pipeline

Located at `backend/app/services/extraction/`:
- **`PDFDocumentExtractor`**: Extracts structured tables and text from vector PDF bank statements using `pdfplumber`, calculating table structure confidence and flagging uncertain cells.
- **`ImageDocumentExtractor`**: Extensible interface for receipt and voucher processing. If local Tesseract OCR or cloud OCR providers are not yet configured in the environment, it transparently returns `requires_ocr_config=True` with documented setup options, ensuring cashFlow **never invents or fabricates financial figures**.

---

## 6. Directory Structure

```
Cash_Flow/
├── backend/
│   ├── alembic/                 # Alembic migration environment and versions
│   │   ├── versions/            # 9c2481321bb2_initial_schema.py
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py          # Auth & RBAC dependencies
│   │   │   └── v1/              # Auth, Businesses, Members, Accounts, Uploads, Imports, Audit
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic settings
│   │   │   ├── security.py      # Password hashing, JWT, reset tokens
│   │   │   ├── audit.py         # Audit logging with credential redaction
│   │   │   └── storage.py       # Safe file upload storage & MIME magic validation
│   │   ├── db/
│   │   │   └── session.py       # SQLAlchemy engine and session
│   │   ├── models/              # User, Business, Membership, Account, File, ImportJob, Record, Audit
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   ├── services/
│   │   │   ├── csv_parser.py
│   │   │   ├── excel_parser.py
│   │   │   ├── column_detector.py
│   │   │   ├── validator.py
│   │   │   └── extraction/      # Extensible PDF & OCR interfaces
│   │   └── main.py              # FastAPI app with CORS & security middleware
│   ├── tests/                   # 11 comprehensive automated tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── public/
│   │   └── images/
│   │       └── cashflow-logo.png # Official logo
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/          # login, register, forgot-password, reset-password
│   │   │   ├── (dashboard)/     # dashboard, onboarding, imports, settings, team members
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/          # Logo, Navbar, Sidebar, EmptyState, StatusBadge
│   │   └── lib/                 # api.ts, auth.tsx, utils.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── tsconfig.json
├── docker-compose.yml
├── sample_bank_statement.csv    # Synthetic sample statement for testing
├── .env.example
└── README.md
```

---

## 7. Installation & Running Locally

### Prerequisites
- Python 3.12+
- Node.js 18+ (Node 20+ recommended)
- Git

### Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

5. Run database migrations:
   ```bash
   python -m alembic upgrade head
   ```

6. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --port 8000 --reload
   ```
   - API Documentation (Swagger UI): `http://localhost:8000/docs`
   - Healthcheck: `http://localhost:8000/health`

### Frontend Setup

1. Open a second terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install --legacy-peer-deps
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev -- -p 3000
   ```
   - Open your browser at: `http://localhost:3000`

---

## 8. Running Automated Tests

cashFlow includes an automated pytest suite covering tenant isolation, RBAC governance, password hashing, file type validation, CSV & Excel parsing, column mapping, and audit logging.

Run all backend tests:
```bash
cd backend
python -m pytest tests -v
```

### Verified Test Suite (11/11 Passed):
- `tests/test_audit.py`: Audit log recording & zero password/token leakage.
- `tests/test_auth.py`: User registration, password hashing, and tokenized password recovery.
- `tests/test_csv_import.py`: 8-step CSV import workflow, column mapping, and row-level validation.
- `tests/test_excel_import.py`: OpenPyXL Excel (.xlsx) parsing, signed amount handling, and ledger commit.
- `tests/test_rbac.py`: Granular RBAC permissions across `OWNER`, `FINANCE_MANAGER`, `ACCOUNTANT`, and `VIEWER`.
- `tests/test_tenancy.py`: Tenant isolation proving Business A cannot access Business B data.
- `tests/test_uploads.py`: MIME magic number verification, file size enforcement, and duplicate upload prevention (HTTP 409).

---

## 9. Current Limitations & Stage 2 Roadmap

- **Scanned PDF & Image OCR**: Standard digital PDFs and Excel/CSV statements are fully parsed. Scanned image-only PDFs and receipt photos utilize the extensible OCR interface in `backend/app/services/extraction/image_extractor.py`. When Tesseract or cloud OCR (AWS Textract / Google Cloud Document AI) is configured, automated extraction will be enabled without manual transcription.
- **Stage 2 (Upcoming)**: Automated bank feeds, intelligent transaction categorization, reconciliation rules, and tax compliance.
