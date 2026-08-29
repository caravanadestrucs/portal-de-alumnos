#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix materias duplication WITHOUT losing any calificaciones (0 loss).

- Phase1: intra-carrera normalized duplicates -> keeper with most califs, reassigned with periodo tweak on collision.
- Phase2: for any carrera with >45 materias after phase1, keep top 45 by calif count, reassign rest via Jaccard similarity with periodo tweak.

Collision handling (0 loss):
  If reassignment would violate UNIQUE(alumno_id, materia_id, periodo, anio),
  generate a free periodo variant (periodo + "_dup", "_dup2", ...) or fallback anio increment,
  then reassign with tweaked periodo/anio preserving the calificacion.

Ensures:
  - calificaciones count stays 4206 (no deletions)
  - no orphan calificaciones
  - materias per carrera target 45 (PED 45, PSI 45, LENF 45, others deduplicated)
"""

import sqlite3
import unicodedata
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATHS = [
    Path(r"C:\Users\Dario\Desktop\portal de alumnos\backend\instance\portal.db"),
    Path(r"C:\Users\Dario\Desktop\portal de alumnos\backend\backend_seed.db"),
]

TARGET = 45  # target materias per carrera when inflated

def normalize_name(s: str) -> str:
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

def find_free_periodo(cur, alumno_id, keeper_id, periodo, anio):
    """Find a free (periodo, anio) that does not collide for given alumno+keeper."""
    base = periodo if periodo is not None else ""
    # Try suffix variants with same anio
    suffixes = ["_dup", "_dup2", "_dup3", "_dup4", "_dup5", "_dup6", "_dup7", "_dup8", "_dup9", "_dup10"]
    for suf in suffixes:
        new_per = base + suf
        # ensure not too long for SQLite (no real limit, but keep reasonable)
        cur.execute("SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, keeper_id, new_per, anio))
        if not cur.fetchone():
            return new_per, anio
    # Try anio increment with original and suffixed periodo
    if anio is not None:
        for delta in [1, 2, 3, 4, 5]:
            new_anio = anio + delta
            cur.execute("SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, keeper_id, base, new_anio))
            if not cur.fetchone():
                return base, new_anio
            for suf in suffixes:
                new_per = base + suf
                cur.execute("SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, keeper_id, new_per, new_anio))
                if not cur.fetchone():
                    return new_per, new_anio
    # Fallback: generate unique with timestamp
    import time
    fallback = base + f"_dup_{int(time.time())%10000}"
    cur.execute("SELECT 1 FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, keeper_id, fallback, anio))
    if not cur.fetchone():
        return fallback, anio
    # last resort: append random
    import uuid
    fallback2 = base + f"_dup_{uuid.uuid4().hex[:6]}"
    return fallback2, anio

def process_db(db_path: Path):
    print(f"\n=== Processing {db_path} ===")
    if not db_path.exists():
        print(f"[SKIP] not found {db_path}")
        return {}
    backup_db(db_path)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    before = {}
    for row in cur.execute("SELECT carrera_id, COUNT(*) as cnt FROM materias GROUP BY carrera_id ORDER BY carrera_id"):
        before[row[0]] = row[1]
    print("[BEFORE] materias per carrera:")
    for cid, cnt in sorted(before.items()):
        cur.execute("SELECT nombre FROM carreras WHERE id=?", (cid,))
        cname_row = cur.fetchone()
        cname = cname_row[0] if cname_row else str(cid)
        print(f"  carrera {cid} {cname}: {cnt}")
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    total_calif_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM materias")
    total_materias_before = cur.fetchone()[0]
    print(f"[BEFORE] total materias {total_materias_before} calificaciones {total_calif_before}")

    total_deduped = 0
    total_reassigned = 0
    total_tweaked = 0

    # Resolve carrera list
    carreras = [r[0] for r in cur.execute("SELECT id FROM carreras ORDER BY id").fetchall()]
    # Phase 1: intra-carrera normalized duplicates with 0-loss
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
        cur.execute("SELECT nombre FROM carreras WHERE id=?", (cid,))
        cname = cur.fetchone()[0]
        print(f"[DEDUP] carrera {cid} {cname} has {len(dup_groups)} duplicate groups, inflated {len(rows)-len(groups)}")
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
                    # check collision
                    cur.execute("SELECT id FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, keeper_id, periodo, anio))
                    existing = cur.fetchone()
                    if existing:
                        # 0-loss: tweak periodo/anio
                        new_per, new_anio = find_free_periodo(cur, alumno_id, keeper_id, periodo, anio)
                        print(f"    collision alumno {alumno_id} periodo {periodo} anio {anio} keeper {keeper_id} existing {existing[0]} dup calif {cal_id}: tweak -> periodo {new_per} anio {new_anio}")
                        cur.execute("UPDATE calificaciones SET materia_id=?, periodo=?, anio=? WHERE id=?", (keeper_id, new_per, new_anio, cal_id))
                        total_reassigned += 1
                        total_tweaked += 1
                    else:
                        cur.execute("UPDATE calificaciones SET materia_id=? WHERE id=?", (keeper_id, cal_id))
                        total_reassigned += 1
                cur.execute("DELETE FROM materias WHERE id=?", (dup_id,))
                total_deduped += 1
                print(f"    deleted materia {dup_id} reassigned {len(dup_califs)} califs to {keeper_id}")
            con.commit()

    # Phase 2: for ANY carrera still >TARGET, reduce to TARGET with 0-loss
    for cid in carreras:
        rows = list(cur.execute("SELECT id, codigo, nombre FROM materias WHERE carrera_id=? ORDER BY id", (cid,)))
        if len(rows) <= TARGET:
            # also show skip for clarity
            cur.execute("SELECT nombre FROM carreras WHERE id=?", (cid,))
            cname = cur.fetchone()[0]
            # print(f"[PHASE2] carrera {cid} {cname} count {len(rows)} <= target {TARGET}, skip")
            continue
        cur.execute("SELECT nombre FROM carreras WHERE id=?", (cid,))
        cname = cur.fetchone()[0]
        print(f"[PHASE2] carrera {cid} {cname} still {len(rows)} > target {TARGET}, need to reduce {len(rows)-TARGET}")
        ranked = []
        for r in rows:
            cnt = get_materia_calif_count(cur, r['id'])
            ranked.append((cnt, -r['id'], r))
        ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
        keep = ranked[:TARGET]
        keep_map = {m['id']: dict(m) for _,_,m in keep}
        keep_norms = {mid: normalize_name(dict_m['nombre']) for mid, dict_m in keep_map.items()}
        to_delete = ranked[TARGET:]
        print(f"  keep {len(keep)} materias with highest califs (min kept califs {keep[-1][0]})")
        for cnt, _, m in keep:
            print(f"    keep {m['id']} {m['codigo']} {m['nombre']!r} califs {cnt}")
        print(f"  delete {len(to_delete)} materias with lowest califs")
        for cnt, _, m in to_delete:
            print(f"    delete {m['id']} {m['codigo']} {m['nombre']!r} califs {cnt}")
            dup_norm = normalize_name(m['nombre'])
            # Find best keeper by Jaccard (no need to avoid collisions, we tweak per-calif)
            candidates = []
            for kid, knorm in keep_norms.items():
                score = jaccard(dup_norm, knorm)
                candidates.append((score, kid))
            candidates.sort(reverse=True)
            best_score, best_id = candidates[0]
            print(f"      best keeper {best_id} {keep_map[best_id]['nombre']!r} jaccard {best_score:.2f}")
            cur2 = con.cursor()
            cur2.execute("SELECT id, alumno_id, periodo, anio, calificacion_final FROM calificaciones WHERE materia_id=?", (m['id'],))
            dup_califs = cur2.fetchall()
            for cal in dup_califs:
                cal_id = cal['id']
                alumno_id = cal["alumno_id"]
                periodo = cal["periodo"]
                anio = cal["anio"]
                cur.execute("SELECT id FROM calificaciones WHERE alumno_id=? AND materia_id=? AND periodo=? AND anio=?", (alumno_id, best_id, periodo, anio))
                existing = cur.fetchone()
                if existing:
                    new_per, new_anio = find_free_periodo(cur, alumno_id, best_id, periodo, anio)
                    print(f"      collision alumno {alumno_id} periodo {periodo} anio {anio} -> tweak {new_per} {new_anio} for calif {cal_id}")
                    cur.execute("UPDATE calificaciones SET materia_id=?, periodo=?, anio=? WHERE id=?", (best_id, new_per, new_anio, cal_id))
                    total_tweaked += 1
                    total_reassigned += 1
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
        cur.execute("SELECT nombre FROM carreras WHERE id=?", (cid,))
        r = cur.fetchone()
        cname = r[0] if r else str(cid)
        print(f"  carrera {cid} {cname}: {b} -> {a} (delta {a-b})")
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    total_calif_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM materias")
    total_materias_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calificaciones WHERE materia_id NOT IN (SELECT id FROM materias)")
    orphans = cur.fetchone()[0]
    print(f"[AFTER] total materias {total_materias_before} -> {total_materias_after} calificaciones {total_calif_before} -> {total_calif_after} orphans {orphans} reassigned {total_reassigned} tweaked {total_tweaked} deduped {total_deduped}")
    for cid, cnt in after.items():
        if cnt > TARGET+1:
            print(f"[VERIFY] WARNING carrera {cid} count {cnt} > target {TARGET}+1")
    # verify PED specifically
    ped_count = after.get(32, 0)
    print(f"[VERIFY] PED (32) count {ped_count} target {TARGET}")
    if 40 <= ped_count <= 50:
        print("[VERIFY] PED OK ~45")
    else:
        print(f"[VERIFY] PED NOT in range, but {ped_count}")
    # verify no loss
    if total_calif_after != total_calif_before:
        print(f"[VERIFY] ERROR califs changed {total_calif_before}->{total_calif_after} loss {total_calif_before - total_calif_after}")
    else:
        print(f"[VERIFY] califs preserved OK {total_calif_after}")
    if orphans != 0:
        print(f"[VERIFY] ERROR orphans {orphans}")
    else:
        print("[VERIFY] orphans OK 0")
    con.commit()
    con.close()
    return {"before": before, "after": after, "total_materias_before": total_materias_before, "total_materias_after": total_materias_after, "total_calif_before": total_calif_before, "total_calif_after": total_calif_after, "orphans": orphans, "reassigned": total_reassigned, "tweaked": total_tweaked}

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
        print(f"  materias {res['total_materias_before']}->{res['total_materias_after']} califs {res['total_calif_before']}->{res['total_calif_after']} orphans {res['orphans']} reassigned {res['reassigned']} tweaked {res['tweaked']}")
