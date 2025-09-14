"""saved views and minor indexes

Revision ID: 0004
Revises: 0003
Create Date: 2025-08-30

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'saved_views',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('view_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('filters_json', sa.Text(), nullable=True),
        sa.Column('layout_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('updated_at', sa.String(), nullable=True),
    )
    op.create_index('ix_saved_views_view_id', 'saved_views', ['view_id'])
    op.create_index('ix_saved_views_user_id', 'saved_views', ['user_id'])
    op.create_index('ix_saved_views_created_at', 'saved_views', ['created_at'])
    op.create_index('ix_saved_views_updated_at', 'saved_views', ['updated_at'])


def downgrade() -> None:
    op.drop_index('ix_saved_views_updated_at', table_name='saved_views')
    op.drop_index('ix_saved_views_created_at', table_name='saved_views')
    op.drop_index('ix_saved_views_user_id', table_name='saved_views')
    op.drop_index('ix_saved_views_view_id', table_name='saved_views')
    op.drop_table('saved_views')
