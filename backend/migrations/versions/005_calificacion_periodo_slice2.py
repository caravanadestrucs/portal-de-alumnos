"""Calificacion.periodo_id + exact-match backfill (slice 2).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def _backfill():
    conn = op.get_bind()
    periodos = {r.nombre: r.id for r in
                conn.execute(sa.text('SELECT id, nombre FROM periodos')).mappings()}
    rows = conn.execute(sa.text('SELECT id, periodo, anio FROM calificaciones')).mappings().all()
    for row in rows:
        periodo, anio = row['periodo'], row['anio']
        cands = []
        if periodo:
            if anio is not None:
                cands.append(f'{periodo} {anio}')
            cands.append(periodo)
        match = next((periodos[c] for c in cands if c in periodos), None)
        if match is not None:
            conn.execute(sa.text('UPDATE calificaciones SET periodo_id = :pid WHERE id = :cid')
                         .bindparams(pid=match, cid=row['id']))


def upgrade():
    with op.batch_alter_table('calificaciones') as batch:
        batch.add_column(sa.Column('periodo_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_calificaciones_periodo_id', 'periodos', ['periodo_id'], ['id'])
    _backfill()


def downgrade():
    with op.batch_alter_table('calificaciones') as batch:
        batch.drop_constraint('fk_calificaciones_periodo_id', type_='foreignkey')
        batch.drop_column('periodo_id')
