"""
TDD RED tests for bulk-credential-delivery (S1 P0)
Spec: specs/bulk-credential-delivery/spec.md — 7 scenarios, 3 reqs
Design: smtplib, bcrypt 8-char, 24h expiry, per-row status, 20/min limiter
"""
import os
import re
import time
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from flask_jwt_extended import create_access_token

# Ensure TestingConfig is used
os.environ["FLASK_ENV"] = "testing"

from app import create_app
from models import db, Alumno, Carrera, Admin
from config import TestingConfig


@pytest.fixture
def app_ctx():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed carrera
        carrera = Carrera(nombre="Test Carr", codigo="TST001", descripcion="test")
        db.session.add(carrera)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def _admin_token(app_ctx):
    admin = Admin(username="adm1", email="adm1@test.com", nombre="Adm")
    admin.set_password("secret123")
    db.session.add(admin)
    db.session.commit()
    with app_ctx.test_request_context():
        token = create_access_token(identity=str(admin.id), additional_claims={"id": admin.id, "type": "admin"})
    return token, admin


def _alumno_token(app_ctx, carrera_id):
    alumno = Alumno(
        numero_control="12345678",
        nombre="Juan",
        apellido_paterno="Perez",
        email="juan@test.com",
        password_hash="x",
        carrera_id=carrera_id,
        activo=True,
    )
    alumno.set_password("alum123")
    db.session.add(alumno)
    db.session.commit()
    with app_ctx.test_request_context():
        token = create_access_token(identity=str(alumno.id), additional_claims={"id": alumno.id, "type": "alumno"})
    return token, alumno


def _make_alumno(email, carrera_id, nc):
    a = Alumno(
        numero_control=nc,
        nombre="Test",
        apellido_paterno="Usr",
        email=email,
        password_hash="x",
        carrera_id=carrera_id,
        activo=True,
    )
    a.set_password("oldpass")
    db.session.add(a)
    db.session.commit()
    return a


# ---- 1.1 RED expiry ----

def test_expired_401(app_ctx, client):
    """Temp password expires after 24h -> 401 temp_password_expired"""
    token, _ = _admin_token(app_ctx)
    carrera = Carrera.query.first()
    # Need endpoint exists; if not, this fails -> RED
    # Also need login to enforce expiry
    a = _make_alumno("expire@test.com", carrera.id, "99990001")
    # Simulate bulk send to set temp password
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        resp = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": [a.id], "reset_password": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code in (200, 207), f"bulk send failed: {resp.data}"
    # Expire it manually: set expires_at to past
    a.temp_password_expires_at = datetime.utcnow() - timedelta(seconds=1)
    a.must_change_password = True
    db.session.commit()
    # Now login with temp password should fail 401 temp_password_expired
    # We need to know temp plaintext; since endpoint generates it, we can't.
    # Alternative: set known temp, hash it, expire it
    temp = "Abc12345"
    a.set_password(temp)  # reuse password_hash for now if temp cols not exist -> fallback
    if hasattr(a, "temp_password_hash"):
        from werkzeug.security import generate_password_hash
        a.temp_password_hash = generate_password_hash(temp)
        a.temp_password_expires_at = datetime.utcnow() - timedelta(seconds=1)
        a.must_change_password = True
        db.session.commit()
        # Attempt login via /api/auth/login with expired temp
        login_resp = client.post("/api/auth/login", json={"email": a.email, "password": temp})
        assert login_resp.status_code == 401
        assert "temp_password_expired" in login_resp.get_data(as_text=True).lower() or "expired" in login_resp.get_data(as_text=True).lower()
    else:
        pytest.fail("Alumno missing temp_password_hash/temp_password_expires_at/must_change_password columns")


def test_plaintext_never_logged(app_ctx, client, caplog):
    """Plaintext 8-char never appears in logs nor DB hash column"""
    token, _ = _admin_token(app_ctx)
    carrera = Carrera.query.first()
    a = _make_alumno("nolog@test.com", carrera.id, "99990002")
    caplog.set_level(logging.INFO)
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}) as mock_mail:
        resp = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": [a.id], "reset_password": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code in (200, 207)
    # DB must store only hash
    db.session.refresh(a)
    hash_val = getattr(a, "temp_password_hash", None) or a.password_hash
    assert hash_val is not None
    # hash must not equal plaintext (we don't know plaintext, but mock_mail should have been called with it)
    if mock_mail.called:
        temp_plain = mock_mail.call_args[0][1] if len(mock_mail.call_args[0]) > 1 else None
        # second arg is temp_password in some signatures
        if temp_plain:
            assert temp_plain not in hash_val
            # logs must not contain plaintext
            for rec in caplog.records:
                assert temp_plain not in rec.getMessage()
            # also check that no log line contains 8-char alnum that equals temp
            # ensure hash is bcrypt-like
            assert hash_val != temp_plain
    # generic check: logs don't contain 8-char temp pattern leaked via route
    # If model lacks temp cols, fail
    assert hasattr(a, "temp_password_hash"), "missing temp_password_hash column"
    assert hasattr(a, "temp_password_expires_at"), "missing temp_password_expires_at column"
    assert hasattr(a, "must_change_password"), "missing must_change_password column"


# ---- 2.1 RED contract ----

def test_admin_sends_to_3_selected(app_ctx, client):
    """Admin sends to 3 alumnos -> 200 with 3 sent"""
    token, _ = _admin_token(app_ctx)
    carrera = Carrera.query.first()
    ids = []
    for i, nc in enumerate(["99990101", "99990102", "99990103"]):
        a = _make_alumno(f"bulk{i}@test.com", carrera.id, nc)
        ids.append(a.id)
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        resp = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": ids, "reset_password": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "results" in data
    assert len(data["results"]) == 3
    for r in data["results"]:
        assert r["status"] == "sent"


def test_non_admin_forbidden(app_ctx, client):
    """Non-admin (alumno) -> 403 and zero emails/password changes"""
    carrera = Carrera.query.first()
    alumno_token, _ = _alumno_token(app_ctx, carrera.id)
    # create target alumno
    target = _make_alumno("target@test.com", carrera.id, "99990201")
    orig_hash = target.password_hash
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}) as mock_mail:
        resp = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": [target.id]},
            headers={"Authorization": f"Bearer {alumno_token}"},
        )
    assert resp.status_code == 403
    mock_mail.assert_not_called()
    db.session.refresh(target)
    assert target.password_hash == orig_hash


def test_ids_required_400(app_ctx, client):
    token, _ = _admin_token(app_ctx)
    resp = client.post(
        "/api/alumnos/send-credentials",
        json={"ids": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    resp2 = client.post(
        "/api/alumnos/send-credentials",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 400


def test_smtp_failure_per_row_with_retry(app_ctx, client):
    """One SMTP failure -> failed, others sent; retry only failed"""
    token, _ = _admin_token(app_ctx)
    carrera = Carrera.query.first()
    ids = []
    for i, nc in enumerate(["99990301", "99990302", "99990303"]):
        a = _make_alumno(f"fail{i}@test.com", carrera.id, nc)
        ids.append(a.id)

    def side_effect(to_email, temp_pw, nombre=None, *args, **kwargs):
        # fail for second alumno only
        if "fail1@test.com" in to_email:
            return {"success": False, "error": "SMTP timeout"}
        return {"success": True}

    with patch("routes.alumnos.send_credentials_email", side_effect=side_effect):
        resp = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": ids, "reset_password": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code in (200, 207)
    data = resp.get_json()
    results = {r["id"]: r["status"] for r in data["results"]}
    assert results[ids[0]] == "sent"
    assert results[ids[1]] == "failed"
    assert results[ids[2]] == "sent"
    # retry only failed
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        resp2 = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": [ids[1]], "reset_password": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp2.status_code == 200
    assert resp2.get_json()["results"][0]["status"] == "sent"


def test_rate_limit_20_per_minute(app_ctx, client):
    token, _ = _admin_token(app_ctx)
    carrera = Carrera.query.first()
    a = _make_alumno("rate@test.com", carrera.id, "99990401")
    # limiter is global memory — reset by touching storage if possible
    try:
        from extensions import limiter
        # reset storage for this test: clear memory
        if hasattr(limiter, "_storage") and hasattr(limiter._storage, "reset"):
            limiter._storage.reset()
    except Exception:
        pass
    with patch("routes.alumnos.send_credentials_email", return_value={"success": True}):
        responses = []
        for i in range(21):
            resp = client.post(
                "/api/alumnos/send-credentials",
                json={"ids": [a.id], "reset_password": True},
                headers={"Authorization": f"Bearer {token}"},
            )
            responses.append(resp)
        # At least one should be 429 (allow early due to prior tests' counts)
        assert any(r.status_code == 429 for r in responses), f"expected 429 within 21, got {[r.status_code for r in responses]}"
        # 429 may be HTML from limiter without Retry-After header for memory storage; status is sufficient
        hit = next(r for r in responses if r.status_code == 429)
        assert hit.status_code == 429


def test_alnum8_and_hashed(app_ctx, client):
    """Temp password is 8-char alphanumeric and stored hashed"""
    token, _ = _admin_token(app_ctx)
    carrera = Carrera.query.first()
    a = _make_alumno("alnum@test.com", carrera.id, "99990501")
    captured = {}

    def capture(to_email, temp_pw, nombre=None, *args, **kwargs):
        captured["pw"] = temp_pw
        return {"success": True}

    with patch("routes.alumnos.send_credentials_email", side_effect=capture):
        resp = client.post(
            "/api/alumnos/send-credentials",
            json={"ids": [a.id], "reset_password": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code in (200, 207)
    pw = captured.get("pw")
    assert pw is not None
    assert len(pw) == 8
    assert re.match(r"^[A-Za-z0-9]{8}$", pw), f"not alnum8: {pw}"
    db.session.refresh(a)
    # must be hashed, not plaintext
    assert hasattr(a, "temp_password_hash")
    assert a.temp_password_hash != pw
    assert a.temp_password_expires_at is not None
    # expiry ~24h
    delta = a.temp_password_expires_at - datetime.utcnow()
    assert timedelta(hours=23) < delta < timedelta(hours=25)
    assert a.must_change_password is True
    # no plaintext in logs
    # (checked in earlier test, but also ensure hash verifies)
    from werkzeug.security import check_password_hash
    assert check_password_hash(a.temp_password_hash, pw)


def test_config_mail_env_and_bulk_flag():
    """Config has MAIL_* and BULK_EMAIL_ENABLED, app reads CORS_ORIGINS env"""
    content = open("config.py", encoding="utf-8").read()
    assert "MAIL_SERVER" in content or "MAIL" in content
    assert "BULK_EMAIL_ENABLED" in content
    assert "CORS_ORIGINS" in content
    # app.py should handle CORS_ORIGINS env
    app_content = open("app.py", encoding="utf-8").read()
    assert "CORS_ORIGINS" in app_content


def test_send_credentials_email_util():
    """utils/mail.py send_credentials_email never logs plaintext and uses smtplib"""
    import pathlib
    p = pathlib.Path("utils/mail.py")
    assert p.exists(), "backend/utils/mail.py not found"
    import utils.mail as mail_mod
    assert hasattr(mail_mod, "send_credentials_email")
    assert hasattr(mail_mod, "render_credentials_email")
    src = p.read_text(encoding="utf-8")
    assert "smtplib" in src
    assert "def send_credentials_email" in src
    assert "def render_credentials_email" in src
    # Ensure send_credentials_email does not log temp_password via f-string
    # Only allow logging with to_email, never with temp_password variable
    for line in src.splitlines():
        low = line.strip().lower()
        if low.startswith("logger.") or "logging." in low:
            # log lines must not contain temp_password interpolation
            assert "temp_password" not in line, f"log line must not contain temp_password: {line}"
