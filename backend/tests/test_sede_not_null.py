"""
Post-archive hardening: migration 003 makes sede_id NOT NULL.

Verifies:
- migration file exists in backend/migrations/versions and migrations/versions
- PRAGMA table_info shows notnull=1 for alumnos.sede_id and grupos.sede_id
- INSERT without sede_id fails (IntegrityError) both via ORM and raw pragma
- INSERT with valid sede_id succeeds
"""
import os
import pathlib
import pytest

os.environ["FLASK_ENV"] = "testing"

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import create_app
from config import TestingConfig
from models import db, Alumno, Carrera, Grupo, Sede


@pytest.fixture
def app_ctx():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed required FKs: carrera and sedes
        carrera = Carrera(nombre="Test Carr NOTNULL", codigo="TSTNOTNULL", descripcion="for not null test")
        db.session.add(carrera)
        db.session.flush()
        teo = Sede(nombre="Teotitlan", codigo="TEO", direccion="Teotitlan", activa=True)
        hua = Sede(nombre="Huautla", codigo="HUA", direccion="Huautla", activa=True)
        db.session.add_all([teo, hua])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


def _find_migration():
    # Try both locations
    candidates = [
        pathlib.Path(__file__).resolve().parents[1] / "migrations" / "versions" / "003_make_sede_not_null.py",
        pathlib.Path(__file__).resolve().parents[2] / "migrations" / "versions" / "003_make_sede_not_null.py",
        pathlib.Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions" / "003_make_sede_not_null.py",
        pathlib.Path("backend/migrations/versions/003_make_sede_not_null.py"),
        pathlib.Path("migrations/versions/003_make_sede_not_null.py"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def test_migration_003_exists():
    """Migration 003 must exist in at least one location."""
    m = _find_migration()
    assert m is not None, "003_make_sede_not_null.py not found in backend/migrations/versions or migrations/versions"
    content = m.read_text(encoding="utf-8")
    assert "c3d4e5f6a7b8" in content
    assert "b2c3d4e5f6a7" in content
    assert "alumnos" in content.lower()
    assert "grupos" in content.lower()
    assert "batch_alter" in content
    assert "nullable=False" in content
    # Ensure it handles backfill
    assert "UPDATE" in content and "sede_id" in content


def test_pragma_not_null_via_orm(app_ctx):
    """PRAGMA table_info should report notnull=1 for both alumnos and grupos."""
    for table in ("alumnos", "grupos"):
        rows = db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
        # rows: (cid, name, type, notnull, dflt_value, pk)
        sede_col = [r for r in rows if r[1] == "sede_id"]
        assert len(sede_col) == 1, f"sede_id not found in {table} pragma"
        notnull = sede_col[0][3]
        assert notnull == 1, f"{table}.sede_id should be NOT NULL (pragma notnull=1), got {notnull} rows={rows}"

    # Also verify model metadata reflects NOT NULL
    assert Alumno.__table__.c.sede_id.nullable is False
    assert Grupo.__table__.c.sede_id.nullable is False
    # Profesor should remain nullable (optional)
    from models import Profesor
    assert Profesor.__table__.c.sede_id.nullable is True


def test_insert_alumno_without_sede_fails(app_ctx):
    """INSERT alumno without sede_id must raise IntegrityError."""
    carrera = Carrera.query.first()
    teo = Sede.query.filter_by(codigo="TEO").first()
    assert teo is not None

    # Valid insert should succeed
    good = Alumno(
        numero_control="NOTNULL01",
        nombre="Good",
        apellido_paterno="Test",
        email="good.notnull@test.com",
        password_hash="x",
        carrera_id=carrera.id,
        sede_id=teo.id,
        activo=True,
    )
    good.set_password("pass123")
    db.session.add(good)
    db.session.commit()
    assert good.id is not None
    assert good.sede_id == teo.id

    # Invalid: sede_id=None should fail
    bad = Alumno(
        numero_control="NOTNULL02",
        nombre="Bad",
        apellido_paterno="Test",
        email="bad.notnull@test.com",
        password_hash="x",
        carrera_id=carrera.id,
        sede_id=None,
        activo=True,
    )
    bad.set_password("pass123")
    db.session.add(bad)
    with pytest.raises((IntegrityError, Exception)):
        db.session.commit()
    db.session.rollback()

    # Also verify via raw SQL insert without sede_id fails at DB level
    # Use direct connection to bypass ORM defaults
    with pytest.raises(Exception):
        db.session.execute(
            text("INSERT INTO alumnos (numero_control, nombre, apellido_paterno, email, password_hash, carrera_id, activo) VALUES (:nc, :nom, :ap, :email, :ph, :cid, 1)"),
            {"nc": "RAWFAIL01", "nom": "Raw", "ap": "Fail", "email": "rawfail@test.com", "ph": "x", "cid": carrera.id},
        )
        db.session.commit()
    db.session.rollback()


def test_insert_grupo_without_sede_fails(app_ctx):
    """INSERT grupo without sede_id must raise IntegrityError after migration 003."""
    carrera = Carrera.query.first()
    teo = Sede.query.filter_by(codigo="TEO").first()

    # Valid
    g_ok = Grupo(nombre="GRP_OK", carrera_id=carrera.id, sede_id=teo.id)
    db.session.add(g_ok)
    db.session.commit()
    assert g_ok.sede_id == teo.id

    # Invalid
    g_bad = Grupo(nombre="GRP_BAD", carrera_id=carrera.id, sede_id=None)
    db.session.add(g_bad)
    with pytest.raises((IntegrityError, Exception)):
        db.session.commit()
    db.session.rollback()


def test_file_db_pragma_after_migration():
    """Check the file DB (backend/instance/portal.db) also has NOT NULL after manual migration."""
    import sqlite3
    db_path = pathlib.Path(__file__).resolve().parents[1] / "instance" / "portal.db"
    if not db_path.exists():
        # Try project root backend/instance
        db_path = pathlib.Path(__file__).resolve().parents[2] / "backend" / "instance" / "portal.db"
    if not db_path.exists():
        pytest.skip(f"portal.db not found at {db_path}, skipping file DB check")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    for tbl in ("alumnos", "grupos"):
        cur.execute(f"PRAGMA table_info({tbl})")
        rows = cur.fetchall()
        sede = [r for r in rows if r[1] == "sede_id"]
        assert sede, f"sede_id not found in {tbl}"
        notnull = sede[0][3]
        assert notnull == 1, f"file DB {tbl}.sede_id should be NOT NULL, got {notnull}"
        # Also ensure 0 NULLs remain
        cur.execute(f"SELECT COUNT(*) FROM {tbl} WHERE sede_id IS NULL")
        null_count = cur.fetchone()[0]
        assert null_count == 0, f"{tbl} still has {null_count} NULL sede_id rows after migration"
    # Verify alumnos count still 109 and distributed TEO/HUA via boletas/ (not 109/0)
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT sede_id) FROM alumnos")
    total, distinct = cur.fetchone()
    assert total == 109, f"expected 109 alumnos after migration, got {total}"
    cur.execute("SELECT s.codigo, COUNT(*) FROM alumnos a JOIN sedes s ON a.sede_id=s.id GROUP BY s.codigo")
    rows = cur.fetchall()
    dist = {r[0]: r[1] for r in rows}
    assert sum(dist.values()) == 109, f"sum should be 109, got {dist}"
    assert dist.get("TEO", 0) + dist.get("HUA", 0) == 109
    assert dist.get("TEO", 0) > 0 and dist.get("HUA", 0) > 0, f"both TEO and HUA should have >0, got {dist}"
    # Expected from real boletas/ parsing via UNIDAD field: 56 HUA files / 30 TEO files (86 total)
    # alumnos distribution: 73 HUA / 36 TEO (90 HUA names + 30 TEO names, 109 alumnos, 5 without docx flagged TEO)
    # Previous buggy assignment used folder heuristic (9 huautla paths) -> 79 TEO / 30 HUA reversed; now corrected.
    assert dist.get("HUA") == 73 and dist.get("TEO") == 36, f"expected HUA 73 TEO 36 (UNIDAD truth), got {dist}"
    conn.close()
