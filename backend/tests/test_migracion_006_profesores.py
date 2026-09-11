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
