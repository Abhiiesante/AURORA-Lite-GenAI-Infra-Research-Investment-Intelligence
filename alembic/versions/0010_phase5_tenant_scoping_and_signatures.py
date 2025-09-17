"""
Phase 5: tenant scoping for KG and snapshot signatures

Adds columns:
- kg_nodes.tenant_id (int, nullable, index)
- kg_edges.tenant_id (int, nullable, index)
- kg_snapshots.signature (text), kg_snapshots.signature_backend (string, index), kg_snapshots.cert_chain_pem (text)

Revision ID: 0010_phase5_tenant_scoping_and_signatures
Revises: 0009_phase5_certification_success_fee
Create Date: 2025-09-14
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0010_phase5_tenant_scope_sign'
down_revision = '0009_phase5_cert_success_fee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('kg_nodes') as batch:
        batch.add_column(sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index('ix_kg_nodes_tenant_id', 'kg_nodes', ['tenant_id'], unique=False)

    with op.batch_alter_table('kg_edges') as batch:
        batch.add_column(sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index('ix_kg_edges_tenant_id', 'kg_edges', ['tenant_id'], unique=False)

    with op.batch_alter_table('kg_snapshots') as batch:
        batch.add_column(sa.Column('signature', sa.Text(), nullable=True))
        batch.add_column(sa.Column('signature_backend', sa.String(length=64), nullable=True))
        batch.add_column(sa.Column('cert_chain_pem', sa.Text(), nullable=True))
    op.create_index('ix_kg_snapshots_signature_backend', 'kg_snapshots', ['signature_backend'], unique=False)


def downgrade() -> None:
    try:
        op.drop_index('ix_kg_snapshots_signature_backend', table_name='kg_snapshots')
    except Exception:
        pass
    with op.batch_alter_table('kg_snapshots') as batch:
        for col in ('cert_chain_pem', 'signature_backend', 'signature'):
            try:
                batch.drop_column(col)
            except Exception:
                pass

    try:
        op.drop_index('ix_kg_edges_tenant_id', table_name='kg_edges')
    except Exception:
        pass
    with op.batch_alter_table('kg_edges') as batch:
        try:
            batch.drop_column('tenant_id')
        except Exception:
            pass

    try:
        op.drop_index('ix_kg_nodes_tenant_id', table_name='kg_nodes')
    except Exception:
        pass
    with op.batch_alter_table('kg_nodes') as batch:
        try:
            batch.drop_column('tenant_id')
        except Exception:
            pass
