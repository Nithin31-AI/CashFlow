-- ==============================================================================
-- cashFlow PostgreSQL Synthetic Dataset — Acme Consulting Tech Ltd
-- Adapted to match cashFlow's multi-tenant architecture and schema constraints.
-- ==============================================================================

BEGIN;

-- 1. Multi-Tenant Business & Team Setup
INSERT INTO businesses (
    id, name, slug, currency, country, timezone, minimum_cash_reserve, created_at, updated_at
) 
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Acme Consulting Tech Ltd',
    'acme-consulting-tech-ltd',
    'INR',
    'IN',
    'Asia/Kolkata',
    500000.00,
    NOW(),
    NOW()
) 
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    minimum_cash_reserve = EXCLUDED.minimum_cash_reserve;

-- Users: Passwords hashed with bcrypt (password: 'Password123!')
INSERT INTO users (id, email, full_name, hashed_password, is_active, created_at, updated_at) VALUES
  ('user-owner-001', 'owner@acme.com', 'Alice Owner', '$2b$12$rqNFvHL9duioB/Xs5qD1pe1Hry4ft65VoYBG30Udl1ozhuxu1GZs2', true, NOW(), NOW()),
  ('user-fin-002', 'finance@acme.com', 'Bob Finance', '$2b$12$rqNFvHL9duioB/Xs5qD1pe1Hry4ft65VoYBG30Udl1ozhuxu1GZs2', true, NOW(), NOW()),
  ('user-acc-003', 'acct@acme.com', 'Charlie Acct', '$2b$12$rqNFvHL9duioB/Xs5qD1pe1Hry4ft65VoYBG30Udl1ozhuxu1GZs2', true, NOW(), NOW()),
  ('user-view-004', 'viewer@acme.com', 'David Viewer', '$2b$12$rqNFvHL9duioB/Xs5qD1pe1Hry4ft65VoYBG30Udl1ozhuxu1GZs2', true, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active;

-- Business Memberships
INSERT INTO business_memberships (id, business_id, user_id, role, created_at, updated_at) VALUES
  ('mem-user-owner-001', '11111111-1111-1111-1111-111111111111', 'user-owner-001', 'OWNER', NOW(), NOW()),
  ('mem-user-fin-002', '11111111-1111-1111-1111-111111111111', 'user-fin-002', 'FINANCE_MANAGER', NOW(), NOW()),
  ('mem-user-acc-003', '11111111-1111-1111-1111-111111111111', 'user-acc-003', 'ACCOUNTANT', NOW(), NOW()),
  ('mem-user-view-004', '11111111-1111-1111-1111-111111111111', 'user-view-004', 'VIEWER', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role;

-- Link existing user if present in database (fakeed@gmail.com)
INSERT INTO business_memberships (id, business_id, user_id, role, created_at, updated_at)
SELECT 'mem-user-current-session', '11111111-1111-1111-1111-111111111111', id, 'OWNER', NOW(), NOW()
FROM users WHERE email = 'fakeed@gmail.com'
ON CONFLICT DO NOTHING;

-- 2. Financial Accounts
INSERT INTO financial_accounts (
    id, business_id, name, account_type, account_number_mask, currency, institution_name, opening_balance, opening_balance_date, is_active, created_at, updated_at
) 
VALUES 
  ('acc-op-001', '11111111-1111-1111-1111-111111111111', 'HDFC Operating Account', 'BANK', '•••• 4201', 'INR', 'HDFC Bank', 250000.00, '2026-09-01', true, NOW(), NOW()),
  ('acc-sav-002', '11111111-1111-1111-1111-111111111111', 'ICICI Reserve Account', 'BANK', '•••• 9902', 'INR', 'ICICI Bank', 500000.00, '2026-09-01', true, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    opening_balance = EXCLUDED.opening_balance;

-- 3. Invoices & Receivables Trackers
INSERT INTO invoices (
    id, business_id, invoice_number, customer_name, customer_email, subtotal, tax_amount, total_amount, amount_paid, status, issue_date, due_date, currency, predicted_delay_days, notes, created_at, updated_at
)
VALUES 
  ('inv-2026-001', '11111111-1111-1111-1111-111111111111', 'INV-2026-101', 'Client B', 'billing@clientb.com', 250000.00, 0.00, 250000.00, 0.00, 'OVERDUE', '2026-09-01', '2026-09-06', 'INR', 14, 'Client milestone billing - payment delayed pending approval', NOW(), NOW()),
  ('inv-2026-002', '11111111-1111-1111-1111-111111111111', 'INV-2026-102', 'Enterprise Client Alpha', 'ap@clientalpha.com', 450000.00, 0.00, 450000.00, 0.00, 'SENT', '2026-09-15', '2026-10-15', 'INR', 3, 'Q3 Retainer consulting services', NOW(), NOW()),
  ('inv-2026-003', '11111111-1111-1111-1111-111111111111', 'INV-2026-103', 'Global Digital Corp', 'finance@globaldigital.com', 320000.00, 0.00, 320000.00, 320000.00, 'PAID', '2026-08-15', '2026-09-15', 'INR', 0, 'Completed cloud audit engagement', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    status = EXCLUDED.status,
    total_amount = EXCLUDED.total_amount;

-- 4. 30-Day Ledger Transactions
-- Calculated so HDFC Operating Account ends at ₹845,000.00 and ICICI Reserve ends at ₹1,200,000.00
INSERT INTO transactions (
    id, business_id, account_id, transaction_date, description, amount, transaction_type, category, currency, status, is_internal_transfer, reference_number, created_at, updated_at
)
VALUES 
  -- User Excerpt transaction
  ('tx-2026-001', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-15', 'Client Payment Receipt - Batch 0', 150000.00, 'INFLOW', 'REVENUE', 'INR', 'POSTED', false, 'TXN-REV-001', NOW(), NOW()),
  
  -- Additional Revenue Transactions into Operating Account
  ('tx-2026-002', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-05', 'Consulting Retainer - Client Alpha', 480000.00, 'INFLOW', 'REVENUE', 'INR', 'POSTED', false, 'TXN-REV-002', NOW(), NOW()),
  ('tx-2026-003', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-10', 'Cloud Architecture Milestone - TechCorp', 550000.00, 'INFLOW', 'REVENUE', 'INR', 'POSTED', false, 'TXN-REV-003', NOW(), NOW()),
  ('tx-2026-004', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-20', 'Annual Maintenance Contract - Fintech Ltd', 420000.00, 'INFLOW', 'REVENUE', 'INR', 'POSTED', false, 'TXN-REV-004', NOW(), NOW()),

  -- Operating Expenses from Operating Account
  ('tx-2026-005', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-02', 'AWS Cloud Hosting & Infrastructure', -45000.00, 'OUTFLOW', 'SOFTWARE', 'INR', 'POSTED', false, 'TXN-EXP-001', NOW(), NOW()),
  ('tx-2026-006', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-08', 'Office Space Lease & Co-working Rent', -85000.00, 'OUTFLOW', 'RENT', 'INR', 'POSTED', false, 'TXN-EXP-002', NOW(), NOW()),
  ('tx-2026-007', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-12', 'Monthly Engineering Team Payroll', -140000.00, 'OUTFLOW', 'PAYROLL', 'INR', 'POSTED', false, 'TXN-EXP-003', NOW(), NOW()),
  ('tx-2026-008', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-18', 'SaaS Subscriptions (Slack, GitHub, Figma)', -35000.00, 'OUTFLOW', 'SOFTWARE', 'INR', 'POSTED', false, 'TXN-EXP-004', NOW(), NOW()),

  -- Internal Transfer: Operating Account -> Reserve Account (₹700,000)
  ('tx-trans-out', '11111111-1111-1111-1111-111111111111', 'acc-op-001', '2026-09-16', 'Strategic Reserve Allocation to ICICI Reserve', -700000.00, 'INTERNAL_TRANSFER', 'INTERNAL_TRANSFER', 'INR', 'POSTED', true, 'XFER-001', NOW(), NOW()),
  ('tx-trans-in', '11111111-1111-1111-1111-111111111111', 'acc-sav-002', '2026-09-16', 'Strategic Reserve Allocation from HDFC Operating', 700000.00, 'INTERNAL_TRANSFER', 'INTERNAL_TRANSFER', 'INR', 'POSTED', true, 'XFER-001', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    amount = EXCLUDED.amount,
    category = EXCLUDED.category,
    status = EXCLUDED.status;

-- Link internal transfer counterparts
UPDATE transactions SET transfer_counterpart_id = 'tx-trans-in' WHERE id = 'tx-trans-out';
UPDATE transactions SET transfer_counterpart_id = 'tx-trans-out' WHERE id = 'tx-trans-in';

-- 5. Sentinel Alerts & Risk Prediction Rules
INSERT INTO alert_rules (
    id, business_id, name, category, threshold_value, severity, is_active, suppression_window_hours, created_at
)
VALUES (
    'rule-reserve-001',
    '11111111-1111-1111-1111-111111111111',
    'Minimum Cash Buffer Breach Risk',
    'RESERVE_BREACH',
    500000.00,
    'WARNING',
    true,
    24,
    NOW()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_events (
    id, business_id, rule_id, title, message, category, severity, financial_evidence, is_acknowledged, is_resolved, created_at
)
VALUES (
    'alert-001',
    '11111111-1111-1111-1111-111111111111',
    'rule-reserve-001',
    'Minimum Cash Buffer Breach Risk',
    'Projected cash balance falls below ₹500,000 safety threshold in 38 days.',
    'RESERVE_BREACH',
    'WARNING',
    '{"minimum_reserve_threshold": 500000.00, "projected_breach_days": 38, "current_liquid_cash": 2045000.00, "shortfall_amount": 120000.00}'::json,
    false,
    false,
    NOW()
)
ON CONFLICT (id) DO UPDATE SET 
    title = EXCLUDED.title,
    message = EXCLUDED.message,
    severity = EXCLUDED.severity;

-- Also populate risk_assessments for forecasting dashboard integration
INSERT INTO risk_assessments (
    id, business_id, risk_type, severity, title, description, potential_date, estimated_shortfall, contributing_factors, recommended_action, status, created_at
)
VALUES (
    'risk-001',
    '11111111-1111-1111-1111-111111111111',
    'CASH_SHORTAGE',
    'HIGH',
    'Minimum Cash Buffer Breach Risk',
    'Projected cash balance falls below ₹500,000 safety threshold in 38 days.',
    CURRENT_DATE + INTERVAL '38 days',
    120000.00,
    '{"minimum_reserve_threshold": 500000.0, "projected_breach_days": 38}'::json,
    'Accelerate collection of Overdue Invoice INV-2026-101 (Client B - ₹250,000) and defer non-critical software/consulting CapEx.',
    'ACTIVE',
    NOW()
)
ON CONFLICT (id) DO UPDATE SET 
    title = EXCLUDED.title,
    description = EXCLUDED.description;

COMMIT;
