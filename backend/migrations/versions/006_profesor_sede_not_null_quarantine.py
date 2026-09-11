"""Profesor.sede_id NOT NULL with quarantine (Slice 1 Approach A).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-11

RULINGS vs task brief (recorded in task-1-report.md):
- brief revision 'd4e5f6a7b8c9' collides with 004_periodos_catalog_slice1.py;
  using next free id 'f6a7b8c9d0e1'.
- brief down_revision 'c3d4e5f6a7b8' (003) is stale; chain head is
  005 'e5f6a7b8c9d0'. Using head.
- backfill guarded by COUNT(DISTINCT g.sede_id) = 1: only unambiguous rows
  (exactly one sede via asignaciones->grupos) are populated. Multi-sede or
  zero-assignment rows stay NULL (quarantine). The brief's bare scalar
  subquery returns N rows for N sedes and SQLite would silently take the
  first, fabricating scope — forbidden by spec section 3.1.
- drops 001's 'fk_profesores_sede_id' before creating 'fk_profesor_sede'
  (model metadata name) to avoid duplicate FKs. Renames index
  'ix_profesores_sede_id' (001) to spec-mandated 'ix_profesor_sede_id':
  drop old index if exists, create binding name (fix round 1).
- quarantine: any NULL remaining after backfill blocks the release because
  the NOT NULL alter itself fails; Task 11 verifies
  SELECT COUNT(*) FROM profesores WHERE sede_id IS NULL = 0.

Uses batch_alter_table(recreate='always') for SQLite compatibility.
Portable SQLite/Postgres: named FK, no engine-specific defaults.
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Backfill unambiguous only: profesores whose asignaciones resolve to
    # exactly one distinct grupo sede. Ambiguous (multi-sede) or unassigned
    # rows stay NULL for quarantine resolution by general (never defaulted).
    op.execute("""
        UPDATE profesores SET sede_id = (
            SELECT MIN(g.sede_id) FROM asignaciones a
            JOIN grupos g ON g.id = a.grupo_id
            WHERE a.profesor_id = profesores.id
        ) WHERE sede_id IS NULL
        AND (SELECT COUNT(DISTINCT g.sede_id) FROM asignaciones a
             JOIN grupos g ON g.id = a.grupo_id
             WHERE a.profesor_id = profesores.id) = 1
    """)
    # 2. Quarantine: rows still NULL here must be resolved with general input
    # before this migration can succeed (step 3 fails on any NULL).
    # Blocking check (release gate, verified by Task 11):
    # SELECT COUNT(*) FROM profesores WHERE sede_id IS NULL; -- must be 0
    # 3. Harden to NOT NULL + converge FK/index names to spec contract.
    with op.batch_alter_table('profesores', recreate='always') as batch:
        try:
            batch.drop_constraint('fk_profesores_sede_id', type_='foreignkey')
        except Exception:
            pass
        try:
            batch.drop_index('ix_profesores_sede_id')
        except Exception:
            pass
        batch.alter_column('sede_id', existing_type=sa.Integer(), nullable=False, existing_nullable=True)
        batch.create_index('ix_profesor_sede_id', ['sede_id'])
        batch.create_foreign_key('fk_profesor_sede', 'sedes', ['sede_id'], ['id'])


def downgrade():
    with op.batch_alter_table('profesores', recreate='always') as batch:
        try:
            batch.drop_constraint('fk_profesor_sede', type_='foreignkey')
        except Exception:
            pass
        try:
            batch.drop_index('ix_profesor_sede_id')
        except Exception:
            pass
        batch.alter_column('sede_id', existing_type=sa.Integer(), nullable=True, existing_nullable=False)
        batch.create_index('ix_profesores_sede_id', ['sede_id'])
        batch.create_foreign_key('fk_profesores_sede_id', 'sedes', ['sede_id'], ['id'])
