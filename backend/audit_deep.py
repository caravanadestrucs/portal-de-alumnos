from app import create_app
from models import db, Alumno, Materia, Calificacion, Carrera
from sqlalchemy import text
import csv, os, glob, re

app = create_app()
with app.app_context():
    print("="*80)
    print("AUDIT DEEP - Análisis fino de rarezas")
    print("="*80)

    # ---- A. Nombre duplicado: ¿homónimo o mismo DNI con diferente control? ----
    print("\n[A] NOMBRES COMPLETOS DUPLICADOS (case-insensitive) - 43 grupos")
    print("    Hipótesis: misma persona importada 2 veces con controles distintos (CSV vs BOLETAS sin control)")
    dups = db.session.execute(text("""
        SELECT LOWER(TRIM(nombre))||'|'||LOWER(TRIM(apellido_paterno))||'|'||COALESCE(LOWER(TRIM(apellido_materno)),'') as key_norm,
               COUNT(*) as c
        FROM alumnos
        GROUP BY LOWER(TRIM(nombre)), LOWER(TRIM(apellido_paterno)), COALESCE(LOWER(TRIM(apellido_materno)),'')
        HAVING c>1
        ORDER BY c DESC
    """)).fetchall()
    # clasificar: mismo control vs distinto, misma carrera vs distinta
    sospechosos_duplicado_real = []
    for key_norm, c in dups:
        rows = db.session.execute(text("""
            SELECT id, numero_control, email, carrera_id, activo
            FROM alumnos
            WHERE LOWER(TRIM(nombre))||'|'||LOWER(TRIM(apellido_paterno))||'|'||COALESCE(LOWER(TRIM(apellido_materno)),'')=:k
        """), {"k": key_norm}).fetchall()
        # distancia de Levenshtein no needed, check si alguna carrera coincide y emails diferentes
        # si tienen mismo key pero controles muy diferentes (uno real 10 dígitos y otro TEO2025), es sospechoso duplicado
        controles = [r[1] for r in rows]
        carreras = [r[3] for r in rows]
        emails = [r[2] for r in rows]
        # Detectar caso ana maria martinez nepomuceno con 3 apariciones: 2 con control casi idéntico case diff
        # Check controls case-insensitive dup
        controls_lower = [cc.lower() for cc in controles]
        has_control_dup_ci = len(set(controls_lower)) < len(controls_lower)
        print(f"  '{key_norm}' x{c} | nc={controles} | carr={carreras} | emails={[e.split('@')[0][:3]+'***' if '@' in e else e for e in emails]} | control_dup_CI={has_control_dup_ci}")
        # sospechoso si mismo nombre+misma carrera y controles distintos pero uno es TEO2025
        if any("TEO2025" in cc for cc in controles) and any("TEO2025" not in cc for cc in controles):
            sospechosos_duplicado_real.append((key_norm, controles))
        # also sospechoso if exact triple with 2401TEO010ENf vs 2401TEO010ENF case differ
        if has_control_dup_ci:
            sospechosos_duplicado_real.append((key_norm+"_CASE_DUP", controles))

    print(f"\n  => Grupos sospechosos duplicado REAL (mismo nombre, controles TEO vs real): {len(sospechosos_duplicado_real)}")
    for k, cs in sospechosos_duplicado_real[:10]:
        print(f"     - {k}: {cs}")

    # Check specific: ana maria 2401TEO010ENf vs 2401TEO010ENF duplicate case
    print("\n  Caso especial ana maria martinez nepomuceno:")
    rows = db.session.execute(text("""
        SELECT id, numero_control, email, carrera_id, nombre, apellido_paterno, apellido_materno
        FROM alumnos WHERE LOWER(TRIM(nombre))='ana maría' AND LOWER(TRIM(apellido_paterno))='martinez'
    """)).fetchall()
    for r in rows:
        print(f"    id={r[0]} nc={r[1]} carr={r[3]} email={r[2].split('@')[0][:3]+'***'} nombre={r[4]} {r[5]} {r[6]}")

    # Ver si hay duplicado exacto de control case-insensitive
    print("\n  Check numero_control case-insensitive duplicates (LOWER):")
    rows_ci = db.session.execute(text("SELECT LOWER(numero_control), COUNT(*) FROM alumnos GROUP BY LOWER(numero_control) HAVING COUNT(*)>1")).fetchall()
    print(f"    grupos LOWER(numero_control) dup: {len(rows_ci)}")
    for nc, c in rows_ci:
        ex = db.session.execute(text("SELECT numero_control, nombre, apellido_paterno FROM alumnos WHERE LOWER(numero_control)=:nc"), {"nc": nc}).fetchall()
        print(f"      '{nc}' x{c} -> {[(e[0], e[1]+' '+e[2]) for e in ex]}")

    # ---- B. Calificaciones en 0: ¿legítimas o dato faltante? ----
    print("\n[B] CALIFICACIONES en 0.0 - análisis")
    total = Calificacion.query.count()
    zeros = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE calificacion_final=0")).fetchone()[0]
    print(f"  0.0: {zeros}/{total} = {zeros/total*100:.1f}%")
    # desglosar si 0 tiene practicas también 0 y asistencias 0
    both_zero = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE calificacion_final=0 AND practica_1=0 AND practica_2=0 AND extra_1=0 AND extra_2=0")).fetchone()[0]
    print(f"  0.0 con todo en 0 (p1=p2=e1=e2=0): {both_zero} ({both_zero/zeros*100:.1f}% de los ceros)")
    partial = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE calificacion_final=0 AND (practica_1!=0 OR practica_2!=0 OR extra_1!=0 OR extra_2!=0)")).fetchone()[0]
    print(f"  0.0 pero con alguna práctica/extra !=0: {partial}")
    if partial>0:
        ex = db.session.execute(text("SELECT alumno_id, materia_id, practica_1, practica_2, extra_1, extra_2, calificacion_final FROM calificaciones WHERE calificacion_final=0 AND (practica_1!=0 OR practica_2!=0) LIMIT 5")).fetchall()
        for r in ex:
            print(f"    alumno={r[0]} materia={r[1]} p1={r[2]} p2={r[3]} e1={r[4]} e2={r[5]} final={r[6]}")
    # ver distribución por materia si ceros concentrados en materias nuevas PED huérfanas?
    print("\n  Ceros por carrera:")
    rows = db.session.execute(text("""
        SELECT c.codigo, COUNT(*) as total, SUM(CASE WHEN cal.calificacion_final=0 THEN 1 ELSE 0 END) as zeros
        FROM calificaciones cal
        JOIN materias m ON cal.materia_id=m.id
        JOIN carreras c ON m.carrera_id=c.id
        GROUP BY c.codigo
        ORDER BY zeros DESC
    """)).fetchall()
    for cod, tot, z in rows:
        print(f"    {cod:8} total={tot:4} zeros={z:4} ({z/tot*100:.0f}%)")
    # ver si materias con solo ceros son importadas sin nota?
    print("\n  Materias con 100% ceros (posible importación sin notas reales):")
    rows = db.session.execute(text("""
        SELECT m.id, m.nombre, c.codigo, COUNT(*) as tot, SUM(CASE WHEN cal.calificacion_final=0 THEN 1 ELSE 0 END) as zeros
        FROM calificaciones cal JOIN materias m ON cal.materia_id=m.id JOIN carreras c ON m.carrera_id=c.id
        GROUP BY m.id HAVING zeros=tot AND tot>5
        ORDER BY tot DESC LIMIT 10
    """)).fetchall()
    for mid, nom, cod, tot, z in rows:
        print(f"    [{cod}] {nom[:45]} tot={tot} zeros={z}")

    # ---- C. Generic loss vs ambos CSVs ----
    print("\n[C] GENÉRICOS: cruce completo con ambos formularios")
    for csv_path in ["C:/Users/Dario/Desktop/portal de alumnos/Formulario_reparado.csv",
                     "C:/Users/Dario/Desktop/portal de alumnos/BOLETAS TEOTITLAN 2025/Formulario sin título.csv"]:
        if not os.path.exists(csv_path):
            print(f"  {csv_path} NO existe")
            continue
        with open(csv_path, encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            print(f"  CSV: {os.path.basename(csv_path)} columnas={r.fieldnames} filas=", end="")
            rows_csv = list(r)
            print(len(rows_csv))
            # mapear por numero_control y por nombre
            by_nc = {}
            by_email = {}
            for row in rows_csv:
                nc = (row.get("Numero_control") or row.get("numero_control") or row.get("Matricula") or "").strip()
                correo = (row.get("Correo") or row.get("correo") or row.get("Email") or "").strip()
                nombres = (row.get("Nombres") or row.get("Nombre") or "").strip()
                ap = (row.get("Apellido_paterno") or "").strip()
                am = (row.get("Apellido_materno") or "").strip()
                if nc:
                    by_nc[nc] = correo
                # also by name
                key = f"{nombres.lower().strip()}|{ap.lower().strip()}|{am.lower().strip()}"
                if correo:
                    by_email[key] = correo
            # cruzar genericos
            genericos = db.session.execute(text("SELECT numero_control, nombre, apellido_paterno, apellido_materno, email FROM alumnos WHERE email LIKE '%generic.teotitlan%'")).fetchall()
            perdidos_nc = 0
            perdidos_nombre = 0
            for nc, nom, ap, am, em_db in genericos:
                correo_csv = by_nc.get(nc)
                if correo_csv and "@" in correo_csv and "generic" not in correo_csv.lower():
                    perdidos_nc += 1
                    if perdidos_nc <=3:
                        print(f"    PERDIDO por NC: {nc} csv='{correo_csv[:20]}***' db='{em_db.split('@')[0][:3]}***'")
                # por nombre
                key = f"{nom.lower().strip()}|{ap.lower().strip()}|{(am or '').lower().strip()}"
                correo_nombre = by_email.get(key)
                # no contamos doble
            print(f"    perdidos por NC exacto: {perdidos_nc}/{len(genericos)}")
            # also check alumnos_existentes.csv
    if os.path.exists("C:/Users/Dario/Desktop/portal de alumnos/backend/alumnos_existentes.csv"):
        with open("C:/Users/Dario/Desktop/portal de alumnos/backend/alumnos_existentes.csv", encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            print(f"\n  alumnos_existentes.csv columnas={r.fieldnames}")
            rows = list(r)
            print(f"    filas={len(rows)}")
            print(f"    sample {rows[0] if rows else 'vacío'}")

    # ---- D. BAJAS folder mapping ----
    print("\n[D] BAJAS: mapeo inactivos vs carpetas BAJA")
    inactivos = db.session.execute(text("SELECT numero_control, nombre, apellido_paterno, apellido_materno FROM alumnos WHERE activo=0")).fetchall()
    print(f"  Inactivos: {len(inactivos)}")
    # listar archivos en carpetas BAJA
    bajas = glob.glob("C:/Users/Dario/Desktop/portal de alumnos/BOLETAS TEOTITLAN 2025/**/BAJA*", recursive=True)
    for b in bajas:
        print(f"  Carpeta: {b}")
        files = glob.glob(os.path.join(b, "*"))
        print(f"    archivos: {len(files)}")
        for ff in files[:10]:
            print(f"      - {os.path.basename(ff)}")
        # extraer numero_control de filenames si contienen
        # buscar coincidencia inactivos vs filenames
        basenames = " ".join([os.path.basename(x) for x in files])
        matches = 0
        for nc, n, ap, am in inactivos:
            if nc in basenames:
                matches += 1
        print(f"    inactivos encontrados por filename match: {matches}")

    # ---- E. Materias duplicadas detalle LCD ----
    print("\n[E] MATERIA DUPLICADA LCD detalle")
    rows = db.session.execute(text("""
        SELECT id, nombre, codigo, carrera_id FROM materias
        WHERE LOWER(TRIM(nombre))='ciencias del deporte para personas con capacidades diferentes'
        ORDER BY codigo
    """)).fetchall()
    for mid, nom, cod, cid in rows:
        carr = db.session.get(Carrera, cid)
        cal_count = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE materia_id=:mid"), {"mid": mid}).fetchone()[0]
        print(f"  id={mid} codigo={cod} carrera={carr.codigo if carr else cid} califs={cal_count} nombre='{nom}'")
    # check si ambas tienen califs o una huérfana
    # also check materias huérfanas LIC-ADM
    print("\n  Materias LIC-ADM detalle (las 2 huérfanas):")
    rows = db.session.execute(text("SELECT id, nombre, codigo FROM materias WHERE carrera_id=1")).fetchall()
    for mid, nom, cod in rows:
        print(f"    id={mid} cod={cod} nombre={nom}")

    # ---- F. Periodo/anio distribution ----
    print("\n[F] Distribución periodo/anio en calificaciones")
    rows = db.session.execute(text("SELECT periodo, anio, COUNT(*) FROM calificaciones GROUP BY periodo, anio ORDER BY anio, periodo")).fetchall()
    for per, anio, c in rows:
        print(f"  periodo='{per}' anio={anio} count={c}")

    # ---- G. Email domain distribution ----
    print("\n[G] Dominios email (top 10)")
    rows = db.session.execute(text("SELECT SUBSTR(email, INSTR(email,'@')+1) as dom, COUNT(*) as c FROM alumnos GROUP BY dom ORDER BY c DESC")).fetchall()
    for dom, c in rows[:10]:
        print(f"  {dom}: {c}")
