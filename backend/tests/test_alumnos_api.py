"""
Integration contract tests for alumnos API and app config.
No DB, no network — pure file-system assertions + logic emulation.
"""

from pathlib import Path

# Resolve backend dir regardless of cwd (pytest may run from root or backend/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
ALUMNOS_PY = BACKEND_DIR / "routes" / "alumnos.py"
CARRERAS_PY = BACKEND_DIR / "routes" / "carreras.py"
APP_PY = BACKEND_DIR / "app.py"


def test_per_page_cap():
    """Replica la lógica de per_page de alumnos.py y valida caps/fallbacks."""
    def get_per_page(val):
        try:
            return max(1, min(int(val or 20), 100))
        except (ValueError, TypeError):
            return 20

    assert get_per_page("10000") == 100
    assert get_per_page("100") == 100
    assert get_per_page("5") == 5
    # string por debajo del mínimo -> capped a 1
    assert get_per_page("0") == 1
    assert get_per_page("-5") == 1
    # None / vacío -> default 20
    assert get_per_page(None) == 20
    assert get_per_page("") == 20
    # no numérico -> default 20
    assert get_per_page("abc") == 20
    assert get_per_page("12abc") == 20
    # valor normal
    assert get_per_page("20") == 20
    assert get_per_page(50) == 50


def test_per_page_in_list_alumnos_route():
    """Verifica que alumnos.py contiene el cap de per_page."""
    content = ALUMNOS_PY.read_text(encoding="utf-8")
    assert "min(int(request.args.get('per_page'" in content
    assert "100" in content
    # también debe tener el max(1, ...) lower bound
    assert "max(1" in content


def test_per_page_in_carreras_route():
    """Carreras también debe aplicar el mismo cap."""
    content = CARRERAS_PY.read_text(encoding="utf-8")
    assert "min(int(request.args.get('per_page'" in content
    assert "100" in content


def test_jwt_expiry_2h():
    content = APP_PY.read_text(encoding="utf-8")
    assert "timedelta(hours=2)" in content
    assert "timedelta(hours=24)" not in content


def test_no_print_admin_password():
    c = APP_PY.read_text(encoding="utf-8")
    # No debe haber print que filtre la password del admin
    # El archivo sí tiene un print informativo pero no debe contener credenciales
    assert "admin123" not in c or "print(" not in c or c.count("admin123") == 1 and "set_password('admin123')" in c
    # Más estricto: ningún print debe contener la password
    for line in c.splitlines():
        if "print(" in line:
            assert "admin123" not in line
    # Debe usar logger para el mensaje de creación
    assert "logger.info" in c
