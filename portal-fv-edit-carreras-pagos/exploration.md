# Exploration: portal-fv-edit-carreras-pagos

## Current State
Both **Carreras** and **Pagos** pages exist in the admin section, but they have different levels of CRUD functionality:

- **Carreras.jsx**: Full CRUD (Create, Read, Update, Delete) ✓
- **Pagos.jsx**: Partial CRUD — only Create, Toggle Status, and Delete. **Missing Edit functionality**.

The user wants Pagos to match the Carreras pattern with proper edit modal.

## Affected Areas

| File | Role | Changes Needed |
|------|------|----------------|
| `frontend/src/pages/admin/Pagos.jsx` | UI (admin pagos) | Add Edit modal + openEditModal() function |
| `frontend/src/api/pagos.js` | API client | Already has `updatePago()` — no changes needed |
| `backend/routes/pagos.py` | Backend | Already supports PUT `/pagos/<id>` — no changes needed |

## Approaches

### 1. **Mirror Carreras Pattern (Recommended)** — Low Effort
Follow the exact same modal pattern from Carreras.jsx:
- Add `openEditModal(pago)` function that pre-fills form with pago data
- Add `editMode` state (similar to `modalMode`)
- Modify modal to show "Editar Nota" when editing
- Add Edit button in the table actions column
- Use existing `updatePago()` API function

**Pros:**
- Consistent UX with Carreras
- Minimal code (reuse patterns)
- Backend already ready

**Cons:**
- None significant

**Effort: Low**

### 2. **Inline Edit with Row Expansion** — Medium Effort
Instead of a modal, expand the row to show editable fields inline.

**Pros:**
- More compact UI
- Edit multiple items at once

**Cons:**
- Inconsistent with Carreras pattern
- More complex state management
- Breaks UI consistency

**Effort: Medium**

### 3. **Separate Edit Page** — High Effort
Create a dedicated edit page `/admin/pagos/:id/edit`.

**Pros:**
- More complex workflows possible
- Browser history navigation

**Cons:**
- Overkill for this use case
- Inconsistent with existing pattern
- Requires route changes

**Effort: High**

## Recommendation

**Approach 1: Mirror Carreras Pattern**

Rationale:
1. Backend already supports `PUT /pagos/<id>` with full field updates
2. API already has `updatePago()` function
3. The modal pattern in Carreras is proven and familiar
4. Lowest effort with highest consistency payoff

Implementation would:
1. Add Edit button in table (pencil icon, blue)
2. Add `modalMode` state ('create' | 'edit')
3. Add `selectedPago` state
4. Implement `openEditModal(pago)` function
5. Modify modal header/footer based on mode
6. Update `handleSubmit` to call `updatePago()` when editing

## Risks
- **None identified** — backend is ready, API is ready, only frontend UI work

## Ready for Proposal
**Yes.** Clear scope: add edit modal to Pagos.jsx following Carreras pattern. Orchestrator can proceed to `sdd-propose` or `sdd-spec`.