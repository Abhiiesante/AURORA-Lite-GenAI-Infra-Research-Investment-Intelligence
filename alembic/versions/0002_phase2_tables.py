"""phase2 tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-08-18

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # copilot_sessions
    op.create_table(
        'copilot_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('memory_json', sa.Text(), nullable=True),
    )
    op.create_index('ix_copilot_sessions_session_id', 'copilot_sessions', ['session_id'])
    op.create_index('ix_copilot_sessions_user_id', 'copilot_sessions', ['user_id'])
    op.create_index('ix_copilot_sessions_created_at', 'copilot_sessions', ['created_at'])

    # company_metrics
    op.create_table(
        'company_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.String(), nullable=False),
        sa.Column('mentions', sa.Integer(), nullable=True),
        sa.Column('filings', sa.Integer(), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=True),
        sa.Column('commits', sa.Integer(), nullable=True),
        sa.Column('sentiment', sa.Float(), nullable=True),
        sa.Column('signal_score', sa.Float(), nullable=True),
    )
    op.create_index('ix_company_metrics_company_id', 'company_metrics', ['company_id'])
    op.create_index('ix_company_metrics_week_start', 'company_metrics', ['week_start'])
    op.create_index('ix_company_metrics_signal_score', 'company_metrics', ['signal_score'])

    # alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('score_delta', sa.Float(), nullable=True),
        sa.Column('evidence_urls', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
    )
    op.create_index('ix_alerts_company_id', 'alerts', ['company_id'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])

    # topics
    op.create_table(
        'topics',
        sa.Column('topic_id', sa.Integer(), primary_key=True),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('terms_json', sa.Text(), nullable=True),
        sa.Column('examples_json', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.String(), nullable=True),
    )

    # topic_trends
    op.create_table(
        'topic_trends',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.String(), nullable=False),
        sa.Column('freq', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('change_flag', sa.Boolean(), nullable=True),
    )
    op.create_index('ix_topic_trends_topic_id', 'topic_trends', ['topic_id'])
    op.create_index('ix_topic_trends_week_start', 'topic_trends', ['week_start'])

    # insight_cache
    op.create_table(
        'insight_cache',
        sa.Column('key_hash', sa.String(), primary_key=True),
        sa.Column('input_json', sa.Text(), nullable=True),
        sa.Column('output_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('ttl', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('insight_cache')
    op.drop_index('ix_topic_trends_week_start', table_name='topic_trends')
    op.drop_index('ix_topic_trends_topic_id', table_name='topic_trends')
    op.drop_table('topic_trends')
    op.drop_table('topics')
    op.drop_index('ix_alerts_created_at', table_name='alerts')
    op.drop_index('ix_alerts_company_id', table_name='alerts')
    op.drop_table('alerts')
    op.drop_index('ix_company_metrics_signal_score', table_name='company_metrics')
    op.drop_index('ix_company_metrics_week_start', table_name='company_metrics')
    op.drop_index('ix_company_metrics_company_id', table_name='company_metrics')
    op.drop_table('company_metrics')
    op.drop_index('ix_copilot_sessions_created_at', table_name='copilot_sessions')
    op.drop_index('ix_copilot_sessions_user_id', table_name='copilot_sessions')
    op.drop_index('ix_copilot_sessions_session_id', table_name='copilot_sessions')
    op.drop_table('copilot_sessions')
