# cashFlow — AI, ML & Analytical Engine Documentation

## 1. Engine Classification & Status Overview

cashFlow differentiates between deterministic domain logic, statistical models, machine learning predictors, and LLM-assisted decision support:

| Component | Category | Status | Implementation Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Heuristic Column Mapper** | Deterministic Heuristic | `VERIFIED` | `backend/app/services/column_detector.py` | Synonym dictionary scoring and substring matching for financial column detection. |
| **Date Format Heuristic** | Pattern Matching | `VERIFIED` | `backend/app/services/column_detector.py` | Regex parsing of sample rows to infer date format (`%d/%m/%Y`, `%Y-%m-%d`, etc.). |
| **Row Validation Engine** | Deterministic Math | `VERIFIED` | `backend/app/services/validator.py` | Decimal sanitization, sign conversion, parentheses handling `(100.50)` -> `-100.50`. |
| **Extensible Document Extractor** | Rule-based Parsing | `IMPLEMENTED` | `backend/app/services/extraction/` | Structural table extraction via `pdfplumber`; OCR extension points for Tesseract/Cloud. |
| **Cash-Flow Forecasting** | Statistical Time-Series | `VERIFIED` | `backend/app/services/forecasting_service.py` | Multi-horizon projections (7d, 30d, 90d, 180d, 365d) with daily paths, confidence intervals, and burn rate analysis. |
| **Payment Delay Predictor** | Risk Estimation | `VERIFIED` | `backend/app/services/risk_service.py` | Assessment of invoice payment delays based on aging brackets and payment latency. |
| **Cash Shortage Predictor** | Risk Detection | `VERIFIED` | `backend/app/services/risk_service.py` | Compares projected cash against minimum reserve threshold, generating severity and recommendations. |
| **Statistical Expense Anomaly Detector** | Statistical Outlier Detection | `VERIFIED` | `backend/app/services/risk_service.py` | Flags expense transactions deviating by > 2.5 standard deviations (2.5σ) from category baseline. |
| **Explainable Reconciliation Matcher** | Multi-Factor Heuristic | `VERIFIED` | `backend/app/services/reconciliation_service.py` | Candidate matching with Explainable AI confidence scores (0.0 to 1.0) and human review gates. |
| **Monte Carlo Simulation** | Probabilistic Simulation | `VERIFIED` | `backend/app/services/simulation_service.py` | 1000 stochastic revenue/expense paths, daily percentile envelopes (P10/P50/P90), reserve breach probability, expected shortfall, seed reproducibility. |
| **Decision Optimizer** | Constraint Optimization | `VERIFIED` | `backend/app/services/decision_service.py` | Linear constrained solver balancing cash preservation against business goals; advisory-only with human confirmation. |
| **Explainable Recommendations** | Rule-Based AI Engine | `VERIFIED` | `backend/app/services/decision_service.py` | Severity-graded actions with traceable financial evidence, disadvantages, assumptions, and acceptance workflows. |
| **Conversational Assistant** | Grounded Tool-Calling | `VERIFIED` | `backend/app/services/assistant_service.py` | Natural language interface querying verified backend tools with citations, prompt injection defense, and zero hallucinated math. |
| **Automated Sentinel Alerts** | Rule-Based Monitoring | `VERIFIED` | `backend/app/services/alert_service.py` | Automated reserve breach and overdue invoice alarms with 24h duplicate suppression. |

---

## 2. Stage 3 Probabilistic & Decision Intelligence Models

### 2.1 Monte Carlo Cash-Flow Simulation Engine (`simulation_service.py`)
- **Stochastic Path Generation**:
  - Simulates $N = 1000$ independent cash trajectory paths over horizon $H \in [15, 90]$ days.
  - Generates stochastic daily net cash flows using normal distribution calibrated on historical transaction volatility $\sigma_{\text{daily}}$ and drift $\mu_{\text{daily}}$:
    $$\Delta C_{t, p} = \mathcal{N}\left(\mu_{\text{daily}} \cdot \text{multiplier}, \sigma_{\text{daily}}\right)$$
  - Adjusts receivables based on configurable payment delay $D_{\text{delay}}$ and collection probability $P_{\text{collect}}$:
    $$\text{Cash}_{t, p} = \text{Cash}_{t-1, p} + \Delta C_{t, p} + \text{Inflow}_{t - D_{\text{delay}}} \cdot \mathbb{I}(U < P_{\text{collect}})$$
- **Percentile Distributions & Envelopes**:
  - Daily percentiles computed across all paths: $P_{10}, P_{25}, P_{50}, P_{75}, P_{90}$.
  - Ending cash distributions: $P_{10}, P_{50}, P_{90}$.
- **Risk Metrics**:
  - **Reserve Breach Probability**:
    $$P(\text{Breach}) = \frac{1}{N} \sum_{p=1}^{N} \mathbb{I}\left(\min_t \text{Cash}_{t, p} < \text{Minimum Reserve}\right)$$
  - **Expected Shortfall (CVaR)**: Average shortfall amount among paths that breach the reserve.
  - **Potential Shortage Day**: Earliest median day where the cash reserve is breached.
- **Reproducibility**: Supports optional integer `seed` parameter guaranteeing identical stochastic paths across repeated invocations.

### 2.2 Constrained Decision Optimisation Solver (`decision_service.py`)
- **Objective**: Maximize ending liquidity buffer while satisfying all hard constraints.
- **Constraints**:
  - Hard constraints: `MIN_CASH_BUFFER` (cash balance must strictly remain $\ge \text{target}$), `MAX_OVERDUE_DAYS`.
  - Soft constraints: `TARGET_SAVINGS`, `DEBT_REDUCTION`.
- **Status Classification**:
  - `FEASIBLE`: All hard and soft constraints are met without trade-offs.
  - `PARTIALLY_FEASIBLE`: Hard constraints met, but some soft goals relaxed.
  - `INFEASIBLE`: Hard constraints violated given current cash and obligations.
- **Advisory Principle**: Solutions are strictly advisory; automated executions of bank transfers or debt drawdowns are disallowed without explicit human confirmation.

### 2.3 Grounded Conversational Assistant (`assistant_service.py`)
- **Architecture**: Tool-Calling Dispatcher interfacing with 10 deterministic domain tools:
  - `get_actual_cash_balance`: Cleared bank ledger balances and reserve headroom.
  - `get_overdue_invoices`: Unpaid invoices past due date and delay predictions.
  - `get_forecast_summary`: Multi-horizon deterministic forecast projections (with dictionary and object-safe attribute access).
  - `get_simulation_summary`: Latest Monte Carlo run percentiles, breach probability, and expected shortfall.
  - `get_recommendations`: Active explainable recommendations with financial evidence.
  - `get_expenses_summary`: Categorized operational expense totals and breakdown.
  - `get_recorded_payments`: Historical customer payment settlements.
  - `get_cash_flow_risks`: Sentinel alert rules and active breach events.
  - `get_scenario_summary`: Custom comparative decision scenarios.
  - `get_historical_cash_flow`: Aggregated revenue, expenses, and net cash flow.
- **Zero-Hallucination & Scope Guardrails**:
  - Numeric figures are strictly sourced from verified tool payloads using exact Decimal mathematics.
  - Explicit evidence citations returned in every response ("Verified Cleared Bank Ledger", "Accounts Receivable Ledger", etc.).
  - Non-financial, out-of-scope queries (weather, sports, general advice) are safely redirected to financial analysis without fabrication.
  - Explicit assumptions notes appended to responses.
- **Prompt Injection Defense**:
  - Input query sanitized for system override keywords and injection delimiters.
  - Queries attempting to override instructions are safely rejected.

### 2.4 Model Evaluation & Versioning (`ModelEvaluation`)
- Tracks model runs with version strings (`mc-v1.0`), evaluation metrics (MAPE, RMSE, Breach Calibration), sample sizes, and timestamps.
