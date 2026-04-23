# Proposal: portal-fv-edit-carreras-pagos

## Intent

Habilitar la edición de notas de remisión (pagos) desde el panel de admin. Los administradores actualmente pueden crear, eliminar y cambiar el estado de pagado/pendiente, pero NO pueden editar los datos de una nota existente (concepto, monto, fecha). Esta funcionalidad es necesaria para corregir errores de ingreso o ajustar montos cuando hay acuerdos de pago parcial.

## Scope

### In Scope
- Agregar modal de edición en `Pagos.jsx` para notas existentes (concepto, monto, fecha_emision)
- Conectar con API `updatePago` existente
- Validaciones en frontend (campos requeridos, monto > 0)

### Out of Scope
- Edición de carreras — ya existe y funciona correctamente
- Cambios en backend — API ya existe (PUT /pagos/<id>)
- Edición masiva de notas

## Approach

Agregar modal de edición en el componente `AdminPagos` que usa el mismo pattern que `create`, pero pre-carga los datos existentes del pago seleccionado. Reutilizar el diseño actual del modal existente.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/pages/admin/Pagos.jsx` | Modified | Agregar modal de edición |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Confusion con toggle de estado | Low | Edit modifica datos, toggle modifica estado |

## Rollback Plan

Revertir cambios en `Pagos.jsx` — el archivo ya está versionado en git.

## Dependencies

- Backend API `updatePago` (ya existe en `backend/routes/pagos.py` y `frontend/src/api/pagos.js`)

## Success Criteria

- [ ] Modal de edición abre al hacer click en botón de editar en cada fila
- [ ] Datos existentes se cargan correctamente en el form
- [ ] Save modifica la nota en backend
- [ ] UI muestra feedback de éxito/error