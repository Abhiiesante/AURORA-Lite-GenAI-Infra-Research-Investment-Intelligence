"""
Phase 4 enterprise + queue + marketplace unification

Adds:
- webhook_queue (durable webhooks)
- org_seats (enterprise seats)
- watchlists + watchlist_items (workflow)
- marketplace_items back-compat columns (code, description, category, status)

Revision ID: 0007_phase4_enterprise_and_queue
Revises: 0006_phase4_tables
Create Date: 2025-09-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0007_phase4_enterprise_and_queue'
down_revision = '0006_phase4_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Durable webhook queue
    op.create_table(
        'webhook_queue',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=128), nullable=True, index=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('event', sa.String(length=128), nullable=False, index=True),
        sa.Column('body_json', sa.Text(), nullable=False),
        sa.Column('secret', sa.String(length=256), nullable=True),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='0', index=True),
        sa.Column('next_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='pending', index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )

    # Enterprise seats
    op.create_table(
        'org_seats',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('email', sa.String(length=255), nullable=False, index=True),
        sa.Column('role', sa.String(length=64), nullable=True, server_default='member', index=True),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='invited', index=True),
        sa.Column('invited_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('joined_at', sa.String(length=64), nullable=True, index=True),
    )

    # Watchlists + items
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('watchlist_id', sa.Integer(), nullable=False, index=True),
        sa.Column('company_id', sa.Integer(), nullable=False, index=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('added_at', sa.String(length=64), nullable=True, index=True),
    )

    # Marketplace unification: add back-compat columns
    with op.batch_alter_table('marketplace_items') as batch:
        batch.add_column(sa.Column('code', sa.String(length=128), nullable=True))
        batch.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch.add_column(sa.Column('category', sa.String(length=64), nullable=True))
        batch.add_column(sa.Column('status', sa.String(length=32), nullable=True))
    op.create_index('ix_marketplace_items_code', 'marketplace_items', ['code'], unique=False)
    op.create_index('ix_marketplace_items_category', 'marketplace_items', ['category'], unique=False)
    op.create_index('ix_marketplace_items_status', 'marketplace_items', ['status'], unique=False)


def downgrade() -> None:
    # Drop added indexes/columns for marketplace
    op.drop_index('ix_marketplace_items_status', table_name='marketplace_items')
    op.drop_index('ix_marketplace_items_category', table_name='marketplace_items')
    op.drop_index('ix_marketplace_items_code', table_name='marketplace_items')
    with op.batch_alter_table('marketplace_items') as batch:
        try:
            batch.drop_column('status')
        except Exception:
            pass
        try:
            batch.drop_column('category')
        except Exception:
            pass
        try:
            batch.drop_column('description')
        except Exception:
            pass
        try:
            batch.drop_column('code')
        except Exception:
            pass

    # Drop watchlists and seats and webhook queue
    op.drop_table('watchlist_items')
    op.drop_table('watchlists')
    op.drop_table('org_seats')
    op.drop_table('webhook_queue')
