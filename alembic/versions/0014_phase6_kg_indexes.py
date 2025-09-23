"""phase6 kg performance indexes

Revision ID: 0014_phase6_kg_indexes
Revises: 0013_phase3_add_hiring_patents
Create Date: 2025-09-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0014_phase6_kg_indexes"
down_revision = "0013_phase3_add_hiring_patents"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Node temporal lookup indexes
    try:
        op.create_index("ix_kg_nodes_uid_valid_from", "kg_nodes", ["uid", "valid_from"], unique=False)
    except Exception:
        pass
    try:
        op.create_index("ix_kg_nodes_uid_valid_to", "kg_nodes", ["uid", "valid_to"], unique=False)
    except Exception:
        pass
    # Edge traversal indexes
    try:
        op.create_index("ix_kg_edges_src_uid_valid_from", "kg_edges", ["src_uid", "valid_from"], unique=False)
    except Exception:
        pass
    try:
        op.create_index("ix_kg_edges_dst_uid_valid_from", "kg_edges", ["dst_uid", "valid_from"], unique=False)
    except Exception:
        pass
    try:
        op.create_index("ix_kg_edges_src_dst_type", "kg_edges", ["src_uid", "dst_uid", "type"], unique=False)
    except Exception:
        pass


def downgrade() -> None:
    for name in [
        "ix_kg_edges_src_dst_type",
        "ix_kg_edges_dst_uid_valid_from",
        "ix_kg_edges_src_uid_valid_from",
        "ix_kg_nodes_uid_valid_to",
        "ix_kg_nodes_uid_valid_from",
    ]:
        try:
            op.drop_index(name)
        except Exception:
            pass
