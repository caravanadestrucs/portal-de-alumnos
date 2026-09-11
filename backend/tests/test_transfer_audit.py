# backend/tests/test_transfer_audit.py
# Task 5 (Slice 1): general-only ?sede_id override is audited + AuditLog + 007.
import os
os.environ["FLASK_ENV"] = "testing"
from app import create_app
from config import TestingConfig
from models import db, Sede, Admin, Carrera, Alumno


def _general_token(gen):
    from flask_jwt_extended import create_access_token
    return create_access_token(
        identity=str(gen.id),
        additional_claims={"id": gen.id, "type": "admin",
                           "role": "general_admin", "sede_id": None})


def _seed_minimal():
    teo = Sede(nombre="Teotitlan", codigo="TEO")
    hua = Sede(nombre="Huautla", codigo="HUA")
    db.session.add_all([teo, hua])
    db.session.commit()
    car = Carrera(nombre="C", codigo="CX1", descripcion="t")
    db.session.add(car)
    db.session.commit()
    gen = Admin(username="g", email="g@t.com", nombre="G",
                role="general_admin", sede_id=None)
    gen.set_password("s3cret!")
    db.session.add(gen)
    db.session.commit()
    return teo, hua, car, gen


def test_general_explicit_sede_id_writes_audit():
    from flask_jwt_extended import create_access_token
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        teo = Sede(nombre="Teotitlan", codigo="TEO"); hua = Sede(nombre="Huautla", codigo="HUA")
        db.session.add_all([teo, hua]); db.session.commit()
        car = Carrera(nombre="C", codigo="CX1", descripcion="t"); db.session.add(car); db.session.commit()
        gen = Admin(username="g", email="g@t.com", nombre="G", role="general_admin", sede_id=None)
        gen.set_password("s3cret!"); db.session.add(gen); db.session.commit()
        tok = create_access_token(identity=str(gen.id),
            additional_claims={"id": gen.id, "type": "admin", "role": "general_admin", "sede_id": None})
        c = app.test_client()
        resp = c.get(f"/api/alumnos?sede_id={hua.id}", headers={"Authorization": f"Bearer {tok}"})
        assert resp.status_code == 200
        from models import AuditLog
        row = AuditLog.query.filter_by(actor_id=gen.id, target_sede_id=hua.id).first()
        assert row is not None and row.method == "GET" and "/api/alumnos" in row.path
        db.session.remove(); db.drop_all()


def test_audit_log_model_contract():
    from models import AuditLog
    assert AuditLog.__tablename__ == "audit_log"
    fk_names = [fk.name for fk in AuditLog.__table__.foreign_keys]
    assert "fk_audit_sede" in fk_names
    assert AuditLog.__table__.c.actor_id.nullable is False
    assert AuditLog.__table__.c.actor_role.nullable is False
    assert AuditLog.__table__.c.method.nullable is False
    assert AuditLog.__table__.c.path.nullable is False
    assert AuditLog.__table__.c.created_at.nullable is False


def test_007_chains_onto_006_and_covers_audit_log_only():
    import pathlib
    import re
    versions = pathlib.Path(__file__).resolve().parents[1] / "migrations" / "versions"
    f006 = versions / "006_profesor_sede_not_null_quarantine.py"
    matches = sorted(versions.glob("007_*.py"))
    assert len(matches) == 1, f"expected exactly one 007 migration, got {[m.name for m in matches]}"
    f007 = matches[0]
    head_rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]",
                         f006.read_text(encoding="utf-8"), re.M).group(1)
    content = f007.read_text(encoding="utf-8")
    down_rev = re.search(r"^down_revision\s*=\s*['\"]([^'\"]+)['\"]",
                         content, re.M).group(1)
    assert down_rev == head_rev, f"007 down_revision {down_rev!r} != 006 head {head_rev!r}"
    assert "audit_log" in content
    assert "fk_audit_sede" in content
    assert content.lower().count("create_table") == 1, "007 must create audit_log ONLY"
    assert "transfer_history" not in content.lower(), "SedeTransferHistory belongs to Task 7, not 007"


def test_general_write_without_sede_returns_400_sede_required():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        teo, hua, car, gen = _seed_minimal()
        c = app.test_client()
        payload = {
            "numero_control": "T5-0001",
            "nombre": "Sin",
            "apellido_paterno": "Sede",
            "email": "sinsede@t5.com",
            "password": "s3cret!",
            "carrera_id": car.id,
        }
        resp = c.post("/api/alumnos", json=payload,
                      headers={"Authorization": f"Bearer {_general_token(gen)}"})
        assert resp.status_code == 400
        assert resp.get_json().get("code") == "SEDE_REQUIRED"
        db.session.remove(); db.drop_all()
