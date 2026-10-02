import os
os.environ["FLASK_ENV"] = "testing"
from app import create_app
from config import TestingConfig
from models import db, Profesor, Sede, Carrera

def test_profesor_sede_not_null_and_indexed():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        assert Profesor.__table__.c.sede_id.nullable is False
        idx_cols = [c.name for ix in Profesor.__table__.indexes for c in ix.columns]
        assert "sede_id" in idx_cols
        fk_names = [fk.name for fk in Profesor.__table__.foreign_keys]
        assert "fk_profesor_sede" in fk_names
        db.session.remove()
        db.drop_all()


def test_migration_006_chain_and_index_contract():
    """006 must chain onto 005 head and carry the binding index/FK names."""
    import pathlib
    import re
    versions = pathlib.Path(__file__).resolve().parents[1] / "migrations" / "versions"
    f005 = versions / "005_calificacion_periodo_slice2.py"
    f006 = versions / "006_profesor_sede_not_null_quarantine.py"
    assert f006.exists(), "006_profesor_sede_not_null_quarantine.py missing"
    head_rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", f005.read_text(encoding="utf-8"), re.M).group(1)
    content = f006.read_text(encoding="utf-8")
    down_rev = re.search(r"^down_revision\s*=\s*['\"]([^'\"]+)['\"]", content, re.M).group(1)
    assert down_rev == head_rev, f"006 down_revision {down_rev!r} != 005 head {head_rev!r}"
    assert "batch_alter_table" in content
    assert "create_index('ix_profesor_sede_id'" in content or 'create_index("ix_profesor_sede_id"' in content
    assert "fk_profesor_sede" in content
    assert "COUNT(DISTINCT" in content  # unambiguous-only backfill guard
