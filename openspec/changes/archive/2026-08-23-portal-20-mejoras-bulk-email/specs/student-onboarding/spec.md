# student-onboarding Specification

**ID**: student-onboarding | **Priority**: P1 (S2) | **Slice**: S2 UX+Perf

## Purpose

Guide alumnos on first login through a 3-step tour (calificaciones / pagos / requisitos) to reduce confusion and support load.

## Non-Goals

- Admin/profesor tours, product walkthrough beyond 3 steps, server-side persistence.

## Requirements

### Requirement: First-Login Tour Trigger

The system MUST display a 3-step tour only on the alumno's first authenticated login when `localStorage["onboarding_seen"]=null`. Steps: 1 calificaciones, 2 pagos, 3 requisitos — each with title, description, and target highlight. Navigation: Next / Skip.

- **EARS**: When alumno logs in first time and key absent, the system SHALL render step 1 overlay.

#### Scenario: First login shows tour

- GIVEN alumno `legajo=2024-001` with empty localStorage, credentials valid
- WHEN login succeeds and dashboard mounts
- THEN tour overlay MUST appear at step 1 "Tus calificaciones" with Next button

### Requirement: Dismiss Persistently

The system MUST persist dismissal on Skip or completing step 3 by setting `localStorage["onboarding_seen"]="true"` and MUST NOT show tour on subsequent logins on same browser.

- **EARS**: While `onboarding_seen=true`, the system SHALL suppress the tour on every later login.

#### Scenario: Skip closes and never returns

- GIVEN tour visible at step 1
- WHEN alumno clicks Skip
- THEN overlay closes AND `localStorage["onboarding_seen"]=="true"` AND reload/login again shows no tour

#### Scenario: Second login no tour

- GIVEN alumno already completed or skipped tour (`onboarding_seen=true`)
- WHEN alumno logs in again (same browser)
- THEN dashboard MUST render without tour overlay

### Requirement: Step Navigation

The system MUST allow Next through 1→2→3 and Finish on step 3, each transition updating visible content without page reload.

#### Scenario: Complete 3 steps

- GIVEN tour at step 1
- WHEN alumno clicks Next twice then Finish
- THEN step 2 "Pagos" then step 3 "Requisitos" shown sequentially, Finish closes and persists `onboarding_seen=true`
