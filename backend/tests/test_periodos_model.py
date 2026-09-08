import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from app import create_app
from config import TestingConfig
from models import db, Periodo, Asignacion, Profesor, Materia, Grupo, Carrera, Sede


@pytest.fixture()
def app_ctx():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _seed_catalogo():
    sede = Sede(nombre='Teotitlan', codigo='TEO')
    db.session.add(sede)
    db.session.flush()
    carrera = Carrera(nombre='Sistemas', codigo='SIS')
    db.session.add(carrera)
    db.session.flush()
    materia = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    grupo = Grupo(nombre='A', carrera_id=carrera.id, sede_id=sede.id)
    prof = Profesor(numero_empleado='E1', nombre='Ana', apellido_paterno='Paz',
                    email='ana@example.com', password_hash='x')
    db.session.add_all([materia, grupo, prof])
    db.session.flush()
    return sede, carrera, materia, grupo, prof


def test_periodo_to_dict(app_ctx):
    p = Periodo(nombre='Enero-Abril 2026', fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 4, 30), activa=True)
    db.session.add(p)
    db.session.commit()
    assert p.to_dict() == {'id': p.id, 'nombre': 'Enero-Abril 2026',
                           'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-04-30',
                           'activa': True}


def test_asignacion_serializa_periodo_y_sin_periodo(app_ctx):
    _, _, materia, grupo, prof = _seed_catalogo()
    p = Periodo(nombre='Regular', activa=True)
    db.session.add(p)
    db.session.flush()
    con = Asignacion(profesor_id=prof.id, materia_id=materia.id, grupo_id=grupo.id,
                     fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 4, 30),
                     periodo_id=p.id)
    legacy = Asignacion(profesor_id=prof.id, materia_id=materia.id, grupo_id=grupo.id,
                        fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 4, 30),
                        periodo_id=None)
    db.session.add_all([con, legacy])
    db.session.commit()
    assert con.to_dict()['periodo_id'] == p.id
    assert con.to_dict()['periodo_nombre'] == 'Regular'
    assert legacy.to_dict()['periodo_id'] is None
    assert legacy.to_dict()['periodo_nombre'] == 'Sin periodo'
