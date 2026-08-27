# Importación Masiva de Datos — Specification

## Purpose

Agregar funcionalidad de importación masiva vía CSV/XLSX para las entidades Alumnos, Calificaciones y Pagos. El flujo consta de 4 pasos: seleccionar tipo → subir archivo → previsualizar con validación → confirmar.

---

## REQ-IMP-001 — Import UI (Frontend)

**Priority**: MUST

El sistema MUST proveer una interfaz en `/admin/importar` con un flujo de 4 pasos:
1. Selector de tipo de importación (Alumnos / Calificaciones / Pagos)
2. Upload de archivo CSV o XLSX (drag & drop o file picker)
3. Preview: tabla con primeras 10 filas, columnas detectadas y estado de validación por fila
4. Confirmación y reporte de resultado: total filas, importados, errores

### Scenario: Happy path — importación completa exitosa
- GIVEN un admin autenticado en `/admin/importar`
- WHEN selecciona tipo, sube archivo válido, previsualiza y confirma
- THEN el sistema MUST mostrar reporte con `imported = total_rows` y `errors = 0`

### Scenario: Error — archivo inválido
- GIVEN un admin en paso de upload
- WHEN intenta subir un archivo de más de 10MB o formato no soportado
- THEN el sistema MUST mostrar error y bloquear el preview

### Scenario: Error — preview con filas inválidas
- GIVEN un admin en paso de preview
- WHEN el archivo contiene filas con errores de validación
- THEN el sistema MUST mostrar las filas inválidas resaltadas con los errores por campo

---

## REQ-IMP-002 — Alumnos Import

**Priority**: MUST

El sistema MUST permitir importar alumnos con estas reglas:

| Columna | Requerido | Validación |
|---------|-----------|------------|
| `numero_control` | MUST | Único en DB, máx 20 chars |
| `nombre` | MUST | No vacío |
| `apellido_paterno` | MUST | No vacío |
| `apellido_materno` | MAY | — |
| `email` | MUST | Único en DB, formato email |
| `password` | SHOULD | Mín 6 chars; si no se provee → generar `alumno{numero_control}` |
| `carrera` | MUST | Resolver por `codigo` primero, luego por `nombre` |

Auto-set: `activo=true`, `fecha_registro=date.today()`. Error si `numero_control` o `email` ya existen.

### Scenario: Happy path — todos los campos provistos
- GIVEN un CSV con 5 alumnos, todos con datos completos y carrera existente
- WHEN se ejecuta la importación
- THEN los 5 alumnos MUST crearse con `activo=true` y `fecha_registro` hoy

### Scenario: Error — número de control duplicado
- GIVEN un CSV donde una fila tiene `numero_control` ya registrado en DB
- WHEN se ejecuta la importación
- THEN el sistema MUST hacer rollback total y reportar error: "El número de control X ya existe"

### Scenario: Default password — sin columna password
- GIVEN un CSV sin columna `password`
- WHEN se ejecuta la importación
- THEN cada alumno MUST tener contraseña `alumno{NUMERO_CONTROL}`

### Scenario: Carrera resuelta por nombre
- GIVEN una fila donde `carrera` contiene el nombre completo "Ingeniería en Sistemas"
- WHEN se ejecuta la importación
- THEN el sistema MUST resolver la carrera por nombre y asignar el `carrera_id` correcto

---

## REQ-IMP-003 — Calificaciones Import

**Priority**: MUST

El sistema MUST permitir importar calificaciones con upsert sobre la unique constraint `(alumno_id, materia_id, periodo, anio)`:

| Columna | Requerido | Validación |
|---------|-----------|------------|
| `numero_control` | MUST | Debe existir en DB |
| `materia` | MUST | Resolver por `codigo` primero, luego por `nombre` |
| `calificacion_final` | MUST | 0-10 |
| `periodo`, `anio` | MUST | No vacíos |
| `practica_1`, `practica_2` | MAY | 0-10, default 0 |
| `extra_1`, `extra_2` | MAY | 0-10, default 0 |
| `asistencia_1..5` | MAY | 0 o 1, default 0 |

### Scenario: Happy path — nuevas calificaciones
- GIVEN un CSV con 3 calificaciones para alumnos y materias existentes
- WHEN se ejecuta la importación
- THEN las 3 calificaciones MUST crearse en DB

### Scenario: Upsert — calificación existente
- GIVEN un CSV con una calificación para un combo (alumno, materia, periodo, anio) que ya existe
- WHEN se ejecuta la importación
- THEN la calificación existente MUST actualizarse (no duplicarse)

### Scenario: Error — calificación fuera de rango
- GIVEN una fila con `calificacion_final = 15`
- WHEN se ejecuta importación
- THEN el sistema MUST reportar error "calificacion_final debe estar entre 0 y 10" y hacer rollback

### Scenario: Error — alumno no existe
- GIVEN una fila con `numero_control` que no existe en DB
- WHEN se ejecuta importación
- THEN MUST reportar error "El alumno X no existe" y hacer rollback

---

## REQ-IMP-004 — Pagos Import

**Priority**: MUST

El sistema MUST permitir importar pagos (notas de remisión):

| Columna | Requerido | Validación |
|---------|-----------|------------|
| `numero_control` | MUST | Debe existir en DB |
| `concepto` | MUST | No vacío |
| `monto` | MUST | > 0 |
| `fecha_emision` | SHOULD | Formato YYYY-MM-DD; default: hoy |
| `pagada` | SHOULD | true/false; default: false |
| `fecha_pago` | MAY | Solo si `pagada=true` |

### Scenario: Happy path — crear notas de remisión
- GIVEN un CSV con 5 pagos para alumnos existentes
- WHEN se ejecuta la importación
- THEN las 5 notas MUST crearse con `created_by_id` del admin que importa

### Scenario: Default fecha_emision
- GIVEN un CSV sin columna `fecha_emision`
- WHEN se ejecuta importación
- THEN cada nota MUST tener `fecha_emision = date.today()`

### Scenario: Error — monto negativo
- GIVEN una fila con `monto = -100`
- WHEN se ejecuta importación
- THEN MUST reportar error "monto debe ser mayor a 0" y hacer rollback

---

## REQ-IMP-005 — Validation & Error Handling

**Priority**: MUST

| Regla | Especificación |
|-------|---------------|
| Transaccionalidad | MUST: todo o nada — si una fila falla, rollback completo |
| Límite tamaño | MUST: 10MB máximo |
| Formatos | MUST: `.csv` y `.xlsx` |
| CSV injection | MUST: sanitizar valores que empiezan con `=`, `+`, `-`, `@` |
| Reporte errores | MUST: por fila → `{row, field, value, message}` |

### Scenario: Transaccionalidad — rollback en error
- GIVEN un archivo donde la fila 1 es válida y la fila 2 tiene error
- WHEN se ejecuta importación
- THEN MUST hacer rollback completo (nada se guarda) y devolver todos los errores detectados

### Scenario: CSV injection sanitizado
- GIVEN un CSV donde `nombre` contiene `=HYPERLINK(...)`
- WHEN se parsea el archivo
- THEN el sistema MUST escapar/reemplazar el valor para evitar ejecución de fórmulas

### Scenario: Archivo excede límite
- GIVEN un archivo de 15MB
- WHEN el admin intenta subirlo
- THEN el sistema MUST rechazar con error "Archivo excede el límite de 10MB"
