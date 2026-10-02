"""
Tests para la resolución de la URL pública del frontend (links de emails).

Root cause: forgot-password y bulk-credentials construían el link con
os.environ.get('FRONTEND_URL', 'http://localhost:5173'); en producción sin la
variable, los emails apuntaban a localhost. get_frontend_url() centraliza la
resolución: env var -> Config DB (frontend_url) -> default dev.
"""
import os
from unittest.mock import patch

import pytest

os.environ["FLASK_ENV"] = "testing"

from app import create_app
from models import db, Config
from config import TestingConfig
from utils.frontend import get_frontend_url


@pytest.fixture
def app_ctx():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_env_var_gana_sobre_config_db(app_ctx):
    db.session.add(Config(key="frontend_url", value="https://config-db.example.com"))
    db.session.commit()
    with patch.dict(os.environ, {"FRONTEND_URL": "https://alumnos.felipe-villa-nueva-teotitlan.site"}, clear=False):
        assert get_frontend_url() == "https://alumnos.felipe-villa-nueva-teotitlan.site"


def test_config_db_fallback_cuando_no_hay_env(app_ctx):
    db.session.add(Config(key="frontend_url", value="https://config-db.example.com"))
    db.session.commit()
    with patch.dict(os.environ, {}, clear=True):
        assert get_frontend_url() == "https://config-db.example.com"


def test_default_dev_sin_env_ni_config(app_ctx):
    with patch.dict(os.environ, {}, clear=True):
        assert get_frontend_url() == "http://localhost:5173"


def test_env_sin_slash_final(app_ctx):
    with patch.dict(os.environ, {"FRONTEND_URL": "https://alumnos.example.com/"}, clear=False):
        assert get_frontend_url() == "https://alumnos.example.com"


def test_env_vacio_cae_a_config_db(app_ctx):
    db.session.add(Config(key="frontend_url", value="https://config-db.example.com"))
    db.session.commit()
    with patch.dict(os.environ, {"FRONTEND_URL": "   "}, clear=False):
        assert get_frontend_url() == "https://config-db.example.com"


def test_reset_url_se_construye_con_url_resuelta(app_ctx):
    with patch.dict(os.environ, {"FRONTEND_URL": "https://alumnos.felipe-villa-nueva-teotitlan.site"}, clear=False):
        token = "jwt-fake"
        reset_url = f"{get_frontend_url()}/reset-password?token={token}"
        assert reset_url == "https://alumnos.felipe-villa-nueva-teotitlan.site/reset-password?token=jwt-fake"