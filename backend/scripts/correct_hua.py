"""
Correct HUA/TEO assignment using real boletas/ folder.

- Indexes all DOCX in project_root/boletas (86 files, 9 with HUAUTLA in path).
- For each alumno, searches:
  1) Direct filename match (normalized without accents, lower) against any DOCX
     individual file stem (cleaned from PENDIENTE/BAJA/TEMPORAL markers).
  2) If not found, searches inside the 6 bulk HUA DOCX tables (python-docx)
     for NOMBRE: rows. Bulk DOCX paths all contain "huautla".
- If match path contains "huautla" -> HUA (sede 2), else TEO (sede 1).
  Bulk matches are inherently HUA.
- Updates Alumno.sede_id and rewrites backend/instance/manual_review.csv
  with only truly unmatched (fallback) rows flagged.

Usage:
  python backend/scripts/correct_hua.py
  python backend/scripts/correct_hua.py --dry-run
"""

import pathlib
import re
import sys
import csv
import unicodedata

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

PROJECT_ROOT = BACKEND_DIR.parent
BOLETAS_ROOT = PROJECT_ROOT / "boletas"

# Fallback if project structure differs (e.g., when run from different cwd)
if not BOLETAS_ROOT.exists():
    # Try absolute as described in task
    alt = pathlib.Path(r"C:\Users\Dario\Desktop\portal de alumnos\boletas")
    if alt.exists():
        BOLETAS_ROOT = alt


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize(s: str) -> str:
    """Lower, strip accents, keep alphanumeric, collapse spaces."""
    if not s:
        return ""
    s = strip_accents(s.lower())
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_tokens(s: str):
    return normalize(s).split()


def lev(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def tokens_match_set(a_tokens, b_tokens, max_lev=2) -> bool:
    """Order-agnostic token set match with per-token Levenshtein tolerance."""
    a_set = set(a_tokens)
    b_set = set(b_tokens)
    if len(a_set) != len(b_set):
        return False
    b_list = list(b_set)
    used = [False] * len(b_list)
    for at in a_set:
        found = False
        for j, bt in enumerate(b_list):
            if used[j]:
                continue
            if at == bt or lev(at, bt) <= max_lev:
                used[j] = True
                found = True
                break
        if not found:
            return False
    return True


def build_docx_index():
    """Index all DOCX files under BOLETAS_ROOT, cleaned."""
    all_docx = [p for p in BOLETAS_ROOT.rglob("*.docx") if not p.name.startswith("~$")]
    index = {}  # norm_clean_stem -> list[Path]
    token_index = {}  # norm_clean_stem -> (tokens, Path, stem)
    for p in all_docx:
        # Remove PENDIENTE/BAJA/TEMPORAL markers even without word boundaries
        cleaned = re.sub(r"(PENDIENTE|BAJA|TEMPORAL)", " ", p.stem, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        norm_key = normalize(cleaned)
        if not norm_key:
            continue
        index.setdefault(norm_key, []).append(p)
        # also index original without cleaning for exact fallback
        orig_key = normalize(p.stem)
        if orig_key != norm_key:
            index.setdefault(orig_key, []).append(p)
        # token index for robust matching
        tok = normalize_tokens(cleaned)
        token_index[norm_key] = (tok, p, p.stem)
    return all_docx, index, token_index


def build_bulk_hua_index():
    """Parse the 6 bulk HUA DOCX tables and extract normalized NOMBRE entries."""
    from docx import Document

    bulk_dir = BOLETAS_ROOT / "BOLETAS HUAUTLA 1ER. CUAT. SEP-DIC 2025"
    bulk_files = []
    if bulk_dir.exists():
        bulk_files = [p for p in bulk_dir.iterdir() if p.suffix == ".docx" and not p.name.startswith("~")]
    else:
        # Fallback: search any docx whose path contains huautla and has bulk characteristics (>2 tables)
        all_docx = [p for p in BOLETAS_ROOT.rglob("*.docx") if not p.name.startswith("~$")]
        bulk_files = [p for p in all_docx if "huautla" in str(p).lower()]

    bulk_norm_to_name = {}
    bulk_norm_to_tokens = {}
    bulk_norm_to_path = {}
    for f in bulk_files:
        try:
            doc = Document(str(f))
        except Exception as e:
            print(f"[WARN] could not open bulk {f}: {e}")
            continue
        # Only consider bulk files with multiple NOMBRE entries (6 bulk files)
        # Individual HUA files in "2024 Pedagogia en linea Huautla y Teot" also contain huautla but are single-student
        # We distinguish by counting tables; bulk files have >=4 tables
        # But for correctness, we include all huautla files' NOMBRE rows as potential HUA evidence
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    txt = cell.text.strip()
                    if txt.startswith("NOMBRE:"):
                        name = txt.replace("NOMBRE:", "").strip()
                        name = re.sub(r"\s+", " ", name).strip()
                        if not name:
                            continue
                        norm_name = normalize(name)
                        tok = normalize_tokens(name)
                        # Keep first occurrence; also track path
                        if norm_name not in bulk_norm_to_name:
                            bulk_norm_to_name[norm_name] = name
                            bulk_norm_to_tokens[norm_name] = tok
                            bulk_norm_to_path[norm_name] = str(f)
        # Also filter to only bulk bulk: if file is in BOLETAS HUAUTLA ... we already have, else ignore single?
    return bulk_files, bulk_norm_to_name, bulk_norm_to_tokens, bulk_norm_to_path


def main(dry_run=False):
    from app import create_app
    from models import db, Alumno, Sede

    app = create_app()
    with app.app_context():
        db.create_all()
        # Ensure sedes exist
        teo = Sede.query.filter_by(codigo="TEO").first()
        hua = Sede.query.filter_by(codigo="HUA").first()
        if not teo or not hua:
            from scripts.seed_sedes import seed_sedes
            seed_sedes()
            teo = Sede.query.filter_by(codigo="TEO").first()
            hua = Sede.query.filter_by(codigo="HUA").first()

        sede_map = {s.codigo: s.id for s in Sede.query.all()}
        if "TEO" not in sede_map or "HUA" not in sede_map:
            raise RuntimeError("Sede seeding failed")

        alumnos = Alumno.query.all()
        total = len(alumnos)
        print(f"[correct_hua] total alumnos {total}")
        print(f"[correct_hua] boletas root {BOLETAS_ROOT} exists={BOLETAS_ROOT.exists()}")

        all_docx, docx_index, token_index = build_docx_index()
        print(f"[correct_hua] indexed DOCX {len(all_docx)} (86 expected, 9 with HUAUTLA in path)")
        hua_path_count = sum(1 for p in all_docx if "huautla" in str(p).lower())
        print(f"[correct_hua] HUAUTLA path count {hua_path_count} (9 expected)")

        bulk_files, bulk_names, bulk_tokens, bulk_paths = build_bulk_hua_index()
        print(f"[correct_hua] bulk HUA files {len(bulk_files)}")
        for f in bulk_files:
            print(f"  - {f.name}")
        print(f"[correct_hua] bulk distinct names {len(bulk_names)}")

        # Build token list for docx for fallback matching
        # Also handle individual HUA folder: 2024 Pedagogia en linea Huautla y Teot (3 docx)
        # Those are already in all_docx with huautla in path

        to_teo = 0
        to_hua = 0
        flagged = 0
        details = []
        flagged_rows = []

        for alumno in alumnos:
            # Build alumno name candidates
            full = f"{alumno.nombre or ''} {alumno.apellido_paterno or ''} {alumno.apellido_materno or ''}".strip()
            full = re.sub(r"\s+", " ", full)
            inv = f"{alumno.apellido_paterno or ''} {alumno.apellido_materno or ''} {alumno.nombre or ''}".strip()
            inv = re.sub(r"\s+", " ", inv)

            norm_full = normalize(full)
            norm_inv = normalize(inv)
            tok_full = normalize_tokens(full)
            # tok_inv is same set as tok_full (just order), but keep for completeness
            tok_set = set(tok_full)

            found_path = None
            reason = ""
            needs_review = False
            codigo = "TEO"

            # 1) Try direct normalized filename match (exact)
            matched = False
            for cand_norm in (norm_full, norm_inv):
                if cand_norm in docx_index:
                    # pick first path; if multiple, prefer huautla if any
                    candidates = docx_index[cand_norm]
                    # Prefer huautla path if exists among candidates
                    hua_cands = [p for p in candidates if "huautla" in str(p).lower()]
                    chosen = hua_cands[0] if hua_cands else candidates[0]
                    found_path = str(chosen)
                    matched = True
                    reason = f"filename:{cand_norm}"
                    break

            # 2) If not matched via exact, try token-set matching against docx stems
            if not matched:
                for norm_key, (tok, path, stem) in token_index.items():
                    if tokens_match_set(tok_full, tok, max_lev=2):
                        found_path = str(path)
                        matched = True
                        reason = f"filename_tokens:{normalize(stem)}"
                        break

            # 3) If still not matched, try bulk HUA tables (inherently HUA)
            is_bulk_match = False
            bulk_match_name = None
            bulk_match_path = None
            if not matched or (found_path and "huautla" not in found_path.lower()):
                # Check bulk regardless, but prioritize bulk HUA if found
                for b_norm, b_tok in bulk_tokens.items():
                    # Exact normalized match
                    if norm_full == b_norm or norm_inv == b_norm:
                        is_bulk_match = True
                        bulk_match_name = bulk_names[b_norm]
                        bulk_match_path = bulk_paths[b_norm]
                        break
                    # Token-set match with tolerance
                    if tokens_match_set(tok_full, b_tok, max_lev=2):
                        is_bulk_match = True
                        bulk_match_name = bulk_names[b_norm]
                        bulk_match_path = bulk_paths[b_norm]
                        break
                    # Also check Levenshtein on full string <=2 (handles XOCHILT vs XOCHITL)
                    if abs(len(norm_full) - len(b_norm)) <= 2 and lev(norm_full, b_norm) <= 2:
                        is_bulk_match = True
                        bulk_match_name = bulk_names[b_norm]
                        bulk_match_path = bulk_paths[b_norm]
                        break
                    if abs(len(norm_inv) - len(b_norm)) <= 2 and lev(norm_inv, b_norm) <= 2:
                        is_bulk_match = True
                        bulk_match_name = bulk_names[b_norm]
                        bulk_match_path = bulk_paths[b_norm]
                        break
                if is_bulk_match:
                    found_path = bulk_match_path
                    matched = True
                    reason = f"bulk_hua:{bulk_match_name}"

            # Determine sede
            if matched and found_path and "huautla" in found_path.lower():
                codigo = "HUA"
                # Bulk or individual HUA path
                if is_bulk_match:
                    reason = f"bulk_hua:{bulk_match_name}" if bulk_match_name else "bulk_hua"
                else:
                    reason = f"folder:huautla:{pathlib.Path(found_path).name}"
                needs_review = False
            elif matched and found_path:
                # Found individual file but not huautla -> TEO
                codigo = "TEO"
                reason = reason or f"folder:teotitlan:{pathlib.Path(found_path).name}"
                needs_review = False
            else:
                # No DOCX evidence at all -> fallback TEO flagged
                codigo = "TEO"
                reason = "fallback:assigned_TEO_flagged:no_docx_match"
                needs_review = True
                found_path = ""

            if codigo == "TEO":
                to_teo += 1
            else:
                to_hua += 1
            if needs_review:
                flagged += 1
                flagged_rows.append({
                    "id": alumno.id,
                    "numero_control": alumno.numero_control,
                    "nombre_completo": alumno.nombre_completo,
                    "email": alumno.email,
                    "inferred_sede": codigo,
                    "reason": reason,
                    "needs_review": True,
                    "docx_path": found_path or "",
                })
            details.append({
                "id": alumno.id,
                "numero_control": alumno.numero_control,
                "nombre_completo": alumno.nombre_completo,
                "inferred_sede": codigo,
                "reason": reason,
                "needs_review": needs_review,
                "docx_path": found_path or "",
            })

            if not dry_run:
                alumno.sede_id = sede_map[codigo]

        if not dry_run:
            db.session.commit()

        # Write manual_review.csv
        output_csv = BACKEND_DIR / "instance" / "manual_review.csv"
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        # Always write header; if flagged_rows empty, write only header + comment
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            # Write informative header comments if no flagged
            if flagged == 0:
                f.write("# CORRECTED HUA/TEO assignment - no manual review required\n")
                f.write(f"# Total {total} -> TEO {to_teo} HUA {to_hua} flagged 0\n")
                f.write(f"# Source: {BOLETAS_ROOT} ({len(all_docx)} DOCX, {hua_path_count} HUA)\n")
                f.write(f"# Bulk HUA files {len(bulk_files)} with {len(bulk_names)} names\n")
            writer = csv.DictWriter(f, fieldnames=["id", "numero_control", "nombre_completo", "email", "inferred_sede", "reason", "needs_review"])
            writer.writeheader()
            for row in flagged_rows:
                # Ensure needs_review is string True for CSV compatibility
                writer.writerow({k: row[k] for k in ["id", "numero_control", "nombre_completo", "email", "inferred_sede", "reason", "needs_review"]})

        print(f"[correct_hua] dry_run={dry_run} total={total} TEO={to_teo} HUA={to_hua} flagged={flagged}")
        if dry_run:
            print("[correct_hua] dry-run: no DB writes")
        else:
            print(f"[correct_hua] DB updated, manual_review.csv written to {output_csv} flagged={flagged}")

        return {
            "total": total,
            "to_teo": to_teo,
            "to_hua": to_hua,
            "flagged": flagged,
            "details": details,
            "flagged_rows": flagged_rows,
            "dry_run": dry_run,
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Correct HUA/TEO via boletas/")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no DB writes")
    args = parser.parse_args()
    report = main(dry_run=args.dry_run)
    # Log summary for verification step
    print(f"{report['to_teo']} TEO, {report['to_hua']} HUA, flagged {report['flagged']}")
