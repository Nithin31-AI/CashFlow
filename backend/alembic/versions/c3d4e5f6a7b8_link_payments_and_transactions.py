"""link_payments_and_transactions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-25 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add payment_id column to transactions with unique constraint to prevent duplicate payments
    op.add_column(
        'transactions',
        sa.Column('payment_id', sa.String(length=36), sa.ForeignKey('payments.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_transactions_payment_id', 'transactions', ['payment_id'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_transactions_payment_id', table_name='transactions')
    op.drop_column('transactions', 'payment_id')
