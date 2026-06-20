# Tasks: Importación Masiva de Datos

## Phase 1: Backend — Core (Foundation)

- **TASK-IMP-1.1** — Crear `backend/routes/imports.py` con blueprint `imports_bp`, `_read_file()` (CSV + XLSX), `_sanitize_value()`, upload handling (temp dir, validación extensión/tamaño, cleanup).  
  Files: `backend/routes/imports.py`  
  AC: Blueprint registrable, `_read_file` retorna headers/rows normalizados, `_sanitize_value` rechaza `= + - @`.  
  Deps: Ninguna.

- **TASK-IMP-1.2** — Implementar `_parse_alumnos()`: header mapping (alias table), validar columnas requeridas, resolver `carrera` (codigo → nombre), validar unicidad de `numero_control`/`email` (preview=informativo, execute=bloqueante), generar password default.  
  Files: `backend/routes/imports.py`  
  AC: Retorna `{rows, errors}`; carrera lookup por codigo exacto luego nombre ilike; password `alumno{numero_control}` si no se provee.  
  Deps: TASK-IMP-1.1

- **TASK-IMP-1.3** — Implementar `_parse_calificaciones()`: header mapping, validar columnas requeridas, resolver `alumno_id` (por `numero_control`), resolver `materia_id` (codigo → nombre), validar rangos (0-10, 1900-2099), lógica de upsert para execute.  
  Files: `backend/routes/imports.py`  
  AC: Retorna `{rows, errors}` con IDs resueltos; upsert por unique constraint `(alumno_id, materia_id, periodo, anio)`.  
  Deps: TASK-IMP-1.1

- **TASK-IMP-1.4** — Implementar `_parse_pagos()`: header mapping, validar columnas requeridas, resolver `alumno_id`, validar `monto > 0`, fechas opcionales con default hoy, `created_by_id` desde JWT.  
  Files: `backend/routes/imports.py`  
  AC: Retorna `{rows, errors}`; `fecha_emision` default date.today(); `pagada` default false.  
  Deps: TASK-IMP-1.1

## Phase 2: Backend — Endpoints

- **TASK-IMP-2.1** — Implementar `POST /api/imports/preview`: recibe `multipart/form-data` (file + tipo), lee solo headers + 10 filas, delega al parser correspondiente, retorna `{columns, rows_preview, total_rows, importable, warnings}`.  
  Files: `backend/routes/imports.py`  
  AC: Retorna preview con validación por fila; no escribe DB; cleanup temp file siempre.  
  Deps: TASK-IMP-1.2, TASK-IMP-1.3, TASK-IMP-1.4

- **TASK-IMP-2.2** — Implementar `POST /api/imports/execute`: parsea TODAS las filas, valida, si hay errores → retorna reporte sin escribir DB (rollback implícito). Si todo OK → transacción con batches de 500, INSERT/UPDATE por tipo, commit. Retorna `{status, imported, created, updated, errors, generated_passwords, details}`.  
  Files: `backend/routes/imports.py`  
  AC: Transaccional (todo o nada); upsert en calificaciones; passwords generadas en response.  
  Deps: TASK-IMP-2.1

- **TASK-IMP-2.3** — Registrar `imports_bp` en `app.py` con prefijo `/api/imports` y configurar `MAX_CONTENT_LENGTH = 10 * 1024 * 1024`.  
  Files: `backend/app.py`  
  AC: Blueprint registrado; archivos >10MB rechazados con 413.  
  Deps: TASK-IMP-2.2

## Phase 3: Frontend — API & Page

- **TASK-IMP-3.1** — Crear `frontend/src/api/imports.js` con funciones `previewImport(file, tipo)` y `executeImport(file, tipo)` usando `FormData` + axios. Timeouts: preview 30s, execute 120s.  
  Files: `frontend/src/api/imports.js`  
  AC: Preview retorna preview data; execute retorna resultado con passwords; errores HTTP propagados.  
  Deps: TASK-IMP-2.3

- **TASK-IMP-3.2** — Crear `frontend/src/pages/admin/Importar.jsx` con wizard de 4 pasos: (1) selector tipo con cards, (2) drag & drop zone con validación client-side (extensión, tamaño <10MB), (3) tabla preview con estado por fila (✅/❌) y tooltip de errores, (4) resultados con resumen, tabla de errores, descarga CSV de passwords, botón "Importar otro".  
  Files: `frontend/src/pages/admin/Importar.jsx`  
  AC: Flujo completo 4 pasos funcional; validación client-side bloquea preview si archivo inválido; botón Importar deshabilitado si errores estructurales; descarga de reporte passwords client-side.  
  Deps: TASK-IMP-3.1

## Phase 4: Frontend — Wiring

- **TASK-IMP-4.1** — Agregar ruta `<Route path="importar" element={<AdminImportar />} />` en App.jsx.  
  Files: `frontend/src/App.jsx`  
  AC: Navegación a `/admin/importar` renderiza Importar.jsx.  
  Deps: TASK-IMP-3.2

- **TASK-IMP-4.2** — Agregar item `{ path: '/admin/importar', icon: Upload, label: 'Importar' }` en `adminNavItems` del Sidebar.jsx (entre Asignaciones y Exportar). Importar `Upload` de `lucide-react`.  
  Files: `frontend/src/components/layout/Sidebar.jsx`  
  AC: Sidebar muestra "Importar" con icono Upload; navegación funcional.  
  Deps: TASK-IMP-4.1
