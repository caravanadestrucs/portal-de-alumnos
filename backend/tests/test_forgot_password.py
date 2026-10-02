"""
Tests para forgot-password: verificación de existencia del email.

Comportamiento (decisión del dueño del sistema):
- Email NO registrado -> 404 con mensaje "Correo no encontrado..."
- Email registrado    -> 200 con mensaje de envío (el SMTP puede no estar
                         configurado en tests; la ruta responde 200 igual)
"""
import os
from unittest.mock import patch

import pytest

os.environ["FLASK_ENV"] = "testing"

from app import create_app
from models import db, Alumno, Carrera, Sede
from config import TestingConfig


@pytest.fixture
def app_ctx():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        carrera = Carrera(nombre="Test Carr", codigo="TST001", descripcion="test")
        db.session.add(carrera)
        db.session.flush()
        teo = Sede(nombre="Teotitlan", codigo="TEO", direccion="Teotitlan", activa=True)
        db.session.add(teo)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def test_email_inexistente_devuelve_404(client):
    resp = client.post("/api/auth/forgot-password", json={"email": "nadie@example.com"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"]
    assert "no encontrado" in data["error"].lower()


def test_email_inexistente_menciona_contactar_admin(client):
    resp = client.post("/api/auth/forgot-password", json={"email": "nadie@example.com"})
    data = resp.get_json()
    assert "administrador" in data["error"].lower()


def test_email_registrado_devuelve_200(client, app_ctx):
    from models import Alumno
    a = Alumno(
        numero_control="NC0001",
        nombre="Ana",
        apellido_paterno="Prueba",
        email="ana@test.com",
        carrera_id=1,
        sede_id=1,
        activo=True,
    )
    a.set_password("secret123")
    db.session.add(a)
    db.session.commit()

    with patch("routes.auth.send_email", return_value={"success": True}) as mock_send:
        resp = client.post("/api/auth/forgot-password", json={"email": "ANA@test.com"})
        assert resp.status_code == 200
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        assert args[0] == "ana@test.com"
        # el body HTML debe contener el link con el token
        assert "reset-password?token=" in args[2]


def test_email_registrado_con_smtp_fallido_sigue_200(client, app_ctx):
    from models import Alumno
    a = Alumno(
        numero_control="NC0002",
        nombre="Luis",
        apellido_paterno="Prueba",
        email="luis@test.com",
        carrera_id=1,
        sede_id=1,
        activo=True,
    )
    a.set_password("secret123")
    db.session.add(a)
    db.session.commit()

    with patch("routes.auth.send_email", return_value={"success": False, "error": "SMTP down"}):
        resp = client.post("/api/auth/forgot-password", json={"email": "luis@test.com"})
        assert resp.status_code == 200


def test_email_invalido_devuelve_400(client):
    resp = client.post("/api/auth/forgot-password", json={"email": "no-es-un-email"})
    assert resp.status_code == 400


def test_email_vacio_devuelve_400(client):
    resp = client.post("/api/auth/forgot-password", json={"email": ""})
    assert resp.status_code == 400