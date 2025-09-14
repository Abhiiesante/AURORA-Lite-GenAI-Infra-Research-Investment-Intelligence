"""
Phase 5 certification and success-fee pilot tables

Adds:
- analyst_certifications
- success_fee_agreements
- intro_events

Revision ID: 0009_phase5_certification_success_fee
Revises: 0008_phase5_sovereign_kernel
Create Date: 2025-09-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0009_phase5_certification_success_fee'
down_revision = '0008_phase5_sovereign_kernel'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'analyst_certifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analyst_email', sa.String(length=255), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='pending', index=True),
        sa.Column('issued_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('revoked_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'success_fee_agreements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('percent_fee', sa.Float(), nullable=False, server_default='0.01'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true(), index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'intro_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('agreement_id', sa.Integer(), nullable=False, index=True),
        sa.Column('company_uid', sa.String(length=255), nullable=False, index=True),
        sa.Column('introduced_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('closed_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('deal_value_usd', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('intro_events')
    op.drop_table('success_fee_agreements')
    op.drop_table('analyst_certifications')
