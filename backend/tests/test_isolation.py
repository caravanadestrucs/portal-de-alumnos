"""
Phase 2 Scoping Sweep — Tenant isolation + bulk + imports sede alias.
Strict TDD RED file — all tests must FAIL until scoping exists, then GREEN.

Covers tasks 2.1-2.5:
- alumnos scoped (list/create/update/delete/transfer) + PATCH sede general-only
- grupos/profesores/asignaciones/admins/carreras/materias scoping
- calificaciones/pagos/boletas/export via Alumno join
- bulk send-credentials per-id 403 for sede_admin, bypass for general_admin
- imports sede alias [sede, sede_codigo, campus], preview warns, execute 400/403
"""
import io
import os
import csv
import pytest

os.environ["FLASK_ENV"] = "testing"

from flask_jwt_extended import create_access_token

from app import create_app
from config import TestingConfig
from models import db, Admin, Alumno, Carrera, Materia, Grupo, Profesor, Sede, Calificacion, NotaRemision


@pytest.fixture
def app_ctx():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # carrera base
        carrera = Carrera(nombre="Test Carr", codigo="TST001", descripcion="test")
        db.session.add(carrera)
        db.session.flush()
        # sedes
        teo = Sede(nombre="Teotitlan", codigo="TEO", direccion="Calle TEO", activa=True)
        hua = Sede(nombre="Huautla", codigo="HUA", direccion="Calle HUA", activa=True)
        db.session.add_all([teo, hua])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def _admin_token(app_ctx, role, sede_id, admin_id=1):
    claims = {"id": admin_id, "type": "admin", "role": role, "sede_id": sede_id, "user_type": "admin"}
    with app_ctx.test_request_context():
        token = create_access_token(identity=str(admin_id), additional_claims=claims)
    return token


def _seed_admins(app_ctx):
    teo = Sede.query.filter_by(codigo="TEO").first()
    hua = Sede.query.filter_by(codigo="HUA").first()
    carrera = Carrera.query.first()
    # create Admin rows for DB fallback (also needed for create general check)
    gen = Admin(username="gen", email="gen@test.com", nombre="General", role="general_admin", sede_id=None)
    gen.set_password("secret123")
    sede_teo_admin = Admin(username="sede_teo", email="sede_teo@test.com", nombre="Sede TEO", role="sede_admin", sede_id=teo.id)
    sede_teo_admin.set_password("secret123")
    sede_hua_admin = Admin(username="sede_hua", email="sede_hua@test.com", nombre="Sede HUA", role="sede_admin", sede_id=hua.id)
    sede_hua_admin.set_password("secret123")
    db.session.add_all([gen, sede_teo_admin, sede_hua_admin])
    db.session.commit()
    # tokens with matching ids
    gen_token = _admin_token(app_ctx, "general_admin", None, admin_id=gen.id)
    teo_token = _admin_token(app_ctx, "sede_admin", teo.id, admin_id=sede_teo_admin.id)
    hua_token = _admin_token(app_ctx, "sede_admin", hua.id, admin_id=sede_hua_admin.id)
    return {
        "gen": gen, "teo_admin": sede_teo_admin, "hua_admin": sede_hua_admin,
        "gen_token": gen_token, "teo_token": teo_token, "hua_token": hua_token,
        "teo_sede": teo, "hua_sede": hua, "carrera": carrera
    }


def _create_alumno(carrera, sede_id, nc_suffix, email_prefix):
    a = Alumno(
        numero_control=f"9000{nc_suffix}",
        nombre="Alumno",
        apellido_paterno=email_prefix,
        email=f"{email_prefix.lower()}@test.com",
        password_hash="x",
        carrera_id=carrera.id,
        sede_id=sede_id,
        activo=True,
    )
    a.set_password("pass123")
    db.session.add(a)
    db.session.commit()
    return a


# ============================================================
# 2.1 alumnos scoped + PATCH sede
# ============================================================

def test_alumnos_list_isolation_sede_admin_sees_only_own(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0001", "A_TEO")
    _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0002", "B_HUA")
    _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0003", "C_TEO2")
    # TEO admin should see 2
    resp = client.get("/api/alumnos", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json()
    alumnos = data.get("alumnos", [])
    assert len(alumnos) == 2, f"TEO admin must see 2, got {len(alumnos)} with {alumnos}"
    assert all(a["sede_id"] == ctx["teo_sede"].id for a in alumnos)
    # HUA sees 1
    resp2 = client.get("/api/alumnos", headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2["alumnos"]) == 1
    assert data2["alumnos"][0]["sede_id"] == ctx["hua_sede"].id


def test_alumnos_list_general_bypass_and_sede_filter(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0011", "G_TEO")
    _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0012", "G_HUA")
    # general sees all 2
    resp = client.get("/api/alumnos", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 2
    # general with ?sede_id=TEO sees 1
    resp2 = client.get(f"/api/alumnos?sede_id={ctx['teo_sede'].id}", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp2.status_code == 200
    assert resp2.get_json()["total"] == 1
    assert resp2.get_json()["alumnos"][0]["sede_id"] == ctx["teo_sede"].id
    # triangulate: HUA filter
    resp3 = client.get(f"/api/alumnos?sede_id={ctx['hua_sede'].id}", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 200
    assert resp3.get_json()["total"] == 1


def test_alumnos_get_cross_sede_403(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0021", "CROSS_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0022", "CROSS_HUA")
    # TEO admin can get TEO
    resp = client.get(f"/api/alumnos/{a_teo.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 200
    # TEO admin trying to get HUA -> 403
    resp2 = client.get(f"/api/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 403, f"expected 403 cross-sede, got {resp2.status_code} {resp2.get_data(as_text=True)}"
    # general can get both
    resp3 = client.get(f"/api/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 200


def test_alumnos_create_requires_sede_id_and_enforces_scope(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # sede_admin without sede_id -> 400
    payload_no_sede = {
        "numero_control": "91000001",
        "nombre": "SinSede",
        "apellido_paterno": "Test",
        "email": "sinsede@test.com",
        "password": "pass123",
        "carrera_id": ctx["carrera"].id,
    }
    resp = client.post("/api/alumnos", json=payload_no_sede, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 400, f"missing sede_id should be 400, got {resp.status_code} {resp.get_data(as_text=True)}"
    # sede_admin with other sede -> 403 (or 400)
    payload_cross = {
        "numero_control": "91000002",
        "nombre": "CrossSede",
        "apellido_paterno": "Test",
        "email": "cross@test.com",
        "password": "pass123",
        "carrera_id": ctx["carrera"].id,
        "sede_id": ctx["hua_sede"].id,
    }
    resp2 = client.post("/api/alumnos", json=payload_cross, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code in (400, 403), f"cross-sede create should be 403/400, got {resp2.status_code}"
    # sede_admin with own sede -> 201
    payload_own = {
        "numero_control": "91000003",
        "nombre": "OwnSede",
        "apellido_paterno": "Test",
        "email": "own@test.com",
        "password": "pass123",
        "carrera_id": ctx["carrera"].id,
        "sede_id": ctx["teo_sede"].id,
    }
    resp3 = client.post("/api/alumnos", json=payload_own, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp3.status_code == 201, f"own sede create should be 201, got {resp3.status_code} {resp3.get_data(as_text=True)}"
    assert resp3.get_json()["alumno"]["sede_id"] == ctx["teo_sede"].id
    # general_admin can create in any sede
    payload_gen_hua = {
        "numero_control": "91000004",
        "nombre": "GenHUA",
        "apellido_paterno": "Test",
        "email": "genhua@test.com",
        "password": "pass123",
        "carrera_id": ctx["carrera"].id,
        "sede_id": ctx["hua_sede"].id,
    }
    resp4 = client.post("/api/alumnos", json=payload_gen_hua, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp4.status_code == 201


def test_alumnos_update_scoped_403_and_transfer_patch(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0031", "UP_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0032", "UP_HUA")
    # TEO admin can update TEO
    resp = client.put(f"/api/alumnos/{a_teo.id}", json={"nombre": "Updated"}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 200
    # TEO admin cannot update HUA -> 403
    resp2 = client.put(f"/api/alumnos/{a_hua.id}", json={"nombre": "Hacked"}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 403
    # general can update HUA
    resp3 = client.put(f"/api/alumnos/{a_hua.id}", json={"nombre": "GenUpdated"}, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 200
    # transfer via PATCH sede — general only
    # TEO admin trying to transfer should be 403
    resp4 = client.patch(f"/api/alumnos/{a_teo.id}/sede", json={"sede_id": ctx["hua_sede"].id}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp4.status_code == 403, f"transfer by sede_admin should be 403, got {resp4.status_code}"
    # general transfer succeeds and is visible to HUA admin afterwards
    resp5 = client.patch(f"/api/alumnos/{a_teo.id}/sede", json={"sede_id": ctx["hua_sede"].id}, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp5.status_code == 200, f"general transfer failed: {resp5.status_code} {resp5.get_data(as_text=True)}"
    assert resp5.get_json()["alumno"]["sede_id"] == ctx["hua_sede"].id
    # now HUA admin should see it
    resp6 = client.get(f"/api/alumnos/{a_teo.id}", headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert resp6.status_code == 200
    # and TEO admin should now get 403 for it
    resp7 = client.get(f"/api/alumnos/{a_teo.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp7.status_code == 403


def test_alumnos_delete_scoped(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0041", "DEL_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0042", "DEL_HUA")
    # TEO admin cannot delete HUA -> 403
    resp = client.delete(f"/api/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 403
    # TEO can delete own
    resp2 = client.delete(f"/api/alumnos/{a_teo.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 200
    # general can delete HUA
    resp3 = client.delete(f"/api/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 200


# ============================================================
# 2.2 grupos / profesores / asignaciones / admins / carreras / materias
# ============================================================

def test_grupos_scoping(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # create grupos per sede via API (need sede_id)
    # TEO admin create TEO grupo should succeed
    payload_teo = {"nombre": "GrupoTEO", "carrera_id": ctx["carrera"].id, "sede_id": ctx["teo_sede"].id}
    resp = client.post("/api/grupos", json=payload_teo, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 201, f"TEO create failed {resp.status_code} {resp.get_data(as_text=True)}"
    grupo_teo_id = resp.get_json()["grupo"]["id"]
    # HUA admin create HUA
    payload_hua = {"nombre": "GrupoHUA", "carrera_id": ctx["carrera"].id, "sede_id": ctx["hua_sede"].id}
    resp2 = client.post("/api/grupos", json=payload_hua, headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert resp2.status_code == 201
    grupo_hua_id = resp2.get_json()["grupo"]["id"]
    # TEO admin list should only see TEO
    resp3 = client.get("/api/grupos", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp3.status_code == 200
    grupos = resp3.get_json()["grupos"]
    assert len(grupos) == 1
    assert grupos[0]["id"] == grupo_teo_id
    # general sees both or filtered
    resp4 = client.get("/api/grupos", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp4.status_code == 200
    assert resp4.get_json()["total"] == 2
    # TEO trying to GET HUA grupo -> 403
    resp5 = client.get(f"/api/grupos/{grupo_hua_id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp5.status_code == 403
    # update cross-sede 403
    resp6 = client.put(f"/api/grupos/{grupo_hua_id}", json={"nombre": "Hacked"}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp6.status_code == 403
    # create without sede_id -> 400 for sede_admin
    resp7 = client.post("/api/grupos", json={"nombre": "NoSede", "carrera_id": ctx["carrera"].id}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp7.status_code == 400
    # triangulate: HUA sees only HUA
    resp8 = client.get("/api/grupos", headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert len(resp8.get_json()["grupos"]) == 1
    assert resp8.get_json()["grupos"][0]["id"] == grupo_hua_id


def test_grupos_integrantes_scoped(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # create alumnos per sede
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0051", "GIN_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0052", "GIN_HUA")
    # create grupo TEO
    payload = {"nombre": "GIntegrantes", "carrera_id": ctx["carrera"].id, "sede_id": ctx["teo_sede"].id}
    resp = client.post("/api/grupos", json=payload, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 201
    gid = resp.get_json()["grupo"]["id"]
    # TEO admin adding TEO alumno -> 201
    resp2 = client.post(f"/api/grupos/{gid}/integrantes", json={"alumno_id": a_teo.id}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 201
    # TEO admin adding HUA alumno -> 403 (cross-sede)
    resp3 = client.post(f"/api/grupos/{gid}/integrantes", json={"alumno_id": a_hua.id}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp3.status_code == 403, f"cross-sede integrante should be 403 got {resp3.status_code}"
    # general can add HUA to TEO grupo (bypass)
    resp4 = client.post(f"/api/grupos/{gid}/integrantes", json={"alumno_id": a_hua.id}, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    # if design restricts mixing, it may still be 201 for general; accept either 201 or 403 but general should be allowed per spec bypass
    assert resp4.status_code == 201, f"general should bypass integrante scoping {resp4.status_code}"


def test_profesores_scoping(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # create profesor TEO via API
    payload_teo = {"numero_empleado": "PROFTEO01", "nombre": "Prof", "apellido_paterno": "TEO", "email": "profteo@test.com", "password": "pass123", "sede_id": ctx["teo_sede"].id}
    resp = client.post("/api/profesores", json=payload_teo, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 201, resp.get_data(as_text=True)
    # HUA profesor
    payload_hua = {"numero_empleado": "PROFHUA01", "nombre": "Prof", "apellido_paterno": "HUA", "email": "profhua@test.com", "password": "pass123", "sede_id": ctx["hua_sede"].id}
    resp2 = client.post("/api/profesores", json=payload_hua, headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert resp2.status_code == 201
    # TEO list sees only TEO
    resp3 = client.get("/api/profesores", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp3.status_code == 200
    profs = resp3.get_json()["profesores"]
    assert len(profs) == 1
    assert profs[0]["sede_id"] == ctx["teo_sede"].id
    # cross get 403
    # find HUA id
    resp_hua_list = client.get("/api/profesores", headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    hua_id = resp_hua_list.get_json()["profesores"][0]["id"]
    teo_id = profs[0]["id"]
    resp_cross = client.get(f"/api/profesores/{hua_id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp_cross.status_code == 403
    # general sees both
    resp_gen = client.get("/api/profesores", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp_gen.get_json()["total"] == 2
    # create without sede_id -> 400 for sede_admin
    resp_nosede = client.post("/api/profesores", json={"numero_empleado": "PROFTEO02", "nombre": "NoSede", "apellido_paterno": "X", "email": "nosedeprof@test.com", "password": "pass123"}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp_nosede.status_code == 400


def test_asignaciones_scoping(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # create profesores per sede
    p_teo = Profesor(numero_empleado="AS_TEO01", nombre="AsTEO", apellido_paterno="P", email="as_teo@test.com", password_hash="x", sede_id=ctx["teo_sede"].id, activo=True)
    p_teo.set_password("pass123")
    p_hua = Profesor(numero_empleado="AS_HUA01", nombre="AsHUA", apellido_paterno="P", email="as_hua@test.com", password_hash="x", sede_id=ctx["hua_sede"].id, activo=True)
    p_hua.set_password("pass123")
    db.session.add_all([p_teo, p_hua])
    db.session.commit()
    # create materias (shared)
    m = Materia(nombre="Mat1", codigo="MAT01", carrera_id=ctx["carrera"].id, creditos=4)
    db.session.add(m)
    db.session.commit()
    # create grupos per sede
    g_teo = Grupo(nombre="AsGTEO", carrera_id=ctx["carrera"].id, sede_id=ctx["teo_sede"].id)
    g_hua = Grupo(nombre="AsGHUA", carrera_id=ctx["carrera"].id, sede_id=ctx["hua_sede"].id)
    db.session.add_all([g_teo, g_hua])
    db.session.commit()
    # create asignacion TEO (via API, need sede_admin TEO)
    payload_teo = {"profesor_id": p_teo.id, "materia_id": m.id, "grupo_id": g_teo.id, "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}
    resp = client.post("/api/asignaciones", json=payload_teo, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 201, resp.get_data(as_text=True)
    as_teo_id = resp.get_json()["asignacion"]["id"]
    # HUA asignacion
    payload_hua = {"profesor_id": p_hua.id, "materia_id": m.id, "grupo_id": g_hua.id, "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}
    resp2 = client.post("/api/asignaciones", json=payload_hua, headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert resp2.status_code == 201
    as_hua_id = resp2.get_json()["asignacion"]["id"]
    # TEO list sees only own (via grupo/profesor sede)
    resp3 = client.get("/api/asignaciones", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp3.status_code == 200
    assert resp3.get_json()["total"] == 1
    assert resp3.get_json()["asignaciones"][0]["id"] == as_teo_id
    # cross get 403
    resp_cross = client.get(f"/api/asignaciones/{as_hua_id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp_cross.status_code == 403
    # general sees both
    resp_gen = client.get("/api/asignaciones", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp_gen.get_json()["total"] == 2
    # triangulate HUA sees only HUA
    resp_hua = client.get("/api/asignaciones", headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert resp_hua.get_json()["total"] == 1


def test_admins_create_verifies_sede(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # general can create sede_admin with sede_id
    payload = {"username": "new_sede", "email": "newsede@test.com", "password": "secret123", "nombre": "New Sede", "role": "sede_admin", "sede_id": ctx["teo_sede"].id}
    resp = client.post("/api/admins/", json=payload, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp.status_code == 201, resp.get_data(as_text=True)
    # sede_admin cannot create admin -> 403
    payload2 = {"username": "hack", "email": "hack@test.com", "password": "secret123", "nombre": "Hack", "role": "sede_admin", "sede_id": ctx["teo_sede"].id}
    resp2 = client.post("/api/admins/", json=payload2, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 403
    # general creating sede_admin without sede_id -> 400
    payload3 = {"username": "bad_sede", "email": "badsede@test.com", "password": "secret123", "nombre": "Bad", "role": "sede_admin"}
    resp3 = client.post("/api/admins/", json=payload3, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 400
    # general creating general_admin should succeed regardless of sede_id NULL
    payload4 = {"username": "new_gen", "email": "newgen@test.com", "password": "secret123", "nombre": "New Gen", "role": "general_admin"}
    resp4 = client.post("/api/admins/", json=payload4, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp4.status_code == 201
    assert resp4.get_json()["admin"]["role"] == "general_admin"
    assert resp4.get_json()["admin"]["sede_id"] is None


def test_carreras_materias_scoping_shared_or_filtered(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # carreras are shared — both sede_admins should see them
    # create carrera via general
    resp = client.post("/api/carreras", json={"nombre": "Carrera X", "codigo": "CRX01", "descripcion": "test"}, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp.status_code == 201
    # both see it
    resp_teo = client.get("/api/carreras", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp_teo.status_code == 200
    assert any(c["codigo"] == "CRX01" for c in resp_teo.get_json()["carreras"])
    resp_hua = client.get("/api/carreras", headers={"Authorization": f"Bearer {ctx['hua_token']}"})
    assert any(c["codigo"] == "CRX01" for c in resp_hua.get_json()["carreras"])
    # materias shared as well
    m = Materia(nombre="Mat Shared", codigo="MSH01", carrera_id=ctx["carrera"].id)
    db.session.add(m)
    db.session.commit()
    resp_m_teo = client.get("/api/materias", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp_m_teo.status_code == 200
    assert resp_m_teo.get_json()["total"] >= 1


# ============================================================
# 2.3 calificaciones / pagos / boletas / export via Alumno join
# ============================================================

def test_calificaciones_via_alumno_join_scoped(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0061", "CAL_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0062", "CAL_HUA")
    m = Materia(nombre="Math", codigo="MTH01", carrera_id=ctx["carrera"].id)
    db.session.add(m)
    db.session.commit()
    # create calificaciones per alumno
    cal_teo = Calificacion(alumno_id=a_teo.id, materia_id=m.id, calificacion_final=9, periodo="2026-1", anio=2026)
    cal_hua = Calificacion(alumno_id=a_hua.id, materia_id=m.id, calificacion_final=8, periodo="2026-1", anio=2026)
    db.session.add_all([cal_teo, cal_hua])
    db.session.commit()
    # TEO admin can see TEO cal via /api/calificaciones/alumnos/<id>
    resp = client.get(f"/api/calificaciones/alumnos/{a_teo.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 200
    # TEO cannot see HUA cal
    resp2 = client.get(f"/api/calificaciones/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 403, f"cross cal should be 403 got {resp2.status_code}"
    # general can see HUA
    resp3 = client.get(f"/api/calificaciones/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 200
    assert len(resp3.get_json()["calificaciones"]) == 1


def test_pagos_via_alumno_join_scoped(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0071", "PAG_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0072", "PAG_HUA")
    nota_teo = NotaRemision(alumno_id=a_teo.id, concepto="Inscripcion", monto=1000, pagada=False, created_by_id=ctx["gen"].id)
    nota_hua = NotaRemision(alumno_id=a_hua.id, concepto="Inscripcion", monto=1200, pagada=False, created_by_id=ctx["gen"].id)
    db.session.add_all([nota_teo, nota_hua])
    db.session.commit()
    # TEO can see own
    resp = client.get(f"/api/pagos/alumnos/{a_teo.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 200
    # TEO cannot see HUA pagos
    resp2 = client.get(f"/api/pagos/alumnos/{a_hua.id}", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 403
    # general sees both via /todas filtered
    resp3 = client.get(f"/api/pagos/todas", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp3.status_code == 200
    assert resp3.get_json()["total"] == 2
    # TEO sees only own in /todas
    resp4 = client.get(f"/api/pagos/todas", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp4.status_code == 200
    assert resp4.get_json()["total"] == 1


def test_boletas_alumnos_scoped(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0081", "BOL_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0082", "BOL_HUA")
    m = Materia(nombre="BoletaMat", codigo="BLT01", carrera_id=ctx["carrera"].id)
    db.session.add(m)
    db.session.commit()
    cal = Calificacion(alumno_id=a_teo.id, materia_id=m.id, calificacion_final=9, periodo="2026-1", anio=2026)
    db.session.add(cal)
    db.session.commit()
    # TEO boletas/alumnos should only list TEO
    resp = client.get("/api/boletas/alumnos", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 200
    ids = [a["id"] for a in resp.get_json()["alumnos"]]
    assert a_teo.id in ids
    assert a_hua.id not in ids
    # general sees both
    resp2 = client.get("/api/boletas/alumnos", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    ids2 = [a["id"] for a in resp2.get_json()["alumnos"]]
    assert a_teo.id in ids2 and a_hua.id in ids2


def test_export_scoped(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0091", "EXP_TEO")
    _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0092", "EXP_HUA")
    # general json export should contain both
    resp_gen = client.get("/api/export/json", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp_gen.status_code == 200
    j = resp_gen.get_json() if resp_gen.is_json else __import__("json").loads(resp_gen.get_data(as_text=True))
    # may be Response json download; check via json parsing
    assert len(j.get("alumnos", [])) == 2
    # TEO export should contain only TEO (if scoped)
    resp_teo = client.get("/api/export/json", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp_teo.status_code == 200
    j2 = resp_teo.get_json() if resp_teo.is_json else __import__("json").loads(resp_teo.get_data(as_text=True))
    # sede_admin should see only own sede's alumnos
    assert len(j2.get("alumnos", [])) == 1
    assert j2["alumnos"][0]["sede_id"] == ctx["teo_sede"].id


# ============================================================
# 2.3 bulk send-credentials scoping
# ============================================================

def test_bulk_send_credentials_sede_admin_scoped_403(app_ctx, client):
    from unittest.mock import patch
    ctx = _seed_admins(app_ctx)
    a_teo = _create_alumno(ctx["carrera"], ctx["teo_sede"].id, "0101", "BULK_TEO")
    a_hua = _create_alumno(ctx["carrera"], ctx["hua_sede"].id, "0102", "BULK_HUA")
    # TEO admin trying to send to TEO+HUA -> per-id 403 cross-sede?
    # Spec says 403 cross-sede per-id check. Could be 403 overall or 207 with per-id.
    # We assert HUA in results is blocked: either status 403 overall or per-id failed with 403 reason.
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        resp = client.post("/api/alumnos/send-credentials", json={"ids": [a_teo.id, a_hua.id]}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
        # Should be 403 if strictly rejected, or 207/200 with per-id failure where HUA is not sent
        if resp.status_code == 403:
            # direct reject is valid
            assert "error" in resp.get_json() or "code" in resp.get_data(as_text=True).lower()
        else:
            data = resp.get_json()
            # must indicate cross-sede blocked for HUA
            # check that HUA id status is failed with forbidden
            results_by_id = {r["id"]: r for r in data.get("results", [])}
            assert results_by_id.get(a_hua.id, {}).get("status") == "failed", f"hua should be failed {data}"
            # ensure HUA email not sent (second call should not have produced email: we check fallback 403 case)
            # Alternatively, check total - impl should not send to HUA
            assert data.get("enviados", 0) <= 1
    # sede_admin sending only own should succeed 200
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        resp2 = client.post("/api/alumnos/send-credentials", json={"ids": [a_teo.id]}, headers={"Authorization": f"Bearer {ctx['teo_token']}"})
        assert resp2.status_code == 200
        assert resp2.get_json()["enviados"] == 1
    # general can send to both -> 200 both sent
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        resp3 = client.post("/api/alumnos/send-credentials", json={"ids": [a_teo.id, a_hua.id]}, headers={"Authorization": f"Bearer {ctx['gen_token']}"})
        assert resp3.status_code == 200
        assert resp3.get_json()["enviados"] == 2


# ============================================================
# 2.4 imports sede alias + 400 + preview warnings + cross-sede 403
# ============================================================

def _csv_bytes(rows, header):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


def test_imports_sede_alias_preview_and_execute(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # header alias sede should be recognized (also sede_codigo, campus)
    for idx, alias in enumerate(["sede", "sede_codigo", "campus"]):
        header = ["numero_control", "nombre", "apellido_paterno", "email", "carrera", alias]
        nc = f"91110{idx}01"
        rows = [[nc, "Imp", "Test", "imp_alias@test.com", "TST001", "TEO"]]
        # but we need unique email per iteration; adjust
        rows[0][3] = f"imp_{alias}@test.com"
        csv_bytes = _csv_bytes(rows, header)
        data = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes), "test.csv")}
        resp = client.post("/api/imports/preview", data=data, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
        assert resp.status_code == 200, f"preview with alias {alias} failed {resp.status_code} {resp.get_data(as_text=True)}"
        j = resp.get_json()
        # preview should not error and should have importable True (or at least not flag sede missing)
        # check no missing sede warning? Actually present sede should not warn
        assert j.get("total_rows") == 1
        # execute should succeed for general with TEO
        csv_bytes2 = _csv_bytes(rows, header)
        data2 = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes2), "test.csv")}
        resp_exec = client.post("/api/imports/execute", data=data2, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
        assert resp_exec.status_code == 200, f"execute alias {alias} failed {resp_exec.get_data(as_text=True)}"
        j2 = resp_exec.get_json()
        assert j2.get("status") == "success", f"expected success for alias {alias} got {j2}"
        assert j2.get("imported") == 1
        # verify sede assigned
        alumno = Alumno.query.filter_by(email=rows[0][3].lower()).first()
        assert alumno is not None
        assert alumno.sede_id == ctx["teo_sede"].id, f"alias {alias} should set sede_id TEO"


def test_imports_preview_warns_missing_sede(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    header = ["numero_control", "nombre", "apellido_paterno", "email", "carrera"]
    rows = [["91220001", "NoSede", "Test", "nosede_imp@test.com", "TST001"]]
    csv_bytes = _csv_bytes(rows, header)
    data = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes), "test.csv")}
    resp = client.post("/api/imports/preview", data=data, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp.status_code == 200
    j = resp.get_json()
    # preview should warn missing sede (warnings list contains sede)
    warnings = j.get("warnings", [])
    # check warnings mention sede
    assert any("sede" in w.lower() for w in warnings), f"preview should warn missing sede, got {warnings}"
    # also rows_preview should indicate valid? but preview warns not blocks
    assert j.get("total_rows") == 1


def test_imports_execute_rejects_missing_sede_400(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    header = ["numero_control", "nombre", "apellido_paterno", "email", "carrera"]
    rows = [["91230001", "NoSede2", "Test", "nosede2@test.com", "TST001"]]
    csv_bytes = _csv_bytes(rows, header)
    data = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes), "test.csv")}
    resp = client.post("/api/imports/execute", data=data, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    # spec: execute rejects 400 if ambiguous/missing sede for alumnos
    assert resp.status_code == 400, f"execute missing sede should be 400, got {resp.status_code} {resp.get_data(as_text=True)}"
    # also sede_admin should get 400
    csv_bytes2 = _csv_bytes(rows, header)
    data2 = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes2), "test.csv")}
    resp2 = client.post("/api/imports/execute", data=data2, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp2.status_code == 400


def test_imports_cross_sede_403_for_sede_admin(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    # TEO admin trying to import HUA sede should be 403
    header = ["numero_control", "nombre", "apellido_paterno", "email", "carrera", "sede"]
    rows = [["91330001", "Cross", "Test", "cross_imp@test.com", "TST001", "HUA"]]
    csv_bytes = _csv_bytes(rows, header)
    data = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes), "test.csv")}
    resp = client.post("/api/imports/execute", data=data, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['teo_token']}"})
    assert resp.status_code == 403, f"cross-sede import for sede_admin should be 403, got {resp.status_code} {resp.get_data(as_text=True)}"
    # general should succeed
    csv_bytes2 = _csv_bytes(rows, header)
    data2 = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes2), "test.csv")}
    resp2 = client.post("/api/imports/execute", data=data2, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp2.status_code == 200
    assert resp2.get_json().get("status") == "success"


def test_imports_invalid_sede_400(app_ctx, client):
    ctx = _seed_admins(app_ctx)
    header = ["numero_control", "nombre", "apellido_paterno", "email", "carrera", "sede"]
    rows = [["91440001", "BadSede", "Test", "badsede@test.com", "TST001", "UNKNOWN"]]
    csv_bytes = _csv_bytes(rows, header)
    data = {"tipo": "alumnos", "file": (io.BytesIO(csv_bytes), "test.csv")}
    resp = client.post("/api/imports/execute", data=data, content_type="multipart/form-data", headers={"Authorization": f"Bearer {ctx['gen_token']}"})
    assert resp.status_code == 400, f"invalid sede should be 400 got {resp.status_code} {resp.get_data(as_text=True)}"
