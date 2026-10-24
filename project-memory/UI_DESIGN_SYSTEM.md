# cashFlow — UI & Design System

## 1. Brand Identity & Official Assets

- **Official Product Name**: `cashFlow` (lowercase 'cash', uppercase 'Flow')
- **Official Tagline**: `PLAN • FORECAST • GROW`
- **Single Canonical Sage-Green Color**: `#8A9A78`
  - In Stage 3, the accent green has been strictly canonicalized to `#8A9A78` across BOTH Dark Mode and Light Cream Mode.
  - Zero conflicting green variations, zero harsh green gradients.
  - Tokenized in `globals.css` as `--color-sage: #8A9A78;`, `--accent-sage: #8A9A78;`, `--color-success: #8A9A78;`, and `--brand-green: #8A9A78;`.
- **Browser Favicon**:
  - Official CF monogram mark extracted from `cashflow-logo.png` (rows 220–570, cols 260–765), transparent background, padded to square, and generated as `frontend/public/favicon.ico`, `frontend/src/app/favicon.ico`, and `frontend/public/images/cashflow-favicon.png`.
  - Configured in Next.js metadata `icons` in `frontend/src/app/layout.tsx`.
- **Theme-Aware Official Logos**:
  - Light Theme Logo: `frontend/public/images/cashflow-logo-light.png` (and `public/cashflow-logo-light.png`). Charcoal text `#171A16` with deep sage accent `#788B63`.
  - Dark Theme Logo: `frontend/public/images/cashflow-logo-dark.png` (and `public/cashflow-logo-dark.png`). Light cream text `#F5F0E6` with vibrant sage accent `#A3B18A`.
  - Monogram contains stylized "CF" with financial growth chart bars, upward trajectory arrow, and Indian Rupee (`₹`) coin icon.
  - Dynamically selected by `frontend/src/components/Logo.tsx` based on active theme context with zero image distortion and configurable sizes (`sm`, `md`, `lg`, `xl`).

---

## 2. Spatial UI & Dual-Theme Architecture (Stage 3 Verified)

The design system implements a refined **Spatial UI** with depth, subtle elevation layers, soft backdrop blurs, and dual-theme switching with zero hydration flash:

### Dark Mode (`theme: 'dark'`)
- Backgrounds: Near-black (`#0B0D0B`) canvas, dark charcoal (`#141714`) main area.
- Elevated Card Surfaces: Deep charcoal (`#191F19`) with translucent 1px borders (`#2A352A`).
- Canonical Accent Color: Unified sage green (`#8A9A78`).
- Typography: Light warm cream (`#F5F0E6`) primary text, muted slate (`#9CA3AF`).
- Logo: Automatically displays `cashflow-logo-dark.png`.

### Light Cream Mode (`theme: 'light'`)
- Backgrounds: Warm light cream (`#F7F4EA`) canvas, soft cream (`#F3EFE0`) main area.
- Elevated Card Surfaces: Warm elevated cream (`#FFFCF5`) with subtle border lines (`#E2DBC8`).
- Canonical Accent Color: Unified sage green (`#8A9A78`).
- Typography: Deep charcoal (`#171A16`) primary text, warm muted gray (`#595E56`).
- Logo: Automatically displays `cashflow-logo-light.png`.

---

## 3. Theme Toggle & Layout Mechanics

- **Theme Switcher**: `frontend/src/components/ThemeToggle.tsx` provides clean pill controls (`Light`, `Dark`, `System`) in the sidebar and auth headers.
- **Persistence**: Managed by `frontend/src/lib/theme.tsx` using `localStorage` key `cashflow_theme` with system `prefers-color-scheme` fallback and mounted protection against FOUC.
- **Natural Vertical Window Scrolling**: Built in `frontend/src/app/(dashboard)/layout.tsx`. Eliminates fixed-height viewport locks or scroll hijacks, allowing natural browser-native scrolling while keeping the sidebar anchored (`sticky top-0 h-screen`).

---

## 4. UI Component Library & Implementation Status

| Component | File Path | Status | Verification Notes |
| :--- | :--- | :--- | :--- |
| **`Logo`** | `frontend/src/components/Logo.tsx` | `VERIFIED` | Dynamic switching between `cashflow-logo-dark.png` and `cashflow-logo-light.png`. |
| **`ThemeToggle`** | `frontend/src/components/ThemeToggle.tsx` | `VERIFIED` | Light/Dark/System switcher with smooth transitions. |
| **`Sidebar`** | `frontend/src/components/Sidebar.tsx` | `VERIFIED` | Sticky sidebar with active route highlights, workspace switcher, and role badge. |
| **`Dashboard`** | `frontend/src/app/(dashboard)/dashboard/page.tsx` | `VERIFIED` | Liquid cash balance, reserve headroom, 30-day forecast chart, risk alerts. |
| **`Invoices`** | `frontend/src/app/(dashboard)/invoices/page.tsx` | `VERIFIED` | Invoice list, overdue aging alerts, and payment allocation modal. |
| **`Transactions`** | `frontend/src/app/(dashboard)/transactions/page.tsx` | `VERIFIED` | Ledger table with category filters and "Record Transfer" modal. |
| **`Reconciliation`** | `frontend/src/app/(dashboard)/reconciliation/page.tsx` | `VERIFIED` | Candidate matches, confidence score pills, explainable AI reasons, approval/rejection buttons. |
| **`Forecast`** | `frontend/src/app/(dashboard)/forecast/page.tsx` | `VERIFIED` | Multi-horizon selector (7d, 30d, 90d, 180d, 365d), runway chart, risk cards, anomaly review. |
| **`Simulation`** | `frontend/src/app/(dashboard)/simulation/page.tsx` | `VERIFIED` | Monte Carlo stochastic simulation interface with P10/P50/P90 cards and daily percentile envelope. |
| **`Decisions`** | `frontend/src/app/(dashboard)/decisions/page.tsx` | `VERIFIED` | Financial goals, scenario simulator, constrained decision optimiser plan with user confirmation, and explainable recommendations. |
| **`Assistant`** | `frontend/src/app/(dashboard)/assistant/page.tsx` | `VERIFIED` | Conversational financial intelligence assistant with prompt pills, verified data citations, and zero hallucination. |
| **`Alerts`** | `frontend/src/app/(dashboard)/alerts/page.tsx` | `VERIFIED` | Sentinel liquidity alarms, acknowledge/resolve workflows, "Evaluate Alerts Now" trigger, and rule management. |
| **Multi-File Queue** | `frontend/src/app/(dashboard)/imports/new/page.tsx` | `VERIFIED` | Batch drag-and-drop queue, per-file status badges, concurrent ingestion, and retry. |
| **`EmptyState`** | `frontend/src/components/EmptyState.tsx` | `VERIFIED` | Clean zero-fabrication guides without synthetic numbers. |
