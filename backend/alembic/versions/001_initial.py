"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'editor', 'chief_editor', 'analyst', 'service', name='userrole'), default='editor'),
        sa.Column('telegram_user_id', sa.BigInteger, unique=True, nullable=True, index=True),
        sa.Column('telegram_username', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_superuser', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('type', sa.Enum('rss', 'scraper', 'custom', 'webhook', name='sourcetype'), default='rss'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('feed_url', sa.Text, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('is_trusted', sa.Boolean, default=False),
        sa.Column('fetch_interval_minutes', sa.Integer, default=15),
        sa.Column('max_items_per_fetch', sa.Integer, default=50),
        sa.Column('normalization_rules', postgresql.JSONB, nullable=True),
        sa.Column('scraper_config', postgresql.JSONB, nullable=True),
        sa.Column('reputation_score', sa.Float, default=0.5),
        sa.Column('total_articles', sa.Integer, default=0),
        sa.Column('approved_articles', sa.Integer, default=0),
        sa.Column('rejected_articles', sa.Integer, default=0),
        sa.Column('last_fetch_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('consecutive_errors', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Source runs table
    op.create_table(
        'source_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'), index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), default='running'),
        sa.Column('articles_found', sa.Integer, default=0),
        sa.Column('articles_new', sa.Integer, default=0),
        sa.Column('articles_duplicate', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
    )
    
    # Batches table
    op.create_table(
        'batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('strategy', sa.Enum('mixed', 'by_category', 'by_source', 'by_priority', name='batchstrategy'), default='mixed'),
        sa.Column('status', sa.Enum('pending', 'sent', 'partial', 'completed', name='batchstatus'), default='pending', index=True),
        sa.Column('articles_count', sa.Integer, default=0),
        sa.Column('avg_quality', sa.Float, default=0.0),
        sa.Column('total_priority', sa.Integer, default=0),
        sa.Column('telegram_message_ids', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Publish targets table
    op.create_table(
        'publish_targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('type', sa.String(50), default='telegram_channel'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('telegram_chat_id', sa.BigInteger, nullable=True, unique=True),
        sa.Column('telegram_chat_username', sa.String(100), nullable=True),
        sa.Column('settings', postgresql.JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('total_published', sa.Integer, default=0),
        sa.Column('last_published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Articles table
    op.create_table(
        'articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('token', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('url', sa.Text, nullable=False),
        sa.Column('url_hash', sa.String(64), nullable=False, index=True),
        sa.Column('content_hash', sa.String(64), nullable=True, index=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('content_raw', sa.Text, nullable=True),
        sa.Column('content_clean', sa.Text, nullable=True),
        sa.Column('pub_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('images', postgresql.JSONB, nullable=True),
        sa.Column('main_image_url', sa.Text, nullable=True),
        sa.Column('quality_score', sa.Float, default=0.5),
        sa.Column('quality_factors', postgresql.JSONB, nullable=True),
        sa.Column('priority_score', sa.Integer, default=50, index=True),
        sa.Column('priority_factors', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'scheduled', 'published', 'failed', 'duplicate', 'needs_review', name='articlestatus'), default='pending', index=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('batches.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('ai_used', sa.Boolean, default=False),
        sa.Column('ai_metadata', postgresql.JSONB, nullable=True),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('moderator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_target_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('publish_targets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('published_external_id', sa.String(100), nullable=True),
        sa.Column('published_snapshot', postgresql.JSONB, nullable=True),
        sa.Column('similar_to_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('similarity_score', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Article versions table
    op.create_table(
        'article_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('content_clean', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('main_image_url', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('change_summary', sa.Text, nullable=True),
    )
    
    # Rules table
    op.create_table(
        'rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('priority', sa.Integer, default=100),
        sa.Column('conditions', postgresql.JSONB, nullable=False, default=dict),
        sa.Column('actions', postgresql.JSONB, nullable=False, default=dict),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('times_matched', sa.Integer, default=0),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Templates table
    op.create_table(
        'templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('scope', sa.String(50), default='global'),
        sa.Column('scope_value', sa.String(255), nullable=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('variables_schema', postgresql.JSONB, nullable=True),
        sa.Column('auto_hashtags', postgresql.JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Publish jobs table
    op.create_table(
        'publish_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), index=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('publish_targets.id', ondelete='CASCADE'), index=True),
        sa.Column('status', sa.Enum('queued', 'scheduled', 'publishing', 'published', 'failed', 'cancelled', name='publishjobstatus'), default='queued', index=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retries_count', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('external_post_id', sa.String(100), nullable=True),
        sa.Column('published_content', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('actor_name', sa.String(255), nullable=True),
        sa.Column('action', sa.Enum(
            'article_created', 'article_approved', 'article_rejected', 'article_edited',
            'article_scheduled', 'article_published', 'article_failed',
            'source_created', 'source_updated', 'source_deleted', 'source_fetch',
            'rule_created', 'rule_updated', 'rule_deleted', 'rule_applied',
            'template_created', 'template_updated', 'template_deleted',
            'user_login', 'user_logout', 'user_created', 'user_updated',
            'batch_created', 'batch_sent', 'ai_processed',
            name='auditaction'
        ), nullable=False, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('before_state', postgresql.JSONB, nullable=True),
        sa.Column('after_state', postgresql.JSONB, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    
    # Create indexes
    op.create_index('ix_articles_status_priority', 'articles', ['status', 'priority_score'])
    op.create_index('ix_articles_source_status', 'articles', ['source_id', 'status'])
    op.create_index('ix_articles_created_at', 'articles', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('publish_jobs')
    op.drop_table('templates')
    op.drop_table('rules')
    op.drop_table('article_versions')
    op.drop_table('articles')
    op.drop_table('publish_targets')
    op.drop_table('batches')
    op.drop_table('source_runs')
    op.drop_table('sources')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS auditaction')
    op.execute('DROP TYPE IF EXISTS publishjobstatus')
    op.execute('DROP TYPE IF EXISTS articlestatus')
    op.execute('DROP TYPE IF EXISTS batchstatus')
    op.execute('DROP TYPE IF EXISTS batchstrategy')
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS userrole')
