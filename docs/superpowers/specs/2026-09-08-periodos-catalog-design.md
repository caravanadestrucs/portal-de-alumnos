# Design Spec — Períodos como catálogo (portal-de-alumnos)

- **Estado:** Aprobado
- **Fecha:** 2026-09-08
- **Stack:** Flask + SQLAlchemy (backend) + React + Vite (frontend)
- **Tipo de documento:** Design spec. No contiene código de aplicación, solo decisiones y requisitos.
- **Decisión aprobada que rige todo el spec:** filtro visual por período en Boletas (la descarga es siempre el historial completo) + tabla `periodos` como catálogo.

## 1. Objetivo y alcance

### Objetivo

Reemplazar el "período" implícito actual (fechas sueltas en asignaciones y strings heterogéneos en calificaciones) por un catálogo único `periodos`, referenciado por `Asignacion` en el slice 1 y por `Calificacion` en el slice 2, con filtro visual por período en Boletas.

### Alcance (un solo ciclo, dos slices)

- Slice 1: tabla `periodos` + `Asignacion.periodo_id` + CRUD `/api/periodos` + formulario y columna de período en Asignaciones + selector visual en Boletas + rescate de la descarga DOCX.
- Slice 2: `Calificacion.periodo_id` heredado de la asignación + backfill por match exacto + históricos sin match quedan en `NULL` ("Sin periodo").

### Fuera de alcance (explícito)

1. **Normalización forzada de históricos:** ningún histórico se reescribe, renombra ni elimina. Lo que no hace match exacto queda en `NULL` y se muestra como "Sin periodo".
2. **Enum cerrado en código:** no se crea enum ni constante cerrada de períodos en backend o frontend. El catálogo vive solo en la tabla `periodos`.
3. **PDFs o DOCXs por período:** no se genera un documento separado por período. La descarga es un único documento con el historial completo.
4. **Limpieza de `Grupo.periodo/anio`:** esos campos quedan intactos en este ciclo (ni se exponen ni se migran). Ver sección 2.
5. **Cambios de roles o de autenticación:** fuera de este spec, salvo lo indicado en la sección 4 para `/api/periodos`.

## 2. Contexto verificado del repo (base del diseño)

- **Asignación = profesor + grupo + materia; su "Período" actual son fechas sueltas.** El POST recibe `{profesor_id, materia_id, grupo_id, fecha_inicio, fecha_fin}` (`backend/routes/asignaciones.py:97-179`). El modelo no tiene período (`backend/models.py:569-582`). El PUT edita esas fechas (`backend/routes/asignaciones.py:216-226`). El formulario de crear vive en `frontend/src/pages/admin/Asignaciones.jsx:26-33,350-433`, la tabla llama "Período" a las fechas (`:252-285`) y el modal de edición en `:110-129`.
- **Grupo ya tiene `periodo/anio` muertos.** Declarados en `backend/models.py:514-515`. El POST de grupos no los asigna (`backend/routes/grupos.py:125-130`) y el PUT los ignora (`:162-167`).
- **Calificación usa `periodo String(20)` + `anio` nullable** (`backend/models.py:288-289`) con unicidad `(alumno_id, materia_id, periodo, anio)`. Valores heterogéneos reales en uso: `"Enero-Abril {year}"` (`backend/routes/profesor.py:73-74,136-137`). El POST exige `periodo` + `anio` (`backend/routes/calificaciones.py:98-101`), el bulk usa por defecto `'Regular'` / `2026` (`:395-396,414-415`), el PUT acepta `periodo` (`:291-294`) pero la UI de admin no lo expone (`frontend/src/pages/admin/Calificaciones.jsx:266-277`). Existe `GET /periodos` (`backend/routes/calificaciones.py:330-355`).
- **Boletas: un solo DOCX con `final > 0`, sin separar por período** (`backend/routes/boletas.py:83-130`, bulk `:138-193`, preview `:200-243`). La importación `from utils.boleta_generator import generar_boleta` está rota: ese módulo no existe en `backend/utils/` y `requirements.txt` no declara `python-docx`.

## 3. Datos

### 3.1 Tabla `periodos` (slice 1)

| Columna | Tipo y restricción | Significado |
|---|---|---|
| `id` | Integer, PK | Identificador del período |
| `nombre` | String, `UNIQUE NOT NULL` | Nombre canónico visible (p. ej. valores ya en uso). Es lo que muestra el dropdown |
| `fecha_inicio` | Date, nullable | Inicio referencial del período |
| `fecha_fin` | Date, nullable | Fin referencial del período |
| `activa` | Boolean, `NOT NULL DEFAULT true` | Si es `false`, no aparece en dropdowns de creación pero sigue visible en históricos |

Reglas:

- `nombre` es único y obligatorio a nivel de base de datos.
- `activa = false` no borra ni oculta históricos; solo excluye el período de los dropdowns de creación. La edición posterior sí puede seleccionar un período inactivo si la asignación ya lo tenía.
- La migración del slice 1 crea la tabla, el índice único sobre `nombre` y el seed. Su downgrade elimina la tabla.

### 3.2 `Asignacion.periodo_id` (slice 1)

- Nueva columna `Asignacion.periodo_id`: Integer, FK a `periodos.id`, **nullable a nivel de base de datos**.
- La nulabilidad existe solo para no romper asignaciones legacy ya creadas con fechas sueltas. Toda asignación legacy sin valor queda en `NULL` y se muestra como "Sin periodo".
- **Toda asignación creada después de este spec lleva `periodo_id` obligatorio vía API** (ver sección 4). "Obligatorio vía API" significa: validación en el endpoint, no constraint `NOT NULL` en la columna durante este ciclo.
- La migración del slice 1 agrega la columna nullable y su FK. Su downgrade retira la FK y la columna. No se rellenan valores automáticamente en el slice 1.
- `fecha_inicio` / `fecha_fin` de `Asignacion` se conservan sin cambios en este ciclo.

### 3.3 Seed (slice 1)

- La migración del slice 1 inserta los valores canónicos ya en uso en el repo (incluye los formatos `"Enero-Abril {year}"` y `"Regular"`) más una fila reservada de nombre exacto `"Sin periodo"`.
- `"Sin periodo"` no se asigna jamás vía API; es solo la etiqueta de presentación para `periodo_id IS NULL`.
- La fila `"Sin periodo"` tiene `activa = false` para que nunca aparezca en dropdowns de creación.
- El downgrade de la migración elimina las filas insertadas por el seed.

### 3.4 `Calificacion.periodo_id` (slice 2, no antes)

- Nueva columna `Calificacion.periodo_id`: Integer, FK a `periodos.id`, **nullable**.
- Valor normativo: se hereda de la asignación correspondiente (profesor + grupo + materia) al momento de crear o actualizar la calificación por flujo de asignación. "Heredado de la asignación" significa exactamente eso: la calificación copia el `periodo_id` de la `Asignacion` que vincula a ese profesor, grupo y materia; no lo deduce de fechas ni de strings.
- Las columnas legacy `Calificacion.periodo` (String) y `Calificacion.anio` se conservan sin cambios en este ciclo; no se renombran, no se recalculan, no se restringen.
- **Backfill del slice 2 por match exacto:** una calificación recibe `periodo_id` solo si la concatenación de su `periodo` + `anio` legacy coincide carácter por carácter con el `nombre` de una fila de `periodos`. Cualquier calificación sin coincidencia exacta (incluye valores raros, mayúsculas distintas, espacios extra o `anio` nulo sin match) queda en `NULL` y se presenta como "Sin periodo".
- La migración del slice 2 agrega la columna nullable, su FK y ejecuta el backfill descrito. Su downgrade retira la FK y la columna.

## 4. Backend

### 4.1 CRUD `/api/periodos`

- `GET /api/periodos`: accesible para todos los roles autenticados. Responde la lista ordenada por `nombre`. Cada elemento contiene `id`, `nombre`, `fecha_inicio`, `fecha_fin`, `activa`.
- `POST /api/periodos`, `PUT /api/periodos/<id>`, `DELETE /api/periodos/<id>`: solo rol `admin`. (Duda abierta: si `sede_admin` también debe escribir; ver sección 7. Hasta que se resuelva, solo `admin`.)
- `POST` exige `nombre` no vacío; sin `nombre` responde 422 con mensaje de campo obligatorio. `nombre` duplicado responde 409.
- `DELETE` es borrado lógico: pone `activa = false`. No existe borrado físico en este ciclo. Eliminar un período con asignaciones o calificaciones asociadas solo lo desactiva; las filas asociadas conservan su `periodo_id`.

### 4.2 Asignaciones

- `POST /api/asignaciones` exige `periodo_id` de un período existente y con `activa = true`. Sin `periodo_id`, con `periodo_id` nulo o con id inexistente/inactivo, responde **422** con error de campo obligatorio o inválido. (El rango aprobado es 400/422; el código normativo en este spec es 422. El 400 queda reservado para payload malformado como JSON inválido.)
- `PUT /api/asignaciones/<id>` acepta cambio de `periodo_id` (edición posterior). Acepta cualquier período existente, activo o inactivo; con id inexistente responde 422. Omitir `periodo_id` en el PUT conserva el valor actual; enviarlo en nulo explícito deja la asignación en "Sin periodo".
- `GET /api/asignaciones` incluye en cada elemento `periodo_id` y `periodo_nombre` (`null` y `"Sin periodo"` cuando no hay período).

### 4.3 Boletas

- `GET /api/boletas/alumnos` acepta query param opcional `?periodo_id=<id>`.
- Con `periodo_id` presente y válido, la respuesta filtra la **lista** a las materias cuyas calificaciones tienen ese `periodo_id`. Sin el parámetro, responde el historial completo. Con id inexistente responde 422.
- La **descarga** del documento (`GET` de descarga y bulk) ignora cualquier filtro y genera siempre un único DOCX con el historial completo (todas las materias con `final > 0`), igual que hoy.
- **Rescate de la descarga (slice 1, obligatorio):** crear el módulo `backend/utils/boleta_generator.py` con la función `generar_boleta` que hoy se importa pero no existe, declarar `python-docx` en `requirements.txt` y cubrir con un test que verifica que la descarga responde 200 con contenido DOCX. Sin este rescate, ninguna descarga funciona.

## 5. Frontend

### 5.1 Asignaciones (`frontend/src/pages/admin/Asignaciones.jsx`)

- Los formularios de crear y de editar agregan un dropdown "Período" que muestra `periodo.nombre` y guarda `periodo.id`.
- El dropdown de crear lista solo períodos con `activa = true` más el estado inicial vacío que bloquea el envío hasta elegir uno. El de editar lista además el período actual de la asignación aunque esté inactivo.
- La tabla reemplaza el encabezado "Período" basado en fechas por dos columnas: "Período" (muestra `periodo_nombre` o `"Sin periodo"`) y "Fechas" (mantiene `fecha_inicio – fecha_fin` actuales).
- Crear sin elegir período bloquea el envío en el cliente y, si igual llega al backend, el backend responde 422.

### 5.2 Boletas

- La vista de Boletas agrega un selector "Período" (opción por defecto: "Todos") que llama a `GET /api/boletas/alumnos?periodo_id=<id>` y filtra solo la **lista visible**.
- El botón de descarga no envía `periodo_id` y descarga siempre el historial completo.
- Cuando el filtro no tiene resultados, la lista muestra estado vacío y la descarga sigue disponible con el historial completo.

## 6. Testing (TDD estricto)

Orden normativo: test que falla → implementación mínima → refactor. Sin excepciones en este ciclo.

- **Backend (pytest), slice 1:** CRUD de `/api/periodos` (GET para todos los roles; escritura solo `admin`; 422 sin nombre; 409 en duplicado; DELETE desactiva); `POST /api/asignaciones` sin `periodo_id` responde 422; `PUT` cambia `periodo_id`; `GET /api/boletas/alumnos?periodo_id=` filtra la lista; test de descarga 200 con DOCX tras el rescate de `boleta_generator`.
- **Backend (pytest), slice 2:** crear calificación hereda `periodo_id` de la asignación; backfill por match exacto asigna solo coincidencias carácter por carácter; históricos raros quedan en `NULL`.
- **Frontend (vitest):** dropdown de Asignaciones muestra `nombre` y envía `id`, bloquea crear sin período, la tabla muestra "Sin periodo" ante `null`; selector de Boletas filtra la lista visible y la descarga no envía `periodo_id`.
- **Migraciones:** cada slice entrega migración con `upgrade` y `downgrade` verificados (subir y bajar sin error en base de prueba). Slice 1: tabla + seed + columna nullable en asignación. Slice 2: columna nullable en calificación + backfill.

## 7. Riesgos y decisiones abiertas (explícito)

1. **[ABIERTA] Rol que escribe períodos.** Este spec deja la escritura de `/api/periodos` solo en `admin`. Si `sede_admin` debe crear períodos por sede, hace falta un campo de sede en `periodos` que hoy no existe y cambia el seed y el CRUD. Se resuelve antes del slice 1.
2. **[ABIERTA] `NOT NULL` vs nullable en el slice 2.** Este spec deja `Calificacion.periodo_id` nullable para preservar históricos raros como "Sin periodo". Hacerlo `NOT NULL` obligaría a asignar un período a historiales que hoy no tienen match exacto, lo que contradice la regla de no normalización forzada de la sección 1. Se resuelve antes del slice 2 y, si cambia a `NOT NULL`, requiere un nuevo spec.

## 8. Self-review del spec (inline)

- **Placeholder scan:** sin marcadores pendientes ni valores por definir. Cada lista (semilla, endpoints, columnas) está cerrada o remite a valores ya verificados en el repo.
- **Consistencia interna:** `periodo_id` nullable en base + obligatorio vía API es intencional y se aplica igual en slice 1 (asignación) y slice 2 (calificación heredada); la descarga es siempre historial completo en backend (sección 4) y frontend (sección 5); `Grupo.periodo/anio` no se toca en ninguna sección.
- **Scope de un solo ciclo:** dos slices consecutivos sin dependencias externas; lo excluido en la sección 1 no reaparece como requisito en ninguna otra sección.
- **Ambigüedad:** cada requisito tiene una sola lectura — 422 (no "400/422") para `periodo_id` faltante, match exacto carácter por carácter para el backfill, `"Sin periodo"` como etiqueta de `NULL`, DELETE como baja lógica, y herencia de `Calificacion.periodo_id` exclusivamente desde la `Asignacion` vinculada.
