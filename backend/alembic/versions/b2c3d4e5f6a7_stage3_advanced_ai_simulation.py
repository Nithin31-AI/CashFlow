"""stage3_advanced_ai_simulation

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-24 23:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. financial_goals
    op.create_table(
        'financial_goals',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('goal_type', sa.String(length=50), nullable=False),
        sa.Column('target_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('is_hard_constraint', sa.Boolean(), default=True, nullable=False),
        sa.Column('priority', sa.Integer(), default=1, nullable=False),
        sa.Column('status', sa.String(length=50), default='ACTIVE', nullable=False, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. simulation_runs
    op.create_table(
        'simulation_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('horizon_days', sa.Integer(), nullable=False, default=30),
        sa.Column('num_paths', sa.Integer(), nullable=False, default=1000),
        sa.Column('seed', sa.Integer(), nullable=True),
        sa.Column('starting_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('min_projected_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('max_projected_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('p10_ending_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('p50_ending_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('p90_ending_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('reserve_breach_probability', sa.Numeric(5, 4), nullable=False, default=0.0),
        sa.Column('expected_shortfall', sa.Numeric(15, 2), nullable=False, default=0.0),
        sa.Column('potential_shortage_day', sa.Integer(), nullable=True),
        sa.Column('assumptions', sa.JSON(), nullable=False),
        sa.Column('percentile_paths', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(length=50), default='monte-carlo-v1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. saved_scenarios
    op.create_table(
        'saved_scenarios',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_baseline', sa.Boolean(), default=False, nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('projected_ending_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('min_cash', sa.Numeric(15, 2), nullable=False),
        sa.Column('shortage_risk_percent', sa.Numeric(5, 2), nullable=False, default=0.0),
        sa.Column('runway_days', sa.Integer(), nullable=False, default=90),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. optimisation_plans
    op.create_table(
        'optimisation_plans',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('scenario_id', sa.String(length=36), sa.ForeignKey('saved_scenarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), default='FEASIBLE', nullable=False),
        sa.Column('objective_value', sa.Numeric(15, 2), nullable=False, default=0.0),
        sa.Column('recommended_actions', sa.JSON(), nullable=False),
        sa.Column('trade_offs', sa.Text(), nullable=True),
        sa.Column('hard_constraints_satisfied', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. financial_recommendations
    op.create_table(
        'financial_recommendations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), default='MEDIUM', nullable=False),
        sa.Column('estimated_impact', sa.Numeric(15, 2), nullable=False, default=0.0),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('supporting_records', sa.JSON(), nullable=True),
        sa.Column('assumptions', sa.Text(), nullable=True),
        sa.Column('disadvantages', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), default='ACTIVE', nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 6. alert_rules
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('threshold_value', sa.Numeric(15, 2), nullable=False, default=0.0),
        sa.Column('severity', sa.String(length=50), default='WARNING', nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('suppression_window_hours', sa.Integer(), default=24, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 7. alert_events
    op.create_table(
        'alert_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rule_id', sa.String(length=36), sa.ForeignKey('alert_rules.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), default='WARNING', nullable=False, index=True),
        sa.Column('financial_evidence', sa.JSON(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_resolved', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )

    # 8. model_evaluations
    op.create_table(
        'model_evaluations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('model_name', sa.String(length=100), nullable=False, index=True),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('evaluation_date', sa.Date(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('baseline_comparison', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), default='ACTIVE', nullable=False),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('model_evaluations')
    op.drop_table('alert_events')
    op.drop_table('alert_rules')
    op.drop_table('financial_recommendations')
    op.drop_table('optimisation_plans')
    op.drop_table('saved_scenarios')
    op.drop_table('simulation_runs')
    op.drop_table('financial_goals')
