# Design: portal-20-mejoras-bulk-email

## Technical Approach
Slice 1 ships bulk credential delivery + security hotfixes as shippable increment (480L). Extends `backend/utils/email.py` (smtplib) with `credentials.html` template, adds `POST /api/alumnos/send-credentials` with per-row status, bulk checkbox UI in `Alumnos.jsx` + `ProgressModal`. Adds `Alumno.temp_password_hash`, `temp_password_expires_at`, `must_change_password` for 24h expiry. Mail config via `.env` MAIL_* fallback to `Config` DB table; feature-flag `BULK_EMAIL_ENABLED`. S2 adds `OnboardingTour` (localStorage flag) + `CurriculumGraph` from `materias`; S3 deferred per proposal. Strict TDD: 12 pytest + 49 vitest gates.

## Architecture Decisions

| Decision | Options | Tradeoff | Choice |
|---|---|---|---|
| Mail transport | Flask-Mail vs `smtplib` stdlib | Flask-Mail adds dependency, async support; smtplib zero-dep, matches existing `utils/email.py`, sync OK for <50 mails | **smtplib** — extend `utils/email.py` with `send_credentials_email()` + `render_credentials_email()` reusing `_get_smtp_config()` |
| Temp credential | random 8-char plaintext+bcrypt vs JWT `secrets.token_urlsafe(8)` | JWT needs verify endpoint; 8-char user-friendly but must hash; token allows stateless reset | **8-char alphanumeric via `secrets.token_urlsafe(6)` truncated + bcrypt** stored in `temp_password_hash`; satisfies spec "8-char alphanumeric", 24h expiry via `temp_password_expires_at`. Alt token reserved for S1 if `reset_password=false` not needed |
| Rate limiter storage | Redis vs `memory://` (current) | Redis durable, distributed; memory resets on restart, single-instance only | **Fallback pattern**: try `REDIS_URL` env, else `memory://` with warning log. `extensions.limiter` already memory — keep for S1, flag Redis for S3 slice |
| Curriculum graph lib | raw SVG/CSS grid vs D3 vs react-flow | D3 heavy, canvas overkill for 45 nodes; react-flow adds 80kb bundle | **No external lib S1/S2**: CSS grid 9 columns + SVG edges for 45 nodes; S2 can upgrade to `react-flow` if interaction needed — document as optional |
| Frontend bulk state | local component state vs Zustand | Zustand overkill for one page | **Local `useState`**: `selectedIds: Set<number>`, `results: Map<id,status>` in `Alumnos.jsx` |

## Data Flow

```
Alumnos.jsx (checkboxes → selectedIds)
  │ ConfirmDialog → POST /api/alumnos/send-credentials {ids, reset_password}
  ▼
alumnos.py: @admin_required + @limiter.limit("20/minute")
  │ loop ids: secrets.token_urlsafe → bcrypt hash → Alumno.temp_password_* → db.commit
  │ send_email(credentials.html) per alumno → collect results[ {id,status,error} ]
  ▼
ProgressModal (pending→sent/failed, retry ids:[failed] only)
  │ Alumno login: check_password → check temp_password_expires_at > now else 401 temp_password_expired
```

Onboarding: `Dashboard mount → localStorage.getItem("onboarding_seen")===null → OnboardingTour step1→2→3 → setItem("true")`.
Curriculum: `GET /api/materias|carreras/{id}/materias → CurriculumGraph grid(9) → color by calificaciones join`.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/utils/mail.py` | Create | `send_credentials_email(to,email,temp_pw)` + `render_credentials_email()` HTML template ES; wraps `smtplib` via `_get_smtp_config` from `Config` + `.env` MAIL_* |
| `backend/utils/email.py` | Modify | Add `MAIL_*` env override priority over DB Config; add `BULK_EMAIL_ENABLED` flag check |
| `backend/models.py` | Modify | `Alumno`: add `temp_password_hash String(256) nullable`, `temp_password_expires_at DateTime nullable`, `must_change_password Bool default False` |
| `backend/routes/alumnos.py` | Modify | `POST /send-credentials` — @admin_required, @limiter 20/min, validates ids[], generates+hashes, sends per-row, returns results |
| `backend/config.py` | Modify | Add `MAIL_HOST/PORT/USER/PASSWORD/TLS`, `BULK_EMAIL_ENABLED`, `CORS_ORIGINS` env parsing |
| `backend/app.py` | Modify | Parse `CORS_ORIGINS` env CSV; init mail config pass-through |
| `backend/extensions.py` | Modify | Redis URL fallback logic for limiter storage |
| `frontend/src/api/alumnos.js` | Modify | Add `sendCredentials(ids, reset_password)` POST helper |
| `frontend/src/pages/admin/Alumnos.jsx` | Modify | Checkboxes + select-all, bulk bar disabled when 0 (tooltip), ConfirmDialog, ProgressModal integration; 860L cap untouched this slice |
| `frontend/src/components/ui/ProgressModal.jsx` | Create | Per-row status list, retry failed only, aria-live |
| `frontend/src/components/ui/OnboardingTour.jsx` | Create | 3-step overlay (calificaciones/pagos/requisitos), Next/Skip, localStorage persist |
| `frontend/src/components/ui/CurriculumGraph.jsx` | Create | 9-column grid 45 nodes, color by estado, click→detail panel |
| `backend/templates/emails/credentials.html` | Create | HTML email template (inline styles) with temp password + login URL |

## Interfaces / Contracts

**API: POST /api/alumnos/send-credentials**
```python
# Request
{ "ids": [7,12,19], "reset_password": true }
# Headers: Authorization: Bearer <JWT admin>
# RateLimit: 20/minute per admin IP+user

# Success 200
{ "results": [
    {"id":7, "status":"sent", "email":"a@fv.mx"},
    {"id":12,"status":"failed","error":"SMTP timeout"},
    {"id":19,"status":"sent"}
  ]
}
# Errors
# 400 {error:"ids required"} | 403 ADMIN_REQUIRED | 429 {error:"rate_limit_exceeded"} + Retry-After | 500 per-row failed
```

**Model delta**
```python
class Alumno:
    temp_password_hash = db.Column(db.String(256), nullable=True)
    temp_password_expires_at = db.Column(db.DateTime, nullable=True)
    must_change_password = db.Column(db.Boolean, default=False)
    # login check: if must_change_password and utcnow() > expires_at → 401 temp_password_expired
```

**Mail contract**
```python
def send_credentials_email(to_email: str, temp_password: str, alumno_nombre: str) -> dict:
    # returns {"success": bool, "error": str} — never raises, never logs temp_password
def render_credentials_email(temp_password: str, login_url: str, app_name: str) -> str:
```

**Frontend state**
```js
// Alumnos.jsx
const [selectedIds, setSelectedIds] = useState(new Set());
const [results, setResults] = useState(null); // Map id→{status,error}
// OnboardingTour
localStorage.getItem("onboarding_seen") // null→show, "true"→hide
// CurriculumGraph props: { materias: [], calificaciones: [], onSelectMateria }
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (pytest) | hash not plaintext, 24h expiry, 401 expired, no log contains pw | Mock `smtplib.SMTP`, assert DB hash via `check_password_hash`, freeze time |
| Unit (vitest) | ProgressModal per-row retry, disabled button 0-selected, localStorage tour | jsdom + @testing-library/react, mock `api.post` |
| Integration | POST /send-credentials 200/403/429, per-row failed isolation, Content-Type | `httpx` / Flask test_client with JWT admin/alumno fixtures |
| E2E (Playwright) | admin selects 3→confirm→progress shows sent/failed→retry single | Seed 3 alumnos, mock SMTP success/failure via test double |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. Bulk endpoint is authenticated REST with rate limit; SMTP is stdlib `smtplib` without shell invocation.

## Migration / Rollout

Nullable columns — no destructive migration. `flask db migrate` adds 3 cols. Rollback: revert route+mail commit, `BULK_EMAIL_ENABLED=false` hides UI, columns stay nullable. Feature flag guards frontend bulk bar. SMTP latency risk: sync loop ≤50 rows, timeout 10s; queue enhancement deferred to S3 if needed. Importar.jsx 860L split deferred to S2 (`useImport` hook).

## Open Questions

- [ ] Confirm 8-char alphanumeric vs `token_urlsafe(8)` 11-char with symbols — spec says alphanumeric, propose `secrets.choice` alnum
- [ ] Email template language ES confirmed? Includes coordinator per carrera or single sender?
- [ ] Redis URL available in dev Docker? Fallback validated for single-instance limiter drift
