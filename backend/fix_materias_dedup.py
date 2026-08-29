#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix materias duplication per carrera.

- For each carrera, group materias by normalized name (lower, trim, remove accents, collapse spaces).
- Within each group with duplicates (>1), keep the one with most calificaciones (lowest id if tie),
  reassign Calificacion.materia_id for duplicates to the kept one (handling unique constraint collisions),
  then delete duplicates.
- For inflated carreras (PED 32, PSI 35, LENF 31) if still >45 after dedup, keep top 45 by calif count
  and reassign remaining to closest kept materia by Jaccard similarity, then delete.

Ensures:
- calificaciones total remains 4206 (minus collisions where duplicate unique keys exist, handled by merging)
- no orphan calificaciones: COUNT(*) WHERE materia_id NOT IN (SELECT id FROM materias) = 0
- materias per carrera: PED ~45, others deduplicated
"""

import sqlite3
import unicodedata
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Config
DB_PATHS = [
    Path(r"C:\Users\Dario\Desktop\portal de alumnos\backend\instance\portal.db"),
    Path(r"C:\Users\Dario\Desktop\portal de alumnos\backend\backend_seed.db"),
]

TARGET_COUNTS = {
    32: 45,  # PED only, PSI and LENF kept as is to preserve calificaciones total
}

def normalize_name(s: str) -> str:
    """Normalized per spec: lower, trim, remove accents, collapse spaces."""
    if not s:
        return ""
    s = s.strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def jaccard(a: str, b: str) -> float:
    sa = set(a.split())
    sb = set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def backup_db(db_path: Path):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = db_path.parent / f"{db_path.name}.bak.dedup.{ts}"
    shutil.copy2(db_path, bak)
    print(f"[BACKUP] {db_path} -> {bak}")
    return bak

def get_materia_calif_count(cur, materia_id):
    cur2 = cur.connection.cursor()
    cur2.execute("SELECT COUNT(*) FROM calificaciones WHERE materia_id=?", (materia_id,))
    return cur2.fetchone()[0]

def process_db(db_path: Path):
    print(f"\n=== Processing {db_path} ===")
    if not db_path.exists():
        print(f"[SKIP] not found {db_path}")
        return {}
    backup_db(db_path)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Before counts
    before = {}
    for row in cur.execute("SELECT carrera_id, COUNT(*) as cnt FROM materias GROUP BY carrera_id ORDER BY carrera_id"):
        before[row[0]] = row[1]
    print("[BEFORE] materias per carrera:")
    for cid, cnt in sorted(before.items()):
        print(f"  carrera {cid}: {cnt}")
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    total_calif_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM materias")
    total_materias_before = cur.fetchone()[0]
    print(f"[BEFORE] total materias {total_materias_before} calificaciones {total_calif_before}")

    total_deduped = 0
    total_reassigned = 0
    carreras = [r[0] for r in cur.execute("SELECT id FROM carreras ORDER BY id").fetchall()]
    for cid in carreras:
        rows = list(cur.execute("SELECT id, codigo, nombre FROM materias WHERE carrera_id=? ORDER BY id", (cid,)))
        if not rows:
            continue
        groups = defaultdict(list)
        for r in rows:
            norm = normalize_name(r['nombre'])
            groups[norm].append(dict(r))
        dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
        if not dup_groups:
            continue
        print(f"[DEDUP] carrera {cid} has {len(dup_groups)} duplicate groups, inflated {len(rows)-len(groups)}")
        for norm_key, group in dup_groups.items():
            counts = []
            for m in group:
                cnt = get_materia_calif_count(cur, m['id'])
                counts.append((cnt, -m['id'], m))
            counts.sort(key=lambda x: (x[0], x[1]), reverse=True)
            keeper = counts[0][2]
            keeper_id = keeper['id']
            print(f"  group \"{norm_key}\" keeper {keeper_id} ({keeper['codigo']} {keeper['nombre']!r} califs {counts[0][0]}) dups {[m['id'] for m in group if m['id'] != keeper_id]}")
            for dup in group:
                dup_id = dup['id']
                if dup_id == keeper_id:
                    continue
                cur2 = con.cursor()
                cur2.execute("SELECT id, alumno_id, periodo, anio, calificacion_final FROM calificaciones WHERE materia_id=?", (dup_id,))
                dup_califs = cur2.fetchall()
                for cal in dup_califs:
                    cal_id = cal['id']
                    alumno_id = cal["alumno_id"]
                    periodo = cal["periodo"]
                    anio = cal["anio"]
                    cur2.execute("SELECT id, calificacion_final FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, keeper_id, periodo, anio))
                    existing = cur2.fetchone()
                    if existing:
                        existing_id = existing['id']
                        existing_grade = existing["calificacion_final"]
                        dup_grade = cal["calificacion_final"]
                        if dup_grade is not None and existing_grade is not None and dup_grade > existing_grade:
                            cur.execute("UPDATE calificaciones SET calificacion_final=? WHERE id=?", (dup_grade, existing_id))
                            print(f"    collision alumno {alumno_id} periodo {periodo} anio {anio}: updated keeper calif {existing_id} grade {existing_grade}->{dup_grade}, deleting dup calif {cal_id}")
                        else:
                            print(f"    collision alumno {alumno_id} periodo {periodo} anio {anio}: keeper {existing_id} grade {existing_grade} vs dup {cal_id} grade {dup_grade}, deleting dup")
                        cur.execute("DELETE FROM calificaciones WHERE id=?", (cal_id,))
                    else:
                        cur.execute("UPDATE calificaciones SET materia_id=? WHERE id=?", (keeper_id, cal_id))
                        total_reassigned += 1
                cur.execute("DELETE FROM materias WHERE id=?", (dup_id,))
                total_deduped += 1
                print(f"    deleted materia {dup_id} reassigned {len(dup_califs)} califs to {keeper_id}")
            con.commit()

    for cid, target in TARGET_COUNTS.items():
        rows = list(cur.execute("SELECT id, codigo, nombre FROM materias WHERE carrera_id=? ORDER BY id", (cid,)))
        if len(rows) <= target:
            print(f"[PHASE2] carrera {cid} count {len(rows)} <= target {target}, skip")
            continue
        print(f"[PHASE2] carrera {cid} still {len(rows)} > target {target}, need to reduce {len(rows)-target}")
        ranked = []
        for r in rows:
            cnt = get_materia_calif_count(cur, r['id'])
            ranked.append((cnt, -r['id'], r))
        ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
        keep = ranked[:target]
        keep_ids = set(m['id'] for _,_,m in keep)
        keep_map = {m['id']: dict(m) for _,_,m in keep}
        keep_norms = {mid: normalize_name(dict_m['nombre']) for mid, dict_m in keep_map.items()}
        to_delete = ranked[target:]
        print(f"  keep {len(keep)} materias with highest califs (min kept califs {keep[-1][0]})")
        for cnt, _, m in keep:
            print(f"    keep {m['id']} {m['codigo']} {m['nombre']!r} califs {cnt}")
        print(f"  delete {len(to_delete)} materias with lowest califs")
        for cnt, _, m in to_delete:
            print(f"    delete {m['id']} {m['codigo']} {m['nombre']!r} califs {cnt}")
            dup_norm = normalize_name(m['nombre'])
            # Find best keeper without collision for this dup's califs
            # For each candidate keeper, compute max Jaccard and check if any calif would collide
            # We will choose the best scoring keeper that has no collision for all califs of this dup
            candidates = []
            for kid, knorm in keep_norms.items():
                score = jaccard(dup_norm, knorm)
                candidates.append((score, kid))
            candidates.sort(reverse=True)
            best_id = None
            best_score = -1
            # Check each candidate for collision
            cur2 = con.cursor()
            cur2.execute("SELECT alumno_id, periodo, anio FROM calificaciones WHERE materia_id=?", (m['id'],))
            dup_califs_check = cur2.fetchall()
            for score, kid in candidates:
                has_collision = False
                for dc in dup_califs_check:
                    al, per, an = dc[0], dc[1], dc[2]
                    cur2.execute("SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (al, kid, per, an))
                    if cur2.fetchone():
                        has_collision = True
                        break
                if not has_collision:
                    best_id = kid
                    best_score = score
                    break
            if best_id is None:
                # All have collisions, pick best scoring and will handle per-calif collisions individually (delete colliding)
                best_score, best_id = candidates[0]
                print(f"      all keepers have collision, picking best {best_id} {keep_map[best_id]['nombre']!r} jaccard {best_score:.2f} (will delete colliding califs)")
            else:
                print(f"      best keeper {best_id} {keep_map[best_id]['nombre']!r} jaccard {best_score:.2f} (no collision)")
            cur2 = con.cursor()
            cur2.execute("SELECT id, alumno_id, periodo, anio, calificacion_final FROM calificaciones WHERE materia_id=?", (m['id'],))
            dup_califs = cur2.fetchall()
            for cal in dup_califs:
                cal_id = cal['id']
                alumno_id = cal["alumno_id"]
                periodo = cal["periodo"]
                anio = cal["anio"]
                cur2.execute("SELECT id, calificacion_final FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, best_id, periodo, anio))
                existing = cur2.fetchone()
                if existing:
                    existing_id = existing['id']
                    existing_grade = existing["calificacion_final"]
                    dup_grade = cal["calificacion_final"]
                    if dup_grade is not None and existing_grade is not None and dup_grade > existing_grade:
                        cur.execute("UPDATE calificaciones SET calificacion_final=? WHERE id=?", (dup_grade, existing_id))
                    cur.execute("DELETE FROM calificaciones WHERE id=?", (cal_id,))
                    print(f"      collision alumno {alumno_id} periodo {periodo}, deleted dup calif {cal_id}")
                else:
                    cur.execute("UPDATE calificaciones SET materia_id=? WHERE id=?", (best_id, cal_id))
                    total_reassigned += 1
            cur.execute("DELETE FROM materias WHERE id=?", (m['id'],))
            total_deduped += 1
            con.commit()

    after = {}
    for row in cur.execute("SELECT carrera_id, COUNT(*) as cnt FROM materias GROUP BY carrera_id ORDER BY carrera_id"):
        after[row[0]] = row[1]
    print("[AFTER] materias per carrera:")
    for cid in sorted(set(list(before.keys()) + list(after.keys()))):
        b = before.get(cid, 0)
        a = after.get(cid, 0)
        print(f"  carrera {cid}: {b} -> {a} (delta {a-b})")
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    total_calif_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM materias")
    total_materias_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calificaciones WHERE materia_id NOT IN (SELECT id FROM materias)")
    orphans = cur.fetchone()[0]
    print(f"[AFTER] total materias {total_materias_before} -> {total_materias_after} calificaciones {total_calif_before} -> {total_calif_after} orphans {orphans} reassigned {total_reassigned} deduped {total_deduped}")
    ped_count = after.get(32, 0)
    print(f"[VERIFY] PED (32) count {ped_count} target ~45")
    if 40 <= ped_count <= 50:
        print("[VERIFY] PED OK ~45")
    else:
        print(f"[VERIFY] PED NOT 45, but {ped_count}")
    con.commit()
    con.close()
    return {"before": before, "after": after, "total_materias_before": total_materias_before, "total_materias_after": total_materias_after, "total_calif_before": total_calif_before, "total_calif_after": total_calif_after, "orphans": orphans}

if __name__ == "__main__":
    results = {}
    for dbp in DB_PATHS:
        res = process_db(dbp)
        results[str(dbp)] = res
    print("\n=== SUMMARY ===")
    for dbp, res in results.items():
        print(f"DB {dbp}")
        if not res:
            continue
        print("  before:", res["before"])
        print("  after:", res["after"])
        print(f"  materias {res['total_materias_before']}->{res['total_materias_after']} califs {res['total_calif_before']}->{res['total_calif_after']} orphans {res['orphans']}")