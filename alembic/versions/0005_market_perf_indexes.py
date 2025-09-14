"""market map performance indexes

Revision ID: 0005
Revises: 0004
Create Date: 2025-08-30

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.create_index('ix_companies_name_lc', 'companies', ['canonical_name'])
    except Exception:
        pass
    try:
        op.create_index('ix_companies_segment', 'companies', ['segments'])
    except Exception:
        pass
    try:
        op.create_index('ix_companies_signal', 'companies', ['signal_score'])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index('ix_companies_signal', table_name='companies')
    except Exception:
        pass
    try:
        op.drop_index('ix_companies_segment', table_name='companies')
    except Exception:
        pass
    try:
        op.drop_index('ix_companies_name_lc', table_name='companies')
    except Exception:
        pass
