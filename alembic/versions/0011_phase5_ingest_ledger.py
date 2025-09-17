"""
Phase 5: Append-only Ingest Ledger

Adds table ingest_ledger

Revision ID: 0011_phase5_ingest_ledger
Revises: 0010_phase5_tenant_scoping_and_signatures
Create Date: 2025-09-14
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0011_phase5_ingest_ledger'
down_revision = '0010_phase5_tenant_scope_sign'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ingest_ledger',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ingest_event_id', sa.String(length=255), nullable=False, index=True),
        sa.Column('snapshot_hash', sa.String(length=128), nullable=True, index=True),
        sa.Column('signer', sa.String(length=255), nullable=True, index=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_table('ingest_ledger')
