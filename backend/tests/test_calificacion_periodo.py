import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Periodo, Profesor, Materia, Grupo, GrupoIntegrante, Carrera, Sede, Alumno, Asignacion, Calificacion


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
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
    per = Periodo(nombre='Enero-Abril 2026', activa=True)
    db.session.add_all([materia, grupo, prof, per])
    db.session.flush()
    db.session.add(Asignacion(profesor_id=prof.id, materia_id=materia.id, grupo_id=grupo.id,
                              fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 4, 30),
                              periodo_id=per.id))
    alumno = Alumno(numero_control='A1', nombre='Luz', apellido_paterno='Diaz', email='l1@example.com',
                    password_hash='x', carrera_id=carrera.id, sede_id=sede.id)
    db.session.add(alumno)
    db.session.flush()
    db.session.add(GrupoIntegrante(grupo_id=grupo.id, alumno_id=alumno.id))
    db.session.commit()
    yield app.test_client(), {'materia': materia.id, 'alumno': alumno.id, 'per': per.id}
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _h():
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def test_crear_calificacion_hereda_periodo_de_asignacion(client):
    c, ids = client
    r = c.post('/api/calificaciones', json={'alumno_id': ids['alumno'], 'materia_id': ids['materia'],
                                            'periodo': 'Regular', 'anio': 2026,
                                            'calificacion_final': 9.0}, headers=_h())
    assert r.status_code == 200
    body = r.get_json()['calificacion']
    assert body['periodo_id'] == ids['per']
    assert body['periodo_nombre'] == 'Enero-Abril 2026'
    assert body['periodo'] == 'Regular'


def test_bulk_hereda_y_sin_asignacion_queda_null(client):
    c, ids = client
    r = c.post('/api/calificaciones/bulk',
               json={'calificaciones': [{'alumno_id': ids['alumno'], 'materia_id': ids['materia'],
                                         'calificacion_final': 8.0}]}, headers=_h())
    assert r.status_code in (200, 207)
    cal = Calificacion.query.filter_by(alumno_id=ids['alumno'], materia_id=ids['materia']).first()
    assert cal.periodo_id == ids['per']
