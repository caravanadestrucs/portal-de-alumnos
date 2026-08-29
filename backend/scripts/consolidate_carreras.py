#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consolidate duplicate carreras 15 -> 8 canonical.

Mapping legacy -> canonical:
  LP(28)  -> PED(32)  Pedagogia
  LENF(31)-> ENF(33)  Enfermeria
  LD(27)  -> DER(34)  Derecho
  LPS(29) -> PSI(35)  Psicologia
  LCD(30) -> CDE(36)  Ciencias del Deporte
  LC(26)  -> CON(37)  Contaduria
  SIS(38) -> ISC(23)  Sistemas -> ISC
Keep LIC-ADM(1) as is.

For each mapping:
  a) For each Materia in legacy carrera, find if canonical already has materia
     with same normalized name (lower+strip accents+collapse spaces).
     If exists (keeper in canonical), reassign Calificacion.materia_id from legacy
     materia to keeper (0-loss: if UNIQUE collision alumno+periodo+anio, tweak
     periodo to _dup variant to preserve). Also reassign Asignacion.materia_id.
     Then delete legacy materia.
  b) If not exists (unique materia), UPDATE materia.carrera_id = canonical (move).
  c) UPDATE Alumno.carrera_id and Grupo.carrera_id from legacy to canonical.
  d) DELETE Carrera legacy row.

Idempotent: if legacy carrera already deleted, skip.
Backup: portal.db.bak.consolidate.* and backend_seed.db.bak.consolidate.*
Verify: counts before/after, no orphan calificaciones.

Run: python backend/scripts/consolidate_carreras.py
"""

import sqlite3
import unicodedata
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Resolve backend dir relative to this script
BACKEND_DIR = Path(__file__).resolve().parent.parent

DB_PATHS = [
    BACKEND_DIR / "instance" / "portal.db",
    BACKEND_DIR / "backend_seed.db",
    # Absolute fallback (Windows dev path)
    Path(r"C:\Users\Dario\Desktop\portal de alumnos\backend\instance\portal.db"),
    Path(r"C:\Users\Dario\Desktop\portal de alumnos\backend\backend_seed.db"),
]

# Dedupe preserve order while removing duplicates (fallback absolute may duplicate)
_seen = set()
_unique_paths = []
for p in DB_PATHS:
    rp = p.resolve() if p.exists() else p
    key = str(rp).lower()
    if key not in _seen:
        _seen.add(key)
        _unique_paths.append(p)
DB_PATHS = _unique_paths

# Mapping legacy -> canonical
MAPPING = {
    28: 32,  # LP -> PED
    31: 33,  # LENF -> ENF
    27: 34,  # LD -> DER
    29: 35,  # LPS -> PSI
    30: 36,  # LCD -> CDE
    26: 37,  # LC -> CON
    38: 23,  # SIS -> ISC
}

# Keep LIC-ADM (1) as is

def normalize_name(s: str) -> str:
    """Normalized per spec: lower, trim, remove accents, collapse spaces."""
    if not s:
        return ""
    s = s.strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def backup_db(db_path: Path):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = db_path.parent / f"{db_path.name}.bak.consolidate.{ts}"
    shutil.copy2(db_path, bak)
    print(f"[BACKUP] {db_path} -> {bak}")
    return bak

def find_free_periodo(cur, alumno_id, keeper_id, periodo, anio):
    """Find a free (periodo, anio) that does not collide for given alumno+keeper."""
    base = periodo if periodo is not None else ""
    suffixes = ["_dup", "_dup2", "_dup3", "_dup4", "_dup5", "_dup6", "_dup7", "_dup8", "_dup9", "_dup10"]
    for suf in suffixes:
        new_per = base + suf
        cur.execute(
            "SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?",
            (alumno_id, keeper_id, new_per, anio),
        )
        if not cur.fetchone():
            return new_per, anio
    if anio is not None:
        for delta in [1, 2, 3, 4, 5]:
            try:
                new_anio = int(anio) + delta
            except (ValueError, TypeError):
                continue
            cur.execute(
                "SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?",
                (alumno_id, keeper_id, base, new_anio),
            )
            if not cur.fetchone():
                return base, new_anio
            for suf in suffixes:
                new_per = base + suf
                cur.execute(
                    "SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?",
                    (alumno_id, keeper_id, new_per, new_anio),
                )
                if not cur.fetchone():
                    return new_per, new_anio
    import time
    import uuid
    fallback = base + f"_dup_{int(time.time())%10000}"
    cur.execute(
        "SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?",
        (alumno_id, keeper_id, fallback, anio),
    )
    if not cur.fetchone():
        return fallback, anio
    fallback2 = base + f"_dup_{uuid.uuid4().hex[:6]}"
    return fallback2, anio

def process_db(db_path: Path):
    print(f"\n{'='*70}")
    print(f"=== Processing {db_path} ===")
    print(f"{'='*70}")
    if not db_path.exists():
        print(f"[SKIP] not found {db_path}")
        return {}

    # Normalize path for existence check dedup
    backup_db(db_path)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    # Enable FK checks
    cur.execute("PRAGMA foreign_keys=ON")

    # Before counts
    print("\n[BEFORE] carreras:")
    before_rows = list(cur.execute(
        "SELECT c.id, c.codigo, c.nombre, "
        "(SELECT COUNT(*) FROM materias WHERE carrera_id=c.id) as mat_cnt, "
        "(SELECT COUNT(*) FROM alumnos WHERE carrera_id=c.id) as alu_cnt "
        "FROM carreras c ORDER BY c.id"
    ))
    for r in before_rows:
        print(f"  {r['id']:2d} {r['codigo']:8s} {r['nombre'][:30]:30s} mats={r['mat_cnt']:2d} alumnos={r['alu_cnt']:2d}")

    cur.execute("SELECT COUNT(*) FROM materias")
    total_mats_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    total_califs_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM carreras")
    total_carr_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alumnos")
    total_alu_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM grupos")
    total_grupos_before = cur.fetchone()[0]
    print(f"[BEFORE] total carreras={total_carr_before} materias={total_mats_before} calificaciones={total_califs_before} alumnos={total_alu_before} grupos={total_grupos_before}")

    total_reassigned = 0
    total_tweaked = 0
    total_deduped = 0
    total_moved_mats = 0
    total_alumnos_moved = 0
    total_grupos_moved = 0

    for legacy_id, canonical_id in MAPPING.items():
        cur.execute("SELECT id, codigo, nombre FROM carreras WHERE id=?", (legacy_id,))
        legacy = cur.fetchone()
        if not legacy:
            print(f"\n[SKIP] legacy carrera {legacy_id} not found (already consolidated) -> canonical {canonical_id}")
            continue
        cur.execute("SELECT id, codigo, nombre FROM carreras WHERE id=?", (canonical_id,))
        canonical = cur.fetchone()
        if not canonical:
            print(f"\n[ERROR] canonical {canonical_id} not found for legacy {legacy_id} {legacy['codigo']}")
            continue

        print(f"\n[MAP] {legacy['codigo']}({legacy_id}) '{legacy['nombre']}' -> {canonical['codigo']}({canonical_id}) '{canonical['nombre']}'")

        # Build canonical normalized map
        cur.execute("SELECT id, codigo, nombre FROM materias WHERE carrera_id=?", (canonical_id,))
        canon_mats = cur.fetchall()
        canon_map = {}  # norm -> keeper_id
        for m in canon_mats:
            norm = normalize_name(m["nombre"])
            if norm not in canon_map:
                canon_map[norm] = m["id"]
            else:
                # intra-canonical duplicate (should not happen after prior dedup)
                # keep first as keeper; the duplicate would have been handled in earlier dedup
                pass
        print(f"  canonical has {len(canon_mats)} materias, {len(canon_map)} unique normalized")

        # Legacy materias
        cur.execute("SELECT id, codigo, nombre FROM materias WHERE carrera_id=? ORDER BY id", (legacy_id,))
        legacy_mats = list(cur.fetchall())
        print(f"  legacy has {len(legacy_mats)} materias")

        deduped = 0
        moved = 0
        reassigned = 0
        tweaked = 0

        for lm in legacy_mats:
            norm = normalize_name(lm["nombre"])
            keeper_id = canon_map.get(norm)
            if keeper_id is not None:
                # Duplicate -> reassign calificaciones to keeper with 0-loss
                cur2 = con.cursor()
                cur2.execute("SELECT id, alumno_id, periodo, anio FROM calificaciones WHERE materia_id=?", (lm["id"],))
                califs = cur2.fetchall()
                for cal in califs:
                    cal_id = cal["id"]
                    alumno_id = cal["alumno_id"]
                    periodo = cal["periodo"]
                    anio = cal["anio"]
                    # Check collision
                    cur.execute(
                        "SELECT id FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?",
                        (alumno_id, keeper_id, periodo, anio),
                    )
                    existing = cur.fetchone()
                    if existing:
                        new_per, new_anio = find_free_periodo(cur, alumno_id, keeper_id, periodo, anio)
                        print(f"    collision alumno {alumno_id} periodo '{periodo}' anio {anio} keeper {keeper_id} dup calif {cal_id}: tweak -> periodo '{new_per}' anio {new_anio}")
                        cur.execute(
                            "UPDATE calificaciones SET materia_id=?, periodo=?, anio=? WHERE id=?",
                            (keeper_id, new_per, new_anio, cal_id),
                        )
                        tweaked += 1
                        reassigned += 1
                    else:
                        cur.execute("UPDATE calificaciones SET materia_id=? WHERE id=?", (keeper_id, cal_id))
                        reassigned += 1
                # Reassign asignaciones if any
                cur.execute("SELECT id FROM asignaciones WHERE materia_id=?", (lm["id"],))
                asigs = cur.fetchall()
                for a in asigs:
                    # Simple reassign; asignaciones has no unique constraint that would conflict
                    try:
                        cur.execute("UPDATE asignaciones SET materia_id=? WHERE id=?", (keeper_id, a["id"]))
                    except sqlite3.IntegrityError as e:
                        print(f"    WARN asignacion {a['id']} reassign failed: {e}")
                # Delete legacy materia
                cur.execute("DELETE FROM materias WHERE id=?", (lm["id"],))
                deduped += 1
            else:
                # Unique -> move materia to canonical
                cur.execute("UPDATE materias SET carrera_id=? WHERE id=?", (canonical_id, lm["id"]))
                canon_map[norm] = lm["id"]
                moved += 1
        print(f"  materias: deduped {deduped} moved {moved} califs reassigned {reassigned} tweaked {tweaked}")
        total_deduped += deduped
        total_moved_mats += moved
        total_reassigned += reassigned
        total_tweaked += tweaked

        # Move alumnos
        cur.execute("SELECT COUNT(*) FROM alumnos WHERE carrera_id=?", (legacy_id,))
        cnt_alu = cur.fetchone()[0]
        if cnt_alu:
            cur.execute("UPDATE alumnos SET carrera_id=? WHERE carrera_id=?", (canonical_id, legacy_id))
            print(f"  alumnos moved {cnt_alu} from {legacy_id} to {canonical_id}")
            total_alumnos_moved += cnt_alu
        else:
            print(f"  alumnos moved 0 (legacy had no alumnos)")

        # Move grupos
        cur.execute("SELECT COUNT(*) FROM grupos WHERE carrera_id=?", (legacy_id,))
        cnt_grupos = cur.fetchone()[0]
        if cnt_grupos:
            cur.execute("UPDATE grupos SET carrera_id=? WHERE carrera_id=?", (canonical_id, legacy_id))
            print(f"  grupos moved {cnt_grupos} from {legacy_id} to {canonical_id}")
            total_grupos_moved += cnt_grupos
        else:
            print(f"  grupos moved 0")

        # Delete legacy carrera
        try:
            cur.execute("DELETE FROM carreras WHERE id=?", (legacy_id,))
            print(f"  deleted carrera {legacy_id} {legacy['codigo']}")
        except sqlite3.IntegrityError as e:
            print(f"  ERROR deleting carrera {legacy_id}: {e}")
            con.rollback()
            # Try to handle orphans? Should not happen if we moved all FKs
            raise
        con.commit()

    # After counts
    print("\n[AFTER] carreras:")
    after_rows = list(cur.execute(
        "SELECT c.id, c.codigo, c.nombre, "
        "(SELECT COUNT(*) FROM materias WHERE carrera_id=c.id) as mat_cnt, "
        "(SELECT COUNT(*) FROM alumnos WHERE carrera_id=c.id) as alu_cnt "
        "FROM carreras c ORDER BY c.id"
    ))
    for r in after_rows:
        print(f"  {r['id']:2d} {r['codigo']:8s} {r['nombre'][:30]:30s} mats={r['mat_cnt']:2d} alumnos={r['alu_cnt']:2d}")

    cur.execute("SELECT COUNT(*) FROM materias")
    total_mats_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    total_califs_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM carreras")
    total_carr_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alumnos")
    total_alu_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM grupos")
    total_grupos_after = cur.fetchone()[0]
    print(f"[AFTER] total carreras={total_carr_after} materias={total_mats_after} calificaciones={total_califs_after} alumnos={total_alu_after} grupos={total_grupos_after}")
    print(f"[SUMMARY] deduped materias={total_deduped} moved materias={total_moved_mats} califs reassigned={total_reassigned} tweaked={total_tweaked} alumnos moved={total_alumnos_moved} grupos moved={total_grupos_moved}")

    # Verify no orphans
    cur.execute("SELECT COUNT(*) FROM calificaciones WHERE materia_id NOT IN (SELECT id FROM materias)")
    orphans_calif = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alumnos WHERE carrera_id NOT IN (SELECT id FROM carreras)")
    orphans_alu = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM grupos WHERE carrera_id NOT IN (SELECT id FROM carreras)")
    orphans_grupos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM materias WHERE carrera_id NOT IN (SELECT id FROM carreras)")
    orphans_mats = cur.fetchone()[0]
    # Asignaciones orphan check
    cur.execute("SELECT COUNT(*) FROM asignaciones WHERE materia_id NOT IN (SELECT id FROM materias)")
    orphans_asig_mat = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM asignaciones WHERE grupo_id NOT IN (SELECT id FROM grupos)")
    orphans_asig_grupo = cur.fetchone()[0]

    print(f"[VERIFY] orphans: calif->{orphans_calif} alumnos->{orphans_alu} grupos->{orphans_grupos} materias->{orphans_mats} asig_mat->{orphans_asig_mat} asig_grupo->{orphans_asig_grupo}")
    # Cleanup orphan asignaciones (pre-existing data issue, e.g., materia 621 missing since 2025 seed)
    if orphans_asig_mat != 0:
        print(f"[CLEANUP] deleting {orphans_asig_mat} orphan asignaciones (materia_id not in materias)")
        cur.execute("DELETE FROM asignaciones WHERE materia_id NOT IN (SELECT id FROM materias)")
        con.commit()
        cur.execute("SELECT COUNT(*) FROM asignaciones WHERE materia_id NOT IN (SELECT id FROM materias)")
        orphans_asig_mat = cur.fetchone()[0]
        print(f"[CLEANUP] after delete orphans_asig_mat={orphans_asig_mat}")
    if orphans_asig_grupo != 0:
        print(f"[CLEANUP] deleting {orphans_asig_grupo} orphan asignaciones (grupo_id not in grupos)")
        cur.execute("DELETE FROM asignaciones WHERE grupo_id NOT IN (SELECT id FROM grupos)")
        con.commit()
        cur.execute("SELECT COUNT(*) FROM asignaciones WHERE grupo_id NOT IN (SELECT id FROM grupos)")
        orphans_asig_grupo = cur.fetchone()[0]
        print(f"[CLEANUP] after delete orphans_asig_grupo={orphans_asig_grupo}")
    if orphans_calif != 0:
        print(f"[VERIFY] ERROR orphans calif {orphans_calif}")
    else:
        print("[VERIFY] orphans calif OK 0")
    if total_califs_after != total_califs_before:
        print(f"[VERIFY] ERROR califs changed {total_califs_before}->{total_califs_after} loss {total_califs_before - total_califs_after}")
    else:
        print(f"[VERIFY] califs preserved OK {total_califs_after}")
    if total_alu_after != total_alu_before:
        print(f"[VERIFY] ERROR alumnos changed {total_alu_before}->{total_alu_after}")
    else:
        print(f"[VERIFY] alumnos preserved OK {total_alu_after}")
    # Carrera count should be 8 (if LIC-ADM kept, 7 mappings deleted)
    expected_carr = total_carr_before - len([k for k in MAPPING.keys() if True])  # will be 8 if all legacy existed
    # Actually check if legacy existed before; we backup before, so expected is 8 if started 15
    print(f"[VERIFY] carreras {total_carr_before} -> {total_carr_after} (expected 8 if started 15)")

    # Detailed after for spec verification
    print("\n[VERIFY] SELECT codigo, nombre, (SELECT COUNT(*) FROM materias WHERE carrera_id=c.id), (SELECT COUNT(*) FROM alumnos WHERE carrera_id=c.id) FROM carreras c ORDER BY id")
    for r in after_rows:
        print(f"  {r['codigo']} | {r['nombre']} | mats={r['mat_cnt']} | alumnos={r['alu_cnt']}")

    con.commit()
    con.close()

    return {
        "db": str(db_path),
        "before_carr": total_carr_before,
        "after_carr": total_carr_after,
        "before_mats": total_mats_before,
        "after_mats": total_mats_after,
        "before_califs": total_califs_before,
        "after_califs": total_califs_after,
        "before_rows": [(r["id"], r["codigo"], r["nombre"], r["mat_cnt"], r["alu_cnt"]) for r in before_rows],
        "after_rows": [(r["id"], r["codigo"], r["nombre"], r["mat_cnt"], r["alu_cnt"]) for r in after_rows],
        "orphans_calif": orphans_calif,
        "orphans_alu": orphans_alu,
        "orphans_grupos": orphans_grupos,
        "reassigned": total_reassigned,
        "tweaked": total_tweaked,
        "deduped": total_deduped,
        "moved_mats": total_moved_mats,
    }

if __name__ == "__main__":
    results = {}
    for dbp in DB_PATHS:
        # Only process once per unique resolved path, skip duplicates
        # Check if already processed via resolved path
        # Use try to avoid duplicate processing due to both relative and absolute pointing same file
        resolved = dbp.resolve()
        if str(resolved) in [str(Path(v["db"]).resolve()) for v in results.values() if v]:
            print(f"[SKIP] already processed resolved {resolved}")
            continue
        if not dbp.exists():
            # Try relative to BACKEND_DIR if absolute not found
            alt = BACKEND_DIR / dbp.name if dbp.name in ["portal.db", "backend_seed.db"] else dbp
            if alt.exists() and alt != dbp:
                dbp = alt
            else:
                print(f"[SKIP] not found {dbp}")
                continue
        res = process_db(dbp)
        results[str(dbp)] = res

    print("\n" + "="*70)
    print("=== SUMMARY ===")
    for dbp, res in results.items():
        if not res:
            continue
        print(f"DB {dbp}")
        print(f"  carreras {res['before_carr']} -> {res['after_carr']}")
        print(f"  materias {res['before_mats']} -> {res['after_mats']}")
        print(f"  califs {res['before_califs']} -> {res['after_califs']} orphans {res['orphans_calif']} reassigned {res['reassigned']} tweaked {res['tweaked']}")
        print(f"  before: {res['before_rows']}")
        print(f"  after: {res['after_rows']}")
