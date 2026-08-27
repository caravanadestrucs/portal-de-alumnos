# curriculum-map Specification

**ID**: curriculum-map | **Priority**: P1 (S2) | **Slice**: S2 UX+Perf

## Purpose

Visualize the study plan (45 materias across 9 cuatrimestres) as an interactive graph in Carreras (admin) and MisCalificaciones (alumno), sourced from `materias`.

## Non-Goals

- Editing the plan, drag-and-drop, prerequisite enforcement, export.

## Requirements

### Requirement: Curriculum Graph Rendering

The system MUST render a graph of 45 nodes grouped by 9 cuatrimestres from `GET /api/materias` (or `GET /api/carreras/{id}/materias`). Each node shows `nombre` and `cuatrimestre`; edges represent curricular order. Available in `Carreras.jsx` (admin, all materias) and `MisCalificaciones.jsx` (alumno).

- **EARS**: Where carrera has materias, the system SHALL display full graph without manual config.

#### Scenario: Admin sees full graph 45 nodes

- GIVEN carrera `id=1` has 45 materias (9×5) and admin authenticated
- WHEN admin opens Carreras detail
- THEN graph MUST render 45 nodes grouped in 9 columns AND each node labeled e.g. "Análisis I — C1"

### Requirement: Progress Coloring

The system MUST color each node per alumno state in MisCalificaciones: `aprobado=green`, `cursando/regular=yellow`, `pendiente/no cursada=gray` based on `calificaciones` + `materias`.

- **EARS**: While alumno views MisCalificaciones, the system SHALL color nodes by derived status.

#### Scenario: Alumno sees colored progress

- GIVEN alumno `id=7` with 10 aprobadas, 5 cursando, 30 pendientes
- WHEN alumno opens MisCalificaciones
- THEN graph MUST show 10 green, 5 yellow, 30 gray nodes AND legend explains colors

### Requirement: Detail Navigation

The system MUST open a detail panel/modal on node click showing `materia.nombre`, `cuatrimestre`, `correlativas` (if any), and alumno's grade/estado when available.

#### Scenario: Click materia shows detail

- GIVEN graph rendered for alumno `id=7`
- WHEN alumno clicks node "Física I — C2"
- THEN detail panel MUST appear with `nombre=Física I`, `cuatrimestre=2`, `estado=aprobado`, `nota=8`
