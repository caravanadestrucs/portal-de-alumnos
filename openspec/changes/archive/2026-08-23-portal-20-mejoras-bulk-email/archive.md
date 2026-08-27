# Archive Report: portal-20-mejoras-bulk-email

**Change**: portal-20-mejoras-bulk-email
**Archived**: 2026-08-23
**Archived to**: `openspec/changes/archive/2026-08-23-portal-20-mejoras-bulk-email/`
**Store**: hybrid (Engram + OpenSpec)
**Verdict**: PASS_WITH_WARNINGS (0 blockers, 0 critical, 4 warnings)
**Slices**: S1 bulk+security (7f7d39e) → S2 tour/graph (28f1447, c124ce3, 2c0f9dd) → S3 remaining (55011c1, 222cb09, be40d83, 6fe27cc)

## Summary — Final State (Authoritative)

Per orchestrator final-state facts (outrank stale snapshots):

- **Verify**: 14/14 scenarios PASS, 9/9 requirements, 0 blockers, 4 warnings (tour key v1 vs spec, admin123 seed, coverage threshold not enforced, Query.get warnings)
- **Tests**: frontend 97/97 (20 files) + backend 24/24 (including test_bulk_credentials 10 + test_grupos_joinedload 2) — all green
- **Build**: vite 5.4.21, 1512 modules, 405.45 kB index + Importar 18.71 kB + Boletas 11.15 kB lazy chunks, 0 errors, built 7.91s
- **Bulk email**: `Alumno.temp_password_hash` nullable String(256), `temp_password_expires_at` nullable DateTime, `must_change_password` Bool; 8-char alphanumeric via `secrets.choice`, bcrypt hash, 24h expiry (`utcnow+24h`), per-row 200/207 (`results[{id,status,email,error}]`), no plaintext log (logs only `to_email`/`alumno_id`), `@admin_required` + `@limiter.limit("20/minute")` 429, `ProgressModal` retry only failed — shippable
- **Tour**: `localStorage["onboarding_seen_v1"]` (spec says `onboarding_seen`; implementation uses `v1`), 3 pasos (calificaciones/pagos/requisitos), Skip/Prev/Next/Finish, persist on Skip or Finish
- **Graph**: `CurriculumGraph.jsx` 45 nodos agrupados en 9 cols CSS `grid-cols-9` from `GET /api/materias`, color `aprobado=green` `cursando=yellow` `pendiente=gray` + legend, click detail panel, wired Carreras/MisCalificaciones
- **Remaining deferred (S3 follow-ups)**: Importar 860L split completo, PDF drag, notifs, Redis rate limit prod, full Select 6 restantes, axe-core CI — documented as suggestions, non-blocking

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| bulk-credential-delivery | Created | 3 requirements, 7 scenarios (Dispatch, Temp Security, Observability+Retry+Guardrails) |
| student-onboarding | Created | 3 requirements, 4 scenarios (First-Login, Dismiss Persistently, Step Navigation) |
| curriculum-map | Created | 3 requirements, 3 scenarios (Graph Rendering, Progress Coloring, Detail Navigation) |

**Mechanical copy**: `cp` via `C:\Program Files\Git\usr\bin\cp.exe` + `diff -r` empty for each domain (bulk → student-onboarding → curriculum-map). Verbatim: `VERIFY EMPTY DIFF OK` ×3.
**Source of truth now**: `openspec/specs/bulk-credential-delivery/spec.md`, `openspec/specs/student-onboarding/spec.md`, `openspec/specs/curriculum-map/spec.md`

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Mail transport | `smtplib` stdlib extend `utils/email.py` + `_get_smtp_config()` env>DB | Zero dep, matches existing, sync ok <50 mails |
| Temp credential | `secrets.choice(alnum)×8` + `generate_password_hash` + 24h | Spec "8-char alphanumeric", user-friendly, bcrypt |
| Rate limiter | `memory://` fallback with `REDIS_URL` try, warning log | Existing `extensions.limiter` memory; Redis deferred S3 |
| Curriculum graph | CSS grid 9 cols + 45 nodes, no external lib | 45 nodes small, react-flow 80kB overkill; SVG edges optional |
| Frontend bulk state | `useState(Set<Map>)` local | Zustand overkill single page |
| Tour storage key | `onboarding_seen_v1` | Versioned key; tests use v1; diverges from spec wording (WARNING) |

## Testing Evidence — Final Numbers

- **Backend**: `python -m pytest tests/test_bulk_credentials.py tests/test_grupos_joinedload.py -v` 12 passed (10 bulk + 2 joinedload); full `tests/` 24 passed
  - `test_expired_401`, `test_plaintext_never_logged`, `test_admin_sends_to_3_selected`, `test_non_admin_forbidden`, `test_ids_required_400`, `test_smtp_failure_per_row_with_retry` (207), `test_rate_limit_20_per_minute`, `test_alnum8_and_hashed`, `test_config_mail_env_and_bulk_flag`, `test_send_credentials_email_util`, `test_grupos_uses_joinedload`, `test_integrantes_uses_joinedload_or_eager`
- **Frontend**: `npx vitest run` 97/97 across 20 files (OnboardingTour 5, CurriculumGraph 3, ProgressModal 4, Alumnos.bulk 2, GlobalSearch 5, EmptyState 5, etc.)
- **Build**: `npx vite build` exit 0, 1512 modules, `index 405.45kB`, `Importar 18.71kB`, `Boletas 11.15kB`
- **Coverage**: not available (`@vitest/coverage-v8` missing, `pytest-cov` not configured) — tasks claim 80% unproven (WARNING)
- **Compliance**: 14/14 scenarios compliant via tests + static (`alumnos.py:363-417`, `mail.py:67-96,139,143`, `auth.py:121-123`, `OnboardingTour.jsx:4`, `CurriculumGraph.jsx`)

## Warnings (from verify.md, still at close)

1. **Tour key divergence**: spec `onboarding_seen` vs impl `onboarding_seen_v1` — functional but violates wording; migration shows tour again for prior `onboarding_seen` users
2. **admin123 not rotated**: `app.py:209` seeds `admin123` if no admin, proposal P0 gap remains; no spec requirement — follow-up `ADMIN_DEFAULT_PASSWORD` env + forced change
3. **Coverage threshold not evidenced**: no runtime 80% report
4. **LegacyApiWarning**: `Query.get()` deprecated 30× in `alumnos.py:364` — use `Session.get()`; Act warnings 20+ in GlobalSearch/OnboardingTour/CurriculumGraph/Alumnos.bulk — wrap in `act()`

No CRITICAL; archive proceeds under Strict-vs-OpenSpec policy (non-blocking warnings).

## Commits

- 7f7d39e feat(bulk): S1 temp 24h + send-credentials + ProgressModal + limiter
- 28f1447 feat(onboarding): tour 3 pasos localStorage
- c124ce3 feat(curriculum): graph 45/9 grid
- 2c0f9dd docs(sdd): S2 tasks complete
- 55011c1 feat(validation): regex helpers
- 222cb09 feat(empty): EmptyState Pagos
- be40d83 feat(search): Cmd+K placeholder
- 6fe27cc chore(dx): joinedload, Select×2, axe placeholder, lazy Importar/Boletas, calendario, export

## Archive Contents

- proposal.md ✅
- specs/bulk-credential-delivery/spec.md ✅
- specs/student-onboarding/spec.md ✅
- specs/curriculum-map/spec.md ✅
- design.md ✅
- tasks.md ✅ (15/15 complete)
- verify.md ✅ (pass_with_warnings 14/14, 0 blockers)
- archive.md ✅ (this report)

### Verification

- [x] Main specs created via mechanical `cp` + empty `diff -r` ×3
- [x] Change folder moved via `git mv` to `archive/2026-08-23-portal-20-mejoras-bulk-email` + empty `diff -r` snapshot vs dest
- [x] Archive contains all artifacts
- [x] Archived `tasks.md` 15/15 checked, no stale unchecked
- [x] Active `openspec/changes/` no longer has `portal-20-mejoras-bulk-email`
- [x] Verbatim diffs included and empty (see Mechanical Copy Contract evidence above)
- [x] Engram IDs recorded (below)

## Engram Traceability

- sdd/portal-20-mejoras-bulk-email/proposal #147 obs-c98c2c0ec5d70f4d
- sdd/portal-20-mejoras-bulk-email/spec #148 obs-fe1d17790f225fb9
- sdd/portal-20-mejoras-bulk-email/design #149 obs-02b508f55cc83133
- sdd/portal-20-mejoras-bulk-email/tasks #150 obs-45c2cedbec373023
- sdd/portal-20-mejoras-bulk-email/verify-report #152 obs-07b16476b8f13482
- Apply Progress S3 #151 obs-444d7647ebbc7aab
- sdd-init/portal-de-alumnos #144 obs-2c6cbf166c2112fb
- This report: sdd/portal-20-mejoras-bulk-email/archive-report (new)

## Next Steps / Follow-ups (Deferred, non-blocking)

All intentionally deferred per S3 follow-ups:
- Importar 860L full split → `useImport` hook + `ImportSteps` 4-step wizard + `tanstack-virtual` (currently stub + TODO)
- PDF drag `extract_pdf` → boletas
- Notifs `grade-changed` polling
- Redis rate limit prod (currently memory fallback)
- Full Select migration (6 remaining + axe-core CI)
- Coverage CI: install `@vitest/coverage-v8` + `pytest-cov`, enforce 80%
- Tour spec amend: `onboarding_seen` → `onboarding_seen_v1` with migration note or align impl
- Admin rotation: `ADMIN_DEFAULT_PASSWORD` env + forced `must_change_password`
- Retry-After header on 429, `Session.get()` migration, act() wrapping

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. Source of truth updated. Ready for next change.

## Mechanical Copy Evidence (verbatim)

```
VERIFY EMPTY DIFF OK bulk-credential-delivery
VERIFY EMPTY DIFF OK student-onboarding
VERIFY EMPTY DIFF OK curriculum-map
diff -r snapshot vs dest: exit 0
VERIFY EMPTY DIFF OK archive move
```
