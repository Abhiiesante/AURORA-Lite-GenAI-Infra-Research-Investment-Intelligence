"""Add hiring and patents columns to company_metrics

Revision ID: 0013_phase3_add_hiring_patents
Revises: 0012_phase5_sigstore_fields
Create Date: 2025-09-15

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013_phase3_add_hiring_patents'
down_revision = '0012_phase5_sigstore_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add optional metrics columns introduced in later phases
    with op.batch_alter_table('company_metrics') as batch_op:
        batch_op.add_column(sa.Column('hiring', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('patents', sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('company_metrics') as batch_op:
        batch_op.drop_column('patents')
        batch_op.drop_column('hiring')
