# Design: Sedes Wiki Multitenancy

## Technical Approach

Shared-schema tenancy + DB wiki on Flask/React/Vite/SQLAlchemy/MySQL single VPS. Add `Sede`, FKs, JWT `role+sede_id`, central `scope_by_sede()` + decorators, 2 new blueprints (`/api/sedes`, `/api/wiki`), scope 12 existing. Covers sede-multitenancy, wiki-manuals, bulk delta. No infra change; Vite `/api` proxy stays.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| A shared-schema `sede_id` | +1 migration, cross-sede easy | **Chosen** |
| B schema-per-sede | -Migrate tooling pain | Rejected |
| C DB-per-sede | -N conns/ops | Rejected |

| Option | Tradeoff | Decision |
|---|---|---|
| A `Admin.role`+`sede_id` CHECK | +1 table, simple | **Chosen** |
| B SedeAdmin join | -join now | Deferred |
| C claims-only | -unenforceable | Rejected |

| Option | Tradeoff | Decision |
|---|---|---|
| A DB WikiPage/Revision/Attachment | +versioned/scoped | **Chosen** |
| B filesystem/git | -perms/mount | Rejected |

| Option | Tradeoff | Decision |
|---|---|---|
| Carrera shared | +simple, reversible | **Chosen** |
| Carrera per sede | -dup now | Deferred |

| Option | Tradeoff | Decision |
|---|---|---|
| Nullable→seed→backfill→NOT NULL | +safe rollback | **Chosen** |

## Data Flow

**Login/scope:** `POST /login` → `generate_tokens(id,type,role,sede_id)` → JWT `{type,role,sede_id}` → `AuthContext` → `Bearer` → `scope_by_sede(q,col)` → `sede_admin WHERE col=token.sede_id` else `general_admin` bypass or `?sede_id`.

**Wiki:** `POST /wiki/pages {sede_id,slug,body}` → `sede_scoped_admin_required` → `WikiPage`+`WikiRevision v1` 201 → `PUT` creates vN+1 → `GET ?slug` via `scope_wiki: sede_id IS NULL OR =caller` → `POST attachments` multipart → `instance/wiki_attachments/<id>/`.

**Migration order:** `1 alembic nullable (sedes+wiki+FKs/indexes)` → `2 seed TEO/HUA idempotent` → `3 backfill --dry-run report → apply heuristic` → `4 alembic NOT NULL (Alumno/Grupo)`.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/models.py` | Modify | Sede, WikiPage/Revision/Attachment, FKs/CHECK/indexes |
| `backend/migrations/versions/*` | Create | 2 revisions (nullable then NOT NULL) |
| `backend/scripts/seed_sedes.py` | Create | Seed TEO/HUA + backfill dry-run/apply + manual_review.csv |
| `backend/utils/security.py` | Modify | `generate_tokens(...,role,sede_id)` |
| `backend/utils/scope.py` | Create | `scope_by_sede`, `scope_wiki` |
| `backend/utils/decorators.py` | Modify | `general_admin_required`, `sede_scoped_admin_required` |
| `backend/routes/auth.py` | Modify | Login/me/refresh include role/sede_id |
| `backend/routes/sedes.py` | Create | /api/sedes CRUD (general write) |
| `backend/routes/wiki.py` | Create | /api/wiki CRUD/history/attachments |
| `backend/routes/alumnos.py` (+11) | Modify | Scoped lists/creates + PATCH /alumnos/:id/sede |
| `backend/routes/imports.py` | Modify | sede CSV alias, preview warn, execute 400 |
| `backend/app.py` | Modify | Register blueprints |
| `frontend/src/context/AuthContext.jsx` | Modify | isGeneralAdmin/isSedeAdmin/sedeId |
| `frontend/src/api/sedes.js`, `wiki.js` | Create | Clients |
| `frontend/src/api/*.js` | Modify | Forward sede_id |
| `frontend/src/App.jsx` | Modify | /admin/sedes, /admin/wiki, /wiki/:slug guards |
| `frontend/src/pages/admin/Sedes.jsx` | Create | Sede CRUD |
| `frontend/src/pages/admin/WikiAdmin.jsx` | Create | Wiki CRUD/history/upload |
| `frontend/src/pages/WikiPage.jsx` | Create | Markdown render |
| `frontend/src/components/layout/Navbar.jsx` | Modify | Badge + switcher for general_admin |
| `frontend/src/pages/admin/Alumnos.jsx` | Modify | Filter/column + scoped Dashboard |

## Interfaces / Contracts

```python
class Sede(db.Model):
    id=db.Column(db.Integer,primary_key=True); nombre=db.Column(db.String(120),nullable=False)
    codigo=db.Column(db.String(10),unique=True,nullable=False) # TEO/HUA
    direccion=db.Column(db.String(255)); activa=db.Column(db.Boolean,default=True)
class Admin: role=db.Column(db.Enum('general_admin','sede_admin'),nullable=False); sede_id=db.Column(db.Integer,db.ForeignKey('sedes.id'),nullable=True,index=True)
    __table_args__=(db.CheckConstraint("(role='general_admin' AND sede_id IS NULL) OR (role='sede_admin' AND sede_id IS NOT NULL)"),)
# Alumno.sede_id FK NOT NULL idx, Grupo.sede_id NOT NULL, Profesor.sede_id NULL
class WikiPage(db.Model):
    id=db.Column(db.Integer,primary_key=True); sede_id=db.Column(db.Integer,db.ForeignKey('sedes.id'),nullable=True,index=True) # NULL=global
    slug=db.Column(db.String(120),nullable=False); title=db.Column(db.String(200),nullable=False); body_markdown=db.Column(db.Text,nullable=False)
    __table_args__=(db.UniqueConstraint('sede_id','slug'),)
class WikiRevision: id, page_id FK, body_markdown, created_by, created_at
class WikiAttachment: id, page_id FK, filename, path, mime, size
```

```python
claims={"id":1,"type":"admin","role":"sede_admin","sede_id":1}
def scope_by_sede(query,col): # sede_admin WHERE col==token.sede_id; general ?sede_id or all
def scope_wiki(q): # WHERE sede_id IS NULL OR ==caller_sede
```

**API:** `GET/POST /api/sedes`, `GET/PUT/DELETE /api/sedes/:id` (general write). `GET /api/wiki/pages?sede_id&slug&search`, `POST /api/wiki/pages {sede_id,slug,title,body}`, `GET/PUT /api/wiki/pages/:id`, `GET /history`, `POST /attachments` multipart → `instance/wiki_attachments`. Scoped: `GET /api/alumnos?search&carrera_id&sede_id`, `POST {sede_id!}`, `PATCH /alumnos/:id/sede {sede_id}` general only. 12 blueprints same: `grupos`,`calificaciones`/`pagos` via alumno join, `profesores`,`asignaciones`,`export`,`boletas`,`imports`,`admins`,`carreras`,`materias`. `POST /alumnos/send-credentials {ids}` 403 if cross-sede for sede_admin. Imports alias `sede`→`[sede,sede_codigo,campus]`; preview warnings, execute 400 if missing for alumnos.

Frontend: `AuthContext {isGeneralAdmin,isSedeAdmin,sedeId,role}`, `ProtectedRoute` + `Admins.jsx` role/sede picker (general only).

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | decorators/scope_by_sede, CHECK, generate_tokens, heuristic | pytest/vitest |
| Integration | cross-sede 403, general bypass, wiki global/private, bulk scoping, import 400 | pytest httpx in-memory |
| E2E | login role/sede, switcher, filter, wiki CRUD→history→attachment, transfer | Playwright |

## Threat Matrix

N/A — no shell/subprocess/VCS/executable classification. Routing is Flask JWT blueprints; wiki writes to `instance/wiki_attachments` with sanitized names/MIME/size checks, not executable. Scoping covered by 403 integration tests.

## Migration / Rollout

Single DB/VPS, Flask-Migrate. Deploy nullable → seed idempotent → dry-run → apply heuristic (folder > numero_control TEO/HUA regex > fallback flagged) → `manual_review.csv` → upgrade NOT NULL → force re-login (JWT bump). Rollback: downgrade drops cols/FKs, revert decorators, wiki droppable.

## Open Questions

- [ ] HUA direccion seed value?
- [ ] Wiki attachment limits beyond 10MB?
- [ ] Profesor single FK confirmed?
