import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Alumno, Calificacion, Materia, Grupo, GrupoIntegrante, Carrera, Sede, Profesor, Periodo, Asignacion


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
    m1 = Materia(carrera_id=carrera.id, nombre='Calculo', codigo='CAL-1')
    m2 = Materia(carrera_id=carrera.id, nombre='Fisica', codigo='FIS-1')
    g = Grupo(nombre='A', carrera_id=carrera.id, sede_id=sede.id)
    prof = Profesor(numero_empleado='E1', nombre='Ana', apellido_paterno='Paz',
                    email='ana@example.com', password_hash='x')
    p1 = Periodo(nombre='Enero-Abril 2026', activa=True)
    p2 = Periodo(nombre='Regular', activa=True)
    db.session.add_all([m1, m2, g, prof, p1, p2])
    db.session.flush()
    db.session.add(Asignacion(profesor_id=prof.id, materia_id=m1.id, grupo_id=g.id,
                              fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 4, 30),
                              periodo_id=p1.id))
    a1 = Alumno(numero_control='A1', nombre='Luz', apellido_paterno='Diaz', email='l1@example.com',
                password_hash='x', carrera_id=carrera.id, sede_id=sede.id)
    a2 = Alumno(numero_control='A2', nombre='Sol', apellido_paterno='Mar', email='l2@example.com',
                password_hash='x', carrera_id=carrera.id, sede_id=sede.id)
    db.session.add_all([a1, a2])
    db.session.flush()
    db.session.add_all([GrupoIntegrante(grupo_id=g.id, alumno_id=a1.id),
                        GrupoIntegrante(grupo_id=g.id, alumno_id=a2.id),
                        Calificacion(alumno_id=a1.id, materia_id=m1.id, calificacion_final=9.0,
                                     periodo='Enero-Abril 2026', anio=2026),
                        Calificacion(alumno_id=a2.id, materia_id=m2.id, calificacion_final=9.0,
                                     periodo='Regular', anio=2026)])
    db.session.commit()
    yield app.test_client(), {'p1': p1.id, 'p2': p2.id}
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _h():
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def test_filtro_por_periodo_solo_lista_visible(client):
    c, ids = client
    full = c.get('/api/boletas/alumnos', headers=_h()).get_json()['alumnos']
    assert len(full) == 2
    f1 = c.get(f"/api/boletas/alumnos?periodo_id={ids['p1']}", headers=_h()).get_json()['alumnos']
    assert [a['numero_control'] for a in f1] == ['A1']
    assert f1[0]['calificaciones_count'] == 1
    assert c.get('/api/boletas/alumnos?periodo_id=9999', headers=_h()).status_code == 422
    assert c.get('/api/boletas/alumnos?periodo_id=abc', headers=_h()).status_code == 422
