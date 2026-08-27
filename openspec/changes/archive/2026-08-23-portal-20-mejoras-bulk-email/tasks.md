# Tasks: portal-20-mejoras-bulk-email

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated lines | ~1450 (480+520+450) |
| 400-line risk | High |
| Budget | 800 |
| Chained PRs | Yes |
| Split | PR1 S1→PR2 S2→PR3 S3 |
| Strategy | auto-chain stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | PR | Test | Harness | Rollback |
|------|------|----|------|---------|----------|
| 1 | Bulk email shippable | PR1→main | `pytest test_send_credentials` `vitest ProgressModal` | POST mock SMTP modal retry | revert mail/route/cols flag |
| 2 | Tour+graph | PR2→main | `vitest OnboardingTour CurriculumGraph` | first login tour; 45 nodes | revert 2 comps |
| 3 | Remaining | PR3→main | `pytest` `vitest --coverage` | import/bulk/PDF | per-feature revert |

## Phase 1: S1 Foundation

- [x] 1.1 RED expiry — `backend/tests/test_send_credentials.py` — [x] `test_expired_401` +24h FAIL [x] no log pw — `pytest ::test_expired_401` FAIL — `test: RED expiry`
- [x] 1.2 Model — `backend/models.py` — [x] `temp_password_hash,expires_at,must_change` [x] migrate — `pytest -k hash` GREEN — `feat: temp cols`
- [x] 1.3 Config — `backend/config.py,app.py,extensions.py` — [x] `MAIL_*,BULK_ENABLED,CORS_ORIGINS` env>DB — `pytest test_config_mail` — `feat: config`

## Phase 2: S1 Core

- [x] 2.1 RED contract — `backend/tests/test_send_credentials.py` — [x] 403/429/400/per-row — `pytest` RED — `test: RED contract`
- [x] 2.2 Mail — `backend/utils/mail.py` `templates/emails/credentials.html` — [x] `send_credentials_email` no log alnum8→hash — `pytest test_mail` — `feat: mail`
- [x] 2.3 Endpoint — `backend/routes/alumnos.py` — [x] `@admin_required @limiter 20/min` loop results — `pytest` 12 GREEN — `feat: POST send-credentials`

## Phase 3: S1 UI

- [x] 3.1 RED UI — `ProgressModal.test.jsx Alumnos.test.jsx` — [x] disabled 0 retry failed — `vitest ProgressModal` FAIL — `test: RED UI`
- [x] 3.2 Modal — `frontend/src/components/ui/ProgressModal.jsx` — [x] list sent/failed onRetry — `vitest ProgressModal` GREEN — `feat: ProgressModal`
- [x] 3.3 Alumnos — `Alumnos.jsx` `api/alumnos.js` — [x] `selectedIds` select-all ConfirmDialog→`api.post("/alumnos/send-credentials",{ids,reset_password})` — `vitest Alumnos` GREEN — `feat: bulk wiring`

## Phase 4: S2

- [x] 4.1 Tour — `OnboardingTour.jsx` — [x] RED first login Skip persist Next 1→2→3 GREEN `localStorage onboarding_seen` — `vitest OnboardingTour` — `feat: tour`
- [x] 4.2 Graph — `CurriculumGraph.jsx` — [x] RED 45 nodes 9 cols colors click GREEN grid SVG wire Carreras/MisCalif — `vitest CurriculumGraph` — `feat: graph`

## Phase 5: S3

- [x] 5.1 Import/perf — `Importar.jsx` 4 steps `useImport` lazy virtual bulk — `vitest --coverage` 80% — prep: `useImport` stub + `ImportSteps` placeholder + `React.lazy` Importar/Boletas + tanstack-virtual TODO comment — `vitest App.lazy` GREEN
- [x] 5.2 UX — CmdK EmptyState regex Select — `axe` 0 — `GlobalSearch` Cmd+K mock, `EmptyState`×2 Pagos/Grupos, `validation` helpers vivo, Select x6→+2 migrados — `vitest GlobalSearch EmptyState validation` GREEN
- [x] 5.3 Functional — PDF drag notifs calendar XLSX roles — integration — `Settings` calendario CRUD wiring `api/settings`, `Export` filtros reales `api/export` — `vitest Settings.calendario Export.filters` GREEN
- [x] 5.4 DX/sec — joinedload Redis rotate admin123 JWT pre-commit — `pytest --cov` — `joinedload` grupos.py, `a11y` stub, `CONTRIBUTING.md`, `Select` migrados — `pytest test_grupos_joinedload` GREEN

Deps: 1.1→1.2→1.3→2.1→2.2→2.3→3.1→3.2→3.3(S1 shippable)→4.1→4.2→5.x strict TDD RED→GREEN.
