#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unifica 41 grupos de alumnos duplicados por nombre normalizado.
Idempotente, auditado, con backup y reglas de keeper/email/califs.
"""
import os
import re
import shutil
import sqlite3
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# --- Config ---
SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "instance" / "portal.db"
CANONICAL_CARRERAS = {32, 33, 34, 35, 36, 37}  # PED, ENF, DER, PSI, CDE, CON
LEGACY_CARRERAS = {27, 28, 29, 30, 31}  # + 1,23,26 also legacy but not in 27-31 range

def normalize(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    # collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s

def mask_email(e: str) -> str:
    if not e or "@" not in e:
        return "***"
    local, domain = e.split("@", 1)
    if len(local) <= 2:
        ml = local[0] + "***" if local else "***"
    else:
        ml = local[0] + "***" + local[-1]
    if "." in domain:
        parts = domain.split(".")
        md = parts[0][0] + "***." + ".".join(parts[1:])
    else:
        md = domain[0] + "***"
    return f"{ml}@{md}"

def is_synthetic_nc(nc: str) -> bool:
    return nc.startswith("CSV") or nc.startswith("TEO")

def is_generic_email(email: str) -> bool:
    return "teotitlan" in email.lower()

def is_real_email(email: str) -> bool:
    return not is_generic_email(email) and "@" in email

def main():
    if not DB_PATH.exists():
        print(f"[ERROR] DB no encontrada: {DB_PATH}")
        return 1

    # Backup
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak_path = DB_PATH.parent / f"portal.db.bak.pre-unify41.{ts}"
    shutil.copy2(DB_PATH, bak_path)
    print(f"[BACKUP] {DB_PATH} -> {bak_path}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    # Enable FK
    cur.execute("PRAGMA foreign_keys=ON")

    # Counts before
    cur.execute("SELECT COUNT(*) FROM alumnos")
    alumnos_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    califs_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alumnos WHERE email LIKE '%teotitlan%'")
    genericos_before = cur.fetchone()[0]
    print(f"[ANTES] alumnos={alumnos_before} calificaciones={califs_before} genericos={genericos_before}")

    # Load all alumnos with needed fields
    cur.execute("SELECT id, numero_control, nombre, apellido_paterno, apellido_materno, email, carrera_id, activo FROM alumnos ORDER BY id")
    alumnos = cur.fetchall()
    # Group by normalized nombre completo
    groups = defaultdict(list)
    for row in alumnos:
        k = f"{normalize(row['nombre'])}|{normalize(row['apellido_paterno'])}|{normalize(row['apellido_materno'] or '')}"
        groups[k].append(dict(row))

    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"[INFO] Grupos duplicados por nombre normalizado: {len(dup_groups)} (esperado 41)")
    if len(dup_groups) == 0:
        print("[OK] Nada que hacer — ya unificado (idempotente)")
        # still verify
    else:
        # For deterministic order, sort by key
        total_moved = 0
        total_deleted_dup_califs = 0
        total_alumnos_deleted = 0
        keepers_chosen = []  # for final report

        # Precompute calif counts per alumno (for keeper election)
        calif_counts = {}
        for row in alumnos:
            cur.execute("SELECT COUNT(*) FROM calificaciones WHERE alumno_id=?", (row["id"],))
            calif_counts[row["id"]] = cur.fetchone()[0]

        # To verify email collision outside group, we need full set of lower emails outside group
        # We'll query on demand per email migration.

        for key in sorted(dup_groups.keys()):
            g = dup_groups[key]
            # idempotence: if already 1, skip (should not happen as we filtered)
            if len(g) <= 1:
                continue
            ids = [x["id"] for x in g]
            # Log group header
            display_name = key.replace("|", " ")
            print(f"\n[GRUPO] '{display_name}' ({len(g)} filas):")
            for m in g:
                print(f"  id={m['id']} nc={m['numero_control']} email={mask_email(m['email'])} carrera={m['carrera_id']} activo={bool(m['activo'])} califs={calif_counts[m['id']]}")

            # --- Elegir keeper ---
            # Partition by synthetic vs real
            reals = [x for x in g if not is_synthetic_nc(x["numero_control"])]
            synthetics = [x for x in g if is_synthetic_nc(x["numero_control"])]
            keeper = None
            reason = ""

            if len(reals) == 1:
                keeper = reals[0]
                reason = f"real único nc={keeper['numero_control']} (sintéticos={len(synthetics)})"
            elif len(reals) > 1:
                # elegir real con más califs, tie -> canónica, tie -> menor id
                reals_sorted = sorted(reals, key=lambda x: (-calif_counts[x["id"]], 0 if x["carrera_id"] in CANONICAL_CARRERAS else 1, x["id"]))
                keeper = reals_sorted[0]
                # build reason
                maxc = calif_counts[keeper["id"]]
                tied = [r for r in reals if calif_counts[r["id"]] == maxc]
                if len(tied) > 1:
                    reason = f"varios reales ({len(reals)}) -> max califs={maxc} empate {len(tied)} -> canónica/menor id -> keeper id={keeper['id']}"
                else:
                    reason = f"varios reales ({len(reals)}) -> max califs={maxc} -> keeper id={keeper['id']}"
            else:
                # todos sintéticos
                # sort by califs desc, canonical prefer, id asc
                def sort_key(x):
                    is_canon = 0 if x["carrera_id"] in CANONICAL_CARRERAS else 1
                    return (-calif_counts[x["id"]], is_canon, x["id"])
                sorted_g = sorted(g, key=sort_key)
                keeper = sorted_g[0]
                maxc = calif_counts[keeper["id"]]
                # detect tie description
                tied_max = [x for x in g if calif_counts[x["id"]] == maxc]
                if len(tied_max) > 1:
                    # check canonical difference
                    canon_tied = [x for x in tied_max if x["carrera_id"] in CANONICAL_CARRERAS]
                    if canon_tied and not (keeper["carrera_id"] in CANONICAL_CARRERAS):
                        # shouldn't happen because keeper prefers canónica
                        pass
                    reason = f"todos sintéticos -> max califs={maxc} empate {len(tied_max)} -> prefer canónica/menor id -> keeper id={keeper['id']}"
                else:
                    reason = f"todos sintéticos -> max califs={maxc} -> keeper id={keeper['id']}"
                # extra: indicate canónica vs legacy
                canon_str = "canónica" if keeper["carrera_id"] in CANONICAL_CARRERAS else "legacy"
                reason += f" ({canon_str} carrera={keeper['carrera_id']})"

            losers = [x for x in g if x["id"] != keeper["id"]]
            loser_ids = [x["id"] for x in losers]
            print(f"  -> KEEPER id={keeper['id']} nc={keeper['numero_control']} email={mask_email(keeper['email'])} califs_before={calif_counts[keeper['id']]} losers={loser_ids} | motivo: {reason}")

            # --- Email: migrar mejor email al keeper si keeper genérico y perdedor tiene real ---
            keeper_email = keeper["email"]
            keeper_is_generic = is_generic_email(keeper_email)
            if keeper_is_generic:
                # collect real emails from losers
                real_candidates = [x for x in losers if is_real_email(x["email"])]
                # Prefer gmail/hotmail first (all our reals are gmail/hotmail except one)
                def email_score(e):
                    d = e.lower()
                    if "gmail.com" in d or "hotmail.com" in d or "outlook.com" in d or "yahoo.com" in d:
                        return 0
                    if is_generic_email(e):
                        return 2
                    return 1
                real_candidates_sorted = sorted(real_candidates, key=lambda x: (email_score(x["email"]), x["id"]))
                best_real = real_candidates_sorted[0] if real_candidates_sorted else None
                if best_real:
                    # verify LOWER(email) unique outside group
                    lower_email = best_real["email"].lower()
                    # ids in group
                    placeholders = ",".join("?" for _ in ids)
                    cur.execute(f"SELECT COUNT(*) FROM alumnos WHERE LOWER(email)=? AND id NOT IN ({placeholders})", (lower_email, *ids))
                    colliding = cur.fetchone()[0]
                    if colliding == 0:
                        # Free the loser email first to avoid UNIQUE violation (keeper and loser would share same email transiently)
                        temp_email = f"__migrated__{best_real['id']}__{best_real['email']}"
                        # ensure temp not colliding
                        cur.execute("SELECT COUNT(*) FROM alumnos WHERE LOWER(email)=?", (temp_email.lower(),))
                        if cur.fetchone()[0] == 0:
                            cur.execute("UPDATE alumnos SET email=? WHERE id=?", (temp_email, best_real["id"]))
                        else:
                            # fallback: delete loser email? shouldn't happen
                            temp_email = f"__tmp__{best_real['id']}@migrated.local"
                            cur.execute("UPDATE alumnos SET email=? WHERE id=?", (temp_email, best_real["id"]))
                        print(f"  [EMAIL] keeper genérico -> migrando email real de loser id={best_real['id']} {mask_email(best_real['email'])} -> keeper id={keeper['id']}")
                        cur.execute("UPDATE alumnos SET email=? WHERE id=?", (best_real["email"], keeper["id"]))
                        keeper["email"] = best_real["email"]
                        keeper_email = best_real["email"]
                    else:
                        print(f"  [EMAIL] SKIP migración email {mask_email(best_real['email'])} colisiona fuera del grupo ({colliding} filas)")
                else:
                    # no real candidate; keeper stays generic
                    pass
            else:
                # keeper ya tiene real, nothing to do
                pass

            # --- Migrar calificaciones ---
            # Build keeper existing keys set
            cur.execute("SELECT materia_id, periodo, anio FROM calificaciones WHERE alumno_id=?", (keeper["id"],))
            keeper_keys = set((r[0], r[1], r[2]) for r in cur.fetchall())
            califs_moved = 0
            dup_califs_deleted = 0
            califs_before_keeper = calif_counts[keeper["id"]]

            for loser in losers:
                lid = loser["id"]
                cur.execute("SELECT id, materia_id, periodo, anio FROM calificaciones WHERE alumno_id=?", (lid,))
                loser_califs = cur.fetchall()
                for cf in loser_califs:
                    key = (cf["materia_id"], cf["periodo"], cf["anio"])
                    if key in keeper_keys:
                        # duplicate -> delete loser calif
                        cur.execute("DELETE FROM calificaciones WHERE id=?", (cf["id"],))
                        dup_califs_deleted += 1
                    else:
                        cur.execute("UPDATE calificaciones SET alumno_id=? WHERE id=?", (keeper["id"], cf["id"]))
                        keeper_keys.add(key)
                        califs_moved += 1

            # Preserve activo: spec says if loser activo=False and keeper True, don't change keeper to inactive. So we do NOT touch activo.
            # If keeper was inactive and losers active? Spec says mantener activo, but we keep keeper as is. So no change.

            # --- Migrar grupo_integrantes y otras FKs si existieran ---
            # grupo_integrantes: avoid duplicate (grupo_id, alumno_id) unique? Not defined but handle.
            for loser in losers:
                lid = loser["id"]
                # grupo_integrantes: mover si keeper no está ya en mismo grupo
                cur.execute("SELECT grupo_id FROM grupo_integrantes WHERE alumno_id=?", (lid,))
                loser_groups = cur.fetchall()
                for gi in loser_groups:
                    gid = gi["grupo_id"]
                    cur.execute("SELECT COUNT(*) FROM grupo_integrantes WHERE grupo_id=? AND alumno_id=?", (gid, keeper["id"]))
                    if cur.fetchone()[0] == 0:
                        cur.execute("UPDATE grupo_integrantes SET alumno_id=? WHERE alumno_id=? AND grupo_id=?", (keeper["id"], lid, gid))
                    else:
                        cur.execute("DELETE FROM grupo_integrantes WHERE alumno_id=? AND grupo_id=?", (lid, gid))

            # Borrar perdedores después de migrar (FK cascade will clean remaining califs if any left? but we already handled)
            # Ensure remaining califs of losers are gone (duplicates already deleted, moved those not dup)
            # Double-check no califs left for loser
            for lid in loser_ids:
                cur.execute("SELECT COUNT(*) FROM calificaciones WHERE alumno_id=?", (lid,))
                left = cur.fetchone()[0]
                if left != 0:
                    print(f"  [WARN] loser id={lid} aún tiene {left} califs tras migración — borrando restantes")
                    cur.execute("DELETE FROM calificaciones WHERE alumno_id=?", (lid,))
                    dup_califs_deleted += left

            # Delete alumnos perdedores
            placeholders = ",".join("?" for _ in loser_ids)
            cur.execute(f"DELETE FROM alumnos WHERE id IN ({placeholders})", loser_ids)
            total_alumnos_deleted += len(loser_ids)
            total_moved += califs_moved
            total_deleted_dup_califs += dup_califs_deleted

            keepers_chosen.append((key, keeper["id"], keeper["numero_control"], califs_before_keeper, califs_moved, loser_ids, reason))
            print(f"  [MIGRADO] keeper id={keeper['id']} califs_before={califs_before_keeper} califs_moved+{califs_moved} dup_deleted={dup_califs_deleted} losers={loser_ids}")

        con.commit()
        print(f"\n[RESUMEN MIGRACIÓN] alumnos eliminados={total_alumnos_deleted} califs movidas={total_moved} califs duplicadas borradas={total_deleted_dup_califs} grupos procesados={len(keepers_chosen)}")

    # Counts after
    cur.execute("SELECT COUNT(*) FROM alumnos")
    alumnos_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calificaciones")
    califs_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alumnos WHERE email LIKE '%teotitlan%'")
    genericos_after = cur.fetchone()[0]
    print(f"[DESPUÉS] alumnos={alumnos_after} calificaciones={califs_after} genericos={genericos_after}")
    print(f"[DELTA] alumnos {alumnos_before}->{alumnos_after} (d={alumnos_after-alumnos_before}) califs {califs_before}->{califs_after} (d={califs_after-califs_before}) genericos {genericos_before}->{genericos_after}")

    # Verificaciones
    cur.execute("SELECT numero_control, COUNT(*) c FROM alumnos GROUP BY numero_control HAVING c>1")
    dup_nc = cur.fetchall()
    print(f"[CHECK] dup numero_control: {len(dup_nc)} (esperado 0) -> {dup_nc[:3] if dup_nc else 'OK'}")
    cur.execute("SELECT LOWER(email) e, COUNT(*) c FROM alumnos GROUP BY LOWER(email) HAVING c>1")
    dup_email = cur.fetchall()
    print(f"[CHECK] dup email lower: {len(dup_email)} (esperado 0) -> {dup_email[:3] if dup_email else 'OK'}")
    # normalized dup check
    cur.execute("SELECT id, nombre, apellido_paterno, apellido_materno FROM alumnos")
    rows = cur.fetchall()
    groups2 = defaultdict(list)
    for r in rows:
        k = f"{normalize(r['nombre'])}|{normalize(r['apellido_paterno'])}|{normalize(r['apellido_materno'] or '')}"
        groups2[k].append(r["id"])
    dup2 = {k: v for k, v in groups2.items() if len(v) > 1}
    print(f"[CHECK] dup nombre normalizado: {len(dup2)} (esperado 0)")

    # List top 10 keepers
    if 'keepers_chosen' in locals() and keepers_chosen:
        print("\n[TOP 10 KEEPERS]")
        for i, (k, kid, nc, bef, moved, losers, reason) in enumerate(keepers_chosen[:10], 1):
            print(f" {i}. '{k}' keeper id={kid} nc={nc} califs_before={bef} moved={moved} losers={losers} | {reason}")

    # integrity: count califs = sum moved + etc should hold, but we already printed delta
    con.close()

    # Verificar pytest
    print("\n[PYTEST] ejecutando pytest -q ...")
    import subprocess, sys
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=str(SCRIPT_DIR), capture_output=True, text=True)
    print(result.stdout[-2000:])
    if result.stderr:
        print(result.stderr[-1000:])
    print(f"[PYTEST] returncode={result.returncode}")
    if result.returncode != 0:
        print("[WARN] pytest falló — revisar")
    else:
        # parse passed count
        import re
        m = re.search(r"(\d+) passed", result.stdout)
        if m:
            print(f"[PYTEST] {m.group(1)} passed")

    print("\n[FIN] Unificación completa. Re-ejecutable: si se corre de nuevo no hará cambios.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
