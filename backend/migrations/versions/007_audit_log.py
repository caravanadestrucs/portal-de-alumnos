"""AuditLog for audited general-only ?sede_id override (Slice 1 Task 5).

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1 (006 head)

RULINGS vs plan 471-581 (recorded in task-5-report.md):
- plan revision 'e5f6a7b8c9d0'/down_revision 'd4e5f6a7b8c9' is STALE
  (those are 005/004). Chaining onto real head 006 'f6a7b8c9d0e1'
  with next free id 'a7b8c9d0e1f2'.
- audit_log ONLY. SedeTransferHistory ships in Task 7 with its own
  migration (filename narrowed to 007_audit_log.py for the same reason).

Portable SQLite/Postgres: named FK, no engine-specific defaults.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('actor_role', sa.String(30), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(300), nullable=False),
        sa.Column('target_sede_id', sa.Integer(), nullable=True),
        sa.Column('resource_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['target_sede_id'], ['sedes.id'], name='fk_audit_sede'))
    op.create_index('ix_audit_actor', 'audit_log', ['actor_id'])
    op.create_index('ix_audit_target_sede', 'audit_log', ['target_sede_id'])


def downgrade():
    op.drop_index('ix_audit_target_sede', table_name='audit_log')
    op.drop_index('ix_audit_actor', table_name='audit_log')
    op.drop_table('audit_log')
