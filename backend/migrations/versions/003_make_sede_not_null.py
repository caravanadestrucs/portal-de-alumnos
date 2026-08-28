"""Make sede_id NOT NULL for alumnos and grupos (post-backfill hardening).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-28

After PR1 backfill all alumnos are assigned (109 TEO, 0 NULL). This migration
hardens the schema so future inserts without sede_id fail at DB level.
Also hardens grupos.sede_id (was nullable, now required) with a safe backfill
to TEO (id=1) for any legacy grupos that were created before multitenancy.

Uses batch_alter for SQLite compatibility.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # Safety backfill: ensure no NULLs remain before enforcing NOT NULL.
    # TEO is id=1 (seeded in 001). HUA assignment must be done manually via
    # PATCH /api/alumnos/:id/sede as general_admin or via Sedes/WikiAdmin UI.
    # See backend/instance/manual_review.csv for flagged rows.
    op.execute("UPDATE grupos SET sede_id = 1 WHERE sede_id IS NULL")
    op.execute("UPDATE alumnos SET sede_id = 1 WHERE sede_id IS NULL")

    # Make alumnos.sede_id NOT NULL
    with op.batch_alter_table('alumnos', recreate='always') as batch:
        batch.alter_column(
            'sede_id',
            existing_type=sa.Integer(),
            nullable=False,
            existing_nullable=True,
        )

    # Make grupos.sede_id NOT NULL
    with op.batch_alter_table('grupos', recreate='always') as batch:
        batch.alter_column(
            'sede_id',
            existing_type=sa.Integer(),
            nullable=False,
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table('grupos', recreate='always') as batch:
        batch.alter_column(
            'sede_id',
            existing_type=sa.Integer(),
            nullable=True,
            existing_nullable=False,
        )
    with op.batch_alter_table('alumnos', recreate='always') as batch:
        batch.alter_column(
            'sede_id',
            existing_type=sa.Integer(),
            nullable=True,
            existing_nullable=False,
        )
