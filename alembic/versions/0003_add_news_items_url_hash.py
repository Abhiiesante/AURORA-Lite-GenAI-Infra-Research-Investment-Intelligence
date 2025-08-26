"""add url_hash to news_items

Revision ID: 0003
Revises: 0002
Create Date: 2025-08-25

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add url_hash column (nullable) and index for dedup
    with op.batch_alter_table('news_items') as batch_op:
        batch_op.add_column(sa.Column('url_hash', sa.String(), nullable=True))
        batch_op.create_index('ix_news_items_url_hash', ['url_hash'])


def downgrade() -> None:
    with op.batch_alter_table('news_items') as batch_op:
        batch_op.drop_index('ix_news_items_url_hash')
        batch_op.drop_column('url_hash')
