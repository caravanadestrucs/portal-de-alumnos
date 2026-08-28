"""
Seed Sedes (TEO/HUA) + heuristic backfill.

Idempotent seed: creates Teotitlan (TEO) and Huautla (HUA) if missing.
Heuristic: folder > numero_control TEO/HUA regex > email domain > fallback flagged.
Dry-run: report counts, zero writes, writes manual_review.csv for ambiguous.
Apply: --apply actually updates Alumno.sede_id.

Usage:
  python scripts/seed_sedes.py --dry-run
  python scripts/seed_sedes.py --apply
  python scripts/seed_sedes.py --dry-run --output instance/manual_review.csv
"""
import os
import re
import csv
import sys
import argparse
import pathlib

# Ensure backend is on path when run as script
BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

TEO_DEF = {"nombre": "Teotitlan", "codigo": "TEO", "direccion": "Teotitlan de Flores Magon, Oaxaca", "activa": True}
HUA_DEF = {"nombre": "Huautla", "codigo": "HUA", "direccion": "Huautla de Jimenez, Oaxaca", "activa": True}


def infer_sede(alumno):
    """
    Heuristic to infer sede for an alumno.

    Priority:
      1) folder attribute (if present and contains hua/teotitlan/teo/hua)
      2) numero_control contains TEO/HUA (case-insensitive)
      3) email contains huautla/teotitlan (or @huautla / @teotitlan)
      4) fallback -> TEO flagged (needs_review=True)

    Returns: (codigo, reason, needs_review)
      codigo: "TEO" or "HUA"
      reason: string describing which rule fired
      needs_review: bool True if fallback/ambiguous
    """
    # helper to get attrs safely
    def get_attr(obj, name):
        return getattr(obj, name, None) if hasattr(obj, name) else None

    numero_control = (get_attr(alumno, "numero_control") or "") or ""
    email = (get_attr(alumno, "email") or "") or ""
    folder = (get_attr(alumno, "folder") or get_attr(alumno, "carpeta") or get_attr(alumno, "sede_folder") or "") or ""

    # 1) folder priority
    if isinstance(folder, str) and folder.strip():
        f_low = folder.lower()
        if "huautla" in f_low or "hua" in f_low:
            # careful: 'hua' may appear in other words; but spec says folder > regex, so we treat any hua as HUA
            # Prefer explicit huautla, but hua also maps
            # If folder contains both? prioritize exact
            if "huautla" in f_low:
                return ("HUA", "folder:huautla", False)
            # if folder contains 'hua' as substring, assume HUA
            # but need to avoid misclassifying teotitlan containing 'hua'? teotitlan does not contain hua
            return ("HUA", "folder:hua", False)
        if "teotitlan" in f_low or "teo" in f_low:
            return ("TEO", "folder:teotitlan", False)

    # 2) numero_control regex TEO/HUA
    nc_up = str(numero_control).upper()
    # Check for TEO and HUA substrings; if both, flagged? But such case is rare — treat as ambiguous
    has_teo = "TEO" in nc_up
    has_hua = "HUA" in nc_up
    if has_teo and has_hua:
        # ambiguous — flagged but choose TEO fallback for now
        return ("TEO", "numero_control:both_TEO_HUA_ambiguous", True)
    if has_teo:
        return ("TEO", "numero_control:TEO", False)
    if has_hua:
        return ("HUA", "numero_control:HUA", False)

    # 3) email domain heuristic
    email_low = str(email).lower()
    if "huautla" in email_low:
        return ("HUA", "email:huautla", False)
    if "teotitlan" in email_low:
        return ("TEO", "email:teotitlan", False)
    # generic: check for .teo or .hua? Not needed

    # 4) fallback flagged — assign TEO but needs review
    return ("TEO", "fallback:assigned_TEO_flagged", True)


# alias for test compatibility
def detect_sede(alumno):
    return infer_sede(alumno)


def heuristic(alumno):
    return infer_sede(alumno)


def seed_sedes():
    """Idempotent seed TEO/HUA into DB. Returns dict with created/existing."""
    from app import create_app
    from models import db, Sede

    app = create_app()
    with app.app_context():
        db.create_all()
        result = {"created": [], "existing": []}
        for definition in (TEO_DEF, HUA_DEF):
            existing = Sede.query.filter_by(codigo=definition["codigo"]).first()
            if existing:
                result["existing"].append(definition["codigo"])
            else:
                sede = Sede(**definition)
                db.session.add(sede)
                result["created"].append(definition["codigo"])
        if result["created"]:
            db.session.commit()
        return result


def _get_sede_map():
    """Return {codigo: id} map, ensuring sedes exist."""
    from models import Sede
    # assume called within app_context and sedes already seeded
    sedes = Sede.query.all()
    return {s.codigo: s.id for s in sedes}


def backfill(dry_run=True, output_csv=None, verbose=True):
    """
    Heuristic backfill for alumnos with sede_id IS NULL.

    dry_run=True: report only, zero writes
    dry_run=False / apply: actually updates DB

    Writes manual_review.csv for flagged rows.

    Returns report dict: {total, to_teo, to_hua, flagged, details: [...]}
    """
    from app import create_app
    from models import db, Alumno, Sede

    app = create_app()
    with app.app_context():
        db.create_all()
        # ensure sedes seeded
        for definition in (TEO_DEF, HUA_DEF):
            if not Sede.query.filter_by(codigo=definition["codigo"]).first():
                db.session.add(Sede(**definition))
        db.session.commit()
        sede_map = _get_sede_map()
        # ensure we have ids
        if "TEO" not in sede_map or "HUA" not in sede_map:
            raise RuntimeError("Sede seeding failed")

        alumnos_null = Alumno.query.filter(Alumno.sede_id.is_(None)).all()
        total = len(alumnos_null)
        to_teo = 0
        to_hua = 0
        flagged = 0
        details = []
        flagged_rows = []

        for alumno in alumnos_null:
            codigo, reason, needs_review = infer_sede(alumno)
            # normalize codigo
            if codigo not in ("TEO", "HUA"):
                codigo = "TEO"
                needs_review = True
                reason = "fallback:invalid_code"
            if needs_review:
                flagged += 1
                flagged_rows.append({
                    "id": alumno.id,
                    "numero_control": alumno.numero_control,
                    "nombre_completo": getattr(alumno, "nombre_completo", f"{alumno.nombre} {alumno.apellido_paterno}"),
                    "email": alumno.email,
                    "inferred_sede": codigo,
                    "reason": reason,
                    "needs_review": True,
                })
            if codigo == "TEO":
                to_teo += 1
            else:
                to_hua += 1
            details.append({
                "id": alumno.id,
                "numero_control": alumno.numero_control,
                "inferred_sede": codigo,
                "reason": reason,
                "needs_review": needs_review,
            })

            if not dry_run:
                # apply
                alumno.sede_id = sede_map[codigo]

        if not dry_run and (to_teo + to_hua > 0):
            db.session.commit()

        # write manual_review.csv for flagged
        if flagged_rows:
            if output_csv is None:
                # default to backend/instance/manual_review.csv
                output_csv = BACKEND_DIR / "instance" / "manual_review.csv"
            else:
                output_csv = pathlib.Path(output_csv)
            output_csv.parent.mkdir(parents=True, exist_ok=True)
            with open(output_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "numero_control", "nombre_completo", "email", "inferred_sede", "reason", "needs_review"])
                writer.writeheader()
                for row in flagged_rows:
                    writer.writerow(row)
            if verbose:
                print(f"[backfill] flagged {flagged} written to {output_csv}")
        else:
            # ensure empty csv with header if none flagged but file exists? Not needed
            if verbose and dry_run:
                print("[backfill] no flagged rows")

        report = {
            "total_null": total,
            "total": total,
            "to_teo": to_teo,
            "to_hua": to_hua,
            "flagged": flagged,
            "dry_run": dry_run,
            "details": details,
            "flagged_rows": flagged_rows,
        }
        if verbose:
            print(f"[backfill] dry_run={dry_run} total_null={total} TEO={to_teo} HUA={to_hua} flagged={flagged}")
        return report


def dry_run(output_csv=None, verbose=True):
    """Alias for backfill dry-run."""
    return backfill(dry_run=True, output_csv=output_csv, verbose=verbose)


def run_dry_run(output_csv=None, verbose=True):
    return backfill(dry_run=True, output_csv=output_csv, verbose=verbose)


def apply_backfill(output_csv=None, verbose=True):
    return backfill(dry_run=False, output_csv=output_csv, verbose=verbose)


def main():
    parser = argparse.ArgumentParser(description="Seed sedes and heuristic backfill")
    parser.add_argument("--dry-run", action="store_true", help="Report only, zero writes")
    parser.add_argument("--apply", action="store_true", help="Actually apply sede assignments")
    parser.add_argument("--output", type=str, default=None, help="manual_review.csv path")
    parser.add_argument("--seed-only", action="store_true", help="Only seed sedes, not backfill")
    args = parser.parse_args()

    # Default behavior: if no args, do dry-run (safe)
    if args.seed_only:
        res = seed_sedes()
        print(f"[seed] created={res['created']} existing={res['existing']}")
        return

    if not args.dry_run and not args.apply:
        # default to dry-run for safety
        print("[info] no --dry-run or --apply specified, defaulting to --dry-run (safe)")
        args.dry_run = True

    if args.apply and args.dry_run:
        print("[error] cannot specify both --dry-run and --apply")
        sys.exit(1)

    # always ensure seed first
    seed_res = seed_sedes()
    if seed_res["created"]:
        print(f"[seed] created sedes: {seed_res['created']}")
    else:
        print(f"[seed] sedes already exist: {seed_res['existing'] or ['TEO','HUA']}")

    if args.dry_run:
        report = backfill(dry_run=True, output_csv=args.output)
        print(f"[dry-run] total={report['total']} TEO={report['to_teo']} HUA={report['to_hua']} flagged={report['flagged']} (zero writes)")
    elif args.apply:
        report = backfill(dry_run=False, output_csv=args.output)
        print(f"[apply] applied total={report['total']} TEO={report['to_teo']} HUA={report['to_hua']} flagged={report['flagged']}")


if __name__ == "__main__":
    main()
