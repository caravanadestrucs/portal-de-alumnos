# Proposal: Sedes Wiki Multitenancy

## Intent
Isolate Teotitlan/Huautla tenants + sede wiki. Fix 109 alumnos placement via row-level enforcement on single VPS/MySQL stack.

## Scope

### In Scope
- `Sede` (TEO/HUA) + seed
- RBAC `general_admin` (NULL, all) vs `sede_admin` (FK, scoped); JWT `role+sede_id`
- `sede_id`: Alumno/Grupo req, Profesor opt, Admin nullable, Wiki NULL=global
- Wiki `WikiPage`/`WikiRevision`/`WikiAttachment` markdown, admin-write/auth-read, iterative upload
- Scope sweep: alumnos/grupos/calificaciones/pagos/boletas/imports; admin create `general_admin`-only
- Backfill 109 alumnos: dry-run + heuristics + manual queue

### Out of Scope
- `Carrera.sede_id` (shared)
- Many-to-many alumno/profesor sede
- Wiki FTS, anon read, schema-per-sede / DB-per-sede
- Reassigning 607 materias / 4206 calificaciones

## Capabilities

### New Capabilities
- `sede-multitenancy`: Sede lifecycle, row-level isolation, RBAC, sede binding, import scoping, transfer
- `wiki-manuals`: Sede-scoped markdown wiki with revisions/attachments

### Modified Capabilities
- `bulk-credential-delivery`: Scope bulk send by `sede_id`; 403 cross-sede for `sede_admin`

## Approach
Shared-schema `sede_id` + `Admin.role`+FK + DB wiki. `scope_by_sede()` + decorators enforce; `general_admin` bypasses or `?sede_id`; NULL=global.

Discarded: DB-per-sede / schema-per-sede (ops/Migrate overkill), filesystem wiki (perms/bypass), claims-only (unenforceable), external docs (auth mismatch).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/models.py` | Modified | Add Sede, wiki; add FKs |
| `backend/migrations/` | New | Migration, seed, dry-run |
| `backend/utils/*` | Modified | JWT role/sede + helpers |
| `backend/routes/*` | Modified | Scope 12 blueprints; new sedes/wiki |
| `frontend/src/context/AuthContext.jsx` | Modified | Expose `isGeneralAdmin`, `sedeId` |
| `frontend/src/pages/admin/*`,`App.jsx` | Modified | Sede badge/filter, wiki CRUD, guards |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Heuristic ~20% wrong | High | Dry-run + manual queue |
| Missed filter leaks | Medium | Central helper + 403 tests |
| JWT invalidates | Medium | Bump version, force re-login |
| Import without sede col | Medium | Preview warn, execute reject |

## Rollback Plan
FKs nullable; dry-run report-only. Downgrade drops FKs/cols, revert decorators to `admin_required`, NULL backfill. Wiki droppable.

## Dependencies
- Alembic nullable FK; re-login after JWT change

## Success Criteria

- [ ] 109 alumnos assigned; zero NULL, ambiguous flagged
- [ ] 56 genericos corrected per sede
- [ ] Isolation: `sede_admin` own sede only (403 cross), `general_admin` all
- [ ] Wiki: sede-private invisible to other sede, global visible both; auth read, admin write

## Assumptions

1. Sedes = TEO + HUA only
2. Carrera shared (no `Carrera.sede_id`)
3. `general_admin` NULL all-access; only it creates `sede_admin`
4. Wiki markdown, NULL=global, admin write / auth read
5. Profesor opt single `sede_id`
6. Detector: folder > `numero_control` TEO/HUA > fallback TEO flagged
7. `Grupo` explicit `sede_id` required
8. Alumno single FK, transfer via UPDATE
