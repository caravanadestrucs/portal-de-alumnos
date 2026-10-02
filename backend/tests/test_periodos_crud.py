import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Periodo


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app.test_client()
    db.session.remove()
    db.drop_all()
    ctx.pop()


def _headers(role='general_admin', utype='admin'):
    tok = create_access_token(identity='t', additional_claims={'type': utype, 'role': role, 'id': 1})
    return {'Authorization': f'Bearer {tok}'}


def test_get_ordenado_para_todos_los_roles(client):
    db.session.add_all([Periodo(nombre='Regular'), Periodo(nombre='Enero-Abril 2026')])
    db.session.commit()
    for role in ('general_admin', 'sede_admin'):
        r = client.get('/api/periodos', headers=_headers(role))
        assert r.status_code == 200
        nombres = [p['nombre'] for p in r.get_json()['periodos']]
        assert nombres == sorted(nombres)


def test_post_valida_nombre_y_duplicado(client):
    assert client.post('/api/periodos', json={}, headers=_headers()).status_code == 422
    assert client.post('/api/periodos', json={'nombre': '  '}, headers=_headers()).status_code == 422
    assert client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers()).status_code == 201
    dup = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers())
    assert dup.status_code == 409
    assert dup.get_json()['error'] == 'Periodo ya existe'


def test_post_fecha_invalida_responde_400(client):
    r = client.post('/api/periodos', json={'nombre': 'X', 'fecha_inicio': 'no-fecha'}, headers=_headers())
    assert r.status_code == 400


def test_escritura_solo_admin_y_baja_logica(client):
    r = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers(utype='alumno'))
    assert r.status_code == 403
    pid = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers()).get_json()['periodo']['id']
    upd = client.put(f'/api/periodos/{pid}', json={'nombre': 'Regular 2'}, headers=_headers())
    assert upd.status_code == 200 and upd.get_json()['periodo']['nombre'] == 'Regular 2'
    dele = client.delete(f'/api/periodos/{pid}', headers=_headers())
    assert dele.status_code == 200
    body = dele.get_json()
    assert body['message'] == 'Período desactivado' and body['periodo']['activa'] is False
    assert db.session.get(Periodo, pid).activa is False


def test_put_activa_string_false_guarda_false(client):
    pid = client.post('/api/periodos', json={'nombre': 'Regular'}, headers=_headers()).get_json()['periodo']['id']
    r = client.put(f'/api/periodos/{pid}', json={'activa': 'false'}, headers=_headers())
    assert r.status_code == 200
    assert r.get_json()['periodo']['activa'] is False
    assert db.session.get(Periodo, pid).activa is False
