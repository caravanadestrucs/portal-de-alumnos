# bulk-credential-delivery Specification

**ID**: bulk-credential-delivery | **Priority**: P0 (S1) | **Slice**: S1 Bulk+Security

## Purpose

Enable admins to send login credentials in bulk to selected alumnos via email with secure temporary passwords, observable progress, and retry.

## Non-Goals

- MySQL/SendGrid/mobile, RBAC beyond carrera, password recovery flow (separate).

## Requirements

### Requirement: Bulk Credential Dispatch

The system MUST provide `POST /api/alumnos/send-credentials` accepting `{ids: number[], reset_password: boolean}`. When admin selects N alumnos and confirms, the system MUST generate a temporary 8-char password per alumno, hash it (bcrypt), store it, and send one email per alumno via `credentials.html`.

- **EARS**: When admin confirms bulk send with selected IDs, the system SHALL create per-alumno temp credentials and enqueue emails.

#### Scenario: Admin sends to 3 selected alumnos

- GIVEN admin authenticated, 3 alumnos selected `ids=[7,12,19]` with valid emails
- WHEN POST /api/alumnos/send-credentials `{ids:[7,12,19], reset_password:true}`
- THEN response 200 with `results:[{id:7,status:"sent"},{id:12,status:"sent"},{id:19,status:"sent"}]` AND 3 emails delivered via template

#### Scenario: Zero selection disabled

- GIVEN Alumnos page with 0 checkboxes checked
- WHEN admin views bulk action bar
- THEN Send Credentials button MUST be disabled AND tooltip "Select at least one student"

### Requirement: Temporary Credential Security

The system MUST generate 8-char temp passwords (alphanumeric), store only bcrypt hash, set `temp_password_expires_at = now+24h`, set `must_change_password=true`, and MUST NOT log plaintext anywhere.

- **EARS**: While credential is temporary, the system SHALL enforce expiry after 24h.

#### Scenario: Temp password expires after 24h

- GIVEN alumno `id=7` received temp password at `2026-08-23T10:00:00Z` (expires 2026-08-24T10:00:00Z)
- WHEN alumno logs in at `2026-08-24T10:00:01Z` with that password
- THEN login MUST fail with `401 temp_password_expired` AND force reset flow

#### Scenario: Plaintext never logged

- GIVEN bulk send for `id=7` succeeds
- WHEN inspecting backend logs and DB column `temp_password_hash`
- THEN no log line contains 8-char plaintext AND DB stores only bcrypt hash

### Requirement: Delivery Observability, Retry, and Guardrails

The system MUST show ProgressModal with per-row status (pending/sent/failed), allow retry of failed rows only, enforce rate limit 20 req/min per admin (429 thereafter), and reject non-admin callers with 403.

- **EARS**: Where SMTP fails for a row, the system SHALL mark `failed` and allow per-row retry without resending successes.

#### Scenario: SMTP failure per alumno with retry

- GIVEN bulk send 3 alumnos where SMTP fails for `id=12` (timeout)
- WHEN request completes
- THEN `results=[sent,failed,sent]` AND modal shows retry button only for `id=12`; WHEN retry clicked THEN second POST with `ids:[12]` succeeds

#### Scenario: Non-admin forbidden

- GIVEN JWT role `alumno` authenticated
- WHEN POST /api/alumnos/send-credentials `{ids:[7]}`
- THEN response 403 AND zero emails sent AND zero password changes

#### Scenario: Rate limit 20/min

- GIVEN admin sent 20 bulk requests in last 60s
- WHEN 21st POST within same window
- THEN response 429 `rate_limit_exceeded` with `Retry-After` header
