# cashFlow — Database Schema & Data Models

## 1. Schema Overview

The database is built using SQLAlchemy 2.0 ORM with schema migrations managed by Alembic. Every tenant-owned entity carries an indexed `business_id` foreign key referencing `businesses.id`, enforcing multi-tenant isolation across all queries.

- **Dialects Supported**: PostgreSQL 16+ (Production/Docker), SQLite 3 (Local Development & In-Memory Testing).
- **Migration Head Revision**: `a1b2c3d4e5f6` (`a1b2c3d4e5f6_stage2_financial_engine.py`).

---

## 2. Table Definitions

### 2.1. `users`
Stores registered user identities and credentials.
- `id`: `VARCHAR(36)` — Primary Key (UUID v4 string).
- `email`: `VARCHAR(255)` — Unique, Indexed, Not Null (lowercased).
- `hashed_password`: `VARCHAR(255)` — Not Null (Bcrypt hash).
- `full_name`: `VARCHAR(255)` — Not Null.
- `is_active`: `BOOLEAN` — Default `TRUE`, Not Null.
- `created_at`, `updated_at`: `TIMESTAMP WITH TIME ZONE`.

### 2.2. `businesses`
The core multi-tenant business entity.
- `id`: `VARCHAR(36)` — Primary Key.
- `name`: `VARCHAR(255)` — Not Null.
- `slug`: `VARCHAR(255)` — Unique, Indexed, Not Null.
- `currency`: `VARCHAR(10)` — Default `'INR'`, Not Null.
- `country`: `VARCHAR(10)` — Default `'IN'`, Not Null.
- `timezone`: `VARCHAR(50)` — Default `'Asia/Kolkata'`, Not Null.
- `minimum_cash_reserve`: `NUMERIC(15, 2)` — Default `0.00` (Stage 2 configurable safety threshold).
- `created_at`, `updated_at`: `TIMESTAMP WITH TIME ZONE`.

### 2.3. `business_memberships`
Role-based access control linking users and business workspaces.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id` (ON DELETE CASCADE), Indexed, Not Null.
- `user_id`: `VARCHAR(36)` — Foreign Key -> `users.id` (ON DELETE CASCADE), Indexed, Not Null.
- `role`: `ENUM('OWNER', 'FINANCE_MANAGER', 'ACCOUNTANT', 'VIEWER')` — Not Null.
- `created_at`, `updated_at`: `TIMESTAMP WITH TIME ZONE`.

### 2.4. `financial_accounts`
Bank accounts, credit cards, or digital wallets belonging to a business.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id` (ON DELETE CASCADE), Indexed, Not Null.
- `name`: `VARCHAR(255)` — Not Null.
- `account_type`: `ENUM('BANK', 'CREDIT_CARD', 'WALLET', 'OTHER')` — Default `'BANK'`, Not Null.
- `account_number_mask`: `VARCHAR(20)` — Nullable.
- `currency`: `VARCHAR(10)` — Default `'INR'`, Not Null.
- `institution_name`: `VARCHAR(100)` — Nullable.
- `opening_balance`: `NUMERIC(15, 2)` — Default `0.00`, Not Null (Stage 2).
- `opening_balance_date`: `DATE` — Nullable (Stage 2).
- `is_active`: `BOOLEAN` — Default `TRUE`.

### 2.5. `exchange_rates` (Stage 2)
Multi-currency conversion rates with audit provenance.
- `id`: `VARCHAR(36)` — Primary Key.
- `from_currency`: `VARCHAR(10)` — Indexed, Not Null.
- `to_currency`: `VARCHAR(10)` — Indexed, Not Null.
- `rate`: `NUMERIC(18, 6)` — Not Null (e.g. 83.250000).
- `rate_date`: `DATE` — Indexed, Not Null.
- `source`: `VARCHAR(50)` — Default `'RBI_BENCHMARK'`, Not Null.
- `source_reference`: `VARCHAR(100)` — Nullable.

### 2.6. `transactions` (Stage 2 Ledger)
The definitive double-entry and classified financial transaction ledger.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id` (ON DELETE CASCADE), Indexed, Not Null.
- `account_id`: `VARCHAR(36)` — Foreign Key -> `financial_accounts.id` (ON DELETE SET NULL), Indexed, Nullable.
- `imported_record_id`: `VARCHAR(36)` — Foreign Key -> `imported_records.id` (ON DELETE SET NULL), Indexed, Nullable.
- `transaction_date`: `DATE` — Indexed, Not Null.
- `amount`: `NUMERIC(15, 2)` — Not Null (positive = inflow, negative = outflow).
- `currency`: `VARCHAR(10)` — Default `'INR'`, Not Null.
- `transaction_type`: `ENUM('INCOME', 'EXPENSE', 'TRANSFER', 'ADJUSTMENT')` — Not Null.
- `category`: `ENUM('REVENUE', 'PAYROLL', 'RENT', 'SOFTWARE', 'MARKETING', 'OPERATING', 'TAX', 'FINANCING', 'OTHER')` — Not Null.
- `status`: `ENUM('PENDING', 'POSTED', 'RECONCILED', 'VOID')` — Default `'POSTED'`, Not Null.
- `description`: `TEXT` — Not Null.
- `reference_number`: `VARCHAR(100)` — Nullable.
- `counterparty_name`: `VARCHAR(255)` — Nullable.
- `is_internal_transfer`: `BOOLEAN` — Default `FALSE`, Indexed, Not Null.
- `transfer_matched_transaction_id`: `VARCHAR(36)` — Nullable.
- `reconciliation_status`: `ENUM('UNRECONCILED', 'SUGGESTED', 'RECONCILED')` — Default `'UNRECONCILED'`.
- `reporting_currency`: `VARCHAR(10)` — Default `'INR'`, Not Null.
- `reporting_amount`: `NUMERIC(15, 2)` — Not Null.
- `exchange_rate_used`: `NUMERIC(18, 6)` — Default `1.0`.

### 2.7. `invoices` (Stage 2)
Customer billings, payment delay prediction tracking, and receivables.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id` (ON DELETE CASCADE), Indexed, Not Null.
- `customer_name`: `VARCHAR(255)` — Indexed, Not Null.
- `customer_email`: `VARCHAR(255)` — Nullable.
- `invoice_number`: `VARCHAR(100)` — Indexed, Not Null.
- `issue_date`: `DATE` — Indexed, Not Null.
- `due_date`: `DATE` — Indexed, Not Null.
- `currency`: `VARCHAR(10)` — Default `'INR'`, Not Null.
- `subtotal`: `NUMERIC(15, 2)` — Not Null.
- `tax_amount`: `NUMERIC(15, 2)` — Default `0.00`.
- `total_amount`: `NUMERIC(15, 2)` — Not Null.
- `paid_amount`: `NUMERIC(15, 2)` — Default `0.00`.
- `status`: `ENUM('DRAFT', 'SENT', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'CANCELLED')` — Default `'SENT'`, Indexed.
- `notes`: `TEXT` — Nullable.

### 2.8. `payments` & `invoice_payment_allocations` (Stage 2)
Tracks payments made against invoices with partial allocation support.
- `payments`: `id`, `business_id`, `payment_date`, `amount`, `currency`, `payment_method`, `reference_number`, `account_id`, `transaction_id`.
- `invoice_payment_allocations`: `id`, `invoice_id`, `payment_id`, `allocated_amount`, `allocation_date`.

### 2.9. `reconciliation_records` (Stage 2)
Explainable candidate matching records between ledger transactions and invoices/expenses.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id` (ON DELETE CASCADE), Indexed, Not Null.
- `transaction_id`: `VARCHAR(36)` — Foreign Key -> `transactions.id` (ON DELETE CASCADE), Indexed, Not Null.
- `matched_entity_type`: `ENUM('INVOICE', 'EXPENSE', 'TRANSFER')` — Not Null.
- `matched_entity_id`: `VARCHAR(36)` — Indexed, Not Null.
- `match_type`: `ENUM('EXACT', 'PROBABLE', 'AMBIGUOUS', 'MANUAL')` — Not Null.
- `confidence_score`: `NUMERIC(5, 4)` — Not Null (0.0000 to 1.0000).
- `status`: `ENUM('PENDING_REVIEW', 'APPROVED', 'REJECTED')` — Default `'PENDING_REVIEW'`.
- `explanation`: `TEXT` — Explainable AI rationale for match confidence.
- `reviewed_by_user_id`: `VARCHAR(36)` — Nullable.
- `reviewed_at`: `TIMESTAMP WITH TIME ZONE` — Nullable.

### 2.10. `forecast_runs`, `risk_assessments`, `expense_anomalies` (Stage 2)
- `forecast_runs`: Multi-horizon cash projections (7d, 30d, 90d, 180d, 365d), starting/ending cash, confidence bounds, assumptions JSON, daily projection points JSON.
- `risk_assessments`: Cash shortages, payment delay risks, severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), estimated shortfall, and actionable recommendations.
- `expense_anomalies`: Flags transactions exceeding 2.5σ baseline with z-score and human review gate.

### 2.11. `uploaded_files`, `import_jobs`, `imported_records`, `audit_logs`
Carried forward from Stage 1 with full source provenance, SHA-256 deduplication, and credential redaction.

### 2.12. `financial_goals` (Stage 3)
Business targets and hard/soft constraints for constrained decision optimisation.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id`, Indexed, Not Null.
- `name`: `VARCHAR(255)` — Not Null.
- `goal_type`: `ENUM('MIN_CASH_BUFFER', 'TARGET_SAVINGS', 'DEBT_REDUCTION', 'MAX_OVERDUE_DAYS')` — Not Null.
- `target_amount`: `NUMERIC(15, 2)` — Not Null.
- `target_date`: `TIMESTAMP WITH TIME ZONE` — Nullable.
- `is_hard_constraint`: `BOOLEAN` — Default `TRUE`, Not Null.
- `priority`: `INTEGER` — Default `1`, Not Null.
- `status`: `ENUM('ACTIVE', 'ACHIEVED', 'BREACHED', 'ARCHIVED')` — Default `'ACTIVE'`.
- `notes`: `TEXT` — Nullable.

### 2.13. `simulation_runs` (Stage 3)
Monte Carlo cash-flow simulation executions with stochastic paths.
- `id`: `VARCHAR(36)` — Primary Key.
- `business_id`: `VARCHAR(36)` — Foreign Key -> `businesses.id`, Indexed, Not Null.
- `horizon_days`: `INTEGER` — Default `30`, Not Null.
- `num_paths`: `INTEGER` — Default `1000`, Not Null.
- `seed`: `INTEGER` — Nullable (for reproducibility).
- `starting_cash`, `min_projected_cash`, `max_projected_cash`: `NUMERIC(15, 2)`.
- `p10_ending_cash`, `p50_ending_cash`, `p90_ending_cash`: `NUMERIC(15, 2)`.
- `reserve_breach_probability`: `FLOAT` — Not Null (e.g. 0.0450).
- `expected_shortfall`: `NUMERIC(15, 2)` — Default `0.00`.
- `potential_shortage_day`: `INTEGER` — Nullable.
- `assumptions`: `JSON` — Stored simulation parameters and variance drivers.
- `percentile_paths`: `JSON` — Daily P10, P25, P50, P75, P90 percentile envelopes.
- `model_version`: `VARCHAR(50)` — Default `'mc-v1.0'`.

### 2.14. `saved_scenarios` & `optimisation_plans` (Stage 3)
- `saved_scenarios`: Custom what-if scenarios (delay days, collection %, expense multiplier, CapEx), projected ending cash, min cash, shortage risk %, runway days, baseline flag.
- `optimisation_plans`: Output of linear constrained solver (`FEASIBLE`, `INFEASIBLE`, `PARTIALLY_FEASIBLE`), objective value, recommended actions JSON, trade-offs, hard constraints satisfied flag.

### 2.15. `financial_recommendations` (Stage 3)
Explainable actionable recommendations with severity, estimated impact, reasoning, supporting records JSON, disadvantages, and assumptions.

### 2.16. `alert_rules` & `alert_events` (Stage 3)
- `alert_rules`: Configurable liquidity thresholds, category (`RESERVE_BREACH`, `OVERDUE_INVOICES`, `EXPENSE_SPIKE`, `CASH_DEFICIT`), severity (`INFO`, `WARNING`, `CRITICAL`), suppression window hours (default 24h), active toggle.
- `alert_events`: Triggered alarms with financial evidence JSON, suppression fingerprint, `is_acknowledged`, `is_resolved`.

### 2.17. `model_evaluations` (Stage 3)
ML model versioning, evaluation metric (MAPE/RMSE), metric value, sample size, parameters JSON.

---

## 3. Migration History

| Revision | Down Revision | Description | Date |
| :--- | :--- | :--- | :--- |
| `9c2481321bb2` | None | Initial schema creation (Stage 1 base tables) | 2026-10-24 |
| `a1b2c3d4e5f6` | `9c2481321bb2` | Stage 2 financial engine: transactions, invoices, payments, reconciliation, forecasts, risks, anomalies, multi-currency | 2026-10-24 |
| `b2c3d4e5f6a7` | `a1b2c3d4e5f6` | Stage 3 advanced AI: goals, simulations, scenarios, optimisation plans, recommendations, alerts, evaluations | 2026-10-24 |

---

## 4. Benchmark & Seed Datasets

### 4.1. `Acme Consulting Tech Ltd` Synthetic Dataset
- **Database Script**: [`backend/app/db/seeds/acme_synthetic_dataset.sql`](file:///c:/Users/NITHIN/OneDrive/Desktop/Cash_Flow/backend/app/db/seeds/acme_synthetic_dataset.sql)
- **Seeding & Analytical Engine Runner**: [`backend/app/scripts/seed_acme_synthetic_data.py`](file:///c:/Users/NITHIN/OneDrive/Desktop/Cash_Flow/backend/app/scripts/seed_acme_synthetic_data.py)
- **Business Profile**:
  - `id`: `11111111-1111-1111-1111-111111111111`
  - `name`: `Acme Consulting Tech Ltd`
  - `currency`: `INR` (`₹`)
  - `minimum_cash_reserve`: `₹500,000.00`
- **Team Users**:
  - `owner@acme.com` (`OWNER`), `finance@acme.com` (`FINANCE_MANAGER`), `acct@acme.com` (`ACCOUNTANT`), `viewer@acme.com` (`VIEWER`).
  - Default password: `Password123!` (Bcrypt hashed).
- **Accounts & Actual Liquid Balances**:
  - `acc-op-001` (HDFC Operating Account): Opening ₹250,000.00 -> Ending ₹845,000.00.
  - `acc-sav-002` (ICICI Reserve Account): Opening ₹500,000.00 -> Ending ₹1,200,000.00.
  - Consolidated Liquid Cash: **₹2,045,000.00**.
- **Invoices & Receivables**:
  - `INV-2026-101`: Client B, ₹250,000.00 (`OVERDUE`).
  - `INV-2026-102`: Enterprise Client Alpha, ₹450,000.00 (`SENT`).
  - `INV-2026-103`: Global Digital Corp, ₹320,000.00 (`PAID`).
- **30-Day Ledger**:
  - Revenue inflows: ₹1,600,000.00 (Client receipts, retainer, cloud architecture milestones).
  - Operating outflows: ₹305,000.00 (AWS infrastructure, office lease, engineering payroll, SaaS).
  - Internal reserve transfer: ₹700,000.00 from HDFC to ICICI (neutral transfer, excluded from income/expense).
- **Sentinel Alerts & Risk**:
  - `alert-001`: `Minimum Cash Buffer Breach Risk` (Warning, projected buffer breach in 38 days against ₹500,000 reserve).
  - `risk-001`: In `risk_assessments` model with mitigation recommendations.
- **Analytical Outputs**:
  - 7d, 30d, 90d cash forecasts.
  - Monte Carlo simulation: 1,000 stochastic paths, P50 ₹2,886,777.18, reserve breach probability 0.1%.
  - Constrained decision optimization plan: status `FEASIBLE`, ₹780,000 actionable mitigations.

