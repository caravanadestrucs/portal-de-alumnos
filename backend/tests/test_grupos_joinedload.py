def test_grupos_uses_joinedload():
    with open('routes/grupos.py', encoding='utf-8') as f:
        content = f.read()
    assert 'joinedload' in content, 'grupos.py must use joinedload to avoid N+1'
    assert 'Grupo.carrera' in content or 'carrera' in content

def test_integrantes_uses_joinedload_or_eager():
    with open('routes/grupos.py', encoding='utf-8') as f:
        content = f.read()
    # should eager load alumno for integrantes
    assert 'joinedload' in content
