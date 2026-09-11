import os
os.environ["FLASK_ENV"] = "testing"
import pytest

from app import create_app
from config import TestingConfig
from models import db


@pytest.fixture
def app_ctx():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def test_login_profesor_jwt_has_sede_and_slug(app_ctx, client):
    from models import db, Sede, Profesor
    sede = Sede(nombre="Teotitlan", codigo="TEO"); db.session.add(sede); db.session.commit()
    p = Profesor(numero_empleado="PROF-SLUG1", nombre="Ana", apellido_paterno="Lopez",
                 email="slug1@test.com", password_hash="x", sede_id=sede.id, activo=True)
    p.set_password("pass123"); db.session.add(p); db.session.commit()
    resp = client.post("/api/auth/login", json={"email": "slug1@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["sede_id"] == sede.id
    from flask_jwt_extended import decode_token
    with app_ctx.test_request_context():
        claims = decode_token(data["access_token"])
    assert claims["sede_id"] == sede.id
    assert claims["sede_slug"] == "TEO"


def test_login_alumno_jwt_has_sede_and_slug(app_ctx, client):
    from models import db, Sede, Carrera, Alumno
    sede = Sede(nombre="Huautla", codigo="HUA"); db.session.add(sede); db.session.commit()
    car = Carrera(nombre="C", codigo="CX-SLUG", descripcion="t"); db.session.add(car); db.session.commit()
    a = Alumno(numero_control="88000002", nombre="Luis", apellido_paterno="Perez",
               email="slug-alumno@test.com", password_hash="x",
               carrera_id=car.id, sede_id=sede.id, activo=True)
    a.set_password("pass123"); db.session.add(a); db.session.commit()
    resp = client.post("/api/auth/login", json={"email": "slug-alumno@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["sede_id"] == sede.id
    assert data["user"]["sede_slug"] == "HUA"
    from flask_jwt_extended import decode_token
    with app_ctx.test_request_context():
        claims = decode_token(data["access_token"])
    assert claims["sede_id"] == sede.id
    assert claims["sede_slug"] == "HUA"


def test_login_admin_jwt_has_sede_slug(app_ctx, client):
    from models import db, Sede, Admin
    from flask_jwt_extended import decode_token
    sede = Sede(nombre="Teotitlan", codigo="TEO"); db.session.add(sede); db.session.commit()
    gen = Admin(username="sluggen", email="sluggen@test.com", nombre="Gen",
                role="general_admin", sede_id=None)
    gen.set_password("pass123"); db.session.add(gen)
    sad = Admin(username="slugsede", email="slugsede@test.com", nombre="Sede",
                role="sede_admin", sede_id=sede.id)
    sad.set_password("pass123"); db.session.add(sad); db.session.commit()
    resp = client.post("/api/auth/login", json={"email": "sluggen@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["sede_id"] is None
    assert data["user"]["sede_slug"] is None
    with app_ctx.test_request_context():
        claims = decode_token(data["access_token"])
    assert claims["role"] == "general_admin"
    assert claims["sede_id"] is None
    assert claims["sede_slug"] is None
    resp2 = client.post("/api/auth/login", json={"email": "slugsede@test.com", "password": "pass123"})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["user"]["sede_id"] == sede.id
    assert data2["user"]["sede_slug"] == "TEO"
    with app_ctx.test_request_context():
        claims2 = decode_token(data2["access_token"])
    assert claims2["role"] == "sede_admin"
    assert claims2["sede_id"] == sede.id
    assert claims2["sede_slug"] == "TEO"


def test_refresh_preserves_sede_slug(app_ctx, client):
    from models import db, Sede, Profesor
    from flask_jwt_extended import decode_token
    sede = Sede(nombre="Teotitlan", codigo="TEO"); db.session.add(sede); db.session.commit()
    p = Profesor(numero_empleado="PROF-SLUG2", nombre="Ana", apellido_paterno="Lopez",
                 email="slug2@test.com", password_hash="x", sede_id=sede.id, activo=True)
    p.set_password("pass123"); db.session.add(p); db.session.commit()
    resp = client.post("/api/auth/login", json={"email": "slug2@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.get_json()
    resp2 = client.post("/api/auth/refresh",
                        headers={"Authorization": f"Bearer {data['refresh_token']}"})
    assert resp2.status_code == 200
    with app_ctx.test_request_context():
        claims = decode_token(resp2.get_json()["access_token"])
    assert claims["sede_id"] == sede.id
    assert claims["sede_slug"] == "TEO"


def _sede_token(app_ctx, adm):
    from flask_jwt_extended import create_access_token
    return create_access_token(identity=str(adm.id),
        additional_claims={"id": adm.id, "type": "admin", "role": "general_admin", "sede_id": None})


def test_assign_profesor_grupo_mismatch_403(app_ctx, client):
    from models import db, Sede, Carrera, Profesor, Grupo, Admin, Materia, Periodo
    teo = Sede(nombre="Teotitlan", codigo="TEO"); hua = Sede(nombre="Huautla", codigo="HUA")
    db.session.add_all([teo, hua]); db.session.commit()
    car = Carrera(nombre="C", codigo="CX2", descripcion="t"); db.session.add(car); db.session.commit()
    p = Profesor(numero_empleado="PROF-MM1", nombre="P", apellido_paterno="X",
                 email="mm1@t.com", password_hash="x", sede_id=teo.id, activo=True)
    p.set_password("pass123"); db.session.add(p)
    g = Grupo(nombre="A", carrera_id=car.id, sede_id=hua.id); db.session.add(g)
    adm = Admin(username="mmg", email="mmg@t.com", nombre="G", role="general_admin", sede_id=None)
    adm.set_password("s3cret!"); db.session.add(adm); db.session.commit()
    tok = _sede_token(app_ctx, adm)
    m = Materia(carrera_id=car.id, nombre="Mat", codigo="MAT1"); db.session.add(m)
    per = Periodo(nombre="P-MM1", activa=True); db.session.add(per); db.session.commit()
    resp = client.post("/api/asignaciones",
        json={"profesor_id": p.id, "materia_id": m.id, "grupo_id": g.id,
              "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31",
              "periodo_id": per.id},
        headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403
    assert resp.get_json()["code"] == "CROSS_SEDE"


def test_assign_same_sede_201_echoes_sedes(app_ctx, client):
    from models import db, Sede, Carrera, Profesor, Grupo, Admin, Materia, Periodo
    teo = Sede(nombre="Teotitlan", codigo="TEO"); db.session.add(teo); db.session.commit()
    car = Carrera(nombre="C", codigo="CX3", descripcion="t"); db.session.add(car); db.session.commit()
    p = Profesor(numero_empleado="PROF-SS1", nombre="P", apellido_paterno="X",
                 email="ss1@t.com", password_hash="x", sede_id=teo.id, activo=True)
    p.set_password("pass123"); db.session.add(p)
    g = Grupo(nombre="A", carrera_id=car.id, sede_id=teo.id); db.session.add(g)
    adm = Admin(username="ssg", email="ssg@t.com", nombre="G", role="general_admin", sede_id=None)
    adm.set_password("s3cret!"); db.session.add(adm); db.session.commit()
    tok = _sede_token(app_ctx, adm)
    m = Materia(carrera_id=car.id, nombre="Mat", codigo="MAT2"); db.session.add(m)
    per = Periodo(nombre="P-SS1", activa=True); db.session.add(per); db.session.commit()
    resp = client.post("/api/asignaciones",
        json={"profesor_id": p.id, "materia_id": m.id, "grupo_id": g.id,
              "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31",
              "periodo_id": per.id},
        headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["profesor_sede_id"] == teo.id
    assert body["grupo_sede_id"] == teo.id


def test_update_asignacion_mismatch_403(app_ctx, client):
    from models import db, Sede, Carrera, Profesor, Grupo, Admin, Materia, Periodo
    teo = Sede(nombre="Teotitlan", codigo="TEO"); hua = Sede(nombre="Huautla", codigo="HUA")
    db.session.add_all([teo, hua]); db.session.commit()
    car = Carrera(nombre="C", codigo="CX4", descripcion="t"); db.session.add(car); db.session.commit()
    p = Profesor(numero_empleado="PROF-UM1", nombre="P", apellido_paterno="X",
                 email="um1@t.com", password_hash="x", sede_id=teo.id, activo=True)
    p.set_password("pass123"); db.session.add(p)
    g_teo = Grupo(nombre="A", carrera_id=car.id, sede_id=teo.id); db.session.add(g_teo)
    g_hua = Grupo(nombre="B", carrera_id=car.id, sede_id=hua.id); db.session.add(g_hua)
    adm = Admin(username="umg", email="umg@t.com", nombre="G", role="general_admin", sede_id=None)
    adm.set_password("s3cret!"); db.session.add(adm); db.session.commit()
    tok = _sede_token(app_ctx, adm)
    m = Materia(carrera_id=car.id, nombre="Mat", codigo="MAT3"); db.session.add(m)
    per = Periodo(nombre="P-UM1", activa=True); db.session.add(per); db.session.commit()
    created = client.post("/api/asignaciones",
        json={"profesor_id": p.id, "materia_id": m.id, "grupo_id": g_teo.id,
              "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31",
              "periodo_id": per.id},
        headers={"Authorization": f"Bearer {tok}"})
    assert created.status_code == 201
    aid = created.get_json()["asignacion"]["id"]
    resp = client.put(f"/api/asignaciones/{aid}", json={"grupo_id": g_hua.id},
        headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403
    assert resp.get_json()["code"] == "CROSS_SEDE"


def test_validate_same_sede_unit():
    from utils.validators import validate_same_sede, SameSedeError
    import pytest as _pytest
    class _O:
        def __init__(self, sede_id): self.sede_id = sede_id
    assert validate_same_sede(_O(1), _O(1)) is True
    with _pytest.raises(SameSedeError):
        validate_same_sede(_O(1), _O(2))
