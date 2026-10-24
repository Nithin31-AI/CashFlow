# cashFlow — Architectural Decisions Log

This document records significant architectural, technical, and design decisions made throughout the lifecycle of the cashFlow platform.

---

### DEC-001: Technology Stack Selection
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Need a production-oriented, scalable SaaS architecture for a financial intelligence application with strong computational, parsing, and UI requirements.
- **Problem**: Selecting a backend with robust data/numerical processing and a frontend with modern, responsive component rendering.
- **Chosen Approach**: Python FastAPI for backend; Next.js 15 App Router (TypeScript, Tailwind CSS) for frontend; PostgreSQL / SQLite with SQLAlchemy 2.0 and Alembic for data persistence.
- **Reason**: Python provides best-in-class data manipulation (`pandas`, `openpyxl`, `pdfplumber`) and rapid REST API development with Pydantic v2. Next.js 15 App Router delivers fast client-side navigation, clean layout nesting, and responsive styling.
- **Alternatives Considered**:
  - Full-stack Django: Heavier, more monolithic, less flexible for decoupled Next.js frontend.
  - Node.js Express/NestJS backend: Weaker native support for complex financial/tabular document parsing and future AI/ML libraries.
- **Consequences**: Separate backend and frontend development servers in local development; decoupled deployment via Docker Compose.
- **Affected Files**: Entire repository root, `backend/`, `frontend/`, `docker-compose.yml`.

---

### DEC-002: Multi-Tenant Architecture & Authorization
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: cashFlow serves multiple business entities whose financial records must be strictly isolated.
- **Problem**: Choosing between schema-per-tenant, database-per-tenant, or column-based multi-tenancy with dependency-injected verification.
- **Chosen Approach**: Shared database with column-based tenant isolation (`business_id` foreign key on every tenant table) combined with FastAPI dependency injection (`RequireBusinessRole`).
- **Reason**: Simplifies database migrations, keeps connection pools efficient, and provides strict security as long as backend dependencies verify tenant membership on every request.
- **Alternatives Considered**:
  - Schema-per-tenant in PostgreSQL: Highly complex Alembic migrations across hundreds of schemas; difficult for local SQLite developer workflow.
- **Consequences**: Developers must always inject `RequireBusinessRole` or `require_viewer_or_higher` on tenant endpoints. URL parameter `business_id` is never trusted without membership verification.
- **Affected Files**: `backend/app/api/deps.py`, `backend/app/models/`, `backend/app/api/v1/`.

---

### DEC-003: Stateless JWT Authentication & Timing-Safe Password Recovery
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Secure user authentication and password recovery without leaking customer identity.
- **Problem**: Session management across decoupled frontend/backend and privacy-preserving password recovery.
- **Chosen Approach**: Bearer JWT tokens signed with HS256. Password reset generates a 32-byte URL-safe token whose SHA-256 hash is saved to `password_reset_tokens` with 60-minute expiration. The endpoint always returns a generic message regardless of email existence. In development mode (`DEV_MODE=true`), a `dev_reset_token` is included to facilitate offline automated testing.
- **Reason**: Prevents user enumeration attacks while ensuring unblocked development without external SMTP setup.
- **Alternatives Considered**: Stateful server sessions (requires Redis).
- **Consequences**: Token expiration requires periodic re-login; tokens stored in client `localStorage`.
- **Affected Files**: `backend/app/core/security.py`, `backend/app/api/v1/auth.py`.

---

### DEC-004: File Ingestion Security & SHA-256 Deduplication
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Small businesses frequently re-upload bank statements, risking duplicate ledger transactions.
- **Problem**: Preventing accidental duplicate imports, malicious file uploads, and directory traversal.
- **Chosen Approach**:
  1. Validate MIME magic numbers (first 64 bytes) against an allowlist.
  2. Enforce 15 MB size limit.
  3. Store files outside public directory with UUID-randomized filenames.
  4. Compute SHA-256 hash of byte content. If a file with the same hash exists within the business, reject with HTTP 409 Conflict.
- **Reason**: Protects server file systems and prevents duplicate financial figures before parsing begins.
- **Alternatives Considered**: Allowing duplicate uploads and attempting deduplication during reconciliation.
- **Consequences**: If a user uploads the exact same file twice, they receive a clear 409 Conflict alert detailing when it was previously ingested.
- **Affected Files**: `backend/app/core/storage.py`, `backend/app/api/v1/uploads.py`.

---

### DEC-005: 8-Step Import Pipeline with Explicit Approval
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Financial records cannot be blindly dumped into an accounting ledger without verification.
- **Problem**: Accommodating diverse bank statement formats (different column names, date formats, debit/credit structures) without silently dropping bad rows.
- **Chosen Approach**: A structured 8-step pipeline: Upload -> Structure Detection -> Column Suggestions -> User Adjustment -> Row Validation -> Interactive Preview -> Role-Enforced Approval (`OWNER` or `FINANCE_MANAGER`) -> Provenance Storage.
- **Reason**: Ensures user is in total control, errors are clearly highlighted per row, and verified ledger records preserve direct links to original row cells.
- **Alternatives Considered**: One-click automatic ingestion without preview or mapping review.
- **Consequences**: Requires multi-step UI flow (`/new`, `/[id]/mapping`, `/[id]/preview`), but delivers rock-solid financial accuracy.
- **Affected Files**: `backend/app/api/v1/imports.py`, `frontend/src/app/(dashboard)/imports/`.

---

### DEC-006: Extensible Document Extraction Interface
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Users upload both digital PDF statements and physical receipt images.
- **Problem**: Extracting text/tables without inventing or hallucinating missing numbers when OCR tools are not installed.
- **Chosen Approach**: Implemented `BaseDocumentExtractor` with `PDFDocumentExtractor` (using `pdfplumber` for vector tables) and `ImageDocumentExtractor`. If Tesseract/Cloud OCR is not configured, the extractor returns `requires_ocr_config=True` with explicit documentation rather than synthesizing numbers.
- **Reason**: Upholds Core Principle 9 ("Zero Fabricated Financial Data").
- **Alternatives Considered**: Mocking random extracted transaction numbers for images. (Strictly rejected).
- **Consequences**: Users are clearly notified when optical OCR infrastructure is pending configuration.
- **Affected Files**: `backend/app/services/extraction/`.

---

### DEC-007: SQLite In-Memory Test Isolation via StaticPool
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Automated tests require isolated in-memory databases with rapid execution.
- **Problem**: Default SQLite `:memory:` connections open independent in-memory databases per connection, preventing sessions from seeing tables created during setup.
- **Chosen Approach**: Configured `StaticPool` (`from sqlalchemy.pool import StaticPool`) in `tests/conftest.py`.
- **Reason**: Forces all sessions within a test case to share the exact same in-memory database, eliminating 400 Bad Request registration errors.
- **Consequences**: Fast test execution (19 tests in ~22 seconds) with 100% isolation between test functions.
- **Affected Files**: `backend/tests/conftest.py`.

---

### DEC-008: Strict Decimal Financial Mathematics & Separation of Cash vs Receivables
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: In financial accounting, floating-point rounding errors are catastrophic, and confusing receivables with available cash creates fatal liquidity misjudgments.
- **Problem**: Python `float` and JavaScript `number` cause binary IEEE 754 precision errors.
- **Chosen Approach**: Python `decimal.Decimal` with 2 decimal places (`ROUND_HALF_UP`) and database `NUMERIC(15, 2)`.
  Formula: `Ending Balance = Opening Balance + Actual Inflows - Actual Outflows + Approved Adjustments`.
  Unpaid invoices belong strictly to `outstanding_receivables` and are never added to liquid cash.
- **Reason**: Guarantees accounting correctness and eliminates liquidity illusion.
- **Affected Files**: `backend/app/services/financial_service.py`, `backend/app/api/v1/financial.py`.

---

### DEC-009: Internal Transfer Pairing & Revenue/Expense Exclusion
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Moving money from a checking account to a savings account or paying a business credit card creates equal and opposite ledger records.
- **Problem**: Naive aggregation counts these transfers as both revenue and expense, distorting net income.
- **Chosen Approach**: Automatic pairing of transfers using `is_internal_transfer=True` and `transfer_matched_transaction_id`. In `FinancialService.calculate_cash_position`, internal transfers net out to zero and are explicitly excluded from total revenue and expense metrics.
- **Reason**: Prevents double-counting and accurately reflects true business operational performance.
- **Affected Files**: `backend/app/services/financial_service.py`, `backend/app/api/v1/transactions.py`.

---

### DEC-010: Explainable AI Reconciliation Candidate Matching with Human Review Gate
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Matching unallocated bank transactions to customer invoices must be automated but transparent and reviewable.
- **Problem**: Fully automated matching without explanation causes catastrophic silent misallocations.
- **Chosen Approach**: Multi-factor candidate scoring combining exact amount matching (0.45 weight), date proximity decay (0.25 weight), reference number match (0.20 weight), and fuzzy text similarity (0.10 weight). Each candidate provides an Explainable AI explanation string and confidence score. Candidates are sorted by confidence and require explicit human approval/rejection.
- **Reason**: Gives operators high-speed matching while preserving full auditability and human oversight.
- **Affected Files**: `backend/app/services/reconciliation_service.py`, `backend/app/api/v1/reconciliation.py`.

---

### DEC-011: Spatial UI Dual-Theme Architecture with Zero Hydration Flash
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Users demanded both an ultra-sleek Dark Mode (black/charcoal/sage) and a warm Light Cream Mode (cream/sage), with smooth spatial depth and zero flash of unstyled content (FOUC).
- **Problem**: Next.js SSR hydration mismatches when reading `localStorage` during initial page load.
- **Chosen Approach**: Implemented `ThemeProvider` with mounted guard and CSS variables mapped in `tailwind.config.ts` and `globals.css`. System preference `prefers-color-scheme` acts as default with `localStorage` persistence.
- **Reason**: Eliminates white/black flashes on load and gives cohesive spatial depth styling across both modes.
- **Affected Files**: `frontend/src/lib/theme.tsx`, `frontend/src/components/ThemeToggle.tsx`, `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`.

---

### DEC-012: Theme-Aware Logo Assets & Dynamic Selection
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: The official cashFlow logo must render with perfect contrast on both dark and light backgrounds.
- **Problem**: A single dark logo is unreadable on dark mode; a white logo is unreadable on light cream mode.
- **Chosen Approach**: Generated `cashflow-logo-dark.png` (light cream text `#F5F0E6` with vibrant sage accent `#A3B18A`) and `cashflow-logo-light.png` (charcoal text `#171A16` with sage accent `#788B63`). Upgraded `Logo.tsx` to automatically bind to the active theme context.
- **Reason**: Delivers brand visual perfection across all themes without logo distortion.
- **Affected Files**: `frontend/public/images/cashflow-logo-dark.png`, `frontend/public/images/cashflow-logo-light.png`, `frontend/src/components/Logo.tsx`.

---

### DEC-013: Canonical Sage-Green Accent (`#8A9A78`) & Official Monogram Favicon
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Stage 3 branding mandated a single, authoritative sage-green token `#8A9A78` across BOTH dark and light modes, and the official CF monogram emblem as the browser tab favicon.
- **Problem**: Previous stages had slightly different green hexes (`#788B63` in light vs `#A3B18A` in dark), causing visual inconsistency.
- **Chosen Approach**: Unified all green CSS variables to `#8A9A78` in `frontend/src/app/globals.css`. Extracted the high-resolution CF monogram mark from `cashflow-logo.png` (transparent background, padded to square) and generated `favicon.ico`, `cashflow-favicon.png`, and linked them in Next.js metadata.
- **Reason**: Guarantees pure branding consistency and crisp browser tab recognition without conflicting greens or gradients.
- **Affected Files**: `frontend/src/app/globals.css`, `frontend/public/favicon.ico`, `frontend/public/images/cashflow-favicon.png`, `frontend/src/app/layout.tsx`.

---

### DEC-014: Monte Carlo Simulation Engine with Seed Reproducibility
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Businesses need stochastic stress testing of cash flows accounting for payment delays, collection variance, and expense shocks.
- **Problem**: Deterministic forecasts cannot model downside tail risks or reserve breach probabilities.
- **Chosen Approach**: Implemented `SimulationService` executing 1000 independent stochastic trajectory paths with configurable parameters (horizon, delay days, collection %, expense multiplier). Computes daily percentile envelopes (P10, P25, P50, P75, P90), reserve breach probability, and expected shortfall. Supports optional integer `seed` parameter for exact reproducibility.
- **Reason**: Enables empirical quantification of solvency risks with reproducible testability.
- **Affected Files**: `backend/app/services/simulation_service.py`, `backend/app/api/v1/simulations.py`, `frontend/src/app/(dashboard)/simulation/page.tsx`.

---

### DEC-015: Advisory-Only Constrained Decision Optimisation Solver with Human Confirmation Gate
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Small business owners need algorithmic assistance balancing cash preservation against operating goals.
- **Problem**: Autonomous AI execution of financial payments or debt transfers could lead to unintended liquidity shocks.
- **Chosen Approach**: Linear constrained solver in `decision_service.py` evaluates hard constraints (`MIN_CASH_BUFFER`, `MAX_OVERDUE_DAYS`) and soft targets. The output provides status (`FEASIBLE`, `PARTIALLY_FEASIBLE`, `INFEASIBLE`), objective value, and recommended action sequence. The UI renders interactive user confirmation checkboxes and an advisory disclaimer: "Advisory-only. Final execution requires manual confirmation by business owner."
- **Reason**: Preserves owner sovereignty and fiduciary responsibility while providing powerful decision intelligence.
- **Affected Files**: `backend/app/services/decision_service.py`, `backend/app/api/v1/decisions.py`, `frontend/src/app/(dashboard)/decisions/page.tsx`.

---

### DEC-016: Grounded Conversational AI Assistant with Tool-Calling Architecture & Zero Hallucinated Math
- **Date**: 2026-10-24
- **Status**: `ACTIVE`
- **Context**: Users want to ask natural questions like "What is our actual cash balance?" or "Which invoices are overdue?".
- **Problem**: Direct LLM answers hallucinate financial numbers, violating the core integrity principle of cashFlow.
- **Chosen Approach**: Implemented tool-calling dispatcher in `assistant_service.py` querying verified domain methods (`get_actual_cash_balance`, `get_overdue_invoices`, `get_forecast_summary`, `get_simulation_summary`, `get_recommendations`). Answers cite verified data sources ("Verified Cleared Bank Ledger", etc.), include assumptions notes, and sanitize prompt injection delimiters.
- **Reason**: Guarantees zero fabricated figures while providing intuitive conversational intelligence.
- **Affected Files**: `backend/app/services/assistant_service.py`, `backend/app/api/v1/assistant.py`, `frontend/src/app/(dashboard)/assistant/page.tsx`.
