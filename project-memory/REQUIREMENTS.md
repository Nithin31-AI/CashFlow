# cashFlow — Requirements Inventory

This document defines the complete requirements specification for **cashFlow** across all stages, tracking their current verification and implementation status.

---

## 1. Authentication & Session Management (AUTH)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUTH-001** | User registration with email, password (min 8 chars), and full name. | P0 | `VERIFIED` | `backend/app/api/v1/auth.py`<br>`frontend/src/app/(auth)/register/page.tsx` | `tests/test_auth.py::test_registration_and_login`<br>Browser subagent verification |
| **AUTH-002** | User login verifying email and hashed password, issuing JWT access token. | P0 | `VERIFIED` | `backend/app/api/v1/auth.py`<br>`frontend/src/app/(auth)/login/page.tsx` | `tests/test_auth.py::test_registration_and_login`<br>Browser subagent verification |
| **AUTH-003** | Passwords must never be stored in plaintext; hashed using Bcrypt. | P0 | `VERIFIED` | `backend/app/core/security.py` | `tests/test_auth.py::test_password_hashing` |
| **AUTH-004** | Token-based password recovery workflow without leaking email registration status. | P1 | `VERIFIED` | `backend/app/api/v1/auth.py`<br>`frontend/src/app/(auth)/forgot-password/page.tsx` | `tests/test_auth.py::test_password_recovery_workflow` |
| **AUTH-005** | Session persistence and secure logout clearing tokens on client and backend. | P1 | `VERIFIED` | `frontend/src/lib/auth.tsx`<br>`frontend/src/components/Sidebar.tsx` | Browser subagent verification |

---

## 2. Multi-Tenancy & Governance (TEN)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEN-001** | User can create multiple business workspaces or join existing businesses. | P0 | `VERIFIED` | `backend/app/api/v1/businesses.py`<br>`frontend/src/app/(dashboard)/onboarding/page.tsx` | `tests/test_tenancy.py`<br>Browser subagent verification |
| **TEN-002** | Every business-owned record must store foreign key `business_id`. | P0 | `VERIFIED` | `backend/app/models/` | Verified in schema & migrations |
| **TEN-003** | Backend must never trust client-supplied `business_id` without verifying active membership and role. | P0 | `VERIFIED` | `backend/app/api/deps.py` (`RequireBusinessRole`) | `tests/test_tenancy.py::test_strict_tenant_isolation` |
| **TEN-004** | Strict tenant isolation: Business A users cannot view, edit, or infer Business B data. | P0 | `VERIFIED` | `backend/app/api/deps.py` | `tests/test_tenancy.py::test_strict_tenant_isolation` (All 403 Forbidden checks passed) |
| **TEN-005** | Role-Based Access Control enforcing `OWNER`, `FINANCE_MANAGER`, `ACCOUNTANT`, and `VIEWER`. | P0 | `VERIFIED` | `backend/app/api/deps.py`<br>`backend/app/models/membership.py` | `tests/test_rbac.py::test_rbac_permissions` |
| **TEN-006** | Safety guard preventing demoting or removing the last remaining OWNER of a business. | P1 | `VERIFIED` | `backend/app/api/v1/members.py` | Unit tested in members router |

---

## 3. Financial Data Ingestion (IMP)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IMP-001** | Support uploading CSV, Excel (.xlsx/.xls), PDF statements, and image receipts. | P0 | `VERIFIED` | `backend/app/core/storage.py`<br>`frontend/src/app/(dashboard)/imports/new/page.tsx` | `tests/test_uploads.py`<br>Browser subagent verification |
| **IMP-002** | File type validation via MIME magic numbers, not extensions alone. | P0 | `VERIFIED` | `backend/app/core/storage.py` | `tests/test_uploads.py::test_file_type_and_extension_validation` |
| **IMP-003** | Maximum file size limit enforced (15 MB default). | P1 | `VERIFIED` | `backend/app/core/storage.py` | `tests/test_uploads.py::test_file_type_and_extension_validation` |
| **IMP-004** | SHA-256 duplicate file upload detection within the same business tenant. | P1 | `VERIFIED` | `backend/app/api/v1/uploads.py` | `tests/test_uploads.py::test_duplicate_upload_detection` (HTTP 409 verified) |
| **IMP-005** | Heuristic column mapping auto-suggesting Date, Description, Reference, Debit, Credit, Amount. | P0 | `VERIFIED` | `backend/app/services/column_detector.py` | `tests/test_csv_import.py`<br>Browser subagent verification |
| **IMP-006** | Row-level validation reporting date errors, decimal amounts, and negative parentheses. | P0 | `VERIFIED` | `backend/app/services/validator.py` | `tests/test_csv_import.py` (3 invalid rows flagged, 4 valid rows approved) |
| **IMP-007** | Invalid rows must never be silently discarded; displayed in interactive preview. | P0 | `VERIFIED` | `frontend/src/app/(dashboard)/imports/[id]/preview/page.tsx` | `tests/test_csv_import.py`<br>Browser subagent verification |
| **IMP-008** | Explicit user approval required to commit imported records into ledger. | P0 | `VERIFIED` | `backend/app/api/v1/imports.py` | `tests/test_csv_import.py`<br>Browser subagent verification |
| **IMP-009** | Ledger records preserve source provenance (`import_job_id`, row index, raw row). | P0 | `VERIFIED` | `backend/app/models/transaction.py` | `tests/test_csv_import.py` |
| **IMP-010** | Multi-file batch upload queue interface with per-file status badges and retry. | P0 | `VERIFIED` | `backend/app/api/v1/uploads.py`<br>`frontend/src/app/(dashboard)/imports/new/page.tsx` | `tests/test_batch_uploads.py::test_batch_upload_workflow`<br>Browser subagent verification |
| **IMP-011** | Extensible extraction interface for PDF and images without fabricating numbers. | P1 | `IMPLEMENTED` | `backend/app/services/extraction/` | Code implemented; OCR configuration extension point ready |

---

## 4. Financial Calculation & Ledger (FIN)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FIN-001** | Net cash position calculated strictly from cleared, verified transactions using exact Decimal arithmetic. | P0 | `VERIFIED` | `backend/app/services/financial_service.py`<br>`frontend/src/app/(dashboard)/dashboard/page.tsx` | `tests/test_financial_engine.py::test_authoritative_balance_calculation`<br>Browser subagent |
| **FIN-002** | Zero synthetic or fabricated financial metrics displayed to users. | P0 | `VERIFIED` | `frontend/src/components/EmptyState.tsx`<br>`backend/app/services/financial_service.py` | Verified in browser and tests |
| **FIN-003** | Support separate Debit/Credit columns or single signed Net Amount. | P0 | `VERIFIED` | `backend/app/services/validator.py` | `tests/test_csv_import.py`<br>`tests/test_excel_import.py` |
| **FIN-004** | Internal bank transfers must be paired, net to zero, and excluded from revenue/expense metrics. | P0 | `VERIFIED` | `backend/app/services/financial_service.py`<br>`backend/app/api/v1/transactions.py` | `tests/test_financial_engine.py::test_internal_transfer_exclusion` |
| **FIN-005** | Multi-currency processing with default reporting INR (`₹`), rate provenance, and fallback RBI benchmarks. | P0 | `VERIFIED` | `backend/app/services/currency_service.py`<br>`backend/app/api/v1/currencies.py` | `tests/test_financial_engine.py::test_multi_currency_processing` |
| **FIN-006** | Invoice management with payment allocations, overdue tracking, and receivable separation. | P0 | `VERIFIED` | `backend/app/models/invoice.py`<br>`backend/app/api/v1/invoices.py` | `tests/test_reconciliation.py::test_reconciliation_workflow` |
| **FIN-007** | Intelligent transaction-to-invoice reconciliation matching with Explainable AI confidence scoring and human approval/rejection gates. | P0 | `VERIFIED` | `backend/app/services/reconciliation_service.py`<br>`backend/app/api/v1/reconciliation.py` | `tests/test_reconciliation.py::test_reconciliation_workflow` |

---

## 5. Forecasting & Risk Prediction (FCST)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FCST-001** | Multi-horizon cash-flow forecasting (7d, 30d, 90d, 180d, 365d) with daily projection paths, confidence intervals, and assumptions. | P0 | `VERIFIED` | `backend/app/services/forecasting_service.py`<br>`backend/app/api/v1/forecasting.py` | `tests/test_forecasting_and_risk.py::test_cash_flow_forecast_horizons` |
| **FCST-002** | Cash-shortage risk prediction against configurable minimum cash reserve with severity and actionable recommendations. | P0 | `VERIFIED` | `backend/app/services/risk_service.py`<br>`backend/app/api/v1/forecasting.py` | `tests/test_forecasting_and_risk.py::test_risk_prediction_and_reserve_shortfall` |
| **FCST-003** | Invoice payment-delay risk estimation based on historical aging and overdue indicators. | P0 | `VERIFIED` | `backend/app/services/risk_service.py`<br>`backend/app/api/v1/invoices.py` | `tests/test_forecasting_and_risk.py::test_payment_delay_risk` |
| **FCST-004** | 2.5σ statistical expense anomaly detection with human review workflow. | P0 | `VERIFIED` | `backend/app/services/risk_service.py`<br>`backend/app/api/v1/forecasting.py` | `tests/test_forecasting_and_risk.py::test_expense_anomaly_detection` |

---

## 6. UI, Branding & Design System (UI)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UI-001** | Official product name `cashFlow` used across all screens. | P0 | `VERIFIED` | `frontend/src/components/Logo.tsx`<br>`frontend/src/app/` | Verified in browser |
| **UI-002** | Official tagline `PLAN • FORECAST • GROW` displayed in branding. | P0 | `VERIFIED` | `frontend/src/components/Logo.tsx` | Verified in browser |
| **UI-003** | Spatial UI design system with floating depth cards, smooth transitions, and glassmorphic elevation. | P0 | `VERIFIED` | `frontend/src/app/globals.css`<br>`frontend/tailwind.config.ts` | Browser subagent verification |
| **UI-004** | Dual Theme Architecture: Dark Mode (Near-black `#0B0D0B`, sage green `#A3B18A`) and Light Cream Mode (Warm cream `#F7F4EA`, sage green `#788B63`) with zero hydration flash. | P0 | `VERIFIED` | `frontend/src/lib/theme.tsx`<br>`frontend/src/components/ThemeToggle.tsx` | Browser subagent verification |
| **UI-005** | Theme-aware logo rendering: `cashflow-logo-dark.png` for dark mode and `cashflow-logo-light.png` for light mode. | P0 | `VERIFIED` | `frontend/src/components/Logo.tsx`<br>`frontend/public/images/` | Browser subagent verification |
| **UI-006** | Natural vertical window scrolling across all dashboard pages without sticky viewport locks. | P0 | `VERIFIED` | `frontend/src/app/(dashboard)/layout.tsx` | Browser subagent verification |
| **UI-007** | Responsive UI suitable for desktop, tablet, and mobile. | P1 | `VERIFIED` | Tailwind responsive utilities | Verified in browser |

---

## 7. Security, Privacy & Audit (SEC)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Secure HTTP headers (X-Frame-Options: DENY, X-Content-Type-Options: nosniff). | P0 | `VERIFIED` | `backend/app/main.py` | FastAPI middleware verified |
| **SEC-002** | Strict CORS restriction to configured trusted origins. | P0 | `VERIFIED` | `backend/app/main.py`<br>`backend/app/core/config.py` | Verified in backend configuration |
| **SEC-003** | Passwords, tokens, and authorization headers redacted from audit logs. | P0 | `VERIFIED` | `backend/app/core/audit.py` | `tests/test_audit.py::test_audit_logs_and_security_redaction` |
| **SEC-004** | File uploads stored outside web root with path traversal protection. | P0 | `VERIFIED` | `backend/app/core/storage.py` | Verified in storage manager |
| **SEC-005** | No plaintext secrets committed to repository (`.env.example` provided). | P0 | `VERIFIED` | `.env.example`<br>`backend/.env.example` | Repository inspection |

---

---

## 8. Testing Requirements (TEST)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-001** | Automated test suite covering auth, tenancy, RBAC, uploads, imports, financial engine, reconciliation, forecasting, and risk. | P0 | `VERIFIED` | `backend/tests/` | **25/25 pytest tests passed in 14.24s** |
| **TEST-002** | Frontend TypeScript type validation across all routes and components. | P0 | `VERIFIED` | `frontend/` | **`npx tsc --noEmit` exited with code 0 (zero errors)** |
| **TEST-003** | Interactive end-to-end browser verification of full Stage 2 and Stage 3 user workflows. | P0 | `VERIFIED` | Browser subagent | Verified recordings: `stage2_verification_1792861824162.webp` and `stage3_verification_1792867272444.webp` |

---

## 9. Advanced AI, Simulation & Decision Intelligence (Stage 3)

| Identifier | Description | Priority | Status | Implementation Files | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SIM-001** | Monte Carlo simulation engine with 1,000 stochastic paths, P10/P50/P90 daily envelopes, reserve breach probability, expected shortfall, and seed reproducibility. | P0 | `VERIFIED` | `backend/app/services/simulation_service.py`<br>`frontend/src/app/(dashboard)/simulation/page.tsx` | `tests/test_simulations.py`<br>Browser subagent |
| **DEC-001** | Business financial goals and constraints tracking (`MIN_CASH_BUFFER`, `TARGET_SAVINGS`, `DEBT_REDUCTION`, `MAX_OVERDUE_DAYS`) with hard vs soft constraint flags. | P0 | `VERIFIED` | `backend/app/models/goal.py`<br>`frontend/src/app/(dashboard)/decisions/page.tsx` | `tests/test_decisions_and_scenarios.py`<br>Browser subagent |
| **DEC-002** | Interactive scenario creation and comparative impact evaluation (delay days, collection %, expense multiplier, CapEx) against baseline. | P0 | `VERIFIED` | `backend/app/models/scenario.py`<br>`frontend/src/app/(dashboard)/decisions/page.tsx` | `tests/test_decisions_and_scenarios.py`<br>Browser subagent |
| **DEC-003** | Constrained decision optimisation solver balancing cash preservation against operating goals; advisory-only with human confirmation checkboxes. | P0 | `VERIFIED` | `backend/app/services/decision_service.py`<br>`frontend/src/app/(dashboard)/decisions/page.tsx` | `tests/test_decisions_and_scenarios.py`<br>Browser subagent |
| **DEC-004** | Explainable financial recommendations with severity rating, estimated impact, reasoning, trade-offs, and acceptance workflows. | P0 | `VERIFIED` | `backend/app/models/recommendation.py`<br>`frontend/src/app/(dashboard)/decisions/page.tsx` | `tests/test_decisions_and_scenarios.py`<br>Browser subagent |
| **AST-001** | Conversational AI financial assistant querying verified backend tools with citations, prompt injection defense, and zero hallucinated math. | P0 | `VERIFIED` | `backend/app/services/assistant_service.py`<br>`frontend/src/app/(dashboard)/assistant/page.tsx` | `tests/test_alerts_and_assistant.py`<br>Browser subagent |
| **ALT-001** | Configurable sentinel alert rules and event stream with 24h duplicate suppression window, acknowledge, and resolve workflows. | P0 | `VERIFIED` | `backend/app/services/alert_service.py`<br>`frontend/src/app/(dashboard)/alerts/page.tsx` | `tests/test_alerts_and_assistant.py`<br>Browser subagent |
| **BRD-001** | Canonical Sage Green accent color (`#8A9A78`) standardized across BOTH Dark Mode and Light Cream Mode. | P0 | `VERIFIED` | `frontend/src/app/globals.css`<br>`frontend/tailwind.config.ts` | Browser subagent |
| **BRD-002** | Official CF Monogram brand mark configured as browser tab favicon. | P0 | `VERIFIED` | `frontend/public/favicon.ico`<br>`frontend/src/app/layout.tsx` | Browser subagent |
