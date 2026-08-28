# Tasks: Sedes Wiki Multitenancy

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated | ~1350 (350+350+300+350) |
| Risk 400 | High |
| Chained PRs | Yes |
| Split | PR1→PR2→PR3→PR4 |
| Delivery | auto-chain |
| Chain | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | PR | Focused test | Harness | Rollback |
|------|------|----|--------------|---------|----------|
| 1 | Sede RBAC JWT scope | PR1→main | `pytest test_scope.py -v` | `seed_sedes.py --dry-run` | `models.py` `utils/` `migrations/` |
| 2 | 12-route scoping + bulk/import | PR2→main | `pytest test_isolation.py -v` | `curl /api/alumnos` TEO≠HUA 403 | `routes/alumnos.py` (+11) |
| 3 | Wiki + /api/sedes | PR3→main | `pytest test_wiki.py -v` | `curl /api/wiki/pages` CRUD+attach | `routes/wiki.py` wiki tables |
| 4 | Frontend UI + e2e | PR4→main | `vitest run; playwright wiki-sede` | `Vite` TEO/HUA login switcher | `context/Auth` `pages/admin/*` |

## Phase 1: Foundational (PR1)

- [x] 1.1 Sede+Admin CHECK — F:`models.py` A:Seed/Constraint D:- E:S
- [x] 1.2 Two alembics nullable→NOT NULL — F:`migrations/` A:migration safe D:1.1 E:S
- [x] 1.3 seed_sedes heuristic + dry-run — F:`scripts/seed_sedes.py` A:Dry-run 0 writes D:1.1 E:M
- [x] 1.4 JWT role/sede_id + Auth — F:`utils/security.py`,`routes/auth.py` A:JWT scope D:1.1 E:S
- [x] 1.5 scope_by_sede/scope_wiki + decorators — F:`utils/scope.py`,`decorators.py` A:403 D:1.4 E:S
- [x] 1.6 Unit RED→GREEN — F:`tests/test_scope.py` A:CHECK/JWT/heuristic D:1.1-1.5 E:M

## Phase 2: Scoping Sweep (PR2)

- [x] 2.1 alumnos scoped + PATCH sede — F:`routes/alumnos.py` A:400/Isolation/403/Transfer D:P1 E:M
- [x] 2.2 grupos/profesores/asignaciones/admins/carreras/materias — F:`routes/*.py` A:Isolation D:2.1 E:M
- [x] 2.3 calificaciones/pagos/boletas/export via Alumno join + bulk send-credentials — F:`routes/*.py` A:403/bypass D:2.1 E:M
- [x] 2.4 imports sede alias + 400 — F:`routes/imports.py` A:Import 400/Cross-reject D:2.1 E:S
- [x] 2.5 Integration 403/general — F:`tests/test_isolation.py` A:12 routes, bulk D:2.1-2.4 E:M

## Phase 3: Wiki (PR3)

- [x] 3.1 WikiPage/Revision/Attachment UNIQUE(sede_id,slug) NULL=global — F:`models.py` A:Global/private D:P1 E:M
- [x] 3.2 /api/sedes CRUD general-only — F:`routes/sedes.py` A:general 201 D:3.1 E:S
- [x] 3.3 /api/wiki CRUD+history sanitize — F:`routes/wiki.py` A:201/403/409 D:3.1 E:M
- [x] 3.4 Attachments multipart — F:`routes/wiki.py` A:201 list D:3.3 E:S
- [x] 3.5 Tests wiki — F:`tests/test_wiki.py` A:global,401,409,attach D:3.2-3.4 E:M

## Phase 4: Frontend (PR4)

- [x] 4.1 AuthContext + api clients — F:`context/AuthContext.jsx`,`api/sedes.js,wiki.js` D:P1 E:S
- [x] 4.2 Routes/guards + Navbar badge/switcher — F:`App.jsx`,`Navbar.jsx` A:guards D:4.1 E:S
- [x] 4.3 Sedes/WikiAdmin/WikiPage — F:`pages/admin/Sedes.jsx`,`Wiki*.jsx` A:CRUD/history D:4.1 E:M
- [x] 4.4 Alumnos filter/column + Dashboard + Admins picker — F:`pages/admin/Alumnos.jsx` A:Zero disabled D:4.1 E:M
- [x] 4.5 E2E wiki-sede — F:`e2e/wiki-sede.spec.js` A:global/private/attach/transfer D:4.2-4.4 E:M
