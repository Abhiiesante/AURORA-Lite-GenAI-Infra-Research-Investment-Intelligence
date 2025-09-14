"""
Phase 4 monetization tables: tenants, api_keys, plans, subscriptions, usage_events,
entitlement_overrides, marketplace_items, orders.

Revision ID: 0006_phase4_tables
Revises: 0005_market_perf_indexes
Create Date: 2025-08-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_phase4_tables'
down_revision = '0005_market_perf_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active', index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('prefix', sa.String(length=32), nullable=False, index=True),
        sa.Column('key_hash', sa.String(length=128), nullable=False, index=True),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('rate_limit_per_min', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active', index=True),
    )
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('price_usd', sa.Float(), nullable=True),
        sa.Column('period', sa.String(length=32), nullable=True, server_default='monthly', index=True),
        sa.Column('entitlements_json', sa.Text(), nullable=True),
    )
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('plan_id', sa.Integer(), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active', index=True),
        sa.Column('current_period_end', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'usage_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('actor', sa.String(length=255), nullable=True, index=True),
        sa.Column('product', sa.String(length=64), nullable=False, index=True),
        sa.Column('verb', sa.String(length=64), nullable=False, index=True),
        sa.Column('units', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_type', sa.String(length=64), nullable=True),
        sa.Column('meta_json', sa.Text(), nullable=True),
        sa.Column('ts', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'entitlement_overrides',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('key', sa.String(length=128), nullable=False, index=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'marketplace_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sku', sa.String(length=128), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False, index=True),
        sa.Column('price_usd', sa.Float(), nullable=True),
        sa.Column('seller_id', sa.Integer(), nullable=True, index=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
    )
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('item_id', sa.Integer(), nullable=False, index=True),
        sa.Column('price_paid_usd', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='paid', index=True),
        sa.Column('ts', sa.String(length=64), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_table('orders')
    op.drop_table('marketplace_items')
    op.drop_table('entitlement_overrides')
    op.drop_table('usage_events')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_table('api_keys')
    op.drop_table('tenants')
