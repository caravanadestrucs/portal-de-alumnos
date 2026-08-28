# Sede Multitenancy Specification

## Purpose
Row-level isolation TEO/HUA via `sede_id`; RBAC general/sede_admin; 12 blueprints; backfill 109.

## Requirements

### Requirement: Sede Model and Seed
MUST provide `Sede(id,nombre,codigo,direccion,activa)` UNIQUE {TEO,HUA}, idempotent seed.

#### Scenario: Seed
- GIVEN empty sedes
- WHEN seed runs
- THEN TEO and HUA exist

### Requirement: Admin RBAC and JWT
MUST add `Admin.role` {general_admin,sede_admin} + nullable `sede_id` CHECK, JWT embeds `role,sede_id`, decorators enforce.

#### Scenario: Constraint
- GIVEN sede_admin without sede_id
- WHEN insert
- THEN CHECK fails

#### Scenario: JWT scope
- GIVEN sede_admin TEO login
- WHEN POST /api/auth/login
- THEN token has role and sede_id

### Requirement: Tenant Columns
MUST add `sede_id`: `Alumno` NOT NULL, `Grupo` NOT NULL, `Profesor` NULL, `Admin` per-role; `Carrera` shared. Migration nullable->backfill->NOT NULL.

#### Scenario: Alumno requires sede
- GIVEN sede_admin POST alumno no sede_id
- WHEN request
- THEN 400

### Requirement: Row-Level Scoping
MUST scope via `scope_by_sede()`; sede_admin own sede only else 403; general sees all or `?sede_id`. Covers 12 blueprints: alumnos, carreras, materias, grupos, boletas, calificaciones, pagos, export, imports, profesores, asignaciones, admins.

#### Scenario: Isolation
- GIVEN A TEO B HUA sede_admin TEO GET /api/alumnos
- WHEN list
- THEN only A

#### Scenario: Cross-sede 403
- GIVEN sede_admin TEO GET HUA alumno 99
- WHEN request
- THEN 403

### Requirement: Backfill and Transfer
MUST provide `seed_sedes.py --dry-run` report-only and apply idempotent; heuristic folder>numero_control TEO|HUA>fallback flagged; ambiguous->manual_review.csv; PATCH /api/alumnos/:id/sede general-only. Success 109 zero NULL 56 genericos fixed.

#### Scenario: Dry-run
- GIVEN 109 NULL
- WHEN dry-run
- THEN report counts zero writes

#### Scenario: Transfer
- GIVEN alumno 7 TEO general PATCH sede 2
- WHEN transfer
- THEN alumno HUA visible to HUA admin
