"""
Phase 5 sovereign kernel & agents & deal rooms

Adds:
- kg_nodes, kg_edges, provenance_records, kg_snapshots
- agent_runs
- deal_rooms, deal_room_items, deal_room_comments, dd_checklist_items

Revision ID: 0008_phase5_sovereign_kernel
Revises: 0007_phase4_enterprise_and_queue
Create Date: 2025-09-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0008_phase5_sovereign_kernel'
down_revision = '0007_phase4_enterprise_and_queue'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'kg_nodes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uid', sa.String(length=255), nullable=False, index=True),
        sa.Column('type', sa.String(length=64), nullable=False, index=True),
        sa.Column('properties_json', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.String(length=64), nullable=True, index=True),
        sa.Column('valid_to', sa.String(length=64), nullable=True, index=True),
        sa.Column('provenance_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'kg_edges',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('src_uid', sa.String(length=255), nullable=False, index=True),
        sa.Column('dst_uid', sa.String(length=255), nullable=False, index=True),
        sa.Column('type', sa.String(length=64), nullable=False, index=True),
        sa.Column('properties_json', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.String(length=64), nullable=True, index=True),
        sa.Column('valid_to', sa.String(length=64), nullable=True, index=True),
        sa.Column('provenance_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'provenance_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ingest_event_id', sa.String(length=255), nullable=True, index=True),
        sa.Column('snapshot_hash', sa.String(length=128), nullable=True, index=True),
        sa.Column('signer', sa.String(length=255), nullable=True, index=True),
        sa.Column('pipeline_version', sa.String(length=128), nullable=True),
        sa.Column('model_version', sa.String(length=128), nullable=True),
        sa.Column('evidence_json', sa.Text(), nullable=True),
        sa.Column('doc_urls_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'kg_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('at_ts', sa.String(length=64), nullable=False, index=True),
        sa.Column('snapshot_hash', sa.String(length=128), nullable=False, index=True),
        sa.Column('signer', sa.String(length=255), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )

    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type', sa.String(length=64), nullable=False, index=True),
        sa.Column('input_json', sa.Text(), nullable=True),
        sa.Column('output_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='running', index=True),
        sa.Column('started_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('finished_at', sa.String(length=64), nullable=True, index=True),
        sa.Column('error', sa.Text(), nullable=True),
    )

    op.create_table(
        'deal_rooms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='active', index=True),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'deal_room_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('room_id', sa.Integer(), nullable=False, index=True),
        sa.Column('item_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('ref_uid', sa.String(length=255), nullable=True, index=True),
        sa.Column('content_json', sa.Text(), nullable=True),
        sa.Column('added_by', sa.String(length=255), nullable=True, index=True),
        sa.Column('added_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'deal_room_comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('room_id', sa.Integer(), nullable=False, index=True),
        sa.Column('author', sa.String(length=255), nullable=True, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.String(length=64), nullable=True, index=True),
    )
    op.create_table(
        'dd_checklist_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('room_id', sa.Integer(), nullable=False, index=True),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True, server_default='open', index=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True, index=True),
        sa.Column('due_date', sa.String(length=64), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_table('dd_checklist_items')
    op.drop_table('deal_room_comments')
    op.drop_table('deal_room_items')
    op.drop_table('deal_rooms')
    op.drop_table('agent_runs')
    op.drop_table('kg_snapshots')
    op.drop_table('provenance_records')
    op.drop_table('kg_edges')
    op.drop_table('kg_nodes')
