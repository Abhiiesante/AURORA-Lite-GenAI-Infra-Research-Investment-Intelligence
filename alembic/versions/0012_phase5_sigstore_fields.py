"""
Phase 5: Sigstore metadata fields for KG snapshots

Adds columns to kg_snapshots:
- dsse_bundle_json (text)
- rekor_log_id (string, indexed)
- rekor_log_index (integer, indexed)

Revision ID: 0012_phase5_sigstore_fields
Revises: 0011_phase5_ingest_ledger
Create Date: 2025-09-14
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0012_phase5_sigstore_fields'
down_revision = '0011_phase5_ingest_ledger'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('kg_snapshots') as batch:
        batch.add_column(sa.Column('dsse_bundle_json', sa.Text(), nullable=True))
        batch.add_column(sa.Column('rekor_log_id', sa.String(length=128), nullable=True))
        batch.add_column(sa.Column('rekor_log_index', sa.Integer(), nullable=True))
    op.create_index('ix_kg_snapshots_rekor_log_id', 'kg_snapshots', ['rekor_log_id'], unique=False)
    op.create_index('ix_kg_snapshots_rekor_log_index', 'kg_snapshots', ['rekor_log_index'], unique=False)


def downgrade() -> None:
    try:
        op.drop_index('ix_kg_snapshots_rekor_log_index', table_name='kg_snapshots')
    except Exception:
        pass
    try:
        op.drop_index('ix_kg_snapshots_rekor_log_id', table_name='kg_snapshots')
    except Exception:
        pass
    with op.batch_alter_table('kg_snapshots') as batch:
        for col in ('rekor_log_index', 'rekor_log_id', 'dsse_bundle_json'):
            try:
                batch.drop_column(col)
            except Exception:
                pass
