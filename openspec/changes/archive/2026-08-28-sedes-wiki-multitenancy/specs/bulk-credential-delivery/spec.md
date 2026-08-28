# Delta for bulk-credential-delivery

## MODIFIED Requirements

### Requirement: Bulk Credential Dispatch
MUST provide `POST /api/alumnos/send-credentials {ids,reset_password}` scoped by `sede_id`. Generates 8-char temp password bcrypt, expires 24h, email via credentials.html. `sede_admin` MUST only target own sede else 403; `general_admin` MAY target any.

(Previously: No sede check; any admin could send to any alumno.)

- **EARS**: When admin confirms bulk send, SHALL create per-alumno credentials subject to sede scope.

#### Scenario: Admin sends to 3 in own sede
- GIVEN admin 3 alumnos ids [7,12,19] same sede
- WHEN POST {ids:[7,12,19],reset_password:true}
- THEN 200 results sent*3 and 3 emails

#### Scenario: Zero selection disabled
- GIVEN 0 checked WHEN view bar
- THEN button disabled

#### Scenario: Cross-sede rejected
- GIVEN sede_admin TEO ids [7 TEO,12 HUA]
- WHEN POST {ids:[7,12]}
- THEN 403 for HUA id

#### Scenario: general_admin allowed
- GIVEN general_admin ids [7,12]
- WHEN POST
- THEN 200 both sent
