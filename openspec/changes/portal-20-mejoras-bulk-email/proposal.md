# Proposal: portal-20-mejoras-bulk-email

## Intent
Stop manual credential hand-off for 50 alumnos + close gaps (admin123, CORS *, memory limiter). Ship 20 UX/perf/DX items.

## Scope

### In Scope
- P0 Bulk email: POST /alumnos/send-credentials {ids,reset_password} @admin 20/min, temp 8-char or 24h token (hashed), smtplib+credentials.html, per-row status+retry
- Security 15,16: rotate admin123+must_change_password, CORS_ORIGINS env, JWT refresh
- UX 1-5: tour 3 steps, curriculum graph, Cmd+K, EmptyState+CTA, inline validation
- Perf 11,13,14: Importar 860L→4 steps+useImport, lazy+virtual, bulk califs POST
- Functional 6-10: PDF drag→extract_pdf, notifs grade-changed, calendar CRUD mora*5, XLSX filtered, roles per carrera
- DX 12,17-20: joinedload verify, Select×6, Redis limit, axe CI+80%+pre-commit, CONTRIBUTING

### Out of Scope
- MySQL prod switch, SendGrid, mobile, RBAC beyond carrera, rebrand

## Capabilities

### New Capabilities
- `bulk-credential-delivery`: temp/token+mail+progress
- `student-onboarding`: 3-step tour
- `curriculum-map`: graph from docx
- `global-search`: Cmd+K
- `payment-calendar`: CRUD mora
- `notifications`: grade-changed
- `fine-grained-roles`: per-carrera
- `legacy-pdf-import`: drag boletas

### Modified Capabilities
- `alumno-management`: bulk+limiter+CORS
- `calificaciones`: bulk+virtual
- `import-export`: wizard+XLSX
- `auth-security`: rotation+refresh
- `ui-system`: Select+EmptyState+axe

## Approach — 3 Slices auto-chain

**S1 Bulk+Security shippable**: mail.py, alumnos.py bulk, security temp, .env MAIL_*, Alumnos.jsx checkboxes+ConfirmDialog, ProgressModal, alumnos.js. Flag MAIL_ENABLED. Mock SMTP tests.

**S2 UX+Perf**: tour, graph react-flow, CmdK cmdk/fuse, EmptyState, regex, useImport+4 steps, lazy+react-window, bulk califs.

**S3 Functional+DX**: PDF drop, notifs polling, Settings calendar, openpyxl, role decorator, Redis fallback memory, Select×6, axe+coverage.

## Affected Areas

| Area | Impact | Desc |
|------|--------|------|
| `backend/routes/alumnos.py` | Modified | bulk endpoint |
| `backend/utils/mail.py` | New | credentials mail |
| `backend/utils/security.py` | Modified | temp+flag |
| `backend/config.py` | Modified | CORS/JWT/MAIL |
| `frontend/src/pages/admin/Alumnos.jsx` | Modified | checkboxes |
| `frontend/src/components/ui/ProgressModal.jsx` | New | progress retry |
| `frontend/src/pages/Importar.jsx` | Modified | split |
| `frontend/src/components/ui/*` | Modified | EmptyState/Select |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Pass leak | Med | bcrypt 24h no-log 20/min |
| SMTP down | High | flag mock queue |
| Scope creep | High | S1 merges alone |
| Redis down | Med | memory fallback |

## Rollback Plan
S1: revert route+mail, nullable column, BULK_EMAIL_ENABLED=false hides UI. S2/3: git revert per PR. No destructive migration.

## Dependencies
MAIL_* SMTP; Redis (fallback memory); ConfirmDialog/Input exists

## Success Criteria
- [ ] N→N mails ≤1s/row progress ✓/✗ retry no pwd log
- [ ] admin123 rotated forced; CORS+refresh ok
- [ ] tour once CmdK<200ms bundle 75kB Importar<300L
- [ ] caps 1-100 Select12/12 axe0 coverage≥80% tests 49+12+7 green

## Delivery Strategy
~1450 lines (S1 480+S2 520+S3 450) >800 → auto-chain 3 PRs <550 TDD.

## Proposal question round
Assumes 8-char 24h token ES templates coordinador per carrera. Confirm or round2.
