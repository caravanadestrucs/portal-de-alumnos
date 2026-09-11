import os
os.environ["FLASK_ENV"] = "testing"
from app import create_app
from config import TestingConfig
from models import db, Sede
from flask import jsonify


def test_require_sede_denies_cross_sede_uniform_403():
    from utils.decorators import require_sede
    from flask_jwt_extended import create_access_token
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        teo = Sede(nombre="Teotitlan", codigo="TEO"); hua = Sede(nombre="Huautla", codigo="HUA")
        db.session.add_all([teo, hua]); db.session.commit()

        @require_sede(resolve="body_sede_id")
        def dummy():
            return jsonify({"ok": True}), 200
        with app.test_request_context(json={"sede_id": hua.id},
                headers={"Authorization": "Bearer " + create_access_token(identity="9",
                    additional_claims={"id": 9, "type": "admin", "role": "sede_admin",
                                       "sede_id": teo.id, "sede_slug": "TEO"})}):
            resp, status = dummy()
            assert status == 403
            body = resp.get_json()
            assert body["code"] == "CROSS_SEDE"
            assert "hua" not in str(body).lower() and "teotitlan" not in str(body).lower()
        db.session.remove(); db.drop_all()


def test_registry_19_of_19_have_scope_marker():
    import pathlib
    routes_dir = pathlib.Path(__file__).resolve().parents[1] / "routes"
    missing = []
    for f in sorted(routes_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        text = f.read_text(encoding="utf-8")
        if "@require_sede" not in text and "@public_route" not in text and "@global_route" not in text:
            missing.append(f.name)
    assert missing == [], f"routes without scope marker: {missing}"
    assert len(list(routes_dir.glob("*.py"))) - 1 == 19


# Anti-enumeración en detalle (Task 4 fix): un id inexistente no debe
# distinguirse de un recurso de otra sede para actores sin scope global.
# sede_admin -> 403 uniforme (code CROSS_SEDE); general -> 404 real.
DETAIL_NONEXISTENT_PATHS = [
    "/api/alumnos/99999",
    "/api/asignaciones/99999",
    "/api/grupos/99999",
    "/api/grupos/99999/integrantes",
    "/api/calificaciones/99999",
    "/api/calificaciones/alumnos/99999",
    "/api/calificaciones/alumnos/99999/historial",
    "/api/pagos/99999",
    "/api/pagos/alumnos/99999",
    "/api/profesores/99999",
    "/api/wiki/pages/99999",
    "/api/wiki/pages/99999/history",
    "/api/wiki/pages/99999/attachments",
    "/api/wiki/attachments/99999",
    "/api/boletas/download/99999",
    "/api/boletas/preview/99999",
    "/api/profesor/asignacion/99999/calificaciones",
]


def _detail_tokens(app):
    from flask_jwt_extended import create_access_token
    with app.test_request_context():
        sede_admin = create_access_token(identity="7", additional_claims={
            "id": 7, "type": "admin", "user_type": "admin",
            "role": "sede_admin", "sede_id": 1, "sede_slug": "TEO"})
        general = create_access_token(identity="8", additional_claims={
            "id": 8, "type": "admin", "user_type": "admin",
            "role": "general_admin", "sede_id": None, "sede_slug": "GENERAL"})
    return sede_admin, general


import pytest


@pytest.mark.parametrize("path", DETAIL_NONEXISTENT_PATHS)
def test_detail_nonexistent_id_uniform_403_without_scope(path):
    from app import create_app as _mk
    app = _mk(TestingConfig)
    with app.app_context():
        db.create_all()
        sede_tok, gen_tok = _detail_tokens(app)
        client = app.test_client()
        r = client.get(path, headers={"Authorization": f"Bearer {sede_tok}"})
        assert r.status_code == 403, (
            f"{path}: sede_admin probing missing id must get uniform 403, "
            f"got {r.status_code}")
        assert r.get_json().get("code") == "CROSS_SEDE"
        r2 = client.get(path, headers={"Authorization": f"Bearer {gen_tok}"})
        assert r2.status_code == 404, (
            f"{path}: general must still get real 404, got {r2.status_code}")
        db.session.remove(); db.drop_all()
