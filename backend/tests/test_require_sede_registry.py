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
