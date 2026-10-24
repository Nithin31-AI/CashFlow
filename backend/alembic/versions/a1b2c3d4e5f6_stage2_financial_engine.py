"""stage2_financial_engine

Revision ID: a1b2c3d4e5f6
Revises: 9c2481321bb2
Create Date: 2026-10-24 21:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9c2481321bb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update businesses table
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('minimum_cash_reserve', sa.Numeric(15, 2), server_default='100000.00', nullable=False))

    # 2. Update financial_accounts table
    with op.batch_alter_table('financial_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('opening_balance', sa.Numeric(15, 2), server_default='0.00', nullable=False))
        batch_op.add_column(sa.Column('opening_balance_date', sa.Date(), server_default=sa.func.current_date(), nullable=False))

    # 3. exchange_rates table
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('base_currency', sa.String(length=10), nullable=False, index=True),
        sa.Column('target_currency', sa.String(length=10), nullable=False, index=True),
        sa.Column('rate', sa.Numeric(18, 6), nullable=False),
        sa.Column('rate_date', sa.Date(), nullable=False, index=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('base_currency', 'target_currency', 'rate_date', name='uq_exchange_rate_date')
    )

    # 4. transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('account_id', sa.String(length=36), sa.ForeignKey('financial_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('imported_record_id', sa.String(length=36), sa.ForeignKey('imported_records.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('transaction_date', sa.Date(), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='OTHER', nullable=False, index=True),
        sa.Column('transaction_type', sa.String(length=50), server_default='OUTFLOW', nullable=False, index=True),
        sa.Column('status', sa.String(length=50), server_default='POSTED', nullable=False, index=True),
        sa.Column('is_internal_transfer', sa.Boolean(), server_default='0', nullable=False, index=True),
        sa.Column('transfer_counterpart_id', sa.String(length=36), sa.ForeignKey('transactions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 5. invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=False, index=True),
        sa.Column('due_date', sa.Date(), nullable=False, index=True),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0.00', nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('amount_paid', sa.Numeric(15, 2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False, index=True),
        sa.Column('expected_payment_date', sa.Date(), nullable=True),
        sa.Column('predicted_delay_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('business_id', 'invoice_number', name='uq_business_invoice_number')
    )

    # 6. payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('account_id', sa.String(length=36), sa.ForeignKey('financial_accounts.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('payment_date', sa.Date(), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('payment_method', sa.String(length=50), server_default='BANK_TRANSFER', nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True, index=True),
        sa.Column('payer_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('unallocated_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 7. invoice_payment_allocations table
    op.create_table(
        'invoice_payment_allocations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('invoice_id', sa.String(length=36), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('payment_id', sa.String(length=36), sa.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('allocated_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('allocated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('invoice_id', 'payment_id', name='uq_invoice_payment_allocation')
    )

    # 8. reconciliations table
    op.create_table(
        'reconciliations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transaction_id', sa.String(length=36), sa.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('matched_entity_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('matched_entity_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('match_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING_REVIEW', nullable=False, index=True),
        sa.Column('matched_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('reviewed_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('transaction_id', 'matched_entity_type', 'matched_entity_id', name='uq_reconciliation_match')
    )

    # 9. forecast_runs table
    op.create_table(
        'forecast_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('run_date', sa.Date(), nullable=False, index=True),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('starting_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('projected_inflows', sa.Numeric(15, 2), nullable=False),
        sa.Column('projected_outflows', sa.Numeric(15, 2), nullable=False),
        sa.Column('net_change', sa.Numeric(15, 2), nullable=False),
        sa.Column('ending_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('confidence_lower', sa.Numeric(15, 2), nullable=False),
        sa.Column('confidence_upper', sa.Numeric(15, 2), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('assumptions', sa.JSON(), nullable=True),
        sa.Column('daily_projections', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 10. risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('risk_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('severity', sa.String(length=50), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('potential_date', sa.Date(), nullable=True, index=True),
        sa.Column('estimated_shortfall', sa.Numeric(15, 2), nullable=True),
        sa.Column('contributing_factors', sa.JSON(), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 11. expense_anomalies table
    op.create_table(
        'expense_anomalies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transaction_id', sa.String(length=36), sa.ForeignKey('transactions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('anomaly_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('expected_amount_range', sa.String(length=100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('reviewed', sa.Boolean(), server_default='0', nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('expense_anomalies')
    op.drop_table('risk_assessments')
    op.drop_table('forecast_runs')
    op.drop_table('reconciliations')
    op.drop_table('invoice_payment_allocations')
    op.drop_table('payments')
    op.drop_table('invoices')
    op.drop_table('transactions')
    op.drop_table('exchange_rates')
    with op.batch_alter_table('financial_accounts', schema=None) as batch_op:
        batch_op.drop_column('opening_balance_date')
        batch_op.drop_column('opening_balance')
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_column('minimum_cash_reserve')
