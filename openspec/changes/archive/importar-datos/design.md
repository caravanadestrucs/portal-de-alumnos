# Design: Importación Masiva de Datos

## 1. Architecture

### 1.1 Visión General

Se agrega un nuevo blueprint `imports_bp` montado en `/api/imports` que expone dos endpoints:
- **Preview** (`POST /api/imports/preview`) — analiza el archivo, valida headers y primeras filas, devuelve vista previa.
- **Execute** (`POST /api/imports/execute`) — procesa **todas** las filas dentro de una transacción; si hay **cualquier** error, rollback total.

Ambos endpoints reciben `multipart/form-data` con los campos `file` (archivo) y `tipo` (string: `alumnos|calificaciones|pagos`).

### 1.2 Flujo de 2 Fases

```
                  ┌──────────────┐
                  │  Upload File  │
                  │  + Select Type │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   PREVIEW    │  ← Lee headers + primeras 10 filas
                  │  (sin DB)    │  ← Valida estructura y datos
                  └──────┬───────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       ┌──────────────┐    ┌──────────────┐
       │  All OK       │    │  Has errors  │
       │  → Show table │    │  → Show      │
       │  → "Import"   │    │    errors    │
       └──────┬───────┘    └──────────────┘
              │
              ▼
       ┌──────────────┐
       │   EXECUTE    │  ← Transacción DB
       │  (full file) │  ← Batch de 500 filas
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │  Resultados  │
       │  ✓ imported  │
       │  ✗ errors    │
       │  🔑 passwords│
       └──────────────┘
```

### 1.3 Estructura de Archivos

```
backend/
├── routes/
│   └── imports.py          # NUEVO — blueprint + parsers
├── app.py                  # MODIFICAR — registrar imports_bp
└── utils/
    └── validators.py       # NUEVO (opcional) — helpers compartidos

frontend/
├── src/
│   ├── api/
│   │   └── imports.js      # NUEVO — funciones previewImport / executeImport
│   ├── pages/
│   │   └── admin/
│   │       └── Importar.jsx # NUEVO — wizard de 4 pasos
│   ├── components/
│   │   └── layout/
│   │       └── Sidebar.jsx # MODIFICAR — item "Importar"
│   └── App.jsx             # MODIFICAR — ruta /admin/importar
```

---

## 2. Backend Endpoints

### 2.1 Preview
```
POST /api/imports/preview
Content-Type: multipart/form-data

Body:
  file: <archivo .csv o .xlsx>
  tipo: "alumnos" | "calificaciones" | "pagos"
```

**Proceso**:
1. Validar que `tipo` sea uno de los valores permitidos.
2. Validar extensión del archivo (`.csv` o `.xlsx`).
3. Validar tamaño máximo (10 MB) — se controla via `request.content_length`.
4. Guardar archivo a directorio temporal con `secure_filename`.
5. Detectar tipo de archivo real por extensión.
6. Leer **solamente headers + primeras 10 filas** (para preview rápido).
7. Validar columnas requeridas según el tipo.
8. Validar cada fila contra reglas de negocio (tipos, FK lookups, unicidad).
9. Limpiar archivo temporal.
10. Retornar respuesta.

**Response** `(200)`:
```json
{
  "columns": ["numero_control", "nombre", "apellido_paterno", "email", "carrera"],
  "rows_preview": [
    { "row": 1, "data": { "numero_control": "FV2024001", "nombre": "Juan", ... }, "valid": true, "errors": [] },
    { "row": 2, "data": { ... }, "valid": false, "errors": [{ "field": "email", "message": "Email inválido" }] }
  ],
  "total_rows": 150,
  "importable": true,
  "warnings": []
}
```

- `importable`: `true` si no hay errores estructurales (columnas faltantes). Errores por fila no bloquean el preview.
- `warnings`: ej. "La carrera 'XYZ' no existe. Se ignorarán esas filas."
- Los FK lookups en preview son informativos (no bloquean).

**Response** `(400)` si el archivo no pasa validación estructural:
```json
{
  "error": "Formato de archivo no soportado",
  "code": "INVALID_FILE_TYPE"
}
```

### 2.2 Execute
```
POST /api/imports/execute
Content-Type: multipart/form-data

Body:
  file: <archivo .csv o .xlsx>
  tipo: "alumnos" | "calificaciones" | "pagos"
```

**Proceso**:
1. Mismas validaciones de entrada que Preview.
2. Parsear **todas** las filas del archivo completo.
3. Validar cada fila contra reglas de negocio.
4. Acumular errores por fila.
5. **Si hay algún error** → retornar reporte de errores **sin modificar la DB** (rollback implícito).
6. **Si no hay errores** → ejecutar INSERT/UPDATE en batches de 500 filas dentro de una transacción.
7. Para **alumnos**: generar contraseña default (`alumno{NUMERO_CONTROL}`) si no se especificó.
8. Para **calificaciones**: upsert basado en unique constraint `(alumno_id, materia_id, periodo, anio)`.
9. Commit transacción.
10. Retornar reporte de éxito.

**Response** `(200)` — éxito (0 errores):
```json
{
  "status": "success",
  "imported": 150,
  "created": 140,
  "updated": 10,
  "errors": [],
  "generated_passwords": [
    { "numero_control": "FV2024001", "password": "alumnoFV2024001" }
  ],
  "details": {
    "alumnos_importados": 150,
    "calificaciones_creadas": 0,
    "calificaciones_actualizadas": 0,
    "pagos_creados": 0
  }
}
```

**Response** `(200)` — con errores (commit no ejecutado):
```json
{
  "status": "error",
  "imported": 0,
  "errors": [
    { "row": 5, "field": "email", "value": "email-invalido", "message": "Formato de email inválido" },
    { "row": 12, "field": "carrera", "value": "INEXISTENTE", "message": "La carrera con código 'INEXISTENTE' no existe" },
    { "row": 15, "field": "numero_control", "value": "FV2024001", "message": "El número de control ya existe" }
  ],
  "total_rows": 150,
  "error_count": 3
}
```

**Response** `(413)` — archivo demasiado grande (manejado por Flask/nginx):
```json
{
  "error": "El archivo excede el límite de 10MB",
  "code": "FILE_TOO_LARGE"
}
```

---

## 3. Parser Design

Los parsers viven en el mismo archivo `routes/imports.py` como funciones privadas (`_parse_alumnos`, `_parse_calificaciones`, `_parse_pagos`). Si crecen demasiado, se extraen a `backend/utils/parsers.py`.

### 3.1 Interfaz Común

```python
def _parse_file(file_path: str, tipo: str) -> dict:
    """
    Detecta extensión, delega al parser específico.
    
    Returns:
        rows: list[dict] — datos parseados y validados
        errors: list[dict] — errores por fila
    """
```

### 3.2 File Type Detection

```python
def _read_file(file_path: str) -> tuple[list[str], list[list]]:
    """
    Lee archivo CSV o XLSX.
    Returns: (headers, rows) donde headers es lista de strings normalizados.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        with open(file_path, 'r', encoding='utf-8-sig') as f:  # BOM-aware
            reader = csv.reader(f)
            headers = [h.strip().lower().replace(' ', '_') for h in next(reader)]
            rows = list(reader)
    elif ext == '.xlsx':
        wb = load_workbook(file_path, read_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h).strip().lower().replace(' ', '_') if h else '' for h in next(rows_iter)]
        rows = [list(row) for row in rows_iter]
    else:
        raise ValueError(f"Formato no soportado: {ext}")
    
    return headers, rows
```

### 3.3 Columnas Requeridas por Tipo

| Tipo | Columnas Requeridas | Columnas Opcionales |
|------|--------------------|-------------------|
| `alumnos` | `numero_control`, `nombre`, `apellido_paterno`, `email`, `carrera` | `apellido_materno`, `password` |
| `calificaciones` | `numero_control`, `materia`, `calificacion_final`, `periodo`, `anio` | — |
| `pagos` | `numero_control`, `concepto`, `monto` | `fecha_emision`, `fecha_corte` |

### 3.4 Header Mapping (Case-Insensitive)

Los headers del archivo se normalizan a `snake_case` y se mapean a nombres de campo del sistema. El matching es **flexible**:

| Header en archivo | Normalizado | Campo mapeado |
|------------------|-------------|---------------|
| `No. Control` | `no._control` | → `numero_control` |
| `Número de Control` | `número_de_control` | → `numero_control` |
| `Numero Control` | `numero_control` | → `numero_control` |
| `Nombre Completo` | `nombre_completo` | → NO se usa (error) |
| `apellido paterno` | `apellido_paterno` | → `apellido_paterno` |
| `email` | `email` | → `email` |
| `carrera` | `carrera` | → `carrera` (lookup por código o nombre) |
| `materia` | `materia` | → `materia` (lookup por código o nombre) |
| `calificacion` / `calificación` | `calificación` / `calificacion` | → `calificacion_final` |
| `periodo` | `periodo` | → `periodo` |
| `año` / `anio` | `año` / `anio` | → `anio` |
| `concepto` | `concepto` | → `concepto` |
| `monto` | `monto` | → `monto` |

Se implementa un **alias map** por tipo que permite variaciones comunes. Si después del mapeo faltan columnas requeridas, se retorna error.

### 3.5 Alumnos — `_parse_alumnos`

```python
def _parse_alumnos(headers: list[str], rows: list[list]) -> dict:
    """
    Parsea y valida filas de alumnos.
    
    Validation:
        - numero_control: string no vacío, único en sistema (chequeo contra DB en preview informativo, en execute blocking)
        - nombre, apellido_paterno: string no vacío
        - email: formato email válido, único en sistema
        - carrera: lookup por código (exact) o nombre (ilike).
          Si hay match exacto por código, se usa ese.
          Si no, se busca por nombre ilike.
          Si no se encuentra, error.
        - password: si no se provee, se genera: f"alumno{numero_control}"
    
    Returns:
        rows: list[dict] con keys normalizadas + carrera_id resuelto
        errors: list[{row, field, value, message}]
        
    Nota: Para preview, los FK lookups (carrera) se hacen contra DB real
    pero NO bloquean si fallan — se marcan como error por fila.
    Para execute, errores de FK sí bloquean el commit.
    """
```

### 3.6 Calificaciones — `_parse_calificaciones`

```python
def _parse_calificaciones(headers: list[str], rows: list[list]) -> dict:
    """
    Parsea y valida filas de calificaciones.
    
    Validation:
        - numero_control: lookup → alumno_id (debe existir)
        - materia: lookup por código → materia_id (debe existir)
        - calificacion_final: float, 0-10
        - periodo: string no vacío
        - anio: int, 1900-2099
    
    Upsert (en execute):
        - Buscar Calificacion por (alumno_id, materia_id, periodo, anio)
        - Si existe → actualizar calificacion_final
        - Si no existe → crear nueva
        - Las demás columnas (asistencia_*, practica_*, extra_*) se dejan en 0
          a menos que el archivo las incluya.
    
    Returns:
        rows: list[dict] con alumno_id, materia_id resueltos
        errors: list[{row, field, value, message}]
    """
```

### 3.7 Pagos — `_parse_pagos`

```python
def _parse_pagos(headers: list[str], rows: list[list]) -> dict:
    """
    Parsea y valida filas de pagos (notas de remisión).
    
    Validation:
        - numero_control: lookup → alumno_id (debe existir)
        - concepto: string no vacío
        - monto: float > 0
        - fecha_emision (opcional): date ISO format
        - fecha_corte (opcional): date ISO format
    
    Nota: created_by_id se asigna del JWT del admin en execute.
    
    Returns:
        rows: list[dict] con alumno_id resuelto
        errors: list[{row, field, value, message}]
    """
```

### 3.8 CSV Injection Protection

```python
def _sanitize_value(value: str) -> str:
    """
    Previene CSV injection al mostrar en preview.
    
    Si el string comienza con =, +, -, @, se rechaza con error:
    "El valor contiene una fórmula potencialmente maliciosa"
    """
    DANGEROUS_PREFIXES = ('=', '+', '-', '@')
    
    if isinstance(value, str) and value and value[0] in DANGEROUS_PREFIXES:
        raise ValueError("Valor contiene fórmula maliciosa")
    return value
```

Esta validación se aplica a **todos** los campos string en **ambas fases** (preview y execute).

### 3.9 Batch Processing

Para archivos grandes, el execute procesa en batches de 500 filas para evitar memory issues con SQLAlchemy:

```python
BATCH_SIZE = 500

def _execute_batch(session, rows: list[dict], tipo: str, admin_id: int):
    """
    Procesa un batch de filas dentro de la transacción actual.
    """
```

---

## 4. File Upload Handling

### 4.1 Flujo

```
request.files['file']
    │
    ▼
secure_filename(file.filename)
    │
    ▼
temp_dir = tempfile.gettempdir() / 'portal_imports'
os.makedirs(temp_dir, exist_ok=True)
    │
    ▼
temp_path = os.path.join(temp_dir, secure_name)
file.save(temp_path)
    │
    ▼
try:
    result = parse_file(temp_path, tipo)
finally:
    os.remove(temp_path)
```

### 4.2 Size Limit

Se configura en Flask vía:

```python
# En app.py o config:
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
```

O se verifica manualmente en el endpoint:
```python
if request.content_length and request.content_length > 10 * 1024 * 1024:
    return jsonify({'error': 'El archivo excede el límite de 10MB'}), 413
```

### 4.3 Extensiones Permitidas

```python
ALLOWED_EXTENSIONS = {'.csv', '.xlsx'}
```

### 4.4 Encoding

- CSV: se lee con `utf-8-sig` para manejar BOM automáticamente.
- XLSX: openpyxl maneja encoding internamente.

---

## 5. Validaciones Detalladas por Tipo

### 5.1 Alumnos

| Campo | Tipo Esperado | Validación | Error si |
|-------|--------------|------------|----------|
| `numero_control` | string | `1 <= len <= 20`, not empty | vacío, demasiado largo, duplicado en DB |
| `nombre` | string | `1 <= len <= 100`, not empty | vacío |
| `apellido_paterno` | string | `1 <= len <= 100`, not empty | vacío |
| `apellido_materno` | string (opcional) | `len <= 100` | — |
| `email` | string | regex email, `len <= 120` | formato inválido, duplicado en DB |
| `password` | string (opcional) | `len >= 6` si se provee | demasiado corta |
| `carrera` | string | lookup por código o nombre | no encontrada |

### 5.2 Calificaciones

| Campo | Tipo Esperado | Validación | Error si |
|-------|--------------|------------|----------|
| `numero_control` | string | lookup → `alumno_id` | alumno no existe en DB |
| `materia` | string | lookup por código → `materia_id` | materia no existe en DB |
| `calificacion_final` | float | `0 <= x <= 10` | fuera de rango, no numérico |
| `periodo` | string | not empty | vacío |
| `anio` | int | `1900 <= x <= 2099` | fuera de rango, no numérico |

### 5.3 Pagos

| Campo | Tipo Esperado | Validación | Error si |
|-------|--------------|------------|----------|
| `numero_control` | string | lookup → `alumno_id` | alumno no existe en DB |
| `concepto` | string | `1 <= len <= 255`, not empty | vacío |
| `monto` | float | `x > 0` | <= 0, no numérico |
| `fecha_emision` | date (opcional) | ISO format `YYYY-MM-DD` | formato inválido |
| `fecha_corte` | date (opcional) | ISO format `YYYY-MM-DD` | formato inválido |

### 5.4 Reglas Transversales

- **CSV Injection**: cualquier campo string que comience con `=`, `+`, `-`, `@` se rechaza.
- **Espacios**: todos los strings se hacen `.strip()`.
- **Email**: se normaliza a `lowercase`.
- **Duplicados (alumnos)**: se verifica `numero_control` y `email` contra DB existente. Si ya existe, error.
- **Duplicados (calificaciones)**: el upsert maneja el unique constraint `(alumno_id, materia_id, periodo, anio)`.
- **FK Resolución**: se intenta lookup por código primero, luego por nombre.

---

## 6. Frontend Components

### 6.1 Importar.jsx — Wizard de 4 Pasos

```
┌──────────────────────────────────────────────────────┐
│  Paso 1: Seleccionar Tipo                             │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Alumnos  │  │Calificac.│  │  Pagos   │            │
│  │  (icon)  │  │  (icon)  │  │  (icon)  │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                       │
│  Botón: Siguiente →                                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Paso 2: Subir Archivo                                │
│                                                       │
│  ┌────────────────────────────────────┐              │
│  │                                    │              │
│  │   📁 Arrastra o haz clic          │              │
│  │   CSV o XLSX (max 10MB)           │              │
│  │                                    │              │
│  └────────────────────────────────────┘              │
│                                                       │
│  ← Atrás    Botón: Previsualizar →                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Paso 3: Previsualización                             │
│                                                       │
│  Archivo: alumnos.xlsx | Filas: 150 | Errores: 2     │
│                                                       │
│  ┌──────────┬────────┬────────┬───────┬───────┐      │
│  │ # Control│ Nombre │ Apell. │ Email │Estado │      │
│  ├──────────┼────────┼────────┼───────┼───────┤      │
│  │ FV24001  │ Juan   │ Pérez  │ ✅    │ ✅    │      │
│  │ FV24002  │ María  │ López  │ ❌    │ ❌    │      │
│  └──────────┴────────┴────────┴───────┴───────┘      │
│                                                       │
│  ⚠ Error fila 2: email inválido                       │
│                                                       │
│  ← Atrás    Botón: Importar {N} registros →          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Paso 4: Resultados                                   │
│                                                       │
│  ✅ Importación completada                            │
│                                                       │
│  ✓ 148 registros importados                          │
│  ✓ 0 errores                                          │
│                                                       │
│  🔑 Contraseñas generadas:                            │
│  ┌────────────────────────────────────┐              │
│  │ FV24001 → alumnoFV24001            │              │
│  │ FV24002 → alumnoFV24002            │              │
│  └────────────────────────────────────┘              │
│                                                       │
│  [Descargar reporte] [Importar otro archivo]         │
└──────────────────────────────────────────────────────┘
```

**Estados del wizard:**

1. **Tipo**: selección visual con cards.
2. **Upload**: drag & drop zone con validación de extensión y tamaño en cliente.
3. **Preview**: tabla con columna de estado (✅/❌ por fila). Tooltip con errores. Botón "Importar" deshabilitado si hay errores estructurales (columnas faltantes).
4. **Resultados**: reporte post-importación. Si hubo errores, tabla de errores. Si éxito, resumen + contraseñas generadas + botón descargar reporte (CSV con contraseñas).

### 6.2 API Module — `imports.js`

```javascript
import api from './index';

export const previewImport = async (file, tipo) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tipo', tipo);
  
  const response = await api.post('/imports/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000, // 30s porque puede tardar en archivos grandes
  });
  return response.data;
};

export const executeImport = async (file, tipo) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tipo', tipo);
  
  const response = await api.post('/imports/execute', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000, // 2min para archivos grandes
  });
  return response.data;
};
```

### 6.3 Modificaciones a App.jsx

Se agrega import y ruta:

```jsx
import AdminImportar from './pages/admin/Importar';

// Dentro del grupo de rutas admin:
<Route path="importar" element={<AdminImportar />} />
```

### 6.4 Modificaciones a Sidebar.jsx

Se agrega item en `adminNavItems`:

```javascript
import { Upload } from 'lucide-react';

// En adminNavItems, entre Asignaciones y Exportar:
{ path: '/admin/importar', icon: Upload, label: 'Importar' },
```

### 6.5 Drag & Drop Zone

Se utiliza un componente funcional dentro de `Importar.jsx` que maneja:
- `onDragOver` / `onDrop` para drag & drop.
- `onChange` para click.
- Validación de extensión en cliente (`.csv`, `.xlsx`).
- Validación de tamaño en cliente (< 10 MB).
- Feedback visual (borde coloreado, mensaje de error).

---

## 7. Sequence Diagrams

### 7.1 Preview Flow

```
Admin                  Frontend                    Backend (imports.py)           DB
  │                        │                            │                        │
  │  Select type + file    │                            │                        │
  │───────────────────────>│                            │                        │
  │                        │                            │                        │
  │                        │  POST /api/imports/preview │                        │
  │                        │  (FormData: file + tipo)   │                        │
  │                        │───────────────────────────>│                        │
  │                        │                            │                        │
  │                        │                            │── validate file type   │
  │                        │                            │── validate extension   │
  │                        │                            │── validate size        │
  │                        │                            │── save to temp         │
  │                        │                            │                        │
  │                        │                            │── read headers         │
  │                        │                            │── validate required    │
  │                        │                            │   columns              │
  │                        │                            │                        │
  │                        │                            │── read first 10 rows   │
  │                        │                            │                        │
  │                        │                            │── for each row:        │
  │                        │                            │   ├ type coercion      │
  │                        │                            │   ├ CSV inj check      │
  │                        │                            │   ├ FK lookups (info)  │
  │                        │                            │   └ collect errors     │
  │                        │                            │                        │
  │                        │                            │── cleanup temp file    │
  │                        │                            │                        │
  │                        │  { columns, rows_preview,  │                        │
  │                        │    total_rows, importable, │                        │
  │                        │    warnings }              │                        │
  │                        │<───────────────────────────│                        │
  │                        │                            │                        │
  │  Show preview table    │                            │                        │
  │  with status per row   │                            │                        │
  │<───────────────────────│                            │                        │
```

### 7.2 Execute Flow (Success)

```
Admin                  Frontend                    Backend (imports.py)           DB
  │                        │                            │                        │
  │  Click "Importar"      │                            │                        │
  │───────────────────────>│                            │                        │
  │                        │                            │                        │
  │                        │  POST /api/imports/execute │                        │
  │                        │  (FormData: file + tipo)   │                        │
  │                        │───────────────────────────>│                        │
  │                        │                            │                        │
  │                        │                            │── validate file        │
  │                        │                            │── save to temp         │
  │                        │                            │── parse ALL rows       │
  │                        │                            │── validate ALL rows    │
  │                        │                            │                        │
  │                        │                            │── if ANY errors →      │
  │                        │                            │   return error report  │
  │                        │                            │   (NO DB writes)       │
  │                        │                            │                        │
  │                        │                            │── BEGIN TRANSACTION    │
  │                        │                            │                        │>
  │                        │                            │── for each batch(500): │
  │                        │                            │   ├ alumnos: INSERT    │>>>
  │                        │                            │   ├ califs: UPSERT     │>>>
  │                        │                            │   └ pagos: INSERT     │>>>
  │                        │                            │                        │
  │                        │                            │── COMMIT               │
  │                        │                            │────────────────────────>│
  │                        │                            │                        │
  │                        │                            │── cleanup temp file    │
  │                        │                            │                        │
  │                        │  { status: "success",      │                        │
  │                        │    imported: 150,          │                        │
  │                        │    generated_passwords,    │                        │
  │                        │    details }               │                        │
  │                        │<───────────────────────────│                        │
  │                        │                            │                        │
  │  Show success report   │                            │                        │
  │  with passwords        │                            │                        │
  │<───────────────────────│                            │                        │
```

### 7.3 Execute Flow (Error → Rollback)

```
Admin                  Frontend                    Backend (imports.py)           DB
  │                        │                            │                        │
  │  Click "Importar"      │                            │                        │
  │───────────────────────>│                            │                        │
  │                        │  POST /api/imports/execute │                        │
  │                        │───────────────────────────>│                        │
  │                        │                            │                        │
  │                        │                            │── parse ALL rows       │
  │                        │                            │── validate ALL rows    │
  │                        │                            │                        │
  │                        │                            │── FOUND ERRORS:        │
  │                        │                            │   row 5: email inv.    │
  │                        │                            │   row 12: carrera no   │
  │                        │                            │            existe      │
  │                        │                            │                        │
  │                        │                            │── NO DB writes         │
  │                        │                            │── cleanup temp file    │
  │                        │                            │                        │
  │                        │  { status: "error",        │                        │
  │                        │    imported: 0,            │                        │
  │                        │    errors: [...],          │                        │
  │                        │    error_count: 2 }        │                        │
  │                        │<───────────────────────────│                        │
  │                        │                            │                        │
  │  Show error table      │                            │                        │
  │  with row details      │                            │                        │
  │<───────────────────────│                            │                        │
```

---

## 8. Manejo de Errores

### 8.1 Backend

| Situación | HTTP Status | Código | Acción |
|-----------|-------------|--------|--------|
| Tipo inválido | 400 | `INVALID_TYPE` | Retornar error |
| Extensión no permitida | 400 | `INVALID_FILE_TYPE` | Retornar error |
| Archivo sin contenido | 400 | `EMPTY_FILE` | Retornar error |
| Archivo excede 10MB | 413 | `FILE_TOO_LARGE` | Flask o manual |
| Columnas requeridas faltan | 400 | `MISSING_COLUMNS` | Retornar error + columnas esperadas |
| Errores en filas (execute) | 200 | — | Retornar reporte con errores, sin commit |
| Error interno (DB connection, etc.) | 500 | `INTERNAL_ERROR` | Rollback + error genérico |
| CSV Injection detectado | 200 | — | Error por fila (no bloquea preview) |

### 8.2 Frontend

- **Errores de red**: mostrar toast con "Error de conexión. Intenta de nuevo."
- **Archivo inválido**: mostrar mensaje debajo del drop zone.
- **Preview con errores**: cada fila inválida se marca en rojo; tooltip con detalles.
- **Execute con errores**: paso 4 muestra tabla de errores en lugar de éxito.
- **Timeout**: si la petición tarda > 2min, mostrar "El archivo es demasiado grande o el servidor está ocupado."

---

## 9. Reporte Descargable

Después de un execute exitoso (alumnos), se ofrece descargar un archivo CSV con las contraseñas generadas:

```
numero_control,password
FV2024001,alumnoFV2024001
FV2024002,alumnoFV2024002
```

Este reporte se genera en frontend (client-side) a partir de `generated_passwords` en la respuesta.

---

## 10. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Archivo corrupto | try/except al abrir; mensaje claro "El archivo no pudo ser leído" |
| Encoding incorrecto | `utf-8-sig` para CSV; openpyxl maneja XLSX |
| Archivo enorme (>100MB) | Límite de 10MB en Flask + frontend |
| Duplicados accidentales | Validación de unicidad en preview y execute |
| SQL Injection | Los valores se insertan vía SQLAlchemy ORM (parametrizado) |
| CSV Injection | Sanitización de valores que empiezan con `= + - @` |
| Timeout de conexión | Timeout de 2min en axios para execute |
| Carrera/materia no encontrada | Error por fila con nombre del registro faltante |

---

## 11. Checklist de Implementación

### Backend
- [ ] Crear `backend/routes/imports.py` con blueprint `imports_bp`
- [ ] Implementar `_read_file()` con soporte CSV + XLSX
- [ ] Implementar header mapping (case-insensitive)
- [ ] Implementar `_sanitize_value()` para CSV injection
- [ ] Implementar `_parse_alumnos()`
- [ ] Implementar `_parse_calificaciones()`
- [ ] Implementar `_parse_pagos()`
- [ ] Implementar `POST /api/imports/preview`
- [ ] Implementar `POST /api/imports/execute` con transacción
- [ ] Registrar `imports_bp` en `backend/app.py` con prefijo `/api/imports`
- [ ] Configurar `MAX_CONTENT_LENGTH` en Flask (10MB)

### Frontend
- [ ] Crear `frontend/src/api/imports.js`
- [ ] Crear `frontend/src/pages/admin/Importar.jsx` con wizard de 4 pasos
- [ ] Agregar ruta `/admin/importar` en `App.jsx`
- [ ] Agregar item "Importar" en `Sidebar.jsx`
- [ ] Implementar drag & drop zone
- [ ] Implementar tabla de preview con validación por fila
- [ ] Implementar pantalla de resultados con tabla de errores
- [ ] Implementar descarga de reporte de contraseñas (client-side CSV)
