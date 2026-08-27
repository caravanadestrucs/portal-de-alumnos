#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit NO-SORPRESAS - Portal de Alumnos
Solo LECTURA. Genera reporte anti-duplicados y anti-rarezas post migración BOLETAS TEOTITLAN 2025.
"""
import os
import csv
import re
import glob
from collections import defaultdict

from app import create_app
from models import db, Alumno, Materia, Calificacion, Carrera
from sqlalchemy import text

app = create_app()

def mask_email(e):
    if not e or '@' not in e:
        return '***'
    local, domain = e.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    if '.' in domain:
        parts = domain.split('.')
        masked_domain = parts[0][0] + '***.' + '.'.join(parts[1:])
    else:
        masked_domain = domain[0] + '***'
    return f"{masked_local}@{masked_domain}"

def run():
    print("="*80)
    print("AUDIT NO-SORPRESAS - Portal de Alumnos (solo lectura)")
    print("="*80)
    with app.app_context():
        checks = []

        def ok(name, detalle): checks.append((name, "OK", detalle))
        def warn(name, detalle): checks.append((name, "WARN", detalle))
        def fail(name, detalle): checks.append((name, "FAIL", detalle))

        # ------------------------------------------------------------
        # 0. Conteos generales
        # ------------------------------------------------------------
        print("\n[0] CONTEOS GENERALES")
        n_alumnos = Alumno.query.count()
        n_carreras = Carrera.query.count()
        n_materias = Materia.query.count()
        n_califs = Calificacion.query.count()
        print(f"  alumnos={n_alumnos} carreras={n_carreras} materias={n_materias} calificaciones={n_califs}")

        # Carreras detalle
        print("\n  Detalle carreras:")
        carreras = Carrera.query.order_by(Carrera.id).all()
        for c in carreras:
            print(f"    {c.id:>3} | {c.codigo:<10} | {c.nombre:<40} | alumnos={c.alumnos.count():>3} materias={c.materias.count():>3} activa={c.activa}")

        # ------------------------------------------------------------
        # 1. Alumnos duplicados: numero_control
        # ------------------------------------------------------------
        print("\n[1] ALUMNOS DUPLICADOS: numero_control")
        rows = db.session.execute(text("SELECT numero_control, COUNT(*) as c FROM alumnos GROUP BY numero_control HAVING c>1")).fetchall()
        if not rows:
            ok("Alumno.numero_control dup", "0 duplicados")
            print("  OK - 0 duplicados por numero_control")
        else:
            fail("Alumno.numero_control dup", f"{len(rows)} grupos duplicados")
            for r in rows[:5]:
                print(f"  FAIL: {r[0]} x{r[1]}")

        # ------------------------------------------------------------
        # 1b. Alumnos duplicados: email case-insensitive
        # ------------------------------------------------------------
        print("\n[1b] ALUMNOS DUPLICADOS: email case-insensitive (LOWER)")
        rows = db.session.execute(text("SELECT LOWER(email) as em, COUNT(*) as c FROM alumnos GROUP BY LOWER(email) HAVING c>1")).fetchall()
        if not rows:
            ok("Alumno.email dup (LOWER)", "0 duplicados case-insensitive")
            print("  OK - 0 duplicados por email LOWER")
        else:
            fail("Alumno.email dup (LOWER)", f"{len(rows)} grupos duplicados")
            for r in rows[:5]:
                # recuperar ejemplos
                ex = db.session.execute(text("SELECT numero_control, email, carrera_id FROM alumnos WHERE LOWER(email)=:em LIMIT 3"), {"em": r[0]}).fetchall()
                print(f"  FAIL: {mask_email(r[0])} x{r[1]} ejemplos: {[(e[0], mask_email(e[1]), e[2]) for e in ex]}")

        # También check exact email dup (por si acaso unique no distingue case según collation)
        rows_exact = db.session.execute(text("SELECT email, COUNT(*) as c FROM alumnos GROUP BY email HAVING c>1")).fetchall()
        print(f"  (exact email dup): {len(rows_exact)}")

        # ------------------------------------------------------------
        # 1c. generic emails colisiones
        # ------------------------------------------------------------
        print("\n[1c] GENERIC EMAILS: generic.teotitlan colisiones")
        generic_q = "SELECT id, email, numero_control, carrera_id FROM alumnos WHERE email LIKE '%generic.teotitlan%' ORDER BY email"
        rows = db.session.execute(text(generic_q)).fetchall()
        print(f"  total generic: {len(rows)}")
        # verificar suffix único (local part)
        seen = {}
        dups = []
        for _id, email, nc, carr in rows:
            local = email.split('@')[0] if '@' in email else email
            if local in seen:
                dups.append((email, nc, local))
            else:
                seen[local] = (email, nc)
        if dups:
            fail("generic suffix colisión", f"{len(dups)} colisiones de suffix")
            for d in dups[:5]:
                print(f"  FAIL colisión: {mask_email(d[0])} nc={d[1]} suffix={d[2]}")
        else:
            ok("generic suffix colisión", f"{len(rows)} generic, 0 colisiones de suffix -> OK")

        # verificar formato esperado: alumno_TEO2025XXXX@generic.teotitlan.local ??? listar patrones
        pattern_counts = defaultdict(int)
        for _id, email, nc, carr in rows:
            pattern_counts[email.split('@')[1] if '@' in email else 'NO_DOMAIN'] += 1
        print(f"  dominios generic: {dict(pattern_counts)}")
        # check que numero_control embebido coincide?
        mismatched = []
        for _id, email, nc, carr in rows:
            local = email.split('@')[0]
            # extraer TEO2025XXXX del local
            m = re.search(r'TEO2025\d+', local)
            if m and m.group(0) != nc:
                mismatched.append((nc, email))
        if mismatched:
            warn("generic email / nc mismatch", f"{len(mismatched)} casos donde TEO en email != numero_control")
            for nc, em in mismatched[:5]:
                print(f"  WARN mismatch: nc={nc} email={mask_email(em)}")
        else:
            ok("generic email / nc match", "Todos los generic embeben correctamente el numero_control")

        # ------------------------------------------------------------
        # 1d. TEO2025 colisión con reales
        # ------------------------------------------------------------
        print("\n[1d] numero_control sintético TEO2025XXXX colisión con reales")
        teo = db.session.execute(text("SELECT numero_control FROM alumnos WHERE numero_control LIKE 'TEO2025%'")).fetchall()
        non_teo = db.session.execute(text("SELECT numero_control FROM alumnos WHERE numero_control NOT LIKE 'TEO2025%'")).fetchall()
        print(f"  TEO2025: {len(teo)} | reales: {len(non_teo)}")
        teo_set = set(r[0] for r in teo)
        non_set = set(r[0] for r in non_teo)
        overlap = teo_set & non_set
        if overlap:
            fail("TEO2025 colisión", f"{len(overlap)} colisiones TEO vs real: {list(overlap)[:5]}")
        else:
            ok("TEO2025 colisión", f"0 colisiones (TEO={len(teo)}, reales={len(non_teo)})")

        # Longitud check
        lens = db.session.execute(text("SELECT LENGTH(numero_control) as l, COUNT(*) FROM alumnos GROUP BY LENGTH(numero_control)")).fetchall()
        print(f"  distribución longitud nc: {[(r[0], r[1]) for r in lens]}")
        ejemplos_real = db.session.execute(text("SELECT numero_control, email FROM alumnos WHERE numero_control NOT LIKE 'TEO2025%' LIMIT 3")).fetchall()
        ejemplos_teo = db.session.execute(text("SELECT numero_control, email FROM alumnos WHERE numero_control LIKE 'TEO2025%' LIMIT 3")).fetchall()
        print(f"  ej. reales: {[(r[0], mask_email(r[1])) for r in ejemplos_real]}")
        print(f"  ej. TEO:    {[(r[0], mask_email(r[1])) for r in ejemplos_teo]}")

        # ------------------------------------------------------------
        # 2. Materias duplicadas / extra
        # ------------------------------------------------------------
        print("\n[2] MATERIAS DUPLICADAS por nombre dentro de misma carrera")
        rows = db.session.execute(text("SELECT carrera_id, LOWER(TRIM(nombre)) as norm, COUNT(*) as c FROM materias GROUP BY carrera_id, LOWER(TRIM(nombre)) HAVING c>1")).fetchall()
        if not rows:
            ok("Materia nombre dup por carrera", "0 duplicados exactos por nombre normalizado dentro de misma carrera")
            print("  OK - 0 duplicados por (carrera_id, LOWER(TRIM(nombre)))")
        else:
            fail("Materia nombre dup por carrera", f"{len(rows)} grupos duplicados")
            for carr_id, norm, c in rows[:5]:
                carr = db.session.get(Carrera, carr_id)
                ex = db.session.execute(text("SELECT id, nombre, codigo FROM materias WHERE carrera_id=:cid AND LOWER(TRIM(nombre))=:nm LIMIT 3"), {"cid": carr_id, "nm": norm}).fetchall()
                print(f"  FAIL carrera={carr.codigo if carr else carr_id} norm='{norm}' x{c} -> {[(e[0], e[1], e[2]) for e in ex]}")

        print("\n[2b] MATERIAS DUPLICADAS por codigo global")
        # codigo no es unique global en modelo? Solo unique en algunos casos. Verificamos.
        rows = db.session.execute(text("SELECT codigo, COUNT(*) as c FROM materias GROUP BY codigo HAVING c>1")).fetchall()
        # filtrar vacíos
        rows_nonempty = [r for r in rows if r[0]]
        print(f"  grupos con mismo código (incl. vacío): {len(rows)} | sin vacíos: {len(rows_nonempty)}")
        if rows_nonempty:
            # Esto puede ser ESPERABLE si materias comparten código entre carreras. Lo marcamos como WARN y mostramos.
            # Pero si hay duplicados dentro misma carrera con mismo código -> eso sí es FAIL.
            warn("Materia codigo dup global", f"{len(rows_nonempty)} códigos repetidos globalmente (puede ser normal si se comparten entre carreras)")
            for codigo, c in rows_nonempty[:5]:
                ex = db.session.execute(text("SELECT id, nombre, carrera_id FROM materias WHERE codigo=:cod LIMIT 5"), {"cod": codigo}).fetchall()
                print(f"    codigo='{codigo}' x{c} ejemplos: {[(e[0], e[1], e[2]) for e in ex]}")
            # check intra-carrera codigo dup
            rows_intra = db.session.execute(text("SELECT carrera_id, codigo, COUNT(*) as c FROM materias WHERE codigo!='' AND codigo IS NOT NULL GROUP BY carrera_id, codigo HAVING c>1")).fetchall()
            if rows_intra:
                fail("Materia codigo dup intra-carrera", f"{len(rows_intra)} códigos repetidos DENTRO misma carrera")
                for carr_id, codigo, c in rows_intra[:5]:
                    carr = db.session.get(Carrera, carr_id)
                    print(f"    FAIL carrera={carr.codigo if carr else carr_id} codigo='{codigo}' x{c}")
            else:
                ok("Materia codigo dup intra-carrera", "0 duplicados de código dentro misma carrera")
        else:
            ok("Materia codigo dup global", "0 códigos duplicados (no vacíos)")

        print("\n[2c] MATERIAS HUÉRFANAS (sin calificaciones)")
        # Materias con 0 calificaciones
        rows = db.session.execute(text("""
            SELECT m.id, m.nombre, m.codigo, m.carrera_id, c.codigo as carr_cod, c.nombre as carr_nom
            FROM materias m JOIN carreras c ON m.carrera_id=c.id
            LEFT JOIN calificaciones cal ON cal.materia_id=m.id
            WHERE cal.id IS NULL
            ORDER BY c.codigo, m.nombre
        """)).fetchall()
        print(f"  materias sin calificaciones: {len(rows)} / {n_materias}")
        # agrupar por carrera
        by_carr = defaultdict(list)
        for r in rows:
            by_carr[r[4]] += [r]
        for carr_cod, lst in sorted(by_carr.items()):
            carr_nombre = lst[0][5] if lst else "?"
            n_alus = db.session.execute(text("SELECT COUNT(*) FROM alumnos WHERE carrera_id=(SELECT id FROM carreras WHERE codigo=:cod)"), {"cod": carr_cod}).fetchone()[0]
            print(f"    {carr_cod} ({carr_nombre}): {len(lst)} materias huérfanas | alumnos en carrera={n_alus}")
            # mostrar 2 ejemplos
            for e in lst[:2]:
                print(f"      - [{e[2]}] {e[1]} (id={e[0]})")
        # si carrera tiene 0 alumnos Y 0 calificaciones -> sospechosa? Según lista, LIC-ADM y LC etc son legacy
        print("\n  Análisis esperado vs extra:")
        carreras_legacy = ["LIC-ADM", "ISC", "LC", "LD", "LP", "LPS", "LCD", "LENF"]
        for carr_cod in sorted(by_carr.keys()):
            if carr_cod in carreras_legacy:
                print(f"    {carr_cod}: LEGACY esperable - materias sin alumnos/califs es normal (carreras viejas reemplazadas por PED/ENF/etc)")
            else:
                # PED etc deberían tener califs; si tiene muchas huérfanas revisar
                alus = db.session.execute(text("SELECT COUNT(*) FROM alumnos WHERE carrera_id=(SELECT id FROM carreras WHERE codigo=:cod)"), {"cod": carr_cod}).fetchone()[0]
                mats_huerf = len(by_carr[carr_cod])
                mats_total = db.session.execute(text("SELECT COUNT(*) FROM materias WHERE carrera_id=(SELECT id FROM carreras WHERE codigo=:cod)"), {"cod": carr_cod}).fetchone()[0]
                califs = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE materia_id IN (SELECT id FROM materias WHERE carrera_id=(SELECT id FROM carreras WHERE codigo=:cod))"), {"cod": carr_cod}).fetchone()[0]
                if mats_huerf > 0 and alus > 0:
                    if califs == 0:
                        warn(f"Materia huérfana {carr_cod}", f"{mats_huerf}/{mats_total} sin califs pero con {alus} alumnos -> ¿datos faltantes?")
                    else:
                        ok(f"Materia huérfana {carr_cod}", f"{mats_huerf}/{mats_total} huérfanas pero {califs} califs existen -> probablemente materias legítimas sin cursado aún")

        # ------------------------------------------------------------
        # 3. Calificaciones
        # ------------------------------------------------------------
        print("\n[3] CALIFICACIONES DUPLICADAS (alumno_id, materia_id, periodo, anio)")
        # Probar ambos group by
        try:
            rows = db.session.execute(text("SELECT alumno_id, materia_id, periodo, anio, COUNT(*) as c FROM calificaciones GROUP BY alumno_id, materia_id, periodo, anio HAVING c>1")).fetchall()
            print(f"  duplicados con (alumno,materia,periodo,anio): {len(rows)}")
            if rows:
                fail("Calif dup (alumno+materia+periodo+anio)", f"{len(rows)} grupos")
                for r in rows[:5]:
                    print(f"    FAIL alumno={r[0]} materia={r[1]} periodo={r[2]} anio={r[3]} x{r[4]}")
            else:
                ok("Calif dup (alumno+materia+periodo+anio)", "0 duplicados (UniqueConstraint funciona)")
        except Exception as e:
            print(f"  error: {e}")

        # duplicados solo alumno+materia (ignorando periodo para detectar lógica rara)
        rows = db.session.execute(text("SELECT alumno_id, materia_id, COUNT(*) as c FROM calificaciones GROUP BY alumno_id, materia_id HAVING c>1")).fetchall()
        print(f"  duplicados solo (alumno,materia) sin periodo: {len(rows)}")
        # Esto puede ser LEGÍTIMO si hay múltiples periodos. Verificamos cuántos tienen periodo distinto
        if rows:
            # ver si son mismo periodo
            sample = rows[0]
            details = db.session.execute(text("SELECT id, periodo, anio, calificacion_final FROM calificaciones WHERE alumno_id=:a AND materia_id=:m"), {"a": sample[0], "m": sample[1]}).fetchall()
            print(f"    ejemplo alumno={sample[0]} materia={sample[1]} x{sample[2]} detalles: {[(d[1], d[2], d[3]) for d in details[:5]]}")
            # si periodo distinto -> es esperado (recursada)
            # si todos tienen mismo periodo -> FAIL real
            dup_mismo_periodo = 0
            for a, m, c in rows[:20]:
                per = db.session.execute(text("SELECT DISTINCT periodo, anio FROM calificaciones WHERE alumno_id=:a AND materia_id=:m"), {"a": a, "m": m}).fetchall()
                if len(per) == 1:
                    dup_mismo_periodo += 1
            if dup_mismo_periodo > 0:
                fail("Calif dup mismo periodo", f"{dup_mismo_periodo} casos con mismo periodo/anio -> posible duplicado lógico")
            else:
                ok("Calif dup mismo periodo", f"{len(rows)} duplicados (alumno+materia) pero con periodos distintos -> legítimo (recursadas/historial)")

        print("\n[3b] CALIFICACIONES HUÉRFANAS (FK rota)")
        rows = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE alumno_id NOT IN (SELECT id FROM alumnos)")).fetchone()
        print(f"  califs con alumno_id inexistente: {rows[0]}")
        rows2 = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE materia_id NOT IN (SELECT id FROM materias)")).fetchone()
        print(f"  califs con materia_id inexistente: {rows2[0]}")
        if rows[0]==0 and rows2[0]==0:
            ok("Calif huérfana", "0 huérfanas")
        else:
            fail("Calif huérfana", f"alumno rota={rows[0]} materia rota={rows2[0]}")

        print("\n[3c] CALIFICACIONES fuera de rango (0-10) o NULL")
        rows = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE calificacion_final < 0 OR calificacion_final > 10")).fetchone()
        print(f"  calificacion_final fuera de [0,10]: {rows[0]}")
        rows_null = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE calificacion_final IS NULL")).fetchone()
        print(f"  calificacion_final NULL: {rows_null[0]}")
        rows_extras = db.session.execute(text("SELECT COUNT(*) FROM calificaciones WHERE (practica_1 <0 OR practica_1>10 OR practica_2<0 OR practica_2>10 OR extra_1<0 OR extra_1>10 OR extra_2<0 OR extra_2>10)")).fetchone()
        print(f"  practica/extra fuera [0,10]: {rows_extras[0]}")
        if rows[0]==0 and rows_extras[0]==0:
            ok("Calif rango", "todas en [0,10]")
        else:
            warn("Calif rango", f"final fuera={rows[0]} pract/extra fuera={rows_extras[0]}")
        if rows_null[0]>0:
            warn("Calif NULL", f"{rows_null[0]} NULL")
        else:
            ok("Calif NULL", "0 NULL")

        # Distribución calificaciones
        rows = db.session.execute(text("SELECT calificacion_final, COUNT(*) FROM calificaciones GROUP BY calificacion_final ORDER BY calificacion_final LIMIT 15")).fetchall()
        print(f"  distribución sample: {[(r[0], r[1]) for r in rows[:10]]}")

        # ------------------------------------------------------------
        # 4. Carreras
        # ------------------------------------------------------------
        print("\n[4] CARRERAS: variantes normalizadas / fantasmas")
        for c in carreras:
            print(f"  {c.codigo:10} | alumnos={c.alumnos.count():>3} materias={c.materias.count():>3} | activa={c.activa} | {c.nombre}")
        # carreras sin alumnos y sin materias -> extra/fantasma
        ghosts = [c for c in carreras if c.alumnos.count()==0 and c.materias.count()==0]
        if ghosts:
            warn("Carrera fantasma", f"{len(ghosts)} carreras sin alumnos ni materias: {[c.codigo for c in ghosts]}")
        else:
            ok("Carrera fantasma", "0 carreras 100% vacías")
        ghosts2 = [c for c in carreras if c.alumnos.count()==0 and c.materias.count()>0]
        if ghosts2:
            print(f"  carreras legacy sin alumnos pero con materias (esperable tras migración): {[c.codigo for c in ghosts2]}")
            ok("Carrera legacy sin alumnos", f"{len(ghosts2)} carreras legacy vacías de alumnos pero con materias -> OK (no borrar)")
        # carreras sin materias pero con alumnos -> raro
        ghosts3 = [c for c in carreras if c.alumnos.count()>0 and c.materias.count()==0]
        if ghosts3:
            fail("Carrera sin materias", f"{len(ghosts3)} carreras con alumnos pero 0 materias: {[c.codigo for c in ghosts3]}")
        else:
            ok("Carrera sin materias", "0 carreras con alumnos y 0 materias")

        # ------------------------------------------------------------
        # 5. Integridad general
        # ------------------------------------------------------------
        print("\n[5] INTEGRIDAD GENERAL")

        # alumnos sin carrera_id válido
        rows = db.session.execute(text("SELECT COUNT(*) FROM alumnos WHERE carrera_id NOT IN (SELECT id FROM carreras)")).fetchone()
        print(f"  alumnos con carrera_id inválida: {rows[0]}")
        if rows[0]==0: ok("FK alumno.carrera_id", "0 rotas")
        else: fail("FK alumno.carrera_id", f"{rows[0]} rotas")

        # activo NULL
        rows = db.session.execute(text("SELECT COUNT(*) FROM alumnos WHERE activo IS NULL")).fetchone()
        print(f"  alumnos con activo NULL: {rows[0]}")
        if rows[0]==0: ok("Alumno.activo NULL", "0 NULL")
        else: fail("Alumno.activo NULL", f"{rows[0]} NULL")

        # distribución activo
        rows = db.session.execute(text("SELECT activo, COUNT(*) FROM alumnos GROUP BY activo")).fetchall()
        print(f"  distribución activo: {[(r[0], r[1]) for r in rows]}")

        # genéricos vs CSV original - cruza sample
        print("\n[5b] ¿GENÉRICOS justificados? Cruce con CSV original")
        # buscar CSVs en BOLETAS TEOTITLAN 2025 y backend
        csv_candidates = glob.glob("C:/Users/Dario/Desktop/portal de alumnos/BOLETAS TEOTITLAN 2025/**/*.csv", recursive=True)
        csv_candidates += glob.glob("C:/Users/Dario/Desktop/portal de alumnos/backend/*.csv")
        csv_candidates += glob.glob("C:/Users/Dario/Desktop/portal de alumnos/*.csv")
        print(f"  CSV candidatos encontrados: {len(csv_candidates)}")
        for p in csv_candidates[:10]:
            print(f"    - {p}")
        # intentar leer alumnos_existentes.csv si existe
        check_csv = "C:/Users/Dario/Desktop/portal de alumnos/backend/alumnos_existentes.csv"
        # y buscar el import original log
        # fallback: verificar que los 103 genéricos realmente no tenían email en PDF/formulario
        genericos = db.session.execute(text("SELECT numero_control, email FROM alumnos WHERE email LIKE '%generic.teotitlan%'")).fetchall()
        print(f"  genéricos en DB: {len(genericos)}")
        # si tenemos Formulario_reparado.csv, cruzamos
        form_csv = "C:/Users/Dario/Desktop/portal de alumnos/Formulario_reparado.csv"
        if os.path.exists(form_csv):
            with open(form_csv, newline='', encoding='utf-8-sig') as f:
                r = csv.DictReader(f)
                print(f"  Formulario_reparado.csv columnas: {r.fieldnames}")
                # buscar email column
                emails_form = {}
                for row in r:
                    nc = row.get('numero_control') or row.get('Numero_control') or row.get('NUMERO_CONTROL') or row.get('matricula') or ''
                    email = row.get('email') or row.get('Email') or row.get('correo') or row.get('Correo') or ''
                    if nc:
                        emails_form[nc.strip()] = email.strip() if email else ''
                # cruzar 5 genéricos
                print(f"  Formulario filas: {len(emails_form)}")
                for nc, em in genericos[:5]:
                    val = emails_form.get(nc, "NO_EN_CSV")
                    print(f"    genérico nc={nc} email_db={mask_email(em)} -> en Formulario: '{val[:30] if val else '(vacío)'}' ")
                # contar cuántos genéricos tenían email real en CSV y se perdió
                perdidos = 0
                for nc, em in genericos:
                    v = emails_form.get(nc)
                    if v and v.strip() and '@' in v and 'generic' not in v.lower():
                        perdidos += 1
                if perdidos>0:
                    warn("Pérdida de email en genéricos", f"{perdidos}/{len(genericos)} genéricos tenían email real en Formulario_reparado.csv y se reemplazó por genérico")
                else:
                    ok("Pérdida de email en genéricos", f"0/{len(genericos)} genéricos con email real desperdiciado en Formulario CSV -> fallback correcto")
        else:
            print("  Formulario_reparado.csv no encontrado, salto cruce fino")

        # Cuentas pendientes/BAJA
        print("\n[5c] INACTIVOS (BAJA / PENDIENTE)")
        inactivos = db.session.execute(text("SELECT id, numero_control, nombre, apellido_paterno, email, activo FROM alumnos WHERE activo=0")).fetchall()
        print(f"  inactivos (activo=0): {len(inactivos)}")
        for r in inactivos[:5]:
            print(f"    - {r[1]} | {r[2]} {r[3]} | {mask_email(r[4])} | activo={r[5]}")
        # Verificar si hay PENDIENTE en nombre
        pend_in_name = db.session.execute(text("SELECT COUNT(*) FROM alumnos WHERE nombre LIKE '%PENDIENTE%' OR apellido_paterno LIKE '%PENDIENTE%' OR apellido_materno LIKE '%PENDIENTE%'")).fetchone()[0]
        print(f"  alumnos con 'PENDIENTE' en nombre/apellido: {pend_in_name}")
        # Check BAJA folder
        baja_pat = "C:/Users/Dario/Desktop/portal de alumnos/BOLETAS TEOTITLAN 2025/**/BAJA*"
        baja_files = glob.glob(baja_pat, recursive=True)
        print(f"  archivos/carpetas con BAJA: {len(baja_files)}")
        for p in baja_files[:8]:
            print(f"    - {p}")
        # Listar alumnos en carpeta BAJA si hay csv?
        # También verificar si los inactivos coinciden con carpeta BAJA por número_control en filename
        if len(inactivos)==10:
            ok("Inactivos count", "10 inactivos -> coincide con esperado (carpeta BAJA + PENDIENTE)")
        else:
            warn("Inactivos count", f"{len(inactivos)} inactivos != 10 esperados -> revisar")

        # activos con notas raras
        print("\n[5d] Checks extra")
        dup_names = db.session.execute(text("SELECT LOWER(TRIM(nombre))||'|'||LOWER(TRIM(apellido_paterno))||'|'||COALESCE(LOWER(TRIM(apellido_materno)),''), COUNT(*) as c FROM alumnos GROUP BY LOWER(TRIM(nombre)), LOWER(TRIM(apellido_paterno)), LOWER(TRIM(apellido_materno)) HAVING c>1")).fetchall()
        print(f"  nombres completos duplicados exactos (case-insensitive): {len(dup_names)}")
        if len(dup_names)>0:
            warn("Nombre duplicado", f"{len(dup_names)} grupos con mismo nombre completo -> verificar homónimos vs duplicado real")
            for nm, c in dup_names[:5]:
                ex = db.session.execute(text("SELECT numero_control, carrera_id FROM alumnos WHERE LOWER(TRIM(nombre))||'|'||LOWER(TRIM(apellido_paterno))||'|'||COALESCE(LOWER(TRIM(apellido_materno)),'')=:nm LIMIT 3"), {"nm": nm}).fetchall()
                print(f"    '{nm}' x{c} -> {[(e[0], e[1]) for e in ex]}")
        else:
            ok("Nombre duplicado", "0 homónimos exactos")

        # Email vacío o malformado
        malformed = db.session.execute(text("SELECT COUNT(*) FROM alumnos WHERE email IS NULL OR email='' OR email NOT LIKE '%@%'")).fetchone()[0]
        print(f"  emails malformados/vacíos: {malformed}")
        if malformed>0: fail("Email malformado", f"{malformed} vacíos o sin @")
        else: ok("Email malformado", "0 malformados")

        # ------------------------------------------------------------
        # TABLA RESUMEN
        # ------------------------------------------------------------
        print("\n" + "="*80)
        print("TABLA RESUMEN POR CHECK (OK / WARN / FAIL)")
        print("="*80)
        for name, status, detalle in checks:
            icon = {"OK":"[OK]","WARN":"[WARN]","FAIL":"[FAIL]"}[status]
            print(f"  {icon} {status:4} | {name:<35} | {detalle}")

        # conteo resumen
        n_ok = sum(1 for _, s, _ in checks if s=="OK")
        n_warn = sum(1 for _, s, _ in checks if s=="WARN")
        n_fail = sum(1 for _, s, _ in checks if s=="FAIL")
        print(f"\n  Totales: OK={n_ok} WARN={n_warn} FAIL={n_fail} (total checks={len(checks)})")

        print("\n[FIN AUDIT NO-SORPRESAS - solo lectura, sin modificaciones]")

if __name__ == "__main__":
    run()
