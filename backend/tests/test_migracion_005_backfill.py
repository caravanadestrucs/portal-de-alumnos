from pathlib import Path

MIG = Path(__file__).resolve().parent.parent / 'migrations' / 'versions' / '005_calificacion_periodo_slice2.py'


def _content():
    return MIG.read_text(encoding='utf-8')


def _predicate_src():
    return _content()


def resolve(nombre_por_id, periodo, anio):
    cands = []
    if periodo:
        if anio is not None:
            cands.append(f'{periodo} {anio}')
        cands.append(periodo)
    for cand in cands:
        for pid, nombre in nombre_por_id.items():
            if cand == nombre:
                return pid
    return None


def test_migracion_005_cadena_y_columna():
    c = _content()
    assert "revision = 'e5f6a7b8c9d0'" in c
    assert "down_revision = 'd4e5f6a7b8c9'" in c
    assert "add_column(sa.Column('periodo_id'" in c
    assert 'fk_calificaciones_periodo_id' in c
    assert 'def downgrade():' in c
    assert "drop_column('periodo_id')" in c


def test_backfill_solo_match_exacto():
    c = _predicate_src()
    assert 'f"{periodo} {anio}"' in c or "f'{periodo} {anio}'" in c
    catalogo = {1: 'Enero-Abril 2026', 2: 'Regular'}
    assert resolve(catalogo, 'Enero-Abril 2026', 2026) == 1
    assert resolve(catalogo, 'Regular', 2026) == 2
    assert resolve(catalogo, 'Regular', None) == 2
    assert resolve(catalogo, 'enero-abril 2026', 2026) is None
    assert resolve(catalogo, 'Enero-Abril 2026 ', 2026) is None
    assert resolve(catalogo, 'Raro', 2026) is None
    assert resolve(catalogo, None, 2026) is None
