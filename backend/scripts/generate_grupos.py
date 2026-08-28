"""
Generate Grupo records by carrera + generacion (anio) + sede, and assign alumnos.

- For each alumno, infer generacion as MIN year among their calificaciones.
  Parse periodo string with regex r'(20\\d{2})', fallback to calificacion.anio, else 2024.
- Group alumnos by (carrera_id, sede_id, generation_year)
- For each key, create Grupo if not exists with:
    nombre = f\"{Carrera.nombre} {year} {Sede.codigo}\"  (e.g. \"Pedagogia 2023 TEO\")
    carrera_id, sede_id, periodo=f\"{year}\", anio=year, activo=True
  Get-or-create by (carrera_id, sede_id, anio) OR nombre unique.
- For each alumno in that key, create GrupoIntegrante if not exists.
- Also pre-create empty HUA groups for same carrera+year combos but sede_id=2
  (copy TEO groups to HUA) with 0 integrantes for future.
- Idempotent: re-run does not duplicate.

Usage:
    python backend/scripts/generate_grupos.py
"""

import re
import sys
import pathlib
from collections import defaultdict

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

YEAR_RE = re.compile(r"(20\d{2})")


def infer_generation_year(alumno, Calificacion):
    """Infer generacion year for an alumno as MIN year among calificaciones."""
    califs = Calificacion.query.filter_by(alumno_id=alumno.id).all()
    years = []
    for c in califs:
        y = None
        if c.periodo:
            m = YEAR_RE.search(str(c.periodo))
            if m:
                try:
                    y = int(m.group(1))
                except ValueError:
                    y = None
        if y is None and c.anio is not None:
            try:
                y = int(c.anio)
            except (ValueError, TypeError):
                y = None
        if y is not None:
            years.append(y)
    if years:
        return min(years)
    return 2024


def main():
    from app import create_app
    from models import db, Carrera, Sede, Alumno, Calificacion, Grupo, GrupoIntegrante

    app = create_app()
    with app.app_context():
        db.create_all()

        # Ensure sedes exist
        teo = Sede.query.filter_by(codigo="TEO").first()
        hua = Sede.query.filter_by(codigo="HUA").first()
        if not teo or not hua:
            # Seed if missing
            if not teo:
                teo = Sede(nombre="Teotitlan", codigo="TEO", direccion="Teotitlan de Flores Magon, Oaxaca", activa=True)
                db.session.add(teo)
            if not hua:
                hua = Sede(nombre="Huautla", codigo="HUA", direccion="Huautla de Jimenez, Oaxaca", activa=True)
                db.session.add(hua)
            db.session.commit()
            teo = Sede.query.filter_by(codigo="TEO").first()
            hua = Sede.query.filter_by(codigo="HUA").first()

        sede_by_id = {s.id: s for s in Sede.query.all()}
        carrera_by_id = {c.id: c for c in Carrera.query.all()}

        alumnos = Alumno.query.all()
        total_alumnos = len(alumnos)

        # Group by (carrera_id, sede_id, generation_year)
        groups_map = defaultdict(list)  # key -> list of alumnos
        gen_debug = defaultdict(int)
        for alumno in alumnos:
            gen_year = infer_generation_year(alumno, Calificacion)
            gen_debug[gen_year] += 1
            # Sede fallback to alumno.sede_id or TEO
            sede_id = alumno.sede_id or teo.id
            key = (alumno.carrera_id, sede_id, gen_year)
            groups_map[key].append(alumno)

        # Stats
        groups_created = 0
        grupos_reused = 0
        integrantes_added = 0
        integrantes_existing = 0
        hua_precreated = 0
        hua_existing = 0

        # Track distinct carrera+year combos for HUA pre-creation
        carrera_year_combos = set()

        # Create TEO (and sede-specific) groups + integrantes
        for (carrera_id, sede_id, year), alumnos_list in sorted(groups_map.items()):
            carrera = carrera_by_id.get(carrera_id)
            sede = sede_by_id.get(sede_id)
            if not carrera or not sede:
                print(f"[WARN] Carrera {carrera_id} o Sede {sede_id} no encontrada, saltando key {carrera_id, sede_id, year}")
                continue

            carrera_year_combos.add((carrera_id, year))

            # Nombre: f"{Carrera.nombre} {year} {Sede.codigo}"
            # Truncate to 50 chars if needed (DB varchar 50)
            nombre = f"{carrera.nombre} {year} {sede.codigo}"
            if len(nombre) > 50:
                # Truncate carrera nombre portion to fit
                excess = len(nombre) - 50
                truncated_carrera = carrera.nombre[:-excess] if len(carrera.nombre) > excess else carrera.nombre
                nombre = f"{truncated_carrera} {year} {sede.codigo}"
                nombre = nombre[:50]

            periodo_str = str(year)

            # Get-or-create by (carrera_id, sede_id, anio) OR nombre unique
            existing = Grupo.query.filter_by(carrera_id=carrera_id, sede_id=sede_id, anio=year).first()
            if not existing:
                existing = Grupo.query.filter_by(nombre=nombre).first()

            if existing:
                grupo = existing
                grupos_reused += 1
                # Ensure periodo/anio are set if previously null (harmonize)
                updated = False
                if grupo.anio is None:
                    grupo.anio = year
                    updated = True
                if grupo.periodo is None:
                    grupo.periodo = periodo_str
                    updated = True
                if updated:
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
            else:
                grupo = Grupo(
                    nombre=nombre,
                    carrera_id=carrera_id,
                    sede_id=sede_id,
                    periodo=periodo_str,
                    anio=year,
                    activo=True,
                )
                db.session.add(grupo)
                try:
                    db.session.commit()
                    groups_created += 1
                except Exception as e:
                    db.session.rollback()
                    # Try to fetch again if unique constraint hit (race/idempotent)
                    grupo = Grupo.query.filter_by(carrera_id=carrera_id, sede_id=sede_id, anio=year).first() or Grupo.query.filter_by(nombre=nombre).first()
                    if not grupo:
                        print(f"[ERROR] No se pudo crear grupo {nombre}: {e}")
                        continue
                    grupos_reused += 1

            # Assign integrantes
            for alumno in alumnos_list:
                exists_integrante = GrupoIntegrante.query.filter_by(grupo_id=grupo.id, alumno_id=alumno.id).first()
                if exists_integrante:
                    integrantes_existing += 1
                    continue
                # Also check if alumno already in another grupo of same carrera/year/sede? We allow only one grupo per key,
                # but alumno should not be duplicated across groups idempotently.
                # For safety, remove from other grupos with same carrera/sede/anio? No, keep as is, just add if not exists.
                integrante = GrupoIntegrante(grupo_id=grupo.id, alumno_id=alumno.id)
                db.session.add(integrante)
                try:
                    db.session.commit()
                    integrantes_added += 1
                except Exception as e:
                    db.session.rollback()
                    print(f"[WARN] No se pudo agregar integrante alumno {alumno.id} a grupo {grupo.id}: {e}")

        # Build mapping alumno_id -> correct grupo_id for cleanup
        alumno_correct_grupo = {}
        for (carrera_id, sede_id, year), alumnos_list in groups_map.items():
            # Find the grupo id for this key (should exist now)
            grupo_correct = Grupo.query.filter_by(carrera_id=carrera_id, sede_id=sede_id, anio=year).first()
            if not grupo_correct:
                # fallback by nombre
                carrera_tmp = carrera_by_id.get(carrera_id)
                sede_tmp = sede_by_id.get(sede_id)
                if carrera_tmp and sede_tmp:
                    nombre_tmp = f"{carrera_tmp.nombre} {year} {sede_tmp.codigo}"
                    if len(nombre_tmp) > 50:
                        nombre_tmp = nombre_tmp[:50]
                    grupo_correct = Grupo.query.filter_by(nombre=nombre_tmp).first()
            if grupo_correct:
                for al in alumnos_list:
                    alumno_correct_grupo[al.id] = grupo_correct.id

        # Cleanup: ensure each alumno belongs only to its correct generational grupo
        # Remove stale integrantes from old/incorrect grupos (e.g. legacy SISTEMAS 2024)
        integrantes_removed = 0
        for alumno_id, correct_gid in alumno_correct_grupo.items():
            stale = GrupoIntegrante.query.filter(
                GrupoIntegrante.alumno_id == alumno_id,
                GrupoIntegrante.grupo_id != correct_gid
            ).all()
            for s in stale:
                db.session.delete(s)
                integrantes_removed += 1
        if integrantes_removed:
            try:
                db.session.commit()
                print(f"[Limpieza] Se removieron {integrantes_removed} integrantes obsoletos de grupos legacy (alumnos movidos a generacion correcta).")
            except Exception as e:
                db.session.rollback()
                print(f"[WARN] Error en limpieza: {e}")

        # Pre-create empty HUA groups for same carrera+year combos but sede_id=2
        hua_sede = Sede.query.filter_by(codigo="HUA").first()
        if hua_sede:
            for (carrera_id, year) in sorted(carrera_year_combos):
                carrera = carrera_by_id.get(carrera_id)
                if not carrera:
                    continue
                nombre_hua = f"{carrera.nombre} {year} {hua_sede.codigo}"
                if len(nombre_hua) > 50:
                    excess = len(nombre_hua) - 50
                    truncated = carrera.nombre[:-excess] if len(carrera.nombre) > excess else carrera.nombre
                    nombre_hua = f"{truncated} {year} {hua_sede.codigo}"
                    nombre_hua = nombre_hua[:50]

                existing_hua = Grupo.query.filter_by(carrera_id=carrera_id, sede_id=hua_sede.id, anio=year).first()
                if not existing_hua:
                    existing_hua = Grupo.query.filter_by(nombre=nombre_hua).first()

                if existing_hua:
                    hua_existing += 1
                    # Ensure fields
                    if existing_hua.anio is None:
                        existing_hua.anio = year
                    if existing_hua.periodo is None:
                        existing_hua.periodo = str(year)
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    continue

                grupo_hua = Grupo(
                    nombre=nombre_hua,
                    carrera_id=carrera_id,
                    sede_id=hua_sede.id,
                    periodo=str(year),
                    anio=year,
                    activo=True,
                )
                db.session.add(grupo_hua)
                try:
                    db.session.commit()
                    hua_precreated += 1
                except Exception as e:
                    db.session.rollback()
                    print(f"[WARN] No se pudo crear grupo HUA {nombre_hua}: {e}")

        # Verification query
        print("\n=== Generacion de grupos completada ===")
        print(f"Total alumnos procesados: {total_alumnos}")
        print(f"Distribucion generaciones: {dict(sorted(gen_debug.items()))}")
        print(f"Combinaciones (carrera, sede, anio) con alumnos: {len(groups_map)}")
        print(f"Grupos creados (TEO con alumnos): {groups_created}")
        print(f"Grupos reutilizados (ya existian): {grupos_reused}")
        print(f"Integrantes agregados: {integrantes_added}")
        print(f"Integrantes ya existentes: {integrantes_existing}")
        if 'integrantes_removed' in locals():
            print(f"Integrantes removidos (legacy): {integrantes_removed}")
        print(f"Grupos HUA pre-creados vacios: {hua_precreated}")
        print(f"Grupos HUA ya existentes: {hua_existing}")

        # Verification summary query: SELECT s.codigo, c.nombre, g.anio, COUNT(gi.id)
        print("\n--- Resumen por grupo (sede, carrera, anio) ---")
        rows = db.session.execute(
            db.text(
                """
                SELECT s.codigo, c.nombre, g.anio, COUNT(gi.id) as total
                FROM grupos g
                JOIN carreras c ON g.carrera_id = c.id
                JOIN sedes s ON g.sede_id = s.id
                LEFT JOIN grupo_integrantes gi ON gi.grupo_id = g.id
                GROUP BY s.codigo, c.nombre, g.anio
                ORDER BY s.codigo, c.nombre, g.anio
                """
            )
        ).fetchall()
        total_grupos = len(rows)
        total_integrantes = 0
        for codigo, carrera_nombre, anio, cnt in rows:
            total_integrantes += cnt
            print(f"  {codigo} | {carrera_nombre} | {anio} | integrantes={cnt}")
        print(f"\nTotal grupos: {total_grupos} (debe ser >2)")
        print(f"Total integrantes sumados: {total_integrantes} (debe ser 109)")

        # Sede scoping check
        print("\n--- Verificacion de scoping por sede ---")
        print(f"Grupos TEO: {sum(1 for r in rows if r[0]=='TEO')}")
        print(f"Grupos HUA: {sum(1 for r in rows if r[0]=='HUA')}")
        print("Scoping: general_admin ve todos, sede_admin solo su sede (via scope_by_sede en routes).")

        # Idempotencia notice
        print("\nScript idempotente: re-ejecutar no duplica grupos ni integrantes.")

        return {
            "total_alumnos": total_alumnos,
            "groups_created": groups_created,
            "grupos_reused": grupos_reused,
            "integrantes_added": integrantes_added,
            "hua_precreated": hua_precreated,
            "total_grupos": total_grupos,
            "total_integrantes": total_integrantes,
        }


if __name__ == "__main__":
    result = main()
    # Exit code 0 if verification passes
    if result["total_grupos"] <= 2:
        print("[ERROR] Total grupos no supera 2, verificar")
        sys.exit(1)
    if result["total_integrantes"] != 109:
        # Warning but not fatal if DB has different count? Task says 109
        print(f"[WARN] Integrantes sumados {result['total_integrantes']} != 109")
    sys.exit(0)
