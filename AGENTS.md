# cashFlow — AI Agent & Developer Operating Protocol

> **CRITICAL INSTRUCTION FOR ALL AI DEVELOPMENT SESSIONS:**
> This repository contains a persistent project memory system located in `project-memory/`.
> Every AI agent or developer working on **cashFlow** must strictly follow this protocol.
> Do not rely on conversation context alone. The repository source code, tests, and verified documentation in `project-memory/` are the primary source of truth.

---

## 1. Product Identity & Rules of Truth

- **Official Product Name**: `cashFlow`
- **Official Tagline**: `PLAN • FORECAST • GROW`
- **Domain**: AI-Powered Financial Intelligence SaaS for Small Service-Based Businesses.
- **Source of Truth Hierarchy**:
  1. Actual source code and current configuration files.
  2. Database migrations and verified runtime behavior.
  3. Tests that have actually executed and their empirical results.
  4. Current `project-memory/` documentation.
  5. Historical changelog and decisions log.
  6. Previous AI conversation context.
  7. Unverified assumptions (NEVER treat assumptions as truth).

---

## 2. Mandatory Session Protocols

### SESSION START PROTOCOL
Before making any modifications or proposing changes, the AI agent **MUST**:

1. **Read `AGENTS.md`** (this document).
2. **Read `project-memory/PROJECT_CONTEXT.md`** to understand project identity, target users, core financial rules, and roadmap.
3. **Read `project-memory/CURRENT_STATE.md`** to identify verified vs. planned features, current bugs, and blockers.
4. **Read `project-memory/NEXT_STEPS.md`** to identify the active stage, current task, and priorities.
5. **Read `project-memory/REQUIREMENTS.md`** to verify specific feature requirements and constraints.
6. **Read `project-memory/ARCHITECTURE.md`** to understand system components, data flows, and tech stacks.
7. **Read `project-memory/DECISIONS_LOG.md`** to understand why specific architectural choices were made before proposing changes.
8. **Read supporting documents** relevant to the assigned task:
   - For database work: `DATABASE_SCHEMA.md`
   - For API development: `API_DOCUMENTATION.md`
   - For UI/branding work: `UI_DESIGN_SYSTEM.md`
   - For forecasting/risk models: `AI_ML_DOCUMENTATION.md`
   - For security/auth: `SECURITY_RULES.md`
   - For testing/verification: `TESTING_STATUS.md`
9. **Inspect actual source code and configuration files** to confirm that documentation matches reality.
10. **Verify documentation against repository**: If documentation conflicts with the code, investigate and establish the actual state. Do not blindly trust stale documents.
11. **Identify the current development stage and task**: Confirm what stage is active (e.g. Stage 1 verified, Stage 2 upcoming). Do not jump to later stages prematurely.
12. **Summarize current state** to the user before editing files. Do not ask the user to repeat information that is already documented.

---

### SESSION EXECUTION PROTOCOL
During the development session, the AI agent **MUST**:

1. **Work strictly on the requested task**: Do not introduce out-of-scope refactorings or jump to later project stages.
2. **Preserve existing working functionality**: Ensure existing endpoints, tests, and UI flows continue to function.
3. **Follow documented requirements and architectural decisions**: Honor established patterns (e.g., multi-tenant isolation, decimal financial math).
4. **Avoid unnecessary architectural churn**: Do not swap frameworks, ORMs, or libraries unless explicitly mandated.
5. **Prioritize financial correctness and security**:
   - Actual cash and projected cash must remain strictly separated.
   - Unpaid invoices and credit lines are never treated as available cash.
   - Internal transfers must never be counted as income or expenses.
   - Tenant isolation via `business_id` is mandatory on every query.
   - Financial figures must never be fabricated.
6. **Update tests for changed behavior**: Add unit, integration, or end-to-end tests for all new code.
7. **Run relevant tests**: Execute tests via pytest or npm test scripts.
8. **Record failures honestly**: Never hide or erase test failures; document and fix them systematically.
9. **Update documentation progressively**: Update affected memory documents during implementation for major architectural decisions.

---

### SESSION END PROTOCOL
Before concluding the session and reporting to the user, the AI agent **MUST**:

1. **Review all files changed** during the session (`git status` / `git diff`).
2. **Record implemented features** accurately.
3. **Update `project-memory/CURRENT_STATE.md`**: Update feature statuses (`IMPLEMENTED`, `TESTED`, `VERIFIED`).
4. **Update `project-memory/REQUIREMENTS.md`**: Update requirement statuses and implementation links.
5. **Update `project-memory/ARCHITECTURE.md`**: Update if tech stack, dependencies, or components changed.
6. **Update `project-memory/DATABASE_SCHEMA.md`**: Update if Alembic migrations or models changed.
7. **Update `project-memory/API_DOCUMENTATION.md`**: Update if routes, request/response schemas changed.
8. **Update `project-memory/UI_DESIGN_SYSTEM.md`**: Update if components, styling, or themes changed.
9. **Update `project-memory/AI_ML_DOCUMENTATION.md`**: Update if algorithms or models changed.
10. **Update `project-memory/SECURITY_RULES.md`**: Update if auth, RBAC, or security controls changed.
11. **Update `project-memory/TESTING_STATUS.md`**: Record actual commands run, dates, and test results.
12. **Update `project-memory/DECISIONS_LOG.md`**: Add new records (`DEC-xxx`) for significant architectural decisions.
13. **Add a `project-memory/CHANGELOG.md` entry**: Document files created/modified, bugs fixed, and milestones achieved.
14. **Update `project-memory/NEXT_STEPS.md`**: Check off completed tasks and update the prioritized next actions.
15. **Verify internal consistency**: Ensure no document contradicts the code or another memory document.
16. **Provide the user with a concise implementation report** detailing changes, test results, and next actions.

---

## 3. Memory File Safety & Security Rules

- **NEVER store real secrets, API keys, passwords, private keys, or tokens** in any memory file.
- **NEVER store real customer financial records or PII** in any memory file.
- Use environment variable placeholders (`${JWT_SECRET}`, `DATABASE_URL`) in examples.
- Do not place uploaded customer financial documents into `project-memory/`.

---

## 4. Feature Status Definitions

- `PLANNED`: Feature is defined in requirements but no code exists.
- `IN_PROGRESS`: Feature code is actively being written.
- `IMPLEMENTED`: Feature code is completely written and integrated into the repository.
- `TESTED`: Relevant automated tests have been executed and passed against the feature code.
- `VERIFIED`: The feature's end-to-end behavior has been validated and confirmed via empirical runtime evidence (e.g. browser execution, API responses).
- `BLOCKED`: Development is halted due to an external dependency or critical bug.
- `DEPRECATED`: Feature has been intentionally superseded or removed.

*Rule: Never mark a feature as `VERIFIED` merely because code was written.*
