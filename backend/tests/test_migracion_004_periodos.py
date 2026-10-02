from pathlib import Path

MIG = Path(__file__).resolve().parent.parent / 'migrations' / 'versions' / '004_periodos_catalog_slice1.py'

EXPECTED_SEED = ['Enero-Abril 2024', 'Enero-Abril 2025', 'Enero-Abril 2026', 'Regular', 'Sin periodo']


def _content():
    return MIG.read_text(encoding='utf-8')


def test_migracion_004_cadena_y_tabla():
    c = _content()
    assert "revision = 'd4e5f6a7b8c9'" in c
    assert "down_revision = 'c3d4e5f6a7b8'" in c
    assert "create_table(\n        'periodos'" in c
    assert "uq_periodos_nombre" in c
    assert 'periodo_id' in c
    assert 'fk_asignaciones_periodo_id' in c


def test_migracion_004_seed_cerrado():
    c = _content()
    for nombre in EXPECTED_SEED:
        assert nombre in c
    assert "'Sin periodo'" in c and 'activa' in c


def test_migracion_004_downgrade_reversible():
    c = _content()
    assert 'def downgrade():' in c
    assert "drop_column('periodo_id')" in c
    assert "drop_table('periodos')" in c
    assert 'DELETE FROM periodos' in c
