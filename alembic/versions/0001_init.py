"""init

Revision ID: 0001
Revises: 
Create Date: 2025-08-16

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('canonical_id', sa.String(), nullable=True),
        sa.Column('canonical_name', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('ticker', sa.String(), nullable=True),
        sa.Column('segments', sa.String(), nullable=True),
        sa.Column('hq_country', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('funding_total', sa.Float(), nullable=True),
        sa.Column('signal_score', sa.Float(), nullable=True),
    )
    op.create_index('ix_companies_canonical_id', 'companies', ['canonical_id'])
    op.create_index('ix_companies_canonical_name', 'companies', ['canonical_name'])
    op.create_index('ix_companies_signal_score', 'companies', ['signal_score'])
    op.create_index('ix_companies_ticker', 'companies', ['ticker'])

    op.create_table(
        'news_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('external_id', sa.String(), index=True, nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('published_at', sa.String(), index=True, nullable=True),
        sa.Column('company_canonical_id', sa.String(), index=True, nullable=True),
    )

    op.create_table(
        'filings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('external_id', sa.String(), index=True, nullable=False),
        sa.Column('company_canonical_id', sa.String(), index=True, nullable=True),
        sa.Column('form', sa.String(), index=True, nullable=True),
        sa.Column('filed_at', sa.String(), index=True, nullable=True),
        sa.Column('url', sa.String(), nullable=True),
    )

    op.create_table(
        'repos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('repo_full_name', sa.String(), index=True, nullable=False),
        sa.Column('stars', sa.Integer(), index=True, nullable=True),
        sa.Column('company_canonical_id', sa.String(), index=True, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('repos')
    op.drop_table('filings')
    op.drop_table('news_items')
    op.drop_table('companies')
