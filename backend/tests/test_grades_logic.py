"""
Contract tests for grade hierarchy and badge thresholds.
Replica JS logic from frontend/src/utils/grades.js in Python to ensure
backend/frontend contract alignment. No DB, no network.
"""


def _has_value(v):
    """JS-equivalent: v != null && v !== '' && Number(v) !== 0 && !isNaN."""
    if v is None or v == "":
        return False
    try:
        n = float(v)
    except (TypeError, ValueError):
        return False
    # NaN check
    if n != n:
        return False
    return n != 0


def get_effective(cal):
    """
    Replica getEffectiveGrade de grades.js:
      extra_2 > extra_1 > calificacion_final/final
    Ignora 0, '', null, NaN como en JS.
    """
    if not cal:
        return {"value": None, "source": "Ordinaria"}
    if _has_value(cal.get("extra_2")):
        return {"value": cal["extra_2"], "source": "Extraordinario 2"}
    if _has_value(cal.get("extra_1")):
        return {"value": cal["extra_1"], "source": "Extraordinario 1"}
    final_val = cal.get("calificacion_final")
    if final_val is None:
        final_val = cal.get("final")
    if final_val is None:
        final_val = cal.get("calificacionFinal")
    return {"value": final_val, "source": "Ordinaria"}


def grade_class(n):
    """
    Replica getGradeClass de grades.js (badge variant):
      null/''/0/NaN -> badge-neutral
      >=9           -> badge-success
      >=8           -> badge-warning
      else          -> badge-danger
    """
    if n is None or n == "":
        return "badge-neutral"
    try:
        num = float(n)
    except (TypeError, ValueError):
        return "badge-neutral"
    # NaN
    if num != num:
        return "badge-neutral"
    if num == 0:
        return "badge-neutral"
    if num >= 9:
        return "badge-success"
    if num >= 8:
        return "badge-warning"
    return "badge-danger"


# ---------------------------------------------------------------------------
# Hierarchy tests
# ---------------------------------------------------------------------------

def test_grade_hierarchy_extra2_wins():
    assert get_effective({"final": 6, "extra_1": 8, "extra_2": 9}) == {"value": 9, "source": "Extraordinario 2"}
    assert get_effective({"calificacion_final": 5, "extra_1": 7, "extra_2": 8}) == {"value": 8, "source": "Extraordinario 2"}


def test_grade_hierarchy_extra1_when_no_extra2():
    assert get_effective({"final": 6, "extra_1": 8}) == {"value": 8, "source": "Extraordinario 1"}
    assert get_effective({"calificacion_final": 6, "extra_1": 8, "extra_2": None}) == {"value": 8, "source": "Extraordinario 1"}
    assert get_effective({"calificacion_final": 6, "extra_1": 8, "extra_2": ""}) == {"value": 8, "source": "Extraordinario 1"}
    assert get_effective({"calificacion_final": 6, "extra_1": 8, "extra_2": 0}) == {"value": 8, "source": "Extraordinario 1"}


def test_grade_hierarchy_final_fallback():
    assert get_effective({"calificacion_final": 6}) == {"value": 6, "source": "Ordinaria"}
    assert get_effective({"final": 6}) == {"value": 6, "source": "Ordinaria"}
    assert get_effective({"final": None}) == {"value": None, "source": "Ordinaria"}
    assert get_effective({"calificacionFinal": 7}) == {"value": 7, "source": "Ordinaria"}


def test_grade_hierarchy_ignores_zero_extra():
    assert get_effective({"calificacion_final": 6, "extra_1": 0, "extra_2": ""}) == {"value": 6, "source": "Ordinaria"}
    assert get_effective({"calificacion_final": 6, "extra_1": "", "extra_2": 0}) == {"value": 6, "source": "Ordinaria"}


def test_grade_hierarchy_null_cal():
    assert get_effective(None) == {"value": None, "source": "Ordinaria"}
    assert get_effective({}) == {"value": None, "source": "Ordinaria"}


# ---------------------------------------------------------------------------
# Threshold / badge tests (mirrors spec's cls thresholds)
# ---------------------------------------------------------------------------

def test_grade_class_thresholds():
    assert grade_class(9) == "badge-success"
    assert grade_class(9.5) == "badge-success"
    assert grade_class(10) == "badge-success"
    assert grade_class("9") == "badge-success"

    assert grade_class(8) == "badge-warning"
    assert grade_class(8.9) == "badge-warning"
    assert grade_class("8.5") == "badge-warning"

    assert grade_class(7.9) == "badge-danger"
    assert grade_class(7) == "badge-danger"
    assert grade_class(5) == "badge-danger"
    assert grade_class(0.1) == "badge-danger"
    assert grade_class(1) == "badge-danger"


def test_grade_class_neutral():
    assert grade_class(None) == "badge-neutral"
    assert grade_class("") == "badge-neutral"
    assert grade_class(0) == "badge-neutral"
    assert grade_class("0") == "badge-neutral"
    assert grade_class(float("nan")) == "badge-neutral"
    assert grade_class("abc") == "badge-neutral"
