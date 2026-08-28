"""Wiki pages, revisions, attachments — sede_id NULL=global, UNIQUE(sede_id,slug)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # wiki_pages
    op.create_table(
        'wiki_pages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sede_id', sa.Integer(), nullable=True),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body_markdown', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], name='fk_wiki_pages_sede_id'),
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], name='fk_wiki_pages_created_by'),
        sa.UniqueConstraint('sede_id', 'slug', name='uq_wiki_slug_sede'),
    )
    op.create_index('ix_wiki_pages_sede_id', 'wiki_pages', ['sede_id'])
    op.create_index('ix_wiki_pages_sede_slug', 'wiki_pages', ['sede_id', 'slug'])

    # wiki_revisions
    op.create_table(
        'wiki_revisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('body_markdown', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['page_id'], ['wiki_pages.id'], name='fk_wiki_revisions_page_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], name='fk_wiki_revisions_created_by'),
    )
    op.create_index('ix_wiki_revisions_page_id', 'wiki_revisions', ['page_id'])

    # wiki_attachments
    op.create_table(
        'wiki_attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('mime', sa.String(length=120), nullable=True),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['page_id'], ['wiki_pages.id'], name='fk_wiki_attachments_page_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], name='fk_wiki_attachments_created_by'),
    )
    op.create_index('ix_wiki_attachments_page_id', 'wiki_attachments', ['page_id'])


def downgrade():
    op.drop_index('ix_wiki_attachments_page_id', table_name='wiki_attachments')
    op.drop_table('wiki_attachments')
    op.drop_index('ix_wiki_revisions_page_id', table_name='wiki_revisions')
    op.drop_table('wiki_revisions')
    op.drop_index('ix_wiki_pages_sede_slug', table_name='wiki_pages')
    op.drop_index('ix_wiki_pages_sede_id', table_name='wiki_pages')
    op.drop_table('wiki_pages')
