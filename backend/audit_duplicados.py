#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AUDIT DUPLICADOS - Portal de Alumnos
Solo LECTURA (abre SQLite en modo ro). Detecta duplicados potenciales en
alumnos, materias, profesores, carreras, grupos, periodos, sedes, admins,
calificaciones, pagos, practicas, asignaciones, integrantes de grupo y wiki.

Resistente a drift de esquema: inspecciona columnas reales via PRAGMA y
adapta cada check a lo que exista. No usa ORM ni modifica nada.
"""
import os
import re
import sqlite3
import unicodedata

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "instance", "portal.db")


def normalize(s):
    """Normaliza texto para comparar: lower, sin acentos, espacios colapsados."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def mask_email(e):
    if not e or "@" not in e:
        return "***"
    local, domain = e.split("@", 1)
    local_m = local[0] + "***" + (local[-1] if len(local) > 2 else "")
    return f"{local_m}@{domain}"


def get_tables(cur):
    rows = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return {r[0] for r in rows}


def get_columns(cur, table):
    return {r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}


def run():
    if not os.path.exists(DB_PATH):
        print(f"NO existe la base: {DB_PATH}")
        return
    uri = f"file:{DB_PATH}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    tables = get_tables(cur)
    print("=" * 80)
    print("AUDIT DUPLICADOS - Portal de Alumnos (solo lectura)")
    print(f"DB: {DB_PATH}")
    print(f"Tablas presentes: {', '.join(sorted(tables))}")
    print("=" * 80)

    findings = []

    def report(section, label, rows, limit=8, fmt=None):
        """rows: lista de dicts. Imprime y cuenta."""
        if not rows:
            print(f"  [OK] {label}: 0")
            return
        print(f"  [!!] {label}: {len(rows)}")
        findings.append((section, label, len(rows)))
        for r in rows[:limit]:
            if fmt:
                print("       " + fmt(r))
            else:
                print("       " + " | ".join(f"{k}={v}" for k, v in r.items()))

    def q(sql, params=()):
        return [dict(r) for r in cur.execute(sql, params).fetchall()]

    # ----------------------------------------------------------
    # 1. ALUMNOS
    # ----------------------------------------------------------
    print("\n[1] ALUMNOS")
    n = q("SELECT COUNT(*) AS c FROM alumnos")[0]["c"]
    print(f"  total: {n}")

    report("alumnos", "numero_control duplicado (case-insensitive)", q(
        "SELECT LOWER(numero_control) AS nc, COUNT(*) AS c "
        "FROM alumnos GROUP BY LOWER(numero_control) HAVING c > 1"))

    report("alumnos", "email duplicado (case-insensitive)", q(
        "SELECT LOWER(email) AS email, COUNT(*) AS c "
        "FROM alumnos GROUP BY LOWER(email) HAVING c > 1"),
        fmt=lambda r: f"email={mask_email(r['email'])} x{r['c']}")

    # homónimos: mismo nombre completo normalizado (sin acentos), en Python
    alumnos = q("SELECT id, nombre, apellido_paterno, apellido_materno, "
                "numero_control, email, carrera_id, sede_id, activo FROM alumnos")
    hom_groups = {}
    for a in alumnos:
        key = normalize(f"{a['nombre']}|{a['apellido_paterno']}|{a['apellido_materno'] or ''}")
        hom_groups.setdefault(key, []).append(a)
    hom = {k: v for k, v in hom_groups.items() if len(v) > 1}
    if hom:
        print(f"  [!!] alumnos: mismo nombre completo (homonimos/duplicados): {len(hom)}")
        findings.append(("alumnos", "nombre completo duplicado", len(hom)))
        for key, det in list(hom.items())[:10]:
            line = "; ".join(
                f"id={d['id']} nc={d['numero_control']} carr={d['carrera_id']} "
                f"sede={d['sede_id']} activo={d['activo']} {mask_email(d['email'])}"
                for d in det)
            print(f"       '{key}' x{len(det)} -> {line}")
    else:
        print("  [OK] mismo nombre completo: 0")

    # ----------------------------------------------------------
    # 2. MATERIAS
    # ----------------------------------------------------------
    print("\n[2] MATERIAS")
    n = q("SELECT COUNT(*) AS c FROM materias")[0]["c"]
    print(f"  total: {n}")

    materias = q("SELECT id, nombre, codigo, carrera_id FROM materias")

    # mismo nombre normalizado (sin acentos) dentro de la MISMA carrera
    intra = {}
    for m in materias:
        key = (m["carrera_id"], normalize(m["nombre"]))
        intra.setdefault(key, []).append(m)
    intra_dups = {k: v for k, v in intra.items() if len(v) > 1}
    if intra_dups:
        print(f"  [!!] materias: mismo nombre dentro de la MISMA carrera: {len(intra_dups)}")
        findings.append(("materias", "mismo nombre en misma carrera", len(intra_dups)))
        for (cid, name), det in list(intra_dups.items())[:10]:
            line = "; ".join(f"id={d['id']} cod={d['codigo']}" for d in det)
            print(f"       carrera={cid} nombre='{name}' x{len(det)} -> {line}")
    else:
        print("  [OK] mismo nombre dentro de la MISMA carrera: 0")

    report("materias", "mismo codigo dentro de la MISMA carrera", q(
        "SELECT carrera_id, codigo, COUNT(*) AS c FROM materias "
        "WHERE codigo IS NOT NULL AND codigo != '' "
        "GROUP BY carrera_id, codigo HAVING c > 1"),
        fmt=lambda r: f"carrera={r['carrera_id']} codigo='{r['codigo']}' x{r['c']}")

    # mismo nombre normalizado en DISTINTAS carreras (candidatos a consolidar)
    by_name = {}
    for m in materias:
        by_name.setdefault(normalize(m["nombre"]), []).append(m)
    cross = {k: v for k, v in by_name.items()
             if len(v) > 1 and len({m["carrera_id"] for m in v}) > 1}
    if cross:
        print(f"  [!!] materias: mismo nombre en DISTINTAS carreras: {len(cross)}")
        findings.append(("materias", "mismo nombre entre carreras", len(cross)))
        for name, det in list(cross.items())[:12]:
            line = "; ".join(f"id={d['id']} carr={d['carrera_id']} cod={d['codigo']}"
                             for d in det)
            print(f"       '{name}' x{len(det)} -> {line}")
    else:
        print("  [OK] mismo nombre entre carreras: 0")

    # ----------------------------------------------------------
    # 3. PROFESORES
    # ----------------------------------------------------------
    if "profesores" in tables:
        print("\n[3] PROFESORES")
        n = q("SELECT COUNT(*) AS c FROM profesores")[0]["c"]
        print(f"  total: {n}")
        report("profesores", "numero_empleado duplicado (case-insensitive)", q(
            "SELECT LOWER(numero_empleado) AS ne, COUNT(*) AS c "
            "FROM profesores GROUP BY LOWER(numero_empleado) HAVING c > 1"))
        report("profesores", "email duplicado (case-insensitive)", q(
            "SELECT LOWER(email) AS email, COUNT(*) AS c "
            "FROM profesores GROUP BY LOWER(email) HAVING c > 1"),
            fmt=lambda r: f"email={mask_email(r['email'])} x{r['c']}")
        report("profesores", "mismo nombre completo", q("""
            SELECT LOWER(TRIM(nombre))||'|'||LOWER(TRIM(apellido_paterno))||'|'||
                   COALESCE(LOWER(TRIM(apellido_materno)),'') AS key_norm, COUNT(*) AS c
            FROM profesores
            GROUP BY LOWER(TRIM(nombre)), LOWER(TRIM(apellido_paterno)),
                     COALESCE(LOWER(TRIM(apellido_materno)),'')
            HAVING c > 1"""))

    # ----------------------------------------------------------
    # 4. CATÁLOGOS: carreras, sedes, periodos, admins
    # ----------------------------------------------------------
    print("\n[4] CATALOGOS")
    report("carreras", "carreras codigo duplicado", q(
        "SELECT codigo, COUNT(*) AS c FROM carreras GROUP BY codigo HAVING c > 1"))
    report("carreras", "carreras nombre duplicado (normalizado)", q(
        "SELECT LOWER(TRIM(nombre)) AS nombre, COUNT(*) AS c "
        "FROM carreras GROUP BY LOWER(TRIM(nombre)) HAVING c > 1"))
    report("sedes", "sedes codigo/nombre duplicado", q(
        "SELECT codigo, nombre, COUNT(*) AS c FROM sedes "
        "GROUP BY codigo, nombre HAVING c > 1"))
    if "periodos" in tables:
        report("periodos", "periodos nombre duplicado", q(
            "SELECT nombre, COUNT(*) AS c FROM periodos GROUP BY nombre HAVING c > 1"))
    report("admins", "admins username/email duplicado", q(
        "SELECT username, email, COUNT(*) AS c FROM admins "
        "GROUP BY username, email HAVING c > 1"))

    # ----------------------------------------------------------
    # 5. GRUPOS
    # ----------------------------------------------------------
    if "grupos" in tables:
        print("\n[5] GRUPOS")
        n = q("SELECT COUNT(*) AS c FROM grupos")[0]["c"]
        print(f"  total: {n}")
        report("grupos", "grupo duplicado (nombre+carrera+sede+periodo+anio)", q(
            "SELECT nombre, carrera_id, sede_id, COALESCE(periodo,'') AS periodo, "
            "COALESCE(anio,'') AS anio, COUNT(*) AS c FROM grupos "
            "GROUP BY nombre, carrera_id, sede_id, periodo, anio HAVING c > 1"))

    # ----------------------------------------------------------
    # 6. CALIFICACIONES
    # ----------------------------------------------------------
    if "calificaciones" in tables:
        cols = get_columns(cur, "calificaciones")
        print("\n[6] CALIFICACIONES")
        n = q("SELECT COUNT(*) AS c FROM calificaciones")[0]["c"]
        print(f"  total: {n}")
        if {"periodo", "anio"} <= cols:
            report("calificaciones", "duplicada (alumno+materia+periodo+anio)", q(
                "SELECT alumno_id, materia_id, periodo, anio, COUNT(*) AS c "
                "FROM calificaciones GROUP BY alumno_id, materia_id, periodo, anio "
                "HAVING c > 1"))
        report("calificaciones", "duplicada (alumno+materia, mismo periodo ignorado)", q(
            "SELECT alumno_id, materia_id, COUNT(*) AS c "
            "FROM calificaciones GROUP BY alumno_id, materia_id HAVING c > 1"))
        # Nota: si el check (alumno+materia+periodo+anio) da 0, estos grupos son
        # recursadas/historial con periodos distintos -> legitimos.
        dups_am = q("SELECT alumno_id, materia_id, COUNT(*) AS c "
                    "FROM calificaciones GROUP BY alumno_id, materia_id HAVING c > 1")
        if dups_am:
            # distinguir recursadas legitimas (notas distintas) de duplicados
            # sospechosos (mismas notas exactas en todas las filas)
            identical = 0
            different = 0
            for d in dups_am[:200]:
                rows = q("SELECT calificacion_final, practica_1, practica_2, extra_1, "
                         "extra_2, asistencia_1, asistencia_2, asistencia_3, "
                         "asistencia_4, asistencia_5, periodo, anio "
                         "FROM calificaciones WHERE alumno_id=:a AND materia_id=:m "
                         "ORDER BY periodo, anio",
                         {"a": d["alumno_id"], "m": d["materia_id"]})
                sig = {(r["calificacion_final"], r["practica_1"], r["practica_2"],
                        r["extra_1"], r["extra_2"], r["asistencia_1"], r["asistencia_2"],
                        r["asistencia_3"], r["asistencia_4"], r["asistencia_5"])
                       for r in rows}
                if len(sig) == 1:
                    identical += 1
                else:
                    different += 1
            print(f"       (muestra {min(len(dups_am), 200)} grupos: "
                  f"{identical} con notas IDENTICAS en todas las filas [sospechosos], "
                  f"{different} con notas distintas [recursadas legitimas])")
            if identical:
                findings.append(("calificaciones", "mismas notas en filas repetidas",
                                 identical))
        # ejemplo de periodos para entender el caso
        if dups_am:
            d0 = dups_am[0]
            per = q("SELECT DISTINCT periodo, anio FROM calificaciones "
                    "WHERE alumno_id=:a AND materia_id=:m ORDER BY anio, periodo",
                    {"a": d0["alumno_id"], "m": d0["materia_id"]})
            print(f"       ej. alumno={d0['alumno_id']} materia={d0['materia_id']} "
                  f"x{d0['c']} periodos={[(p['periodo'], p['anio']) for p in per]}")
        fk_alumno = q("SELECT COUNT(*) AS c FROM calificaciones "
                      "WHERE alumno_id NOT IN (SELECT id FROM alumnos)")[0]["c"]
        fk_materia = q("SELECT COUNT(*) AS c FROM calificaciones "
                       "WHERE materia_id NOT IN (SELECT id FROM materias)")[0]["c"]
        if fk_alumno or fk_materia:
            print(f"  [!!] calificaciones: FK rota alumno={fk_alumno} materia={fk_materia}")
            findings.append(("calificaciones", "FK rota", fk_alumno + fk_materia))
        else:
            print("  [OK] FK rotas en calificaciones: 0")

        # periodos que parecen duplicados de importacion (sufijos _dup, copia, etc.)
        periods = q("SELECT periodo, anio, COUNT(*) AS c FROM calificaciones "
                    "GROUP BY periodo, anio ORDER BY anio, periodo")
        suspect = [p for p in periods if re.search(r"_dup|_copia|_2\b|_bis", str(p["periodo"]), re.I)]
        if suspect:
            print(f"  [!!] calificaciones: periodos con sufijo de duplicado: {len(suspect)}")
            findings.append(("calificaciones", "periodos _dup en calificaciones", len(suspect)))
            for p in suspect:
                print(f"       periodo='{p['periodo']}' anio={p['anio']} filas={p['c']}")
        else:
            print("  [OK] periodos con sufijo duplicado: 0")

    # ----------------------------------------------------------
    # 7. NOTAS DE REMISION (pagos)
    # ----------------------------------------------------------
    if "notas_remision" in tables:
        print("\n[7] NOTAS DE REMISION")
        n = q("SELECT COUNT(*) AS c FROM notas_remision")[0]["c"]
        print(f"  total: {n}")
        report("pagos", "nota duplicada (alumno+concepto+monto+fecha_emision)", q(
            "SELECT alumno_id, concepto, monto, fecha_emision, COUNT(*) AS c "
            "FROM notas_remision GROUP BY alumno_id, concepto, monto, fecha_emision "
            "HAVING c > 1"))

    # ----------------------------------------------------------
    # 8. PRACTICAS PROFESIONALES
    # ----------------------------------------------------------
    if "practicas_profesionales" in tables:
        print("\n[8] PRACTICAS PROFESIONALES")
        report("practicas", "practica duplicada (alumno+numero)", q(
            "SELECT alumno_id, numero_practica, COUNT(*) AS c "
            "FROM practicas_profesionales GROUP BY alumno_id, numero_practica "
            "HAVING c > 1"))

    # ----------------------------------------------------------
    # 9. ASIGNACIONES
    # ----------------------------------------------------------
    if "asignaciones" in tables:
        print("\n[9] ASIGNACIONES")
        acols = get_columns(cur, "asignaciones")
        if "periodo_id" in acols:
            report("asignaciones", "asignacion duplicada (profesor+materia+grupo+periodo)", q(
                "SELECT profesor_id, materia_id, grupo_id, COALESCE(periodo_id,'') AS p, "
                "COUNT(*) AS c FROM asignaciones "
                "GROUP BY profesor_id, materia_id, grupo_id, periodo_id HAVING c > 1"))
        else:
            report("asignaciones", "asignacion duplicada (profesor+materia+grupo)", q(
                "SELECT profesor_id, materia_id, grupo_id, COUNT(*) AS c "
                "FROM asignaciones GROUP BY profesor_id, materia_id, grupo_id HAVING c > 1"))

    # ----------------------------------------------------------
    # 10. GRUPO INTEGRANTES
    # ----------------------------------------------------------
    if "grupo_integrantes" in tables:
        print("\n[10] GRUPO INTEGRANTES")
        report("grupos", "integrante duplicado (grupo+alumno)", q(
            "SELECT grupo_id, alumno_id, COUNT(*) AS c FROM grupo_integrantes "
            "GROUP BY grupo_id, alumno_id HAVING c > 1"))

    # ----------------------------------------------------------
    # 11. WIKI
    # ----------------------------------------------------------
    if "wiki_pages" in tables:
        print("\n[11] WIKI")
        report("wiki", "pagina duplicada (sede+slug)", q(
            "SELECT COALESCE(sede_id,'NULL') AS sede_id, slug, COUNT(*) AS c "
            "FROM wiki_pages GROUP BY sede_id, slug HAVING c > 1"))

    # ----------------------------------------------------------
    # RESUMEN
    # ----------------------------------------------------------
    print("\n" + "=" * 80)
    print("RESUMEN DE HALLAZGOS")
    print("=" * 80)
    if not findings:
        print("  Sin duplicados detectados en ningun check.")
    for section, label, c in findings:
        print(f"  [{section}] {label}: {c}")
    print("\n[FIN AUDIT DUPLICADOS - solo lectura, sin modificaciones]")
    con.close()


if __name__ == "__main__":
    run()