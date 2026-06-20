# Propuesta: Importación Masiva de Datos

## Resumen
Agregar funcionalidad de importación masiva vía CSV/XLSX para Alumnos, Calificaciones y Pagos.

## Archivos a Modificar/Crear

### Backend
| Archivo | Acción |
|---------|--------|
| `backend/routes/imports.py` | **NUEVO** blueprint — preview + execute |
| `backend/app.py` | + registro `imports_bp` |

### Frontend
| Archivo | Acción |
|--------|--------|
| `frontend/src/pages/admin/Importar.jsx` | **NUEVO** — flujo de 4 pasos |
| `frontend/src/api/imports.js` | **NUEVO** — API calls con FormData |
| `frontend/src/App.jsx` | + ruta `/admin/importar` |
| `frontend/src/components/layout/Sidebar.jsx` | + item "Importar" |

## Tipos de Importación

| Tipo | Columnas Requeridas | Upsert |
|------|--------------------|--------|
| Alumnos | `numero_control`, `nombre`, `apellido_paterno`, `email`, `carrera` | No |
| Calificaciones | `numero_control`, `materia`, `calificacion_final`, `periodo`, `anio` | Sí (por unique) |
| Pagos | `numero_control`, `concepto`, `monto` | No |

## Decisiones Técnicas
- **Parser**: openpyxl (XLSX) + csv stdlib (CSV). Sin pandas.
- **Validación en 2 fases**: Preview (headers + primeras filas) → Execute (transacción completa)
- **Transaccionalidad total**: si 1 fila falla, rollback completo
- **Resolución referencias**: busca por código o nombre (carreras, materias)
- **Contraseña default**: si no viene en CSV, genera `alumno{NUMERO_CONTROL}`
- **Límite**: 10MB, batches de 500 filas

## Flujo de Usuario
```
1. Seleccionar tipo → 2. Upload archivo → 3. Preview con validaciones → 4. Confirmar importación
```

## Riesgos
- Archivos muy grandes (>10MB)
- CSV injection (sanitizar fórmulas)
- Encoding issues (BOM UTF-8)
- Dependencia de formato exacto de columnas
