# cashFlow — Project Context & Mission

## 1. Product Identity

- **Official Product Name**: `cashFlow`
- **Official Tagline**: `PLAN • FORECAST • GROW`
- **Product Classification**: AI-Powered Financial Intelligence SaaS Platform for Small Service-Based Businesses.
- **Default Locale & Currency**: India-first with Indian Rupee (`INR` / `₹`) default currency formatting, architected for seamless multi-currency support (`USD`, `EUR`, `GBP`, `AED`, `SGD`).

---

## 2. Target Audience

cashFlow is specifically built to address the unique liquidity and cash-timing challenges of small service-based businesses:
- **IT Service Companies**: Managing client milestone billings, payroll runs, and recurring cloud hosting costs.
- **Consulting Firms**: Tracking variable retainer contracts, payment lag times, and consultant payouts.
- **Digital Agencies**: Managing fluctuating project scopes, vendor advances, and contractor invoices.
- **Freelancers & Solopreneurs**: Needing simple, non-cluttered visibility into actual available cash vs. pending receivables.
- **Other Small Service Businesses**: Businesses operating on accrual invoices that need strict cash-basis reality checks.

---

## 3. Central Value Chain & Workflow

cashFlow transforms raw, fragmented financial documents into actionable, explainable decision intelligence:

```
Financial Documents (CSV / Excel / PDF / Images)
                     │
                     ▼
        [1. Financial Data Ingestion]
  (Safe non-public storage, magic byte check, duplicate detection)
                     │
                     ▼
     [2. Verified Financial Position]
 (Row validation, decimal checks, no synthetic values, reconciliation)
                     │
                     ▼
         [3. Cash-Flow Forecast]
 (Separation of confirmed cash vs. projected receivables/payables)
                     │
                     ▼
        [4. Risk Identification]
 (Cash shortage prediction, overdue invoice delays, runway alerts)
                     │
                     ▼
          [5. Scenario Analysis]
 (Hiring plans, CAPEX timing, tax outflows, contract delays)
                     │
                     ▼
  [6. Explainable Decision Support]
(AI recommendations with clear provenance, citations, and user confirmation)
```

---

## 4. Immutable Core Principles

All architectural decisions, algorithms, UI components, and AI prompts in cashFlow must strictly adhere to these non-negotiable principles:

1. **Strict Separation of Actual vs. Projected Cash**: Confirmed, cleared cash balances must never be mingled with pending receivables or expected income.
2. **Unpaid Invoices are Not Available Cash**: An outstanding invoice is an accounts receivable entry, not spendable liquidity.
3. **Credit Limits are Not Cash**: Available credit facility or overdraft limit is debt capacity, not cash on hand.
4. **Internal Transfers are Neutral**: Transfers between bank accounts or wallets of the same business entity are not revenue or operating expenses.
5. **Multi-Currency Discipline**: Different currencies must never be summed directly without verified conversion rates and transparent timestamps.
6. **Complete Provenance & Traceability**: Every financial record must trace back to its verified source file, import job, and original row index.
7. **Verified Financial Service Delegation**: The AI assistant and forecasting engines must rely on verified mathematical calculations from backend domain services, never hallucinated calculations.
8. **User Authority & Consequential Control**: Users must explicitly review and confirm consequential actions (approving imports, executing payouts, modifying settings).
9. **Zero Fabricated Financial Data**: When data is absent, the system displays clear empty states and guidance. Fake balances, mock accounts, or fabricated financial numbers must never be displayed to users.
10. **Absolute Tenant Isolation**: No business may ever access, query, or infer another business's financial data. Enforced at the database and API layer.
11. **Honest AI/ML Capabilities**: Model capabilities, confidence scores, and limitations must be reported transparently without overstating precision.

---

## 5. Four-Stage Development Roadmap

> **Important**: This roadmap defines the intended project scope. The presence of a stage in this roadmap does not imply that the stage is complete. Refer to `CURRENT_STATE.md` for verified implementation status.

### STAGE 1: Foundation, Database, Security, and Financial Data Import
- Multi-tenant architecture and strict tenant isolation.
- Role-Based Access Control (`OWNER`, `FINANCE_MANAGER`, `ACCOUNTANT`, `VIEWER`).
- Database foundation (PostgreSQL/SQLite via SQLAlchemy 2.0 with Alembic migrations).
- Secure authentication, session handling, tokenized password recovery.
- Safe file upload storage with MIME magic-byte validation and duplicate SHA-256 detection.
- Complete 8-step CSV and Excel import pipeline with auto column detection, date format recognition, and row validation.
- Extensible extraction interface for PDF statements and receipt image OCR.
- Application branding with official cashFlow logo and responsive SaaS interface.

### STAGE 2: Financial Engine, Reconciliation, Forecasting, Risk Prediction, Spatial UI, Theme Support, and Multiple-File Uploads
- Cash-flow categorization and transaction tagging engine.
- Bank statement reconciliation with double-entry ledger adjustments.
- Multi-file batch upload queue.
- Cash-flow forecasting models (statistical time-series and cash burn analysis).
- Payment delay prediction and cash shortage alert mechanisms.
- Spatial UI design system with dark mode and light mode theme support, theme-aware logo assets, and natural vertical dashboard scrolling.

### STAGE 3: Advanced AI, Decision Optimization, Simulation, and Conversational Assistant
- Monte Carlo simulations for cash runway under varying revenue scenarios.
- Decision optimization algorithms (optimal payment dates, hiring capacity, CAPEX timing).
- Conversational financial intelligence assistant using verified tool-calling.
- Natural language query answering backed by verified business ledger data.

### STAGE 4: Integration, Security Validation, and Production Deployment
- Real-time Open Banking / aggregator feed integrations.
- Comprehensive security penetration testing, rate-limiting, and compliance validation.
- Production multi-region deployment, CI/CD pipelines, container orchestration, and telemetry.
