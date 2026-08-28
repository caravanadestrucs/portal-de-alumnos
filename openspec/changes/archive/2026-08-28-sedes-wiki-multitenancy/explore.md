# Exploration: sedes-wiki-multitenancy

## Current State

- **No Sede model exists.** `backend/models.py` defines 12 tables (`Admin`, `Alumno`, `Carrera`, `Materia`, `Calificacion`, `Profesor`, `Grupo`, `GrupoIntegrante`, `Asignacion`, `NotaRemision`, `PracticaProfesional`, `Config`). No table or FK references a "sede"/campus. Every query is global.
- **Single global admin.** `admins` has one row (`admin@universidadfv.edu.mx`). JWT claims are `{id, type}` only (`admin`|`alumno`|`profesor`), 24h access / 30d refresh. Decorator `admin_required` checks `type=='admin'` with no scope. Frontend `AuthContext.jsx` stores `type/rol` only.
- **109 alumnos dirty.** Instance DB `portal.db` has 109 alumnos across 15 carreras (8 active duplicated: `Pedagogia` (32) vs `Licenciatura en Pedagogia` (22), `Enfermeria` (12) vs `Licenciatura en Enfermeria` (6), etc.), 607 materias, 4206 calificaciones. `alumnos_genericos_para_contactar.csv` already encodes the needed fix: 56 generic contacts with `numero_control` like `2401TEO015PED`, `TEO20250043` — prefix `TEO` = Teotitlan and `origen=solo_boleta|csv_duplicado_unificado`. Source DOCX folders encode sede but CSV/DB today has no `sede` column. BOLETAS directory names referenced: `2023 Pedagogia`, `2024 Pedagogia en linea Huautla y Teot`, `BOLETAS HUAUTLA 1ER. CUAT.` — implying at least **Teotitlan** and **Huautla** (potential third sede unconfirmed).
- **Imports pipeline is sede-unaware.** `backend/routes/imports.py` (`_parse_alumnos`, `_resolve_carrera`) validates `carrera` but never `sede`. Preview/execute work globally; no tenant isolation.
- **Groups tie to carrera, not sede.** `Grupo.carrera_id` → Carrera; `GrupoIntegrante.alumno_id`. `GET /api/grupos`, `/api/alumnos`, `/api/boletas/alumnos` filter by `carrera_id`/`grupo_id`/`search` but never by sede. `list_alumnos` is globally visible to any admin.
- **Wiki/manuals do not exist.** No model, route, or frontend page for wiki. Manuals referenced as "iteratively uploaded" are not stored anywhere. Closest precedent is `Config` key-value and `imports` file upload, not a content system.
- **Infra single-tenant.** Monorepo Flask (factory `create_app`, 15 blueprints `/api/*`) + React Vite 5 (`/api` proxy → `http://backend:5000`) + Docker/Dokploy VPS `89.116.51.59`. Dev DB SQLite (`instance/portal.db`), prod MySQL via `pymysql`+`Flask-Migrate`. No multi-schema, no RLS, no subdomain routing per sede.
- **Existing specs:** `openspec/specs/` has `bulk-credential-delivery`, `curriculum-map`, `student-onboarding` — all global, none mention sede.

### Inferred Sede Mapping Evidence (to be confirmed)

| Signal | Hint |
|--------|------|
| `numero_control` regex | `^(24|25)01TEO\d+|`TEO2025```` — `TEO` = Teotitlan; no `HUA` codes yet in the 55-row generic CSV, but folder name "Huautla y Teot" suggests shared "Pedagogia en linea" spans both sedes |
| `alumnos_genericos_para_contactar.csv` | `origen` column distinguishes boleta-only vs CSV-unified; 56 rows all `carrera` in canonical form (`Pedagogia`) + `@teotitlan.fv.local` email — suggests generic provisioning per sede before correction |
| `Formulario_reparado.csv` | No sede column; carrera via `carrera_id` → duplicated carreras (LP/PED etc.) may actually represent per-sede carrera instances that should collapse once Sede exists |

## Affected Areas

- `backend/models.py` — add `Sede` model; add `sede_id` FKs to `Alumno`, `Carrera` (optional), `Grupo`, `Admin`, `Profesor` (optional), new `WikiPage`/`WikiRevision` + `SedeAdmin` scoping
- `backend/migrations/` — Alembic migration for new tables, FKs, indexes (`ix_alumnos_sede_id`, `ix_admins_sede_id`), data migration for 109 alumnos
- `backend/utils/decorators.py` — extend `admin_required` → `sede_admin_required` / `general_admin_required`, `get_current_admin()` now returns scoped admin; `profesor_required` may need scoping
- `backend/utils/security.py` — `generate_tokens()` must embed `sede_id` + `role` (`general_admin`|`sede_admin`) claims
- `backend/routes/auth.py` — `/login` and `/me` return `sede`, `/register` sets sede; forgot/reset passthrough
- `backend/routes/alumnos.py` — `list_alumnos`, `list_alumnos` stats, `create/update/delete`, `send-credentials` all need `WHERE sede_id = current_sede` for sede_admin; general_admin sees all or with `?sede_id` filter
- `backend/routes/carreras.py`, `materias.py`, `grupos.py`, `boletas.py`, `calificaciones.py`, `pagos.py`, `export.py`, `imports.py`, `profesores.py`, `asignaciones.py` — every global list must be scoped; `imports.preview/execute` must accept/validate `sede`
- `backend/routes/admins.py` — admin CRUD must enforce general_admin-only creation + sede assignment; self-delete guard extends to sede
- `backend/config.py`, `backend/app.py` — register new blueprints (`sedes`, `wiki`), ensure CORS/ limiter still applies
- `backend/seeds/` (new) — `seed_sedes.py` to create Teotitlan/Huautla + backfill alumnos; correction script using `numero_control` + generic CSV as source
- `frontend/src/context/AuthContext.jsx` — expose `isGeneralAdmin`, `isSedeAdmin`, `sede`, `sedeId`; normalize new JWT claims
- `frontend/src/api/*` — `alumnos.js`, `carreras.js`, `grupos.js`, `boletas.js`, `imports.js` must forward `sede_id`; new `sedes.js`, `wiki.js`
- `frontend/src/App.jsx` — add routes `/admin/sedes`, `/admin/wiki/*`, `/wiki/*`; guard `ProtectedRoute` by `sede_admin` vs `general_admin`
- `frontend/src/pages/admin/*` — `Alumnos.jsx` (sede filter + column), `Carreras.jsx`, `Grupos.jsx`, `Boletas.jsx`, `Importar.jsx`, `Admins.jsx` (role/sede picker), `Dashboard.jsx` (scoped counts)
- `frontend/src/components/layout/*` — Navbar/Layout must show current sede badge and sede switcher for general_admin
- `openspec/specs/*` — new specs `sede-multitenancy` + `wiki-manuals` (delta specs) and modifications to existing specs that assume global admin

## Approaches

### 1) Multitenancy Isolation

| Approach | Pros | Cons | Effort |
|----------|------|------|--------|
| **A. Shared DB, shared schema, `sede_id` FK column (row-level tenant)** — add `Sede(id, nombre, codigo, direccion, activa)`; add `sede_id` nullable FK to `Alumno`, `Grupo`, `Admin` (and optionally `Carrera`/`Materia` if carrera is per-sede); every query filters by `current_user.sede_id` when caller is `sede_admin`; general_admin bypasses filter or filters explicitly via `?sede_id`. | Simplest for 109 rows / single VPS / single MySQL DB; one migration; easy to query cross-sede for general_admin; fits existing Flask-Migrate/SQLAlchemy pattern; no infra change; easy to seed/correct iteratively. | Must audit every route to enforce filter — missed filter = leak; carrera deduplication needs decision (shared vs per-sede); not physical isolation (acceptable at this scale). | Low–Medium |
| **B. Shared DB, separate schema per sede (Postgres schemas / MySQL separate DB per sede)** | Strong physical isolation; per-sede backup/restore; schema migration per tenant is explicit. | Massive over-engineering for 2–3 sedes / 109 alumnos; Flask-SQLAlchemy not configured for dynamic schema switching; VPS MySQL would need multi-DB wiring + migration tooling rewrite; makes general_admin cross-sede queries hard; `Flask-Migrate` per-schema is painful. | High |
| **C. Separate DB instance per sede** | Maximum isolation, independent scaling. | Requires N Docker DBs, N connection strings, routing layer, duplicated seed/migrations; cost and ops overhead for Dokploy single VPS is unjustified; alumnos correction would need N ETLs. | High |

**Tradeoff summary:** For 2–3 sedes and <1k alumnos on a single VPS with SQLite dev / MySQL prod, **A (shared schema + `sede_id`) is the only pragmatic choice**. B/C buy isolation the product does not need and blow up the review budget.

### 2) RBAC for Admins

| Approach | Pros | Cons | Effort |
|----------|------|------|--------|
| **A. Single `Admin` table with `role` + nullable `sede_id`** (`role ENUM('general_admin','sede_admin')`, `sede_id FK NULL`; `general_admin` → `sede_id IS NULL`, `sede_admin` → `sede_id NOT NULL`). JWT claims `{type:'admin', role, sede_id}`; decorators `general_admin_required` and `sede_admin_required` branch on claims. | One table, minimal schema; reuses existing `admins` + `generate_tokens`/`admin_required`; easy to promote/demote; migrations simple. | Need CHECK constraint (`role='sede_admin' ↔ sede_id NOT NULL`); old `username='admin'` must be migrated to `role=general_admin`. | Low |
| **B. Separate `SedeAdmin` table** (keep global `Admin`, add `SedeAdmin(id, admin_id, sede_id)`) | Explicit join table allows one admin to belong to multiple sedes later. | Adds join complexity now for a multi-sede future that may never come; decorators need join; seed/login slower for no current need. | Medium |
| **C. Claims-only without DB column** (derive sede from alumno grouping) | No schema change. | Fragile, not enforceable at DB level; every login must recompute sede from heuristic (`numero_control` prefix). | Low but risky |

**Recommendation:** **A** — single table with role + nullable FK. If multi-sede-per-admin is needed later, migrate A→B via a join table without breaking existing data.

### 3) Wiki / Manuals

| Approach | Pros | Cons | Effort |
|----------|------|------|--------|
| **A. DB-backed markdown with revisions** — `WikiPage(id, sede_id FK NULL (NULL=global), slug UNIQUE per sede, title, body_markdown TEXT, created_by_admin_id, updated_at)` + `WikiRevision` for audit; files/images stored as `WikiAttachment` on disk/S3 or inline; CRUD `GET /api/wiki/pages`, `POST /api/wiki/pages`, `PUT /api/wiki/pages/:slug`, history endpoint; frontend renders with `react-markdown` + file upload (iterative). | Versioned, searchable (`LIKE` or SQLite FTS), sede-scoped by default with global fallback; no filesystem permission headaches; iterative upload is just `POST` rows; fits existing SQLAlchemy + admin auth. | Need markdown sanitization + image upload handling (10 MB limit reuse); not Git-native. | Medium |
| **B. Filesystem / Git-backed markdown (e.g., `wiki/teotitlan/*.md` + commit)** | Git history for free; plain MD files editable outside app. | Needs filesystem writes on VPS, Dokploy volume mapping, authz outside DB; sede scoping via folders is easy to bypass; no DB search without index; deployment must mount writes. | Medium–High |
| **C. External docs (Notion/BookStack/MediaWiki/Docsify) embedded via iframe** | No build; feature-complete. | External dependency, per-sede auth is hard, styling mismatch, offline/manual iterative upload outside portal, not covered by existing auth. | Low build but high integration cost |

**Recommendation:** **A** — DB markdown with `sede_id` scoping is idiomatic for Flask + React, supports iterative upload, preserves audit, and keeps all auth in the portal. B/C can be layered later (export wiki to Git/docs site) without committing infra now.

## Recommendation

**Adopt Approach A across all three axes:**

1. **Multitenancy = shared schema `sede_id` column.** Create `Sede` and add `sede_id` FK to `Alumno` (required), `Grupo` (required), `Admin` (nullable: NULL=general_admin), and optionally `Carrera` if carreras are proven per-sede (see open questions). Enforce row-level filtering in every admin route via a new helper `get_scoped_query(base_query, sede_field)` + updated decorators. General_admin queries may filter by `?sede_id` or omit for "all sedes".

2. **RBAC = `Admin.role` + `sede_id`.** Migrate existing `admin` row to `role=general_admin`. JWT now carries `role` + `sede_id` (+ `type='admin'`). Add decorators:
   - `general_admin_required` (only `role==general_admin`)
   - `sede_scoped_admin_required` (pass if `general_admin` OR (`sede_admin` AND resource.sede_id == token.sede_id))
   Frontend `AuthContext` exposes `isGeneralAdmin` / `isSedeAdmin` / `sedeId`. `Admins.jsx` creation form adds role + sede picker (only general_admin can create sede_admin).

3. **Wiki = DB markdown `WikiPage`+`WikiRevision` scoped by `sede_id`.** `sede_id NULL` = global manual visible to all sedes; non-null = sede-private. CRUD is admin-only; read is `login_required` (or public if decided). Upload is iterative: `POST /api/wiki/pages` creates page, `PUT` edits body, `POST /api/wiki/pages/:id/attachments` for PDFs/images. Frontend: `/admin/wiki` (CRUD) + `/wiki/:slug` (read), rendered with `react-markdown` + sanitizer.

**Why this combination:** Fits the existing single-DB, single-VPS, Flask-Migrate, SQLAlchemy, JWT, and React/Vite stack without infra changes; keeps review budget under 400 lines per PR when chained; and directly enables the stated goal "correct alumnos and put them in corresponding sede" via a one-shot migration that reuses `alumnos_genericos_para_contactar.csv` + `numero_control` heuristics with manual override.

**Data-correction plan (proposed):**
- Seed `Sede` rows: `TEO=Teotitlan` (codigo `TEO`), `HUA=Huautla` (codigo `HUA`). Confirm if a third sede exists before seeding.
- Normalize carreras: collapse duplicates (`LP`→`PED`, `LC`→`CON`, etc.) to canonical 7 carreras (`PED`, `ENF`, `DER`, `PSI`, `CDE`, `CON`, `SIS`); decide if carrera rows should themselves be per-sede or shared (recommend shared + alumno.sede_id for now, unless per-sede curriculum diverges).
- Backfill `Alumno.sede_id`: primary key = `numero_control` prefix (`*TEO*`→Teotitlan; viitor `*HUA*`→Huautla) AND cross-check `alumnos_genericos.csv` + BOLETAS folder names. Mark ambiguous rows (`origen=csv_duplicado_unificado`, `numero_control` like `13`, `CSV0002`, `5654664088`) for manual admin review queue rather than guessing. Dry-run script writes `sede_id` report before committing.

## Risks

- **Data migration for 109 alumnos is heuristic, not exact.** `numero_control` formats are heterogeneous (`2401TEO...`, `TEO2025...`, `CSV0002`, `13`, pure phone-like `5654664088`). Auto-assigning sede from prefix will misclassify ~15–25% without manual review. *Mitigation:* make migration two-phase: (1) auto-assign high-confidence TEO, (2) flag low-confidence rows for admin UI bulk correction (checkbox + sede picker) instead of silently guessing.
- **Existing global admin must be upgraded.** The sole `admin` row has no `role`/`sede_id`. Migration must idempotently set `role=general_admin`. Any missed decorator update leaves sede_admin able to hit unscoped routes (e.g., `/api/alumnos/send-credentials` leaking cross-sede). *Mitigation:* centralize scoping in a reusable `scope_by_sede(query, model)` helper + add integration tests for cross-sede 403.
- **Carrera vs sede ownership ambiguous.** If `Pedagogia` is offered at both Teotitlan and Huautla with different `Materias`, sharing one `Carrera` row causes materias to bleed across sedes. If materias are truly shared, per-sede carrera duplication is wasteful. *Mitigation:* ask POs to confirm before locking schema; provide reversible path (add `Carrera.sede_id` later via nullable FK if needed).
- **Permission isolation sweep is large.** At least 12 blueprints (`alumnos`, `carreras`, `materias`, `grupos`, `calificaciones`, `pagos`, `export`, `boletas`, `imports`, `profesores`, `asignaciones`, `admins`) require audit. *Mitigation:* chain PRs by domain slice; first PR ships `Sede`+`Alumno.sede_id`+ decorator infra, later PRs migrate route groups.
- **Wiki scope creep.** "Wiki with manuals iteratively uploaded" is underspecified: file types, max size, versioning, public vs authenticated read, sede vs global visibility, search. *Mitigation:* MVP defines wiki as markdown + attachments (PDF/images), sede-scoped, admin-write / authenticated-read, no FTS initially — extend later.
- **Import path becomes breaking.** Once `sede_id` is required, legacy CSVs (`Formulario_reparado.csv`) without sede column must either default or fail. *Mitigation:* `imports.preview` detects missing `sede` column, shows warning, and `execute` rejects ambiguous rows with actionable error ("add sede column with values TEO/HUA").
- **JWT claim bloat / stale tokens.** Adding `role`+`sede_id` to claims invalidates existing sessions until re-login. *Mitigation:* bump token version, force re-login after deploy, and document in migration notes.

## Ready for Proposal

**Yes — with 8 blocking questions that must be answered before `sdd-propose`:**

1. **Canonical sede list?** Confirm exact sedes (Teotitlan + Huautla only, or additional?). Provide official `nombre` + `codigo` + address for seeding.
2. **Carrera ownership model?** Is a `Carrera` (e.g., `Pedagogia`) shared across sedes or does each sede have its own `Carrera` instance with its own `Materias`? Shared vs per-sede determines whether `Carrera.sede_id` exists.
3. **Admin hierarchy semantics?** Can `sede_admin` manage profesores/grupos/carreras within their sede, or only alumnos? Can they create other `sede_admin` in same sede? Can `general_admin` impersonate a sede view?
4. **Wiki visibility & writers?** Should wiki pages be per-sede (`sede_admin`+`general_admin` write, all alumnos in that sede read) or global (general_admin writes global, sede_admin writes sede-local)? Authenticated-only or public?
5. **Profesor sede binding?** Does a `Profesor` belong to one sede, multiple, or none? Should `Asignacion` be scoped by sede (profesor can only grade grupos in their sede)?
6. **Sede detector for the 109-row correction?** Confirm that `numero_control` containing `TEO`→Teotitlan (and `HUA`→Huautla) is the canonical rule, and that the 56-row `alumnos_genericos_para_contactar.csv` is the authoritative generic-provisioning source vs the live `portal.db`.
7. **Grupo→sede relationship?** Is a `Grupo` always in exactly one sede? Should `Grupo.sede_id` be derived from its `Carrera`'s sede or stored explicitly?
8. **Cross-sede alumnos?** Can an alumno transfer between sedes, or belong to two sedes at once? Should `Alumno.sede_id` be single FK or many-to-many?

Once these are answered, proposal can define intent, scope, and rollback plan (migration reversible via nullable FK + dry-run) without rework.
