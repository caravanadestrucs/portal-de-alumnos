# Exploration: Importación Masiva de Datos

## Current State

El sistema actual maneja datos de **Alumnos**, **Calificaciones**, y **Pagos (Notas de Remisión)** mediante CRUD individual (formularios uno por uno). No existe funcionalidad de importación masiva.

### Stack técnico relevante:
- **Backend**: Flask + SQLAlchemy (SQLite dev / MySQL prod)
- **Frontend**: React + Vite + Tailwind + axios
- **Archivos existentes**: openpyxl ya incluido en `requirements.txt`
- **Auth**: JWT con decorador `@admin_required`

### Patrones existentes:
- Los blueprints se registran en `app.py` con `url_prefix`
- El endpoint `POST /api/calificaciones/bulk` muestra un patrón de procesamiento por lote con reporte de errores por fila
- El endpoint `GET /api/export/excel` muestra cómo usar openpyxl para generar archivos

---

## Affected Areas

### Backend (nuevos/modificados):
- `backend/routes/imports.py` — **NUEVO**: Blueprint con endpoints de importación
- `backend/app.py` — Registrar el nuevo blueprint `imports_bp`
- `backend/requirements.txt` — Sin cambios (openpyxl ya incluido)

### Frontend (nuevos/modificados):
- `frontend/src/pages/admin/Importar.jsx` — **NUEVA**: Página de importación
- `frontend/src/api/imports.js` — **NUEVO**: Llamadas API para importación
- `frontend/src/App.jsx` — Agregar ruta `/admin/importar`
- `frontend/src/components/layout/Sidebar.jsx` — Agregar item "Importar" al array `adminNavItems`

---

## Formats de Archivo por Tipo de Importación

### 1. Importar Alumnos
**Columnas esperadas (orden flexible, detección por header):**

| Columna | Tipo | Requerido | Validaciones |
|---------|------|-----------|-------------|
| `numero_control` | string | ✅ | Único en DB, máx 20 chars |
| `nombre` | string | ✅ | No vacío |
| `apellido_paterno` | string | ✅ | No vacío |
| `apellido_materno` | string | ❌ | Opcional |
| `email` | string | ✅ | Único en DB, formato email |
| `password` | string | ✅ | Mín 6 chars (o generar default) |
| `carrera` | string | ✅ | Debe coincidir con `codigo` o `nombre` de Carrera |

**Ejemplo CSV:**
```csv
numero_control,nombre,apellido_paterno,apellido_materno,email,password,carrera
FV2024001,Juan,Pérez,López,juan@email.com,pass123,ISC
FV2024002,María,García,,maria@email.com,pass456,ISC
```

### 2. Importar Calificaciones
**Columnas esperadas:**

| Columna | Tipo | Requerido | Validaciones |
|---------|------|-----------|-------------|
| `numero_control` | string | ✅ | Debe existir en DB |
| `materia` | string | ✅ | Debe coincidir con `codigo` de Materia |
| `calificacion_final` | number | ✅ | 0-10 |
| `periodo` | string | ✅ | Ej: "Enero-Abril 2026" |
| `anio` | integer | ✅ | |
| `asistencia_1` | integer (0/1) | ❌ | Default 0 |
| `asistencia_2` | integer (0/1) | ❌ | Default 0 |
| `asistencia_3` | integer (0/1) | ❌ | Default 0 |
| `asistencia_4` | integer (0/1) | ❌ | Default 0 |
| `asistencia_5` | integer (0/1) | ❌ | Default 0 |
| `practica_1` | number | ❌ | 0-10, Default 0 |
| `practica_2` | number | ❌ | 0-10, Default 0 |
| `extra_1` | number | ❌ | 0-10, Default 0 |
| `extra_2` | number | ❌ | 0-10, Default 0 |

**Ejemplo CSV:**
```csv
numero_control,materia,calificacion_final,periodo,anio,practica_1,practica_2
FV2024001,MAT101,8.5,Enero-Abril 2026,2026,9.0,8.5
FV2024001,MAT102,7.0,Enero-Abril 2026,2026,7.5,7.0
```

### 3. Importar Pagos (Notas de Remisión)
**Columnas esperadas:**

| Columna | Tipo | Requerido | Validaciones |
|---------|------|-----------|-------------|
| `numero_control` | string | ✅ | Debe existir en DB |
| `concepto` | string | ✅ | No vacío |
| `monto` | number | ✅ | > 0 |
| `fecha_emision` | date (YYYY-MM-DD) | ❌ | Default: hoy |
| `fecha_corte` | date (YYYY-MM-DD) | ❌ | Opcional |
| `pagada` | boolean (SI/NO, 1/0) | ❌ | Default: false |
| `fecha_pago` | date (YYYY-MM-DD) | ❌ | Solo si pagada=true |

**Ejemplo CSV:**
```csv
numero_control,concepto,monto,fecha_emision,fecha_corte
FV2024001,Inscripción 2026,4500.00,2026-01-15,2026-02-15
FV2024001,Cuota Enero,1200.00,2026-01-15,2026-01-31
```

---

## Backend Endpoints Necesarios

### `POST /api/imports/preview`
**Propósito**: Subir archivo, parsear headers, validar estructura, devolver vista previa

- **Request**: `multipart/form-data` con campos:
  - `file`: el archivo CSV/XLSX
  - `type`: `alumnos` | `calificaciones` | `pagos`

- **Response** (200):
```json
{
  "type": "alumnos",
  "total_rows": 150,
  "preview": [
    { "row": 2, "data": { "numero_control": "FV2024001", "nombre": "Juan", ... }, "errors": [] },
    { "row": 3, "data": { "numero_control": "FV2024002", ... }, "errors": ["Email inválido"] }
  ],
  "columns_detected": ["numero_control", "nombre", "apellido_paterno", ...],
  "columns_expected": ["numero_control", "nombre", "apellido_paterno", "email", "password", "carrera"],
  "errors_count": 0
}
```

- **Errores** (400): Archivo inválido, tipo desconocido, columnas faltantes

### `POST /api/imports/execute`
**Propósito**: Ejecutar la importación real con validación completa

- **Request**: `multipart/form-data` con campos:
  - `file`: el archivo CSV/XLSX
  - `type`: `alumnos` | `calificaciones` | `pagos`

- **Response** (200):
```json
{
  "success": true,
  "type": "alumnos",
  "total_rows": 150,
  "imported": 148,
  "errors": 2,
  "error_details": [
    { "row": 5, "field": "numero_control", "message": "El número de control FV2024001 ya existe" },
    { "row": 12, "field": "carrera", "message": "La carrera 'XYZ' no existe" }
  ]
}
```

- **Si hay errores**: Rollback completo de la transacción (nada se guarda si algo falla). Se devuelven todos los errores encontrados.
- **Response** (207 Multi-Status) en caso de errores parciales (según decisión de diseño).

---

## Frontend Pages/Componentes Necesarios

### Página: `Importar.jsx` (`/admin/importar`)

**Estructura visual (flujo de 4 pasos):**

1. **Selector de tipo** — Cards con iconos para elegir tipo de importación (Alumnos / Calificaciones / Pagos) + descripción del formato esperado
2. **Upload** — Drag & drop + selector de archivo. Validación de extensión (.csv, .xlsx)
3. **Preview** — Tabla con vista previa de datos (primeras 10-20 filas). Muestra validaciones inline (filas con errores resaltadas en rojo). Botón "Importar" + "Cancelar"
4. **Resultado** — Reporte con: total filas, importados, errores. Tabla de errores detallada. Botón "Nueva Importación"

**Componentes reutilizables existentes:**
- `Card` — Para tarjetas de selección de tipo
- `Button` — Con estado loading para el botón de importar
- `Modal` — Para confirmación antes de importar
- `Table` — Para el preview y reporte de errores

**Componentes nuevos necesarios:**
- `FileUpload` — Componente de drag & drop + file input (se puede hacer inline en la página)
- `ImportResultCard` — Resumen del resultado de importación

### API: `imports.js`
```js
export const previewImport = async (file, type) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);
  const response = await api.post('/imports/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const executeImport = async (file, type) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);
  const response = await api.post('/imports/execute', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};
```

---

## Enfoques de Implementación

| Aspecto | Opción Recomendada | Alternativa |
|---------|-------------------|-------------|
| **Parser** | `openpyxl` (XLSX) + `csv` módulo estándar (CSV) | Pandas (más pesado, no necesario) |
| **Lógica de parsing** | Clase `ImportParser` que detecta tipo y formato | Funciones sueltas |
| **Validación** | Dos fases: (1) preview valida headers + primeras filas, (2) execute valida TODO antes de insertar | Una sola fase |
| **Transaccionalidad** | Rollback completo si hay errores (consistencia) | Insertar filas buenas, reportar errores (menos consistente) |
| **Mapping de columnas** | Automático por nombre de header | Manual (el usuario mapea columnas) |
| **Contraseña de alumnos** | Generar contraseña por defecto basada en numero_control o fecha | Pedirla en el archivo |

---

## Validaciones Detalladas por Tipo

### Alumnos
1. `numero_control`: Requerido, único en DB, máximo 20 caracteres
2. `email`: Requerido, único en DB, formato email válido
3. `nombre`, `apellido_paterno`: Requeridos, no vacíos
4. `carrera`: Debe existir en tabla `carreras` — buscar por `codigo` primero, luego por `nombre`
5. `password`: Si no se incluye, generar automática (ej: `alumno{numero_control}` o la fecha de registro)
6. Si el alumno ya existe por `numero_control` → **error**, no se permite actualizar por importación (solo inserción)

### Calificaciones
1. `numero_control`: Debe existir en DB
2. `materia`: Debe existir en DB (buscar por `codigo` de materia)
3. `calificacion_final`: 0-10
4. `practica_1`, `practica_2`, `extra_1`, `extra_2`: 0-10
5. `asistencia_1` a `asistencia_5`: 0 o 1
6. Unique constraint `(alumno_id, materia_id, periodo, anio)`: Si existe el registro, se actualiza (upsert). Si no existe, se crea.
7. `periodo` y `anio`: Requeridos

### Pagos
1. `numero_control`: Debe existir en DB
2. `concepto`: Requerido, no vacío
3. `monto`: Requerido, > 0
4. `fecha_emision`: Formato YYYY-MM-DD válido, default hoy
5. `fecha_corte`: Formato YYYY-MM-DD válido, opcional
6. No hay unique constraint fuerte — se insertan nuevas notas siempre

---

## Estrategia de Manejo de Errores

### Flujo de validación (backend):

```
1. Parsear archivo → lista de filas (dicts)
2. Validar headers vs esperados para el tipo
3. Por cada fila:
   a. Validar formato de campos (tipos, rangos)
   b. Validar existencia de referencias (FKs)
   c. Validar unicidad (si aplica)
   d. Acumular errores por fila
4. Si errors.length > 0 → Rollback + reporte 207
5. Si todo OK → Insertar todo + Commit + reporte 200
```

### Estructura de error por fila:
```python
{
    "row": 5,                    # Número de fila en el archivo (1-indexed, considerando header)
    "field": "email",            # Campo con error
    "value": "email-invalido",   # Valor que causó el error
    "message": "Formato de email inválido"  # Descripción
}
```

### Consideraciones adicionales:
- Para archivos muy grandes (+1000 filas), considerar procesamiento en lotes (chunks de 500) con un solo commit por lote
- Límite de tamaño de archivo: 10 MB (configurable vía `MAX_CONTENT_LENGTH`)
- Logging de cada importación: quién importó, cuándo, cuántas filas

---

## Risk Assessment

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Archivo malicioso (CSV injection) | Alto | Sanitizar valores, no ejecutar fórmulas |
| Timeout con archivos grandes | Medio | Límite de tamaño, procesamiento por lotes |
| Datos duplicados | Medio | Validación estricta de unicidad previa |
| Carrera/materia no encontrada | Medio | Búsqueda flexible (código > nombre) |
| Codificación incorrecta (UTF-8 BOM) | Bajo | Detectar y manejar BOM en CSV |

---

## Ready for Proposal

**Sí.** Esta exploración cubre todos los aspectos necesarios para proceder con la fase de propuesta. El alcance está claro, los formatos definidos, y las validaciones identificadas.

Resumen para el orquestador:
- **3 tipos de importación**: Alumnos, Calificaciones, Pagos
- **2 endpoints**: preview + execute
- **1 nueva página** + sidebar item
- **100% transactional**: si algo falla, rollback total
- **Librerías**: openpyxl (ya instalada) + csv (built-in). **No** necesitamos pandas
- **Preview**: primeras 10-20 filas con validación por fila
