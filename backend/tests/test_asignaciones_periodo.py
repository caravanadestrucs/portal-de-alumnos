import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Periodo, Profesor, Materia, Grupo, Carrera, Sede


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
    activo = Periodo(nombre='Enero-Abril 2026', activa=True)
    inactivo = Periodo(nombre='Viejo', activa=False)
    db.session.add_all([materia, grupo, prof, activo, inactivo])
    db.session.commit()
    yield app.test_client(), {'materia': materia.id, 'grupo': grupo.id, 'prof': prof.id,
                              'activo': activo.id, 'inactivo': inactivo.id}
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _h():
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def _body(ids, **kw):
    data = {'profesor_id': ids['prof'], 'materia_id': ids['materia'], 'grupo_id': ids['grupo'],
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-04-30'}
    data.update(kw)
    return data


def test_post_exige_periodo_activo(client):
    c, ids = client
    assert c.post('/api/asignaciones', json=_body(ids), headers=_h()).status_code == 422
    assert c.post('/api/asignaciones', json=_body(ids, periodo_id=None), headers=_h()).status_code == 422
    assert c.post('/api/asignaciones', json=_body(ids, periodo_id=9999), headers=_h()).status_code == 422
    assert c.post('/api/asignaciones', json=_body(ids, periodo_id=ids['inactivo']), headers=_h()).status_code == 422
    ok = c.post('/api/asignaciones', json=_body(ids, periodo_id=ids['activo']), headers=_h())
    assert ok.status_code == 201
    assert ok.get_json()['asignacion']['periodo_id'] == ids['activo']
    assert ok.get_json()['asignacion']['periodo_nombre'] == 'Enero-Abril 2026'


def test_put_edita_periodo_incluido_inactivo_y_nulo(client):
    c, ids = client
    aid = c.post('/api/asignaciones', json=_body(ids, periodo_id=ids['activo']), headers=_h()).get_json()['asignacion']['id']
    assert c.put(f'/api/asignaciones/{aid}', json={'periodo_id': 9999}, headers=_h()).status_code == 422
    edit = c.put(f'/api/asignaciones/{aid}', json={'periodo_id': ids['inactivo']}, headers=_h())
    assert edit.status_code == 200 and edit.get_json()['asignacion']['periodo_nombre'] == 'Viejo'
    keep = c.put(f'/api/asignaciones/{aid}', json={'activo': True}, headers=_h())
    assert keep.get_json()['asignacion']['periodo_id'] == ids['inactivo']
    clear = c.put(f'/api/asignaciones/{aid}', json={'periodo_id': None}, headers=_h())
    assert clear.get_json()['asignacion']['periodo_nombre'] == 'Sin periodo'
    listed = c.get('/api/asignaciones', headers=_h()).get_json()['asignaciones']
    assert any(a['id'] == aid and a['periodo_nombre'] == 'Sin periodo' for a in listed)
