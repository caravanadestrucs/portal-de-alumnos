import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from models import db, Alumno, Calificacion, Materia, Carrera, Sede


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
    db.session.add(materia)
    db.session.flush()
    alumno = Alumno(numero_control='A1', nombre='Luz', apellido_paterno='Diaz',
                    email='luz@example.com', password_hash='x',
                    carrera_id=carrera.id, sede_id=sede.id)
    db.session.add(alumno)
    db.session.flush()
    db.session.add(Calificacion(alumno_id=alumno.id, materia_id=materia.id,
                                calificacion_final=8.5, periodo='Regular', anio=2026))
    db.session.commit()
    yield app.test_client(), alumno.id
    db.session.remove()
    db.drop_all()
    ctx.pop()


def test_descarga_responde_docx(client):
    c, alumno_id = client
    tok = create_access_token(identity='a', additional_claims={'type': 'admin', 'role': 'general_admin', 'id': 1})
    r = c.get(f'/api/boletas/download/{alumno_id}', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 200
    assert r.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    assert r.data[:2] == b'PK'


def test_requirements_declara_python_docx():
    req = (Path(__file__).resolve().parent.parent / 'requirements.txt').read_text(encoding='utf-8')
    assert 'python-docx' in req
