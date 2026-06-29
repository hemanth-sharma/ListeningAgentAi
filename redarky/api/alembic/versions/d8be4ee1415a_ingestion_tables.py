"""ingestion tables

Revision ID: d8be4ee1415a
Revises: 0237ae6f41c8
Create Date: 2026-06-29 02:30:57.514919

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd8be4ee1415a'
down_revision: Union[str, Sequence[str], None] = '0237ae6f41c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create independent tables first
    op.create_table('monitored_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_type', sa.String(length=32), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('interval_minutes', sa.Integer(), nullable=False),
        sa.Column('subscriber_count', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('apify_schedule_id', sa.String(length=255), nullable=True),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type', 'identifier', name='uq_monitored_source')
    )
    
    op.create_table('raw_posts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('source_run_id', sa.String(length=255), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('comments_count', sa.Integer(), nullable=True),
        sa.Column('post_type', sa.String(length=16), nullable=True),
        sa.Column('subreddit', sa.String(length=255), nullable=True),
        sa.Column('created_at_platform', sa.BigInteger(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'external_id', name='uq_raw_post_source_external_id')
    )

    # 2. Create tables with foreign key dependencies
    op.create_table('keyword_matches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('raw_post_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('matched_keyword', sa.String(length=512), nullable=False),
        sa.Column('match_type', sa.String(length=16), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False),
        sa.Column('matched_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raw_post_id'], ['raw_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_post_id', 'project_id', 'matched_keyword', name='uq_keyword_match_post_project_keyword')
    )
    op.create_index(op.f('ix_keyword_matches_project_id'), 'keyword_matches', ['project_id'], unique=False)
    op.create_index(op.f('ix_keyword_matches_raw_post_id'), 'keyword_matches', ['raw_post_id'], unique=False)

    op.create_table('project_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('monitored_source_id', sa.UUID(), nullable=False),
        sa.Column('source_identifier', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['monitored_source_id'], ['monitored_sources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'monitored_source_id', name='uq_project_source')
    )
    op.create_index(op.f('ix_project_sources_project_id'), 'project_sources', ['project_id'], unique=False)

    # 3. Handle Column alterations & the Enum Type registration safely
    op.alter_column('keywords', 'keyword',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=512),
               existing_nullable=False)

    keyword_type_enum = postgresql.ENUM('INCLUDE', 'EXCLUDE', 'BRAND', name='keyword_type_enum')
    keyword_type_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column('keywords', 'keyword_type',
               existing_type=sa.VARCHAR(length=7),
               type_=keyword_type_enum,
               existing_nullable=False,
               postgresql_using='keyword_type::keyword_type_enum')

    op.drop_column('keywords', 'updated_at')

    # 4. Update legacy posts table columns
    op.add_column('posts', sa.Column('post_type', sa.String(length=32), nullable=True))
    op.add_column('posts', sa.Column('subreddit', sa.String(length=255), nullable=True))
    op.add_column('posts', sa.Column('matched_keyword', sa.String(length=512), nullable=True))
    op.add_column('posts', sa.Column('is_brand_mention', sa.Boolean(), nullable=False, server_default='false'))
    
    op.alter_column('posts', 'source',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=64),
               existing_nullable=False)
    op.alter_column('posts', 'title',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=512),
               existing_nullable=False)
    op.alter_column('posts', 'created_at_platform',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.BigInteger(),
               existing_nullable=True,
               postgresql_using='created_at_platform::bigint')


def downgrade() -> None:
    op.alter_column('posts', 'created_at_platform',
               existing_type=sa.BigInteger(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
    op.alter_column('posts', 'title',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    op.alter_column('posts', 'source',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    op.drop_column('posts', 'is_brand_mention')
    op.drop_column('posts', 'matched_keyword')
    op.drop_column('posts', 'subreddit')
    op.drop_column('posts', 'post_type')
    
    op.add_column('keywords', sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    
    op.alter_column('keywords', 'keyword_type',
               existing_type=postgresql.ENUM('INCLUDE', 'EXCLUDE', 'BRAND', name='keyword_type_enum'),
               type_=sa.VARCHAR(length=7),
               existing_nullable=False,
               postgresql_using='keyword_type::varchar')

    keyword_type_enum = postgresql.ENUM('INCLUDE', 'EXCLUDE', 'BRAND', name='keyword_type_enum')
    keyword_type_enum.drop(op.get_bind(), checkfirst=True)

    op.alter_column('keywords', 'keyword',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
               
    op.drop_index(op.f('ix_project_sources_project_id'), table_name='project_sources')
    op.drop_table('project_sources')
    op.drop_index(op.f('ix_keyword_matches_raw_post_id'), table_name='keyword_matches')
    op.drop_index(op.f('ix_keyword_matches_project_id'), table_name='keyword_matches')
    op.drop_table('keyword_matches')
    op.drop_table('raw_posts')
    op.drop_table('monitored_sources')