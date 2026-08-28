"""Add Sede and multitenancy nullable FKs

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # sedes table
    op.create_table(
        'sedes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('codigo', sa.String(length=10), nullable=False),
        sa.Column('direccion', sa.String(length=255), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('codigo', name='uq_sedes_codigo')
    )
    # admins: role + sede_id nullable (step 1)
    # use batch for SQLite compat
    with op.batch_alter_table('admins') as batch:
        batch.add_column(sa.Column('role', sa.Enum('general_admin', 'sede_admin', name='admin_role_enum'), nullable=False, server_default='general_admin'))
        batch.add_column(sa.Column('sede_id', sa.Integer(), nullable=True))
        batch.create_index('ix_admins_sede_id', ['sede_id'])
        batch.create_foreign_key('fk_admins_sede_id', 'sedes', ['sede_id'], ['id'])
        batch.create_check_constraint('ck_admin_role_sede', "(role='general_admin' AND sede_id IS NULL) OR (role='sede_admin' AND sede_id IS NOT NULL)")

    # alumnos sede_id nullable step 1 (later NOT NULL after backfill)
    with op.batch_alter_table('alumnos') as batch:
        batch.add_column(sa.Column('sede_id', sa.Integer(), nullable=True))
        batch.create_index('ix_alumnos_sede_id', ['sede_id'])
        batch.create_foreign_key('fk_alumnos_sede_id', 'sedes', ['sede_id'], ['id'])

    # grupos sede_id nullable
    with op.batch_alter_table('grupos') as batch:
        batch.add_column(sa.Column('sede_id', sa.Integer(), nullable=True))
        batch.create_index('ix_grupos_sede_id', ['sede_id'])
        batch.create_foreign_key('fk_grupos_sede_id', 'sedes', ['sede_id'], ['id'])

    # profesores sede_id nullable (optional)
    with op.batch_alter_table('profesores') as batch:
        batch.add_column(sa.Column('sede_id', sa.Integer(), nullable=True))
        batch.create_index('ix_profesores_sede_id', ['sede_id'])
        batch.create_foreign_key('fk_profesores_sede_id', 'sedes', ['sede_id'], ['id'])

    # data migration: existing admins -> general_admin, sede_id NULL
    op.execute("UPDATE admins SET role='general_admin', sede_id=NULL WHERE role IS NULL OR role=''")

    # seed sedes idempotent
    op.execute("INSERT OR IGNORE INTO sedes (id, nombre, codigo, direccion, activa, created_at) VALUES (1, 'Teotitlan', 'TEO', 'Teotitlan de Flores Magon, Oaxaca', 1, CURRENT_TIMESTAMP)")
    op.execute("INSERT OR IGNORE INTO sedes (id, nombre, codigo, direccion, activa, created_at) VALUES (2, 'Huautla', 'HUA', 'Huautla de Jimenez, Oaxaca', 1, CURRENT_TIMESTAMP)")


def downgrade():
    with op.batch_alter_table('profesores') as batch:
        batch.drop_constraint('fk_profesores_sede_id', type_='foreignkey')
        batch.drop_index('ix_profesores_sede_id')
        batch.drop_column('sede_id')
    with op.batch_alter_table('grupos') as batch:
        batch.drop_constraint('fk_grupos_sede_id', type_='foreignkey')
        batch.drop_index('ix_grupos_sede_id')
        batch.drop_column('sede_id')
    with op.batch_alter_table('alumnos') as batch:
        batch.drop_constraint('fk_alumnos_sede_id', type_='foreignkey')
        batch.drop_index('ix_alumnos_sede_id')
        batch.drop_column('sede_id')
    with op.batch_alter_table('admins') as batch:
        batch.drop_constraint('ck_admin_role_sede', type_='check')
        batch.drop_constraint('fk_admins_sede_id', type_='foreignkey')
        batch.drop_index('ix_admins_sede_id')
        batch.drop_column('sede_id')
        batch.drop_column('role')
    op.drop_table('sedes')
    # for MySQL enum cleanup
    try:
        sa.Enum('general_admin', 'sede_admin', name='admin_role_enum').drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
