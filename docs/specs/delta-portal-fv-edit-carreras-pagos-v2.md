# DELTA SPEC: portal-fv-edit-carreras-pagos-v2

**Versión:** 1.0  
**Fecha:** 2026-04-23  
**Change ID:** portal-fv-edit-carreras-pagos-v2  
**Parent Spec:** 2026-03-25-portal-fv-design.md  
**Status:** Ready for Review

---

## 1. Overview

| Campo | Descripción |
|-------|-------------|
| **Nombre** | Editar Notas de Remisión (Pagos) - v2 |
| **Resumen** | Agregar funcionalidad de edición de notas de remisión en el panel de administración, permitiendo modificar concepto, monto y fecha de emisión |
| **Contexto** | El cambio `portal-fv-edit-carreras-pagos` (v1) fue propuesto pero no implementado. Esta versión v2 incorpora mejoras basadas en revisión de código existente |
| **Pertenece a** | Fase 4: Pagos y Exportación |

---

## 2. Actors

| Actor | Descripción | Permisos |
|-------|-------------|----------|
| **Administrador** | Usuario con acceso completo al panel de admin | Crear, Leer, Actualizar, Eliminar notas de remisión |
| **Alumno** |Usuario final que solo ve sus pagos | Solo lectura de sus notas |

---

## 3. Goals

### 3.1 Primary Goals

- [ ] **G1:** Agregar botón de editar en cada fila de la tabla de pagos
- [ ] **G2:** Implementar modal de edición que pre-cargue los datos existentes (concepto, monto, fecha_emision)
- [ ] **G3:** Conectar el modal de edición con la API existente `updatePago()`
- [ ] **G4:** Mantener consistencia UI con el patrón existente en Carreras.jsx

### 3.2 Secondary Goals

- [ ] **G5:** Validar campos requeridos en el formulario de edición
- [ ] **G6:** Mostrar feedback visual de éxito/error al guardar
- [ ] **G7:** Actualizar la lista de pagos en tiempo real después de editar

---

## 4. Delta Requirements

### 4.1 Functional Requirements

| ID | Requisito | Prioridad | Descripción |
|----|----------|----------|-------------|
| **FR-01** | Botón Editar en tabla | Must Have | Agregar botón con ícono de lápiz en columna "Acciones" de la tabla de pagos |
| **FR-02** | Modal de edición | Must Have | Modal que abra con datos pre-cargados del pago seleccionado |
| **FR-03** | Campos editables | Must Have | Los campos concepto, monto y fecha_emision deben ser editables |
| **FR-04** | Submit编辑 | Must Have | Al enviar el formulario, llamar a `updatePago(id, data)` |
| **FR-05** | Feedback usuario | Should Have | Mostrar alerta de éxito/error después de guardar |
| **FR-06** | Actualizar lista | Should Have | Después de editar, actualizar el pago en la lista local |

### 4.2 Non-Functional Requirements

| ID | Requisito | Criterio de Aceptación |
|----|----------|---------------------|
| **NFR-01** | Rendimiento | La edición debe completarse en < 2 segundos |
| **NFR-02** | Consistencia UI | El modal de edición debe usar el mismo estilo que el modal de creación |
| **NFR-03** | Accesibilidad | Todos los inputs deben tener labels asociados |
| **NFR-04** | Manejo de errores | Si la API falla, mostrar mensaje de error claro |

---

## 5. Acceptance Criteria

### 5.1 Success Conditions

- [ ] **AC-01:** Al hacer clic en el botón de editar de cualquier fila, el modal de edición abre con los datos correctos pre-cargados
- [ ] **AC-02:** Los campos del formulario (concepto, monto, fecha_emision) muestran los valores actuales del pago
- [ ] **AC-03:** Al modificar un campo y hacer clic en "Guardar", la nota se actualiza en la base de datos
- [ ] **AC-04:** Después de guardar, la tabla muestra los datos actualizados sin necesidad de recargar
- [ ] **AC-05:** El botón "Cancelar" cierra el modal sin guardar cambios

### 5.2 Visual Checkpoints

| Checkpoint | Descripción |
|-----------|-------------|
| **VC-01** | Modal de edición tiene estilo consistente con modal de creación |
| **VC-02** | El header del modal dice "Editar Nota de Remisión" (diferente de "Nueva Nota") |
| **VC-03** | El botón de submit dice "Guardar Cambios" (diferente de "Crear Nota") |
| **VC-04** | El botón de editar usa ícono de lápiz (lápiz/editar) |
| **VC-05** | Los campos del formulario tienen los valores actuales del pago |

---

## 6. Test Scenarios

### 6.1 Positive Scenarios

| ID | Escenario | Pasos | Resultado Esperado |
|----|----------|------|----------------|
| **TS-01** | Editar concepto | 1. Seleccionar alumno con pagos 2. Click en botón editar 3. Cambiar concepto 4. Click guardar | El concepto se actualiza en la tabla |
| **TS-02** | Editar monto | 1. Click editar 2. Cambiar monto a 5000 3. Guardar | El monto se actualiza y muestra formato moneda |
| **TS-03** | Editar fecha | 1. Click editar 2. Cambiar fecha 3. Guardar | La fecha se actualiza en formato DD/MM/YYYY |
| **TS-04** | Cancelar edición | 1. Click editar 2. Cambiar campos 3. Click cancelar | Modal cierra, sin cambios en base de datos |

### 6.2 Negative Scenarios

| ID | Escenario | Pasos | Resultado Esperado |
|----|----------|------|----------------|
| **TS-05** | Concepto vacío | 1. Click editar 2. Borrar concepto 3. Intentar guardar | Validación muestra error "Concepto requerido" |
| **TS-06** | Monto negativo | 1. Click editar 2. Ingresar monto -100 3. Guardar | Validación previene o muestra error |
| **TS-07** | API falla | 1. Click editar 2. Guardar con conexión cortada | Muestra mensaje de error al usuario |

### 6.3 Edge Cases

| ID | Escenario | Pasos | Resultado Esperado |
|----|----------|------|----------------|
| **TS-08** |编辑ar pago ya pagado | 1. Seleccionar alumnocon pago marcado "Pagada" 2. Editar | Permite editar sin cambios en estado |
| **TS-09** | Multiple ediciones | 1. Editar pago A 2. Cerrar 3. Editar pago B | Cada pago carga sus datos correctos |

---

## 7. Data Model Impact

### 7.1 Entidades Afectadas

| Entidad | Operación | Impacto |
|--------|-----------|---------|
| **NotaRemision** | UPDATE | Se modifica concepto, monto, fecha_emision |

### 7.2 API Calls

| Método | Ruta | Payload | Descripción |
|--------|-----|---------|-------------|
| PUT | `/api/pagos/<id>` | `{ concepto, monto, fecha_emision }` | Actualiza nota existente |

### 7.3 No Schema Changes

> **Nota:** No se requieren cambios en el esquema de base de datos. La API existente `PUT /pagos/<id>` ya soporta la actualización completa de notas de remisión.

---

## 8. Affected Files

| Archivo | Rol | Cambios |
|---------|-----|---------|
| `frontend/src/pages/admin/Pagos.jsx` | UI principal | Agregar estado `editingPago`, función `openEditModal()`, modificar modal para soportar modo edición |
| `frontend/src/api/pagos.js` | API client | **Sin cambios** — `updatePago()` ya existe |
| `backend/routes/pagos.py` | Backend | **Sin cambios** — API PUT ya existe |

---

## 9. Dependencies

| Dependencia | Estado | Notas |
|------------|--------|-------|
| Backend API `PUT /api/pagos/<id>` | ✅ Existente | Ya implementada, no requiere cambios |
| API client `updatePago()` | ✅ Existente | Ya en `frontend/src/api/pagos.js` |
| Carreras.jsx como referencia | ✅ Existente | Pattern a seguir para consistencia UI |

---

## 10. Exclusions (Out of Scope)

- Edición de múltiples notas de forma masiva
- Cambios en el backend
- Modificación del estado "pagada/pendiente" desde el modal de edición (solo desde toggle)
- Exportación de notas editadas

---

## 11. Risks & Mitigations

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Confusión entre Edit y Toggle | Baja | Edit modifica datos (concepto/monto/fecha), Toggle modifica estado (pagada) |
| Pérdida de cambios al cerrar | Baja | Confirmar si hay cambios sin guardar (opcional) |

---

## 12. Definition of Done

- [ ] Tests TS-01 a TS-04 pasan exitosamente
- [ ] Tests TS-05 a TS-07 muestran errores apropiados
- [ ] UI consistente con Carreras.jsx
- [ ] Sin errores en consola
- [ ] Código revisado por pares

---

*Documento creado el 23 de abril de 2026*