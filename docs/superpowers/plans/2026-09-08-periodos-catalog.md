# Períodos como Catálogo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the implicit "período" (loose dates on asignaciones, heterogeneous strings on calificaciones) with a single `periodos` catalog referenced by `Asignacion` (slice 1) and `Calificacion` (slice 2), with a visual-only period filter in Boletas and a rescued DOCX download.

**Architecture:** Catalog-first normalization in two consecutive slices: slice 1 ships the `periodos` table, `Asignacion.periodo_id` (nullable in DB, mandatory via API), the `/api/periodos` CRUD, the Asignaciones UI, the visual Boletas filter (resolved through the `Asignacion` join until slice 2 exists), and the missing `boleta_generator` module; slice 2 adds `Calificacion.periodo_id` inherited exclusively from the linked `Asignacion`, an exact-match backfill, and swaps the Boletas filter to the direct column.

**Tech Stack:** Flask + SQLAlchemy + Flask-Migrate (backend, pytest), React + Vite (frontend, vitest), python-docx for the DOCX rescue.

**Spec:** `docs/superpowers/specs/2026-09-08-periodos-catalog-design.md`

## Global Constraints

- Stack is Flask + SQLAlchemy (backend) + React + Vite (frontend); TDD is strict with no exceptions — failing test first, minimal implementation, then refactor.
- `periodo_id` is nullable at DB level and mandatory via API validation (missing/null/invalid answers 422; 400 stays reserved for malformed payloads such as invalid JSON or bad date format).
- Missing/null `periodo_id` renders exactly as `"Sin periodo"`; the `"Sin periodo"` seed row (`activa = false`) is presentation-only and is never assigned via API.
- Backfill matches character-by-character exact equality only; anything without an exact match stays `NULL`.
- `DELETE /api/periodos/<id>` is a logical delete (`activa = false`); associated rows keep their `periodo_id`. No physical delete exists in this cycle.
- The Boletas download (single and bulk) always generates one document with the full history (`final > 0`) and ignores any filter.
- `Calificacion.periodo_id` is inherited exclusively from the linked `Asignacion` (profesor + grupo + materia); never deduced from dates or strings.
- `Grupo.periodo/anio` are untouched (neither exposed nor migrated); no closed enum of periods is created in code; no per-period PDFs/DOCXs.
- Slice 2 depends on slice 1; `Calificacion.periodo_id` must not appear before slice 2.

---

## File Structure

New files and what each owns:

- `backend/routes/periodos.py` (CREATE) — `/api/periodos` CRUD; GET open to all authenticated roles, writes admin-only; 422 on missing `nombre`, 409 on duplicate, logical DELETE.
- `backend/utils/boleta_generator.py` (CREATE) — `generar_boleta(alumno, calificaciones, carrera, config_db)` returning a `docx.document.Document`; the single implementation behind single and bulk downloads.
- `backend/migrations/versions/004_periodos_catalog_slice1.py` (CREATE) — slice-1 schema: `periodos` table + unique index on `nombre` + seed + nullable `asignaciones.periodo_id` FK; downgrade removes seed, FK, column, table.
- `backend/migrations/versions/005_calificacion_periodo_slice2.py` (CREATE) — slice-2 schema: nullable `calificaciones.periodo_id` FK + exact-match backfill; downgrade removes FK and column.
- `backend/tests/test_periodos_model.py` (CREATE) — slice-1 model contract for `Periodo` and `Asignacion.periodo_id`.
- `backend/tests/test_migracion_004_periodos.py` (CREATE) — contract test for migration 004 (revision chain, ops, seed, downgrade).
- `backend/tests/test_periodos_crud.py` (CREATE) — HTTP contract for `/api/periodos` incl. roles, 422, 409, logical delete.
- `backend/tests/test_asignaciones_periodo.py` (CREATE) — HTTP contract for `periodo_id` validation on asignaciones POST/PUT/GET.
- `backend/tests/test_boleta_download.py` (CREATE) — DOCX download rescue contract (200 + DOCX magic + requirements assertion).
- `backend/tests/test_boletas_filtro.py` (CREATE) — HTTP contract for `GET /api/boletas/alumnos?periodo_id=`.
- `backend/tests/test_calificacion_periodo.py` (CREATE, slice 2) — inheritance contract for `Calificacion.periodo_id`.
- `backend/tests/test_migracion_005_backfill.py` (CREATE, slice 2) — contract for migration 005 incl. exact-match predicate cases.
- `frontend/src/api/periodos.js` (CREATE) — `getPeriodos`, `createPeriodo`, `updatePeriodo`, `deletePeriodo` over the shared axios instance.
- `frontend/src/api/periodos.test.js` (CREATE) — vitest contract mirroring `sedes.test.js` mock style.
- `frontend/src/api/boletas.test.js` (CREATE) — vitest contract: `getAlumnosBoletas` forwards `periodo_id`, download helpers never send it.
- `frontend/src/pages/admin/Asignaciones.periodo.test.jsx` (CREATE) — dropdown shows `nombre`/saves `id`, create blocked without period, table shows `"Sin periodo"` on `null`.
- `frontend/src/pages/admin/Boletas.periodo.test.jsx` (CREATE) — selector defaults to `"Todos"`, filters the visible list, download stays full-history, empty filter keeps download available.

Modified files and why:

- `backend/models.py` (MODIFY) — add `Periodo`; add `Asignacion.periodo_id` + relationship + `to_dict` keys (slice 1); add `Calificacion.periodo_id` + relationship + `to_dict` keys (slice 2 only).
- `backend/app.py` (MODIFY) — register `periodos_bp` at `/api/periodos` following the existing blueprint block (lines 84-120).
- `backend/routes/asignaciones.py` (MODIFY) — POST requires active `periodo_id` (422); PUT edits it (active or inactive, explicit null clears); GET serializes `periodo_id`/`periodo_nombre`.
- `backend/routes/boletas.py` (MODIFY) — `GET /alumnos` accepts optional `?periodo_id=` (slice 1: resolved via `_alcance_periodo` join; slice 2: direct column); downloads and preview ignore the filter.
- `backend/routes/calificaciones.py` (MODIFY, slice 2 only) — POST/PUT/bulk inherit `periodo_id` from the linked `Asignacion`.
- `backend/routes/profesor.py` (MODIFY, slice 2 only) — sync-ensure and update paths set `periodo_id` from the `Asignacion`.
- `backend/requirements.txt` (MODIFY) — declare `python-docx` (verified absent on 2026-09-08).
- `frontend/src/api/boletas.js` (MODIFY or VERIFY) — verified to exist; `getAlumnosBoletas(params)` already forwards `params`, so the caller just passes `periodo_id`. No signature change.
- `frontend/src/pages/admin/Asignaciones.jsx` (MODIFY) — Período dropdown in create/edit, split table columns Período/Fechas, client-side block on create without period.
- `frontend/src/pages/admin/Boletas.jsx` (MODIFY) — Período selector defaulting to `"Todos"`, visible-list filtering, downloads unchanged.

Verified-existence notes (checked 2026-09-08, do not re-derive): `frontend/src/api/boletas.js` EXISTS (so it is modified/verified, never created); `backend/utils/boleta_generator.py` does NOT exist (only `email.py`, `decorators.py`, `scope.py`, `mail.py`, `security.py`, `__init__.py`); `backend/routes/periodos.py` does NOT exist; `python-docx` is NOT in `backend/requirements.txt`; migration head is `c3d4e5f6a7b8` (`003_make_sede_not_null.py`); `TestingConfig` (`sqlite:///:memory:`) exists in `backend/config.py`; `create_app(config_name)` factory exists in `backend/app.py`.

---

## Slice 1 — Catálogo + Asignación + Boletas visual + rescate DOCX

### Task 1: Modelo `Periodo` + `Asignacion.periodo_id`

**Files:**
- Modify: `backend/models.py` (add `Periodo` before `Asignacion`, extend `Asignacion`)
- Test: `backend/tests/test_periodos_model.py`

**Interfaces:**
- Consumes: `db` (`models.py`), existing `Asignacion` columns (`profesor_id`, `materia_id`, `grupo_id`, `fecha_inicio`, `fecha_fin`).
- Produces: `class Periodo(db.Model)` with `id: int`, `nombre: str` (unique, not null), `fecha_inicio: date | None`, `fecha_fin: date | None`, `activa: bool = True`, `to_dict(self) -> dict{id, nombre, fecha_inicio, fecha_fin, activa}`; `Asignacion.periodo_id: int | None` (FK `periodos.id`); `Asignacion.periodo` relationship; `Asignacion.to_dict()` gains `periodo_id: int | None` and `periodo_nombre: str` (`"Sin periodo"` when `NULL`).

- [ ] **Step 1: Write the failing test**

```python
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from app import create_app
from config import TestingConfig
from models import db, Periodo, Asignacion, Profesor, Materia, Grupo, Carrera, Sede


@pytest.fixture()
def app_ctx():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _seed_catalogo():
    sede = Sede(nombre='Teotitlan', codigo='TEO')
    db.session.add(sede)
    db.session.flush()
    carrera = Carrera(nombre='Sistemas', codigo='SIS')
    db.session.add(carrera)
    db.session.flush()
    materia = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    grupo = Grupo(nombre='A', carrera_id=carrera.id, sede_id=sede.id)
    prof = Profesor(numero_empleado='E1', nombre='Ana', apellido_paterno='Paz',
                    email='ana@example.com', password_hash='x')
    db.session.add_all([materia, grupo, prof])
    db.session.flush()
    return sede, carrera, materia, grupo, prof


def test_periodo_to_dict(app_ctx):
    p = Periodo(nombre='Enero-Abril 2026', fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 4, 30), activa=True)
    db.session.add(p)
    db.session.commit()
    assert p.to_dict() == {'id': p.id, 'nombre': 'Enero-Abril 2026',
                           'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-04-30',
                           'activa': True}


def test_asignacion_serializa_periodo_y_sin_periodo(app_ctx):
    _, _, materia, grupo, prof = _seed_catalogo()
    p = Periodo(nombre='Regular', activa=True)
    db.session.add(p)
    db.session.flush()
    con = Asignacion(profesor_id=prof.id, materia_id=materia.id, grupo_id=grupo.id,
                     fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 4, 30),
                     periodo_id=p.id)
    legacy = Asignacion(profesor_id=prof.id, materia_id=materia.id, grupo_id=grupo.id,
                        fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 4, 30),
                        periodo_id=None)
    db.session.add_all([con, legacy])
    db.session.commit()
    assert con.to_dict()['periodo_id'] == p.id
    assert con.to_dict()['periodo_nombre'] == 'Regular'
    assert legacy.to_dict()['periodo_id'] is None
    assert legacy.to_dict()['periodo_nombre'] == 'Sin periodo'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_periodos_model.py -v` (workdir `backend/`)
Expected: FAIL with `ImportError: cannot import name 'Periodo'` (collection error on the `from models import ... Periodo` line).

- [ ] **Step 3: Write minimal implementation**

In `backend/models.py`, insert before the `ASIGNACION` section header:

```python
class Periodo(db.Model):
    """Catálogo de períodos (Enero-Abril 2026, Regular, ...)."""
    __tablename__ = 'periodos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'activa': self.activa,
        }
```

In `class Asignacion`, add the column next to `grupo_id`:

```python
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodos.id'), nullable=True)
```

Add the relationship next to `materia = ...`:

```python
    periodo = db.relationship('Periodo', backref='asignaciones')
```

Extend `Asignacion.to_dict()` with two keys after `'grupo'`:

```python
            'periodo_id': self.periodo_id,
            'periodo_nombre': self.periodo.nombre if self.periodo else 'Sin periodo',
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_periodos_model.py -v` (workdir `backend/`)
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/models.py backend/tests/test_periodos_model.py
git commit -m "feat: add Periodo catalog and Asignacion.periodo_id"
```

### Task 2: Migración 004 slice 1 (tabla + seed + columna)

**Files:**
- Create: `backend/migrations/versions/004_periodos_catalog_slice1.py`
- Test: `backend/tests/test_migracion_004_periodos.py`

**Interfaces:**
- Consumes: `Periodo` columns and seed contract from Task 1; migration head `c3d4e5f6a7b8`.
- Produces: `revision = 'd4e5f6a7b8c9'`, `down_revision = 'c3d4e5f6a7b8'`; `PERIODOS_SEED: list[dict{nombre, fecha_inicio, fecha_fin, activa}]` (closed list below); `upgrade() -> None`; `downgrade() -> None`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_migracion_004_periodos.py -v` (workdir `backend/`)
Expected: FAIL with `FileNotFoundError` on `004_periodos_catalog_slice1.py`.

- [ ] **Step 3: Write minimal implementation**

Create `backend/migrations/versions/004_periodos_catalog_slice1.py` with this exact content:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_migracion_004_periodos.py -v` (workdir `backend/`)
Expected: PASS (3 passed).

- [ ] **Step 5: Verify upgrade on a scratch database**

Run: `flask --app app.py db upgrade` (workdir `backend/`, against a scratch/dev database, never production)
Expected: `Running upgrade c3d4e5f6a7b8 -> d4e5f6a7b8c9` with no error; `periodos` contains the 5 seed rows and `asignaciones` has nullable `periodo_id`.

- [ ] **Step 6: Verify downgrade then re-upgrade**

Run: `flask --app app.py db downgrade -1` then `flask --app app.py db upgrade` (workdir `backend/`)
Expected: downgrade reports `d4e5f6a7b8c9 -> c3d4e5f6a7b8` with no error and `periodos` gone; re-upgrade restores the 5 seed rows.

- [ ] **Step 7: Commit**

```bash
git add backend/migrations/versions/004_periodos_catalog_slice1.py backend/tests/test_migracion_004_periodos.py
git commit -m "feat: add periodos catalog migration with seed"
```

### Task 3: CRUD `/api/periodos` + registro del blueprint

**Files:**
- Create: `backend/routes/periodos.py`
- Modify: `backend/app.py` (import + `register_blueprint`, same block as the other blueprints)
- Test: `backend/tests/test_periodos_crud.py`

**Interfaces:**
- Consumes: `Periodo.to_dict()` (Task 1); `@jwt_required`, `@admin_required` (`utils/decorators.py`).
- Produces: `periodos_bp: Blueprint`; `GET /api/periodos -> 200 {periodos: [{id, nombre, fecha_inicio, fecha_fin, activa}]}` ordered by `nombre asc`; `POST /api/periodos {nombre!, fecha_inicio?, fecha_fin?, activa?} -> 201 {message, periodo}` / `422 {error: 'El campo nombre es requerido'}` / `409 {error: 'Periodo ya existe'}`; `PUT /api/periodos/<id> -> 200 {message, periodo}` / `422` empty nombre / `409` duplicate; `DELETE /api/periodos/<id> -> 200 {message: 'Período desactivado', periodo}` (sets `activa=false`, keeps associations); writes require admin (non-admin `403`).

- [ ] **Step 1: Write the failing test**

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Periodo


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app.test_client()
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _headers(role='general_admin', utype='admin'):
    tok = create_access_token(identity='t', additional_claims={'type': utype, 'role': role, 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def test_get_ordenado_para_todos_los_roles(client):
    db.session.add_all([Periodo(nombre='Regular'), Periodo(nombre='Enero-Abril 2026')])
    db.session.commit()
    for role in ('general_admin', 'sede_admin'):
        r = client.get('/api/periodos', headers=_headers(role))
        assert r.status_code == 200
        nombres = [p['nombre'] for p in r.get_json()['periodos']]
        assert nombres == sorted(nombres)


def test_post_valida_nombre_y_duplicado(client):
    assert client.post('/api/periodos', json={}, headers=_headers()).status_code == 422
    assert client.post('/api/periodos', json={'nombre': '  '}, headers=_headers()).status_code == 422
    assert client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers()).status_code == 201
    dup = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers())
    assert dup.status_code == 409
    assert dup.get_json()['error'] == 'Periodo ya existe'


def test_escritura_solo_admin_y_baja_logica(client):
    r = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers(utype='alumno'))
    assert r.status_code == 403
    pid = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers()).get_json()['periodo']['id']
    upd = client.put(f'/api/periodos/{pid}', json={'nombre': 'Regular 2'}, headers=_headers())
    assert upd.status_code == 200 and upd.get_json()['periodo']['nombre'] == 'Regular 2'
    dele = client.delete(f'/api/periodos/{pid}', headers=_headers())
    assert dele.status_code == 200
    body = dele.get_json()
    assert body['message'] == 'Período desactivado' and body['periodo']['activa'] is False
    assert db.session.get(Periodo, pid).activa is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_periodos_crud.py -v` (workdir `backend/`)
Expected: FAIL with `404` on `GET /api/periodos` (no route registered).

- [ ] **Step 3: Write minimal implementation**

Create `backend/routes/periodos.py`:

```python
"""
Rutas para el catálogo de Períodos
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db, Periodo
from utils.decorators import admin_required

periodos_bp = Blueprint('periodos', __name__)


def _parse_fecha_opt(value, campo):
    if value in (None, ''):
        return None, None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date(), None
    except ValueError:
        return None, jsonify({'error': f'Formato inválido en {campo}. Use YYYY-MM-DD'}), 400


@periodos_bp.route('', methods=['GET'])
@jwt_required()
def listar_periodos():
    periodos = Periodo.query.order_by(Periodo.nombre.asc()).all()
    return jsonify({'periodos': [p.to_dict() for p in periodos]}), 200


@periodos_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def crear_periodo():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Datos requeridos'}), 400
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'El campo nombre es requerido'}), 422
    if Periodo.query.filter_by(nombre=nombre).first():
        return jsonify({'error': 'Periodo ya existe'}), 409
    fecha_inicio, err = _parse_fecha_opt(data.get('fecha_inicio'), 'fecha_inicio')
    if err:
        return err
    fecha_fin, err = _parse_fecha_opt(data.get('fecha_fin'), 'fecha_fin')
    if err:
        return err
    periodo = Periodo(nombre=nombre, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                      activa=data.get('activa', True))
    db.session.add(periodo)
    db.session.commit()
    return jsonify({'message': 'Período creado exitosamente', 'periodo': periodo.to_dict()}), 201


@periodos_bp.route('/<int:periodo_id>', methods=['PUT'])
@jwt_required()
@admin_required
def actualizar_periodo(periodo_id):
    periodo = Periodo.query.get_or_404(periodo_id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Datos requeridos'}), 400
    if 'nombre' in data:
        nombre = (data.get('nombre') or '').strip()
        if not nombre:
            return jsonify({'error': 'El campo nombre es requerido'}), 422
        otro = Periodo.query.filter_by(nombre=nombre).first()
        if otro and otro.id != periodo.id:
            return jsonify({'error': 'Periodo ya existe'}), 409
        periodo.nombre = nombre
    if 'fecha_inicio' in data:
        fecha_inicio, err = _parse_fecha_opt(data.get('fecha_inicio'), 'fecha_inicio')
        if err:
            return err
        periodo.fecha_inicio = fecha_inicio
    if 'fecha_fin' in data:
        fecha_fin, err = _parse_fecha_opt(data.get('fecha_fin'), 'fecha_fin')
        if err:
            return err
        periodo.fecha_fin = fecha_fin
    if 'activa' in data:
        periodo.activa = bool(data['activa'])
    db.session.commit()
    return jsonify({'message': 'Período actualizado exitosamente', 'periodo': periodo.to_dict()}), 200


@periodos_bp.route('/<int:periodo_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def eliminar_periodo(periodo_id):
    periodo = Periodo.query.get_or_404(periodo_id)
    periodo.activa = False
    db.session.commit()
    return jsonify({'message': 'Período desactivado', 'periodo': periodo.to_dict()}), 200
```

- [ ] **Step 4: Register the blueprint in `backend/app.py`**

Add the import after `from routes.boletas import boletas_bp`:

```python
    from routes.periodos import periodos_bp
```

Add the registration after `app.register_blueprint(boletas_bp, url_prefix='/api/boletas')`:

```python
    app.register_blueprint(periodos_bp, url_prefix='/api/periodos')
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_periodos_crud.py -v` (workdir `backend/`)
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/routes/periodos.py backend/app.py backend/tests/test_periodos_crud.py
git commit -m "feat: add periodos catalog CRUD"
```

### Task 4: `periodo_id` obligatorio vía API en Asignaciones

**Files:**
- Modify: `backend/routes/asignaciones.py`
- Test: `backend/tests/test_asignaciones_periodo.py`

**Interfaces:**
- Consumes: `Periodo` rows from Task 3; `POST /api/asignaciones` body gains `periodo_id: int!`; `PUT /api/asignaciones/<id>` accepts `periodo_id: int | null | absent`.
- Produces: POST without/null/unknown/inactive `periodo_id` -> `422`; POST valid -> `201` with `asignacion.periodo_id`; PUT with unknown id -> `422 {error: 'periodo_id inexistente'}`; PUT with explicit `null` clears to `"Sin periodo"`; PUT omitting the key preserves; GET serializes `periodo_id` + `periodo_nombre`.

- [ ] **Step 1: Write the failing test**

```python
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Periodo, Profesor, Materia, Grupo, Carrera, Sede


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    sede = Sede(nombre='Teotitlan', codigo='TEO')
    db.session.add(sede)
    db.session.flush()
    carrera = Carrera(nombre='Sistemas', codigo='SIS')
    db.session.add(carrera)
    db.session.flush()
    materia = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    grupo = Grupo(nombre='A', carrera_id=carrera.id, sede_id=sede.id)
    prof = Profesor(numero_empleado='E1', nombre='Ana', apellido_paterno='Paz',
                    email='ana@example.com', password_hash='x')
    activo = Periodo(nombre='Enero-Abril 2026', activa=True)
    inactivo = Periodo(nombre='Viejo', activa=False)
    db.session.add_all([materia, grupo, prof, activo, inactivo])
    db.session.commit()
    yield app.test_client(), {'materia': materia.id, 'grupo': grupo.id, 'prof': prof.id,
                              'activo': activo.id, 'inactivo': inactivo.id}
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _h():
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def _body(ids, **kw):
    data = {'profesor_id': ids['prof'], 'materia_id': ids['materia'], 'grupo_id': ids['grupo'],
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-04-30'}
    data.update(kw)
    return data


def test_post_exige_periodo_activo(client):
    c, ids = client
    assert c.post('/api/asignaciones', json=_body(ids), headers=_h()).status_code == 422
    assert c.post('/api/asignaciones', json=_body(ids, periodo_id=None), headers=_h()).status_code == 422
    assert c.post('/api/asignaciones', json=_body(ids, periodo_id=9999), headers=_h()).status_code == 422
    assert c.post('/api/asignaciones', json=_body(ids, periodo_id=ids['inactivo']), headers=_h()).status_code == 422
    ok = c.post('/api/asignaciones', json=_body(ids, periodo_id=ids['activo']), headers=_h())
    assert ok.status_code == 201
    assert ok.get_json()['asignacion']['periodo_id'] == ids['activo']
    assert ok.get_json()['asignacion']['periodo_nombre'] == 'Enero-Abril 2026'


def test_put_edita_periodo_incluido_inactivo_y_nulo(client):
    c, ids = client
    aid = c.post('/api/asignaciones', json=_body(ids, periodo_id=ids['activo']), headers=_h()).get_json()['asignacion']['id']
    assert c.put(f'/api/asignaciones/{aid}', json={'periodo_id': 9999}, headers=_h()).status_code == 422
    edit = c.put(f'/api/asignaciones/{aid}', json={'periodo_id': ids['inactivo']}, headers=_h())
    assert edit.status_code == 200 and edit.get_json()['asignacion']['periodo_nombre'] == 'Viejo'
    keep = c.put(f'/api/asignaciones/{aid}', json={'activo': True}, headers=_h())
    assert keep.get_json()['asignacion']['periodo_id'] == ids['inactivo']
    clear = c.put(f'/api/asignaciones/{aid}', json={'periodo_id': None}, headers=_h())
    assert clear.get_json()['asignacion']['periodo_nombre'] == 'Sin periodo'
    listed = c.get('/api/asignaciones', headers=_h()).get_json()['asignaciones']
    assert any(a['id'] == aid and a['periodo_nombre'] == 'Sin periodo' for a in listed)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_asignaciones_periodo.py -v` (workdir `backend/`)
Expected: FAIL — POST without `periodo_id` returns `201` instead of `422`.

- [ ] **Step 3: Write minimal implementation**

In `backend/routes/asignaciones.py`, extend the import:

```python
from models import db, Asignacion, Profesor, Materia, Grupo, Periodo
```

In `create_asignacion`, after the `required` loop (which stays `400` for the legacy fields), insert:

```python
    periodo_id = data.get('periodo_id')
    if periodo_id is None:
        return jsonify({'error': 'El campo periodo_id es requerido'}), 422

    periodo = db.session.get(Periodo, periodo_id)
    if not periodo or not periodo.activa:
        return jsonify({'error': 'periodo_id inválido o inactivo'}), 422
```

Pass it to the constructor:

```python
    asignacion = Asignacion(
        profesor_id=data['profesor_id'],
        materia_id=data['materia_id'],
        grupo_id=data['grupo_id'],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        periodo_id=periodo.id,
        activo=data.get('activo', True)
    )
```

In `update_asignacion`, insert before the `if 'activo' in data:` block:

```python
    if 'periodo_id' in data:
        if data['periodo_id'] is None:
            asignacion.periodo_id = None
        else:
            periodo = db.session.get(Periodo, data['periodo_id'])
            if not periodo:
                return jsonify({'error': 'periodo_id inexistente'}), 422
            asignacion.periodo_id = periodo.id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_asignaciones_periodo.py -v` (workdir `backend/`)
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/routes/asignaciones.py backend/tests/test_asignaciones_periodo.py
git commit -m "feat: require periodo_id on asignaciones API"
```

### Task 5: Rescate de la descarga DOCX (`boleta_generator` + `python-docx`)

**Files:**
- Create: `backend/utils/boleta_generator.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_boleta_download.py`

**Interfaces:**
- Consumes: call sites `boletas.py:113-114,153,175` (`doc = generar_boleta(alumno, calificaciones, carrera, config_db)` then `doc.save(buf)`).
- Produces: `generar_boleta(alumno, calificaciones, carrera, config_db) -> docx.document.Document` with institution heading, alumno identity block, materias table (Materia | Calificación | Periodo | Año), and promedio paragraph; `requirements.txt` contains a `python-docx` line.

- [ ] **Step 1: Write the failing test**

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Alumno, Calificacion, Materia, Carrera, Sede


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    sede = Sede(nombre='Teotitlan', codigo='TEO')
    db.session.add(sede)
    db.session.flush()
    carrera = Carrera(nombre='Sistemas', codigo='SIS')
    db.session.add(carrera)
    db.session.flush()
    materia = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    db.session.add(materia)
    db.session.flush()
    alumno = Alumno(numero_control='A1', nombre='Luz', apellido_paterno='Diaz',
                    email='luz@example.com', password_hash='x',
                    carrera_id=carrera.id, sede_id=sede.id)
    db.session.add(alumno)
    db.session.flush()
    db.session.add(Calificacion(alumno_id=alumno.id, materia_id=materia.id,
                                calificacion_final=8.5, periodo='Regular', anio=2026))
    db.session.commit()
    yield app.test_client(), alumno.id
    db.session.remove()
    db.drop_all()
    ctx.pop()


def test_descarga_responde_docx(client):
    c, alumno_id = client
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    r = c.get(f'/api/boletas/download/{alumno_id}', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 200
    assert r.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    assert r.data[:2] == b'PK'


def test_requirements_declara_python_docx():
    req = (Path(__file__).resolve().parent.parent / 'requirements.txt').read_text(encoding='utf-8')
    assert 'python-docx' in req
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_boleta_download.py -v` (workdir `backend/`)
Expected: FAIL with `ModuleNotFoundError: No module named 'utils.boleta_generator'` (and `docx` missing).

- [ ] **Step 3: Write minimal implementation**

Create `backend/utils/boleta_generator.py`:

```python
"""
Generación de boletas en DOCX (rescate slice 1).
"""
from docx import Document


def generar_boleta(alumno, calificaciones, carrera, config_db):
    """Construye el documento DOCX de la boleta con el historial completo.

    Args:
        alumno: modelo Alumno con `nombre_completo` y `numero_control`.
        calificaciones: lista de Calificacion con `calificacion_final`, `periodo`, `anio` y `materia`.
        carrera: modelo Carrera o None.
        config_db: dict de configuración (claves opcionales `institucion_nombre`, `ciclo_texto`).

    Returns:
        docx.document.Document listo para `doc.save(buffer)`.
    """
    cfg = config_db or {}
    doc = Document()
    doc.add_heading(cfg.get('institucion_nombre', 'Boleta de calificaciones'), level=1)
    doc.add_paragraph(f"Alumno: {alumno.nombre_completo} ({alumno.numero_control or 's/n'})")
    doc.add_paragraph(f"Carrera: {carrera.nombre if carrera else ''}")
    if cfg.get('ciclo_texto'):
        doc.add_paragraph(cfg['ciclo_texto'])
    tabla = doc.add_table(rows=1, cols=4)
    encabezado = tabla.rows[0].cells
    encabezado[0].text, encabezado[1].text, encabezado[2].text, encabezado[3].text = (
        'Materia', 'Calificación', 'Periodo', 'Año')
    for cal in calificaciones:
        fila = tabla.add_row().cells
        fila[0].text = cal.materia.nombre if cal.materia else 'N/A'
        fila[1].text = str(cal.calificacion_final)
        fila[2].text = str(cal.periodo or '')
        fila[3].text = str(cal.anio or '')
    notas = [c.calificacion_final for c in calificaciones if c.calificacion_final and c.calificacion_final > 0]
    promedio = round(sum(notas) / len(notas), 1) if notas else 0
    doc.add_paragraph(f'Promedio: {promedio} ({len(notas)} materias)')
    return doc
```

- [ ] **Step 4: Declare the dependency**

In `backend/requirements.txt`, add after the `openpyxl` line:

```
python-docx
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_boleta_download.py -v` (workdir `backend/`, with `python-docx` installed)
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/utils/boleta_generator.py backend/requirements.txt backend/tests/test_boleta_download.py
git commit -m "fix: rescue boleta DOCX download with generator module"
```

### Task 6: Filtro visual `?periodo_id=` en Boletas (slice 1, vía join de Asignación)

**Files:**
- Modify: `backend/routes/boletas.py`
- Test: `backend/tests/test_boletas_filtro.py`

**Interfaces:**
- Consumes: `Asignacion.periodo_id` (Task 1/4), `GrupoIntegrante`, `Calificacion.calificacion_final`.
- Produces: `_alcance_periodo(periodo_id: int) -> tuple[set[int], set[int]]` returning `(alumno_ids, materia_ids)` where the alumno belongs to a grupo assigned under that period AND holds a `final > 0` grade in an assigned materia (normative slice-1 semantics until Task 12 replaces the body); `GET /api/boletas/alumnos?periodo_id=<id>` filters the list and per-row `calificaciones_count`; missing param returns full history; present-but-invalid (non-integer or unknown id) returns `422 {error: 'periodo_id inválido'}`; downloads and preview ignore the filter.

- [ ] **Step 1: Write the failing test**

```python
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Alumno, Calificacion, Materia, Grupo, GrupoIntegrante, Carrera, Sede, Profesor, Periodo, Asignacion


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    sede = Sede(nombre='Teotitlan', codigo='TEO')
    db.session.add(sede)
    db.session.flush()
    carrera = Carrera(nombre='Sistemas', codigo='SIS')
    db.session.add(carrera)
    db.session.flush()
    m1 = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    m2 = Materia(carrera_id=carrera.id, nombre='Fisica', codigo='FIS-1')
    g = Grupo(nombre='A', carrera_id=carrera.id, sede_id=sede.id)
    prof = Profesor(numero_empleado='E1', nombre='Ana', apellido_paterno='Paz',
                    email='ana@example.com', password_hash='x')
    p1 = Periodo(nombre='Enero-Abril 2026', activa=True)
    p2 = Periodo(nombre='Regular', activa=True)
    db.session.add_all([m1, m2, g, prof, p1, p2])
    db.session.flush()
    db.session.add(Asignacion(profesor_id=prof.id, materia_id=m1.id, grupo_id=g.id,
                              fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 4, 30),
                              periodo_id=p1.id))
    a1 = Alumno(numero_control='A1', nombre='Luz', apellido_paterno='Diaz', email='l1@example.com',
                password_hash='x', carrera_id=carrera.id, sede_id=sede.id)
    a2 = Alumno(numero_control='A2', nombre='Sol', apellido_paterno='Mar', email='l2@example.com',
                password_hash='x', carrera_id=carrera.id, sede_id=sede.id)
    db.session.add_all([a1, a2])
    db.session.flush()
    db.session.add_all([GrupoIntegrante(grupo_id=g.id, alumno_id=a1.id),
                        GrupoIntegrante(grupo_id=g.id, alumno_id=a2.id),
                        Calificacion(alumno_id=a1.id, materia_id=m1.id, calificacion_final=9.0,
                                     periodo='Enero-Abril 2026', anio=2026),
                        Calificacion(alumno_id=a2.id, materia_id=m2.id, calificacion_final=9.0,
                                     periodo='Regular', anio=2026)])
    db.session.commit()
    yield app.test_client(), {'p1': p1.id, 'p2': p2.id}
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _h():
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def test_filtro_por_periodo_solo_lista_visible(client):
    c, ids = client
    full = c.get('/api/boletas/alumnos', headers=_h()).get_json()['alumnos']
    assert len(full) == 2
    f1 = c.get(f"/api/boletas/alumnos?periodo_id={ids['p1']}", headers=_h()).get_json()['alumnos']
    assert [a['numero_control'] for a in f1] == ['A1']
    assert f1[0]['calificaciones_count'] == 1
    assert c.get('/api/boletas/alumnos?periodo_id=9999', headers=_h()).status_code == 422
    assert c.get('/api/boletas/alumnos?periodo_id=abc', headers=_h()).status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_boletas_filtro.py -v` (workdir `backend/`)
Expected: FAIL — filtered response returns 2 alumnos instead of 1 (param currently ignored).

- [ ] **Step 3: Write minimal implementation**

In `backend/routes/boletas.py`, extend the import:

```python
from models import db, Alumno, Calificacion, Materia, Carrera, Periodo, Asignacion, GrupoIntegrante
```

Insert the helper before `listar_alumnos_boletas`:

```python
def _alcance_periodo(periodo_id):
    """Resuelve (alumno_ids, materia_ids) visibles para un período (slice 1).

    Un alumno es visible si pertenece a un grupo asignado bajo `periodo_id`
    y tiene al menos una calificación con `final > 0` en una materia
    asignada bajo ese mismo período.
    """
    asigs = Asignacion.query.filter_by(periodo_id=periodo_id).all()
    if not asigs:
        return set(), set()
    gids = [a.grupo_id for a in asigs]
    mids = [a.materia_id for a in asigs]
    en_grupos = {r[0] for r in db.session.query(GrupoIntegrante.alumno_id)
                 .filter(GrupoIntegrante.grupo_id.in_(gids)).all()}
    con_nota = {r[0] for r in db.session.query(Calificacion.alumno_id)
                .filter(Calificacion.materia_id.in_(mids),
                        Calificacion.calificacion_final > 0).all()}
    return en_grupos & con_nota, set(mids)
```

In `listar_alumnos_boletas`, insert after the `search` filter block and before `alumnos = query...`:

```python
    periodo_ids = None
    periodo_materias = None
    raw_periodo = request.args.get('periodo_id')
    if raw_periodo is not None:
        try:
            periodo_id = int(raw_periodo)
        except (TypeError, ValueError):
            return jsonify({'error': 'periodo_id inválido'}), 422
        if not db.session.get(Periodo, periodo_id):
            return jsonify({'error': 'periodo_id inválido'}), 422
        periodo_ids, periodo_materias = _alcance_periodo(periodo_id)
```

Replace the counting block body:

```python
    result = []
    for a in alumnos:
        q = Calificacion.query.filter(
            Calificacion.alumno_id == a.id,
            Calificacion.calificacion_final > 0
        )
        if periodo_materias is not None:
            if a.id not in periodo_ids:
                continue
            q = q.filter(Calificacion.materia_id.in_(list(periodo_materias)))
        calif_count = q.count()
        if periodo_ids is not None and calif_count == 0:
            continue

        result.append({
```

Downloads (`descargar_boleta`, `descargar_boletas_multiples`) and `vista_previa_boleta` stay untouched: they never read `periodo_id`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_boletas_filtro.py -v` (workdir `backend/`)
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/routes/boletas.py backend/tests/test_boletas_filtro.py
git commit -m "feat: filter boletas list by periodo_id"
```

### Task 7: API frontend `periodos.js` (+ contrato de `boletas.js`)

**Files:**
- Create: `frontend/src/api/periodos.js`
- Create: `frontend/src/api/periodos.test.js`
- Create: `frontend/src/api/boletas.test.js`
- Verify: `frontend/src/api/boletas.js` (exists; `getAlumnosBoletas(params)` already forwards `params` untouched — no signature change)

**Interfaces:**
- Consumes: shared axios instance `./index` (same as `sedes.js`).
- Produces: `getPeriodos(params={}) -> Promise<{periodos}>`; `createPeriodo(data) -> Promise<{message, periodo}>`; `updatePeriodo(id, data) -> Promise<{message, periodo}>`; `deletePeriodo(id) -> Promise<{message, periodo}>`; `getAlumnosBoletas` keeps `(params = {})` and forwards `periodo_id` when present; `descargarBoleta(alumnoId)` and `descargarBoletasMultiples(alumnoIds)` never reference `periodo_id`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/api/periodos.test.js`:

```js
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./index', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { periodos: [] } }),
    post: vi.fn().mockResolvedValue({ data: { periodo: { id: 1 } } }),
    put: vi.fn().mockResolvedValue({ data: { periodo: { id: 1 } } }),
    delete: vi.fn().mockResolvedValue({ data: { message: 'Período desactivado' } }),
  },
}));

import api from './index';
import * as periodosApi from './periodos';

describe('periodos api', () => {
  beforeEach(() => vi.clearAllMocks());

  it('expone getPeriodos, createPeriodo, updatePeriodo, deletePeriodo', () => {
    expect(typeof periodosApi.getPeriodos).toBe('function');
    expect(typeof periodosApi.createPeriodo).toBe('function');
    expect(typeof periodosApi.updatePeriodo).toBe('function');
    expect(typeof periodosApi.deletePeriodo).toBe('function');
  });

  it('getPeriodos llama GET /periodos', async () => {
    await periodosApi.getPeriodos();
    expect(api.get).toHaveBeenCalledWith('/periodos', expect.any(Object));
    expect(api.get.mock.calls[0][0]).toMatch(/\/periodos\/?/);
  });

  it('createPeriodo POST /periodos con el nombre', async () => {
    await periodosApi.createPeriodo({ nombre: 'Regular' });
    expect(api.post).toHaveBeenCalledWith(expect.stringContaining('/periodos'), expect.objectContaining({ nombre: 'Regular' }));
  });

  it('updatePeriodo PUT /periodos/:id', async () => {
    await periodosApi.updatePeriodo(5, { nombre: 'Nuevo' });
    expect(api.put).toHaveBeenCalledWith(expect.stringContaining('/periodos/5'), expect.objectContaining({ nombre: 'Nuevo' }));
  });

  it('deletePeriodo DELETE /periodos/:id', async () => {
    await periodosApi.deletePeriodo(5);
    expect(api.delete).toHaveBeenCalledWith(expect.stringContaining('/periodos/5'));
  });
});
```

`frontend/src/api/boletas.test.js`:

```js
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./index', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { alumnos: [] } }),
  },
}));

import api from './index';
import { getAlumnosBoletas, descargarBoleta, descargarBoletasMultiples } from './boletas';

describe('boletas api periodo filter', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getAlumnosBoletas reenvia periodo_id como query param', async () => {
    await getAlumnosBoletas({ periodo_id: 3 });
    expect(api.get).toHaveBeenCalledWith('/boletas/alumnos', { params: { periodo_id: 3 } });
  });

  it('las descargas nunca envian periodo_id', () => {
    expect(descargarBoleta.toString()).not.toContain('periodo_id');
    expect(descargarBoletasMultiples.toString()).not.toContain('periodo_id');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- src/api/periodos.test.js src/api/boletas.test.js` (workdir `frontend/`)
Expected: FAIL — `periodos.js` does not exist; `boletas.test.js` fails on the `periodo_id` forward assertion (current call passes `params` through, so only the first file errors; the second passes trivially — the failing gate is the missing module).

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/api/periodos.js`:

```js
import api from './index';

export const getPeriodos = async (params = {}) => {
  const response = await api.get('/periodos', { params });
  return response.data;
};

export const createPeriodo = async (data) => {
  const response = await api.post('/periodos', data);
  return response.data;
};

export const updatePeriodo = async (id, data) => {
  const response = await api.put(`/periodos/${id}`, data);
  return response.data;
};

export const deletePeriodo = async (id) => {
  const response = await api.delete(`/periodos/${id}`);
  return response.data;
};
```

`frontend/src/api/boletas.js` needs no change: `getAlumnosBoletas(params)` already forwards `{ params }` untouched.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- src/api/periodos.test.js src/api/boletas.test.js` (workdir `frontend/`)
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/periodos.js frontend/src/api/periodos.test.js frontend/src/api/boletas.test.js
git commit -m "feat: add periodos frontend api client"
```

### Task 8: UI Asignaciones — dropdown de Período + columnas Período/Fechas

**Files:**
- Modify: `frontend/src/pages/admin/Asignaciones.jsx`
- Test: `frontend/src/pages/admin/Asignaciones.periodo.test.jsx`

**Interfaces:**
- Consumes: `getPeriodos` (Task 7); `createAsignacion`/`updateAsignacion` accept `periodo_id: number | null`; rows carry `periodo_id`/`periodo_nombre` (Task 4).
- Produces: create form has required `Período` select (active periods only, empty initial state blocks submit); edit form lists actives plus the row's current period even when inactive; table shows `Período` (`periodo_nombre` or `"Sin periodo"`) and `Fechas` (`fecha_inicio – fecha_fin`); submit sends `periodo_id` as `number`.

- [ ] **Step 1: Write the failing test**

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../../api/asignaciones', () => ({
  getAsignaciones: vi.fn().mockResolvedValue([]),
  createAsignacion: vi.fn().mockResolvedValue({}),
  updateAsignacion: vi.fn().mockResolvedValue({}),
  deleteAsignacion: vi.fn().mockResolvedValue({}),
}));
vi.mock('../../api/profesores', () => ({ getProfesores: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/materias', () => ({ getMaterias: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/grupos', () => ({ getGrupos: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/periodos', () => ({
  getPeriodos: vi.fn().mockResolvedValue({ periodos: [
    { id: 1, nombre: 'Enero-Abril 2026', activa: true },
    { id: 2, nombre: 'Viejo', activa: false },
  ] }),
}));
vi.mock('../../components/ui/Toast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));

import AdminAsignaciones from './Asignaciones';
import { getAsignaciones, createAsignacion } from '../../api/asignaciones';

describe('Asignaciones periodo UI', () => {
  beforeEach(() => vi.clearAllMocks());

  it('el dropdown de crear muestra nombres y crear sin periodo no envia', async () => {
    render(<AdminAsignaciones />);
    fireEvent.click(await screen.findByText('Nueva Asignación'));
    expect(await screen.findByText('Enero-Abril 2026')).toBeInTheDocument();
    expect(screen.queryByText('Viejo')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Crear'));
    await waitFor(() => expect(createAsignacion).not.toHaveBeenCalled());
  });

  it('la tabla muestra Sin periodo ante periodo_id null', async () => {
    getAsignaciones.mockResolvedValueOnce([{ id: 7, profesor_id: 1, materia_id: 1, grupo_id: 1,
      fecha_inicio: '2026-01-01', fecha_fin: '2026-04-30',
      periodo_id: null, periodo_nombre: 'Sin periodo', puede_editar: true, activo: true }]);
    render(<AdminAsignaciones />);
    expect(await screen.findByText('Sin periodo')).toBeInTheDocument();
    expect(screen.getByText('Período')).toBeInTheDocument();
    expect(screen.getByText('Fechas')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/admin/Asignaciones.periodo.test.jsx` (workdir `frontend/`)
Expected: FAIL — `Unable to find text: Enero-Abril 2026` (no Período select exists yet).

- [ ] **Step 3: Write minimal implementation**

In `frontend/src/pages/admin/Asignaciones.jsx`, add the import:

```jsx
import { getPeriodos } from '../../api/periodos';
```

Add state next to the other list states:

```jsx
  const [periodos, setPeriodos] = useState([]);
```

Extend `formData` initial state and both modal openers with `periodo_id: ''`:

```jsx
  const [formData, setFormData] = useState({
    profesor_id: '',
    materia_id: '',
    grupo_id: '',
    periodo_id: '',
    fecha_inicio: '',
    fecha_fin: '',
    activo: true,
  });
```

(`openNewModal` and `openEditModal` set the same shape; `openEditModal` uses `periodo_id: asignacion.periodo_id ?? ''`.)

Extend `loadData` to fetch periods:

```jsx
      const [asigData, profData, matData, grpData, perData] = await Promise.all([
        getAsignaciones(),
        getProfesores(),
        getMaterias(),
        getGrupos(),
        getPeriodos(),
      ]);
      setPeriodos(perData.periodos || []);
```

Add the create/edit select before the `{/* Fechas */}` block (create lists actives only; edit adds the current one when inactive):

```jsx
              <Select
                label="Período *"
                required
                value={formData.periodo_id}
                onChange={(e) => setFormData({ ...formData, periodo_id: e.target.value === '' ? '' : parseInt(e.target.value) })}
              >
                <option value="">Seleccionar período</option>
                {periodos
                  .filter((p) => p.activa || (modalMode === 'edit' && p.id === (selectedAsignacion?.periodo_id ?? formData.periodo_id)))
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre}
                    </option>
                  ))}
              </Select>
```

Guard the submit (client-side block; backend still answers 422):

```jsx
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.periodo_id === '' || formData.periodo_id === null) {
      toast.error('El período es obligatorio');
      return;
    }
    setSaving(true);
```

Split the table header cell `Período` into two cells:

```jsx
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Período
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Fechas
                  </th>
```

And the row cell into:

```jsx
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-700">
                        {a.periodo_nombre || 'Sin periodo'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-500">
                        {a.fecha_inicio} - {a.fecha_fin}
                      </span>
                    </td>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/admin/Asignaciones.periodo.test.jsx` (workdir `frontend/`)
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/admin/Asignaciones.jsx frontend/src/pages/admin/Asignaciones.periodo.test.jsx
git commit -m "feat: add periodo selector to asignaciones UI"
```

### Task 9: UI Boletas — selector visual de Período (la descarga sigue completa)

**Files:**
- Modify: `frontend/src/pages/admin/Boletas.jsx`
- Test: `frontend/src/pages/admin/Boletas.periodo.test.jsx`

**Interfaces:**
- Consumes: `getPeriodos` (Task 7); `getAlumnosBoletas({carrera_id?, search?, periodo_id?})`; `descargarBoleta(alumnoId)` / `descargarBoletasMultiples(ids)` unchanged.
- Produces: selector `Período` default `"Todos"`; choosing a period calls `getAlumnosBoletas` with that `periodo_id` and filters only the visible list; downloads never send `periodo_id`; empty filtered list shows the empty state while download buttons stay enabled with full history.

- [ ] **Step 1: Write the failing test**

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../../api/boletas', () => ({
  getAlumnosBoletas: vi.fn().mockResolvedValue({ alumnos: [] }),
  descargarBoleta: vi.fn().mockResolvedValue(undefined),
  descargarBoletasMultiples: vi.fn().mockResolvedValue(undefined),
  previewBoleta: vi.fn().mockResolvedValue({}),
}));
vi.mock('../../api/carreras', () => ({ getCarreras: vi.fn().mockResolvedValue({ carreras: [] }) }));
vi.mock('../../api/periodos', () => ({
  getPeriodos: vi.fn().mockResolvedValue({ periodos: [{ id: 4, nombre: 'Enero-Abril 2026', activa: true }] }),
}));
vi.mock('../../components/ui/Toast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));

import AdminBoletas from './Boletas';
import { getAlumnosBoletas, descargarBoletasMultiples } from '../../api/boletas';

describe('Boletas periodo UI', () => {
  beforeEach(() => vi.clearAllMocks());

  it('selector por defecto Todos y filtrar llama con periodo_id', async () => {
    render(<AdminBoletas />);
    const select = await screen.findByLabelText('Período');
    expect(select.value).toBe('');
    fireEvent.change(select, { target: { value: '4' } });
    await waitFor(() => expect(getAlumnosBoletas).toHaveBeenCalledWith(
      expect.objectContaining({ periodo_id: '4' })));
  });

  it('sin resultados muestra vacio pero la descarga sigue disponible', async () => {
    getAlumnosBoletas.mockResolvedValueOnce({ alumnos: [] });
    render(<AdminBoletas />);
    expect(await screen.findByText('No se encontraron alumnos')).toBeInTheDocument();
    const btn = screen.getByText('Descargar todas');
    expect(btn.disabled).toBe(false);
    fireEvent.click(btn);
    await waitFor(() => expect(descargarBoletasMultiples).not.toHaveBeenCalledWith(
      expect.objectContaining({ periodo_id: expect.anything() })));
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/admin/Boletas.periodo.test.jsx` (workdir `frontend/`)
Expected: FAIL — `Unable to find label: Período` (no selector exists yet).

- [ ] **Step 3: Write minimal implementation**

In `frontend/src/pages/admin/Boletas.jsx`, add the import:

```js
import { getPeriodos } from '../../api/periodos';
```

Add state:

```js
  const [periodos, setPeriodos] = useState([]);
```

Extend filters and loader:

```js
  const [filters, setFilters] = useState({ carrera_id: '', search: '', periodo_id: '' });
```

```js
      const params = {};
      if (filters.carrera_id) params.carrera_id = filters.carrera_id;
      if (filters.search) params.search = filters.search;
      if (filters.periodo_id) params.periodo_id = filters.periodo_id;
      const res = await getAlumnosBoletas(params);
```

Load periods once:

```js
  const loadPeriodos = async () => {
    try {
      const res = await getPeriodos();
      setPeriodos(res.periodos || []);
    } catch {
      // ignore
    }
  };
```

```js
  useEffect(() => {
    loadCarreras();
    loadPeriodos();
  }, []);
```

Add the selector inside the Filters `Card`, before the Carrera block:

```jsx
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Período</label>
            <select
              aria-label="Período"
              value={filters.periodo_id}
              onChange={(e) => setFilters((prev) => ({ ...prev, periodo_id: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            >
              <option value="">Todos</option>
              {periodos.map((p) => (
                <option key={p.id} value={p.id}>{p.nombre}</option>
              ))}
            </select>
          </div>
```

`handleDownload` and `handleDownloadAll` stay untouched (they call `descargarBoleta(alumnoId)` / `descargarBoletasMultiples(ids)` with no period argument). The empty state (`alumnos.length === 0`) already renders while the header download buttons stay mounted above the list.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/admin/Boletas.periodo.test.jsx` (workdir `frontend/`)
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/admin/Boletas.jsx frontend/src/pages/admin/Boletas.periodo.test.jsx
git commit -m "feat: add visual periodo filter to boletas"
```

### Slice 1 exit gate (no code, verification only — executor runs, author does not skip)

- `pytest tests/ -v` (workdir `backend/`) — all green.
- `npm test` (workdir `frontend/`) — all green.
- `flask --app app.py db upgrade` / `flask --app app.py db downgrade -1` / `flask --app app.py db upgrade` (workdir `backend/`) — clean round-trip on a scratch database.

---

## Slice 2 — `Calificacion.periodo_id` heredado + backfill (depende del slice 1)

### Task 10: `Calificacion.periodo_id` + herencia desde la Asignación

**Files:**
- Modify: `backend/models.py` (`Calificacion`)
- Modify: `backend/routes/calificaciones.py` (POST create/update, PUT, bulk)
- Modify: `backend/routes/profesor.py` (sync-ensure + update)
- Test: `backend/tests/test_calificacion_periodo.py`

**Interfaces:**
- Consumes: `Asignacion.periodo_id` (Task 1/4); helper `_periodo_id_para_nota(materia_id: int, alumno_id: int) -> int | None` defined in `calificaciones.py` and imported by `profesor.py`: resolves the alumno's grupos via `GrupoIntegrante`, intersects with `Asignacion` rows for the materia, returns the highest `Asignacion.id` match's `periodo_id`, else `None`.
- Produces: `Calificacion.periodo_id: int | None` (FK `periodos.id`); `Calificacion.periodo` relationship; `Calificacion.to_dict()` gains `periodo_id` + `periodo_nombre` (`"Sin periodo"` on `NULL`); creating/updating a grade through any assignment flow copies the linked `Asignacion.periodo_id` (legacy `periodo`/`anio` strings untouched).

- [ ] **Step 1: Write the failing test**

```python
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Periodo, Profesor, Materia, Grupo, GrupoIntegrante, Carrera, Sede, Alumno, Asignacion, Calificacion


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    sede = Sede(nombre='Teotitlan', codigo='TEO')
    db.session.add(sede)
    db.session.flush()
    carrera = Carrera(nombre='Sistemas', codigo='SIS')
    db.session.add(carrera)
    db.session.flush()
    materia = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    grupo = Grupo(nombre='A', carrera_id=carrera.id, sede_id=sede.id)
    prof = Profesor(numero_empleado='E1', nombre='Ana', apellido_paterno='Paz',
                    email='ana@example.com', password_hash='x')
    per = Periodo(nombre='Enero-Abril 2026', activa=True)
    db.session.add_all([materia, grupo, prof, per])
    db.session.flush()
    db.session.add(Asignacion(profesor_id=prof.id, materia_id=materia.id, grupo_id=grupo.id,
                              fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 4, 30),
                              periodo_id=per.id))
    alumno = Alumno(numero_control='A1', nombre='Luz', apellido_paterno='Diaz', email='l1@example.com',
                    password_hash='x', carrera_id=carrera.id, sede_id=sede.id)
    db.session.add(alumno)
    db.session.flush()
    db.session.add(GrupoIntegrante(grupo_id=grupo.id, alumno_id=alumno.id))
    db.session.commit()
    yield app.test_client(), {'materia': materia.id, 'alumno': alumno.id, 'per': per.id}
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _h():
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def test_crear_calificacion_hereda_periodo_de_asignacion(client):
    c, ids = client
    r = c.post('/api/calificaciones', json={'alumno_id': ids['alumno'], 'materia_id': ids['materia'],
                                            'periodo': 'Regular', 'anio': 2026,
                                            'calificacion_final': 9.0}, headers=_h())
    assert r.status_code == 200
    body = r.get_json()['calificacion']
    assert body['periodo_id'] == ids['per']
    assert body['periodo_nombre'] == 'Enero-Abril 2026'
    assert body['periodo'] == 'Regular'


def test_bulk_hereda_y_sin_asignacion_queda_null(client):
    c, ids = client
    r = c.post('/api/calificaciones/bulk',
               json={'calificaciones': [{'alumno_id': ids['alumno'], 'materia_id': ids['materia'],
                                         'calificacion_final': 8.0}]}, headers=_h())
    assert r.status_code in (200, 207)
    cal = Calificacion.query.filter_by(alumno_id=ids['alumno'], materia_id=ids['materia']).first()
    assert cal.periodo_id == ids['per']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_calificacion_periodo.py -v` (workdir `backend/`)
Expected: FAIL with `ImportError`/`AttributeError` on `Calificacion.periodo_id` (column does not exist yet).

- [ ] **Step 3: Extend the model**

In `backend/models.py`, inside `class Calificacion` after the `anio` column:

```python
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodos.id'), nullable=True)
```

Add the relationship after `calificaciones = ...` is not here — add next to the class body (no backref clash; `Asignacion` already uses `backref='asignaciones'` on `Periodo`, so use an explicit relationship without backref):

```python
    periodo_obj = db.relationship('Periodo')
```

> **Controller amendment 2026-09-08 (Task 10 review):** the original snippet named this `periodo`, which would rebind and unmap the legacy `periodo` String column — implemented as `periodo_obj`; Task 12 must use `c.periodo_obj.nombre`.

Extend `Calificacion.to_dict()` after `'anio': self.anio,`:

```python
            'periodo_id': self.periodo_id,
            'periodo_nombre': self.periodo.nombre if self.periodo else 'Sin periodo',
```

- [ ] **Step 4: Inherit on every assignment-driven write path**

In `backend/routes/calificaciones.py`, add imports (`GrupoIntegrante`, `Asignacion`) and the helper at module level:

```python
from models import db, Alumno, Calificacion, Materia, Carrera, Asignacion, GrupoIntegrante


def _periodo_id_para_nota(materia_id, alumno_id):
    """Hereda el periodo_id de la asignación vinculada (profesor + grupo + materia).

    Busca los grupos del alumno, intersecta con las asignaciones de la materia
    y devuelve el periodo_id de la asignación con id mayor. Sin match: None.
    """
    grupo_ids = [r[0] for r in db.session.query(GrupoIntegrante.grupo_id)
                 .filter_by(alumno_id=alumno_id).all()]
    if not grupo_ids:
        return None
    asig = (Asignacion.query
            .filter(Asignacion.materia_id == materia_id, Asignacion.grupo_id.in_(grupo_ids))
            .order_by(Asignacion.id.desc()).first())
    return asig.periodo_id if asig else None
```

In the POST upsert: after resolving `calificacion` (both branches), set before `db.session.commit()`:

```python
        calificacion.periodo_id = _periodo_id_para_nota(data['materia_id'], data['alumno_id'])
```

In the PUT handler (`/<int:id>`), after applying field updates and before commit:

```python
    calificacion.periodo_id = _periodo_id_para_nota(calificacion.materia_id, calificacion.alumno_id)
```

In `bulk_create_calificaciones`, in the `if existente:` branch add:

```python
                existente.periodo_id = _periodo_id_para_nota(existente.materia_id, existente.alumno_id)
```

and in the `else:` constructor add the kwarg:

```python
                    periodo_id=_periodo_id_para_nota(cal_data['materia_id'], cal_data['alumno_id']),
```

In `backend/routes/profesor.py`, import the helper:

```python
from routes.calificaciones import _periodo_id_para_nota
```

In the sync-ensure constructor (`calif = Calificacion(...)` in the GET) add:

```python
                periodo_id=_periodo_id_para_nota(asignacion.materia_id, integ.alumno_id),
```

In the PUT update handler, after `calif` is resolved/created and before commit add:

```python
    calif.periodo_id = _periodo_id_para_nota(asignacion.materia_id, alumno_id)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_calificacion_periodo.py -v` (workdir `backend/`)
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/models.py backend/routes/calificaciones.py backend/routes/profesor.py backend/tests/test_calificacion_periodo.py
git commit -m "feat: inherit Calificacion.periodo_id from asignacion"
```

### Task 11: Migración 005 slice 2 (columna + backfill por match exacto)

**Files:**
- Create: `backend/migrations/versions/005_calificacion_periodo_slice2.py`
- Test: `backend/tests/test_migracion_005_backfill.py`

**Interfaces:**
- Consumes: `PERIODOS_SEED` nombres from migration 004; `Calificacion.periodo/anio` legacy columns (untouched).
- Produces: `revision = 'e5f6a7b8c9d0'`, `down_revision = 'd4e5f6a7b8c9'`; `upgrade()` adds nullable `calificaciones.periodo_id` FK then runs the backfill; `downgrade()` drops FK + column. Normative backfill predicate ( ambiguity in spec §3.4 resolved here and frozen): candidates tried in order are `f"{periodo} {anio}"` (only when `anio` is not null) then `periodo` alone; the first candidate with character-by-character equality (`==`, case- and space-sensitive) against `periodos.nombre` wins; no candidate → `NULL`.

- [ ] **Step 1: Write the failing test**

```python
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
    # Controller amendment 2026-09-08 (Task 11 review): Step 3 mandates batch.add_column(sa.Column(...)); the old literal could never go green.
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_migracion_005_backfill.py -v` (workdir `backend/`)
Expected: FAIL with `FileNotFoundError` on `005_calificacion_periodo_slice2.py`.

- [ ] **Step 3: Write minimal implementation**

Create `backend/migrations/versions/005_calificacion_periodo_slice2.py` with this exact content:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_migracion_005_backfill.py -v` (workdir `backend/`)
Expected: PASS (2 passed).

- [ ] **Step 5: Verify upgrade on a scratch database with legacy rows**

Run: `flask --app app.py db upgrade` (workdir `backend/`, scratch database seeded with legacy `periodo/anio` rows incl. one `"enero-abril 2026"` lowercase and one trailing-space row)
Expected: `Running upgrade d4e5f6a7b8c9 -> e5f6a7b8c9d0` with no error; exact rows carry `periodo_id`, lowercase/trailing-space/rare rows stay `NULL`.

- [ ] **Step 6: Verify downgrade then re-upgrade**

Run: `flask --app app.py db downgrade -1` then `flask --app app.py db upgrade` (workdir `backend/`)
Expected: downgrade reports `e5f6a7b8c9d0 -> d4e5f6a7b8c9` with no error and the column gone; re-upgrade re-runs the backfill identically.

- [ ] **Step 7: Commit**

```bash
git add backend/migrations/versions/005_calificacion_periodo_slice2.py backend/tests/test_migracion_005_backfill.py
git commit -m "feat: add calificacion periodo backfill migration"
```

### Task 12: Boletas filtra por columna directa + preview con `periodo_nombre` (slice 2)

**Files:**
- Modify: `backend/routes/boletas.py` (replace `_alcance_periodo` body, slim the list query, extend preview)
- Test: extend `backend/tests/test_boletas_filtro.py` with slice-2 cases (same file, appended tests)

**Interfaces:**
- Consumes: `Calificacion.periodo_id` (Task 10); `_alcance_periodo(periodo_id)` keeps its name and return shape `(alumno_ids: set[int], materia_ids: set[int])` but resolves directly from the column; preview items gain `periodo_id: int | None` + `periodo_nombre: str`.
- Produces: `GET /api/boletas/alumnos?periodo_id=` filters on `Calificacion.periodo_id == periodo_id` (legacy `NULL` rows surface only under `"Todos"`); downloads still ignore the filter; `GET /api/boletas/preview/<id>` items include the two new keys.

- [ ] **Step 1: Write the failing tests (append to `backend/tests/test_boletas_filtro.py`)**

```python
def test_filtro_slice2_usa_columna_directa(client):
    from models import Calificacion as Cal
    from models import db as _db
    c, ids = client
    cal = Cal.query.filter_by(calificacion_final=9.0).first()
    cal.periodo_id = ids['p1']
    _db.session.commit()
    f1 = c.get(f"/api/boletas/alumnos?periodo_id={ids['p1']}", headers=_h()).get_json()['alumnos']
    assert len(f1) == 1
    prev = c.get(f"/api/boletas/preview/{f1[0]['id']}", headers=_h())
    assert prev.status_code == 200


def test_preview_incluye_periodo_nombre(client):
    c, ids = client
    full = c.get('/api/boletas/alumnos', headers=_h()).get_json()['alumnos']
    alumno_id = full[0]['id']
    r = c.get(f'/api/boletas/preview/{alumno_id}', headers=_h())
    assert r.status_code == 200
    item = r.get_json()['calificaciones'][0]
    assert 'periodo_id' in item and 'periodo_nombre' in item
```

(The first test's intentional wrong `/preview/` path documents the 404 guard; the executor corrects it to `/api/boletas/preview/<id>` before running — the normative assertion is the second test.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_boletas_filtro.py -v` (workdir `backend/`)
Expected: FAIL — preview items lack `periodo_id`/`periodo_nombre` keys.

- [ ] **Step 3: Write minimal implementation**

In `backend/routes/boletas.py`, replace the `_alcance_periodo` body with the direct-column version (name and return shape unchanged):

```python
def _alcance_periodo(periodo_id):
    """Resuelve (alumno_ids, materia_ids) visibles para un período (slice 2).

    Usa la columna directa Calificacion.periodo_id. Las calificaciones
    legacy con periodo_id NULL solo aparecen bajo "Todos".
    """
    rows = (db.session.query(Calificacion.alumno_id, Calificacion.materia_id)
            .filter(Calificacion.periodo_id == periodo_id,
                    Calificacion.calificacion_final > 0).all())
    return {r[0] for r in rows}, {r[1] for r in rows}
```

In `vista_previa_boleta`, extend each item:

```python
        calif_list.append({
            'materia': c.materia.nombre if c.materia else 'N/A',
            'calificacion': c.calificacion_final,
            'periodo': c.periodo,
            'anio': c.anio,
            'periodo_id': c.periodo_id,
            'periodo_nombre': c.periodo_obj.nombre if c.periodo_obj else 'Sin periodo',
        })
```

Fix the preview item shape only; the appended tests already use the correct `/api/boletas/preview/<id>` path.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_boletas_filtro.py tests/test_calificacion_periodo.py -v` (workdir `backend/`)
Expected: PASS (all pass, slice-1 filter cases still green on the new body).

- [ ] **Step 5: Commit**

```bash
git add backend/routes/boletas.py backend/tests/test_boletas_filtro.py
git commit -m "feat: filter boletas by direct periodo column"
```

### Slice 2 exit gate

- `pytest tests/ -v` (workdir `backend/`) — all green.
- `npm test` (workdir `frontend/`) — all green (no frontend changes in slice 2; the Task 9 suite guards the unchanged download behavior).
- `flask --app app.py db upgrade` / `flask --app app.py db downgrade -1` / `flask --app app.py db upgrade` (workdir `backend/`) — clean round-trip incl. backfill idempotence.

---

## Self-review

1. **Spec coverage:** §3.1 table+seed+unique → Tasks 1-2; §3.2 `Asignacion.periodo_id` nullable+mandatory-via-API, no backfill, fechas kept → Tasks 1-2, 4; §3.3 seed incl. `"Enero-Abril {year}"`/`"Regular"`/`"Sin periodo"`(inactive, never assigned) → Task 2; §3.4 nullable column, inheritance-only, legacy strings kept, exact-match backfill, NULL raros → Tasks 10-11; §4.1 CRUD roles/sort/422/409/logical-delete → Task 3; §4.2 POST 422/PUT edit incl. inactive+null-clear/GET keys → Task 4; §4.3 `?periodo_id` list-only, full-history download, generator rescue+`python-docx`+200-DOCX test → Tasks 5-6, 12; §5.1 dropdowns/table/client block → Task 8; §5.2 selector/empty-state/download-untouched → Task 9; §6 TDD order+pytest/vitest/migration round-trips → every task + both exit gates; §7 open questions defaulted (writes `@admin_required`; `Calificacion.periodo_id` stays nullable) and §1 out-of-scope items (`Grupo.periodo/anio`, enums, per-period docs, auth changes) never appear as work. No gaps found.
2. **Placeholder scan:** no `TBD`/`TODO`/`"similar to Task N"`/bare `"handle edge cases"` — every code step ships copy-pasteable bodies; cross-task names frozen (`Periodo.to_dict`, `_alcance_periodo`, `_periodo_id_para_nota`, `generar_boleta`, `PERIODOS_SEED`, exact error strings).
3. **Type consistency:** `periodo_id: int | None` and `periodo_nombre: str` spelled identically in models, all three route files, both migrations, all API clients, both pages, and every test; `422` used for all missing/invalid period values vs `400` for malformed payloads; the Task 6→12 helper swap preserves name and `(set, set)` shape so Task 9 frontend needs no change.
