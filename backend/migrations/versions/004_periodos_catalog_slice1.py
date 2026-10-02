"""Periodos catalog + Asignacion.periodo_id (slice 1).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-08
"""
from datetime import date
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None

PERIODOS_SEED = [
    {'nombre': 'Enero-Abril 2024', 'fecha_inicio': date(2024, 1, 1), 'fecha_fin': date(2024, 4, 30), 'activa': True},
    {'nombre': 'Enero-Abril 2025', 'fecha_inicio': date(2025, 1, 1), 'fecha_fin': date(2025, 4, 30), 'activa': True},
    {'nombre': 'Enero-Abril 2026', 'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 4, 30), 'activa': True},
    {'nombre': 'Regular', 'fecha_inicio': None, 'fecha_fin': None, 'activa': True},
    {'nombre': 'Sin periodo', 'fecha_inicio': None, 'fecha_fin': None, 'activa': False},
]


def upgrade():
    op.create_table(
        'periodos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=True),
        sa.Column('fecha_fin', sa.Date(), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('nombre', name='uq_periodos_nombre'),
    )
    periodos_tbl = sa.table(
        'periodos',
        sa.column('nombre', sa.String),
        sa.column('fecha_inicio', sa.Date),
        sa.column('fecha_fin', sa.Date),
        sa.column('activa', sa.Boolean),
    )
    op.bulk_insert(periodos_tbl, PERIODOS_SEED)
    with op.batch_alter_table('asignaciones') as batch:
        batch.add_column(sa.Column('periodo_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_asignaciones_periodo_id', 'periodos', ['periodo_id'], ['id'])


def downgrade():
    for row in reversed(PERIODOS_SEED):
        op.execute(sa.text('DELETE FROM periodos WHERE nombre = :n').bindparams(n=row['nombre']))
    with op.batch_alter_table('asignaciones') as batch:
        batch.drop_constraint('fk_asignaciones_periodo_id', type_='foreignkey')
        batch.drop_column('periodo_id')
    op.drop_table('periodos')
