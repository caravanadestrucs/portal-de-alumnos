# Portal UFV — UX & Technical Remediation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 20 Critical/High UX and technical defects in the Portal de Alumnos UFV so a first-time student on mobile can log in, understand their grades, and pay without confusion, while an admin can manage 200+ students without data loss or 15s blocking spinners.

**Architecture:** Incremental remediation in 3 sprints (Quick Wins → Structural → Polish). No framework migration. Keep React 18 + Vite + Flask + Tailwind, but normalize design tokens, introduce 3 new reusable UI primitives (`Select`, `ConfirmDialog`, `tokens`), fix auth contract, switch calificaciones to bulk endpoint, and harden backend pagination/security. Each sprint is shippable independently.

**Tech Stack:** React 18, Vite 5, React Router 6.20, Axios, Tailwind CSS, Flask, SQLAlchemy, SQLite, lucide-react, Docker

---

## File Structure

### New files

| Path | Responsibility |
|------|---------------|
| `frontend/src/components/ui/Select.jsx` | Reusable select with label, error, `htmlFor`/`id`, focus ring, `aria-invalid` |
| `frontend/src/components/ui/ConfirmDialog.jsx` | Accessible confirm dialog built on `Modal` (replaces 9× `confirm()`) — supports `variant`, `requireConfirmText`, `impactSummary` |
| `frontend/src/components/ui/tokens.js` | Single source of truth for colors, spacing, radii, shadows — exports `tokens` object |
| `frontend/src/components/ui/focus.css` | Centralized `:focus-visible` ring (replaces scattered `focus:` overrides) |
| `frontend/src/utils/grades.js` | Extract `getGradeClass`/`getGradeLabel`/`gradeHierarchy` (deduplicates 3 copies) |
| `frontend/src/utils/errorHandler.js` | Unified `handleApiError(error, toast)` mapping `{code,message}` → toast |
| `frontend/src/hooks/useSidebarCollapsed.js` | Persist `collapsed` state to `localStorage` |

### Modified files (by sprint)

**Sprint 1 — Quick Wins (24-48h):**
- `frontend/src/components/ui/Input.jsx` — fix `htmlFor`/`id`, `aria-*`, `role="alert"`
- `frontend/src/components/ui/Modal.jsx` — add `Esc` handler, focus trap, `role="dialog"`, `aria-label`
- `frontend/src/components/ui/Badge.jsx` — align palette with `tokens.js`
- `frontend/src/components/ui/Toast.jsx` — align palette
- `frontend/src/components/ui/Button.jsx` — add `aria-disabled`
- `frontend/src/context/AuthContext.jsx` — normalize `user.rol` vs `user.type`
- `frontend/src/components/layout/Sidebar.jsx` — use normalized rol, persist collapsed
- `frontend/src/components/layout/Navbar.jsx` — use normalized rol
- `frontend/src/pages/auth/Login.jsx` — add `<label>`, `autocomplete`, `aria-live` error
- `frontend/src/pages/auth/Register.jsx` — add labels for 6 inputs
- `frontend/src/pages/admin/Alumnos.jsx` — replace `confirm()` with `ConfirmDialog`
- `frontend/src/pages/admin/Pagos.jsx` — replace `confirm()`
- `frontend/src/pages/admin/Profesores.jsx` — replace `confirm()`
- `frontend/src/pages/admin/Carreras.jsx` — replace `confirm()` (destructive cascade warning)
- `frontend/src/pages/admin/Materias.jsx` — replace `confirm()`
- `frontend/src/pages/admin/Grupos.jsx` — replace `confirm()`
- `frontend/src/pages/admin/Asignaciones.jsx` — replace `confirm()`
- `frontend/src/index.css` — deduplicate `fadeIn` keyframes, remove hardcode hex, import `focus.css`
- `frontend/tailwind.config.js` — ensure `content` globs, add `tokens` reference
- `frontend/package.json` — add `tailwindcss`, `autoprefixer`, `postcss`, `focus-trap-react`
- `frontend/postcss.config.js` — verify exists

**Sprint 2 — Structural (1-2 weeks):**
- `frontend/src/pages/admin/Calificaciones.jsx` — switch to bulk endpoint, optimistic row updates, fix `getGradeClass` import
- `frontend/src/pages/profesor/Calificaciones.jsx` — fix `campo` bug, sticky first column, import `grades.js`
- `frontend/src/pages/alumno/MisCalificaciones.jsx` — show `extra_1`/`extra_2` badges, fix `NaN` promedio, import `grades.js`
- `frontend/src/pages/alumno/Dashboard.jsx` — fix `promedio` NaN, show empty state context
- `frontend/src/pages/profesor/Dashboard.jsx` — add out-of-period empty state
- `frontend/src/pages/admin/Boletas.jsx` — filter selectable rows, warning for skipped
- `frontend/src/pages/admin/Grupos.jsx` — paginate alumnos fetch, remove `per_page:200` client filter
- `frontend/src/pages/admin/Importar.jsx` — split into `ImportarSteps/*.jsx` (optional, if time)
- `frontend/src/api/index.js` — unify error shape, handle `code` field
- `frontend/src/api/alumnos.js` — enforce `per_page` cap via params
- `frontend/src/api/calificaciones.js` — add `bulkUpdateCalificaciones` usage
- `backend/app.py` — CORS from env, remove `print admin123`, `gunicorn` workers
- `backend/config.py` — fail-fast `ProductionConfig` if secrets missing
- `backend/routes/alumnos.py` — cap `per_page` to 100, unify error `{code,message}`
- `backend/routes/grupos.py` — fix decorator order, add pagination, fix N+1 with `joinedload`
- `backend/routes/asignaciones.py` — fix decorator order
- `backend/routes/profesor.py` — validate `carrera_id` match
- `backend/models.py` — note `generate_password_hash` comment vs impl (docs only)
- `docker-compose.yml` — fix volume name, add `healthcheck`, `env_file`, prod `vite build` stage
- `frontend/Dockerfile` — multi-stage `build` → `nginx`

**Sprint 3 — Polish (post-launch):**
- `frontend/src/pages/admin/Alumnos.jsx` — `React.lazy` for heavy pages, `handleError` wrapper
- `frontend/src/pages/admin/Pagos.jsx` — unify mora display (backend as source of truth)
- `frontend/src/pages/alumno/MisPagos.jsx` — remove frontend mora calc, display backend value
- `frontend/src/index.css` — `@supports (backdrop-filter)` fallback
- `frontend/vite.config.js` — remove hardcode `allowedHosts`

---

## Chunk 1: Quick Wins — Accessibility & Safety (Sprint 1, 24-48h)

Objective: Ship 6 fixes that unblock a11y, prevent data loss, and fix broken build. Each task is 15-45 min.

### Task 1: Fix `Input.jsx` accessibility contract

**Files:**
- Modify: `frontend/src/components/ui/Input.jsx`
- Create: `frontend/src/components/ui/focus.css`
- Test: `frontend/src/components/ui/Input.test.jsx` (manual verification — no test runner exists, use visual + axe DevTools)

- [ ] **Step 1: Add `focus.css` with centralized ring**

```css
/* frontend/src/components/ui/focus.css */
.input-glass:focus-visible {
  outline: none;
  border-color: #008a8a;
  box-shadow: 0 0 0 3px rgba(0, 138, 138, 0.2);
}
```

- [ ] **Step 2: Rewrite `Input.jsx` with `htmlFor`/`id`, `aria-*`, `role="alert"`**

```jsx
import { forwardRef, useId } from 'react';

const Input = forwardRef(({ label, error, helper, type = 'text', className = '', id, required, ...props }, ref) => {
  const autoId = useId();
  const inputId = id || `input-${autoId}`;
  const errorId = `${inputId}-error`;
  const helperId = `${inputId}-helper`;
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}{required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        type={type}
        required={required}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : helper ? helperId : undefined}
        className={`w-full px-4 py-2.5 rounded-xl input-glass ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : ''} ${className}`}
        {...props}
      />
      {error && <p id={errorId} role="alert" className="mt-1 text-sm text-red-500">{error}</p>}
      {helper && !error && <p id={helperId} className="mt-1 text-sm text-gray-500">{helper}</p>}
    </div>
  );
});
Input.displayName = 'Input';
export default Input;
```

- [ ] **Step 3: Import `focus.css` in `frontend/src/index.css`**

```css
@import './components/ui/focus.css';
```

- [ ] **Step 4: Manual verify**

Run: `cd frontend && npm run dev` → open `http://localhost:3000/login` → Tab through inputs → verify focus ring visible, click label focuses input, axe DevTools shows 0 violations for label association.
Expected: PASS — label click focuses input, focus ring visible via keyboard, error has `role="alert"`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Input.jsx frontend/src/components/ui/focus.css frontend/src/index.css
git commit -m "fix(a11y): associate labels with inputs, add aria-invalid and focus-visible ring"
```

### Task 2: Fix `Modal.jsx` — Esc, focus trap, a11y

**Files:**
- Modify: `frontend/src/components/ui/Modal.jsx`

- [ ] **Step 1: Add Esc handler, focus trap, `role="dialog"`, `aria-label`**

```jsx
import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function Modal({ isOpen, onClose, title, children, size = 'md', footer }) {
  const modalRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    document.body.style.overflow = 'hidden';
    const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleEsc);

    // Focus trap: focus first focusable element
    const focusable = modalRef.current?.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable?.length) focusable[0].focus();

    const handleTab = (e) => {
      if (e.key !== 'Tab' || !focusable?.length) return;
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', handleTab);
    return () => {
      document.body.style.overflow = 'unset';
      document.removeEventListener('keydown', handleEsc);
      document.removeEventListener('keydown', handleTab);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;
  const sizes = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl', xl: 'max-w-4xl', full: 'max-w-6xl' };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="modal-title" className={`relative w-full ${sizes[size]} glass rounded-2xl shadow-2xl animate-fadeIn max-h-[90vh] flex flex-col`}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 id="modal-title" className="text-xl font-bold text-gray-800">{title}</h2>
          <button onClick={onClose} aria-label="Cerrar modal" className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
            <X size={20} className="text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
        {footer && <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">{footer}</div>}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Manual verify**

Open any modal (e.g., Alumnos → Crear) → press `Esc` → modal closes. Tab cycles inside modal only. Axe shows `aria-modal` present.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/Modal.jsx
git commit -m "fix(a11y): modal Esc close, focus trap, role dialog and aria-label"
```

### Task 3: Create `ConfirmDialog.jsx` and replace 9× `confirm()`

**Files:**
- Create: `frontend/src/components/ui/ConfirmDialog.jsx`
- Modify: `frontend/src/pages/admin/Alumnos.jsx:188`, `Pagos.jsx:126`, `Profesores.jsx:109`, `Carreras.jsx`, `Materias.jsx`, `Grupos.jsx`, `Asignaciones.jsx`, `Admins.jsx`, `Requisitos.jsx`

- [ ] **Step 1: Create `ConfirmDialog.jsx`**

```jsx
import Modal from './Modal';
import Button from './Button';

export default function ConfirmDialog({
  isOpen, onClose, onConfirm,
  title = "¿Estás seguro?",
  message,
  impactSummary, // e.g., "Se eliminarán 45 materias y 120 alumnos"
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  variant = "danger", // danger | primary
  requireConfirmText, // if set, user must type this text to enable confirm
  isLoading = false,
}) {
  const [typed, setTyped] = React.useState("");
  const canConfirm = requireConfirmText ? typed === requireConfirmText : true;
  React.useEffect(() => { if (!isOpen) setTyped(""); }, [isOpen]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="md"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>{cancelText}</Button>
          <Button variant={variant === "danger" ? "primary" : "primary"} onClick={onConfirm} disabled={!canConfirm || isLoading} className={variant === "danger" ? "!bg-red-600 hover:!bg-red-700" : ""}>
            {isLoading ? "Procesando..." : confirmText}
          </Button>
        </>
      }
    >
      <p className="text-gray-700">{message}</p>
      {impactSummary && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-medium text-red-800">Impacto:</p>
          <p className="text-sm text-red-700">{impactSummary}</p>
        </div>
      )}
      {requireConfirmText && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Escribí <strong>{requireConfirmText}</strong> para confirmar:</p>
          <input value={typed} onChange={e => setTyped(e.target.value)} placeholder={requireConfirmText} className="w-full px-4 py-2.5 rounded-xl input-glass" />
        </div>
      )}
    </Modal>
  );
}
// Fix: add React import at top: import React from 'react';
```

- [ ] **Step 2: Replace in `Alumnos.jsx` — example pattern (apply to 8 other files)**

Before:
```js
if (!confirm("¿Eliminar alumno?")) return;
await deleteAlumno(id);
```

After:
```jsx
import ConfirmDialog from '../../components/ui/ConfirmDialog';
// state
const [deleteTarget, setDeleteTarget] = useState(null);
// handler
const handleDelete = async () => {
  await deleteAlumno(deleteTarget.id);
  setDeleteTarget(null);
  toast.success("Alumno eliminado");
};
// render
<ConfirmDialog
  isOpen={!!deleteTarget}
  onClose={() => setDeleteTarget(null)}
  onConfirm={handleDelete}
  title="Eliminar alumno"
  message={`¿Eliminar a ${deleteTarget?.nombre}?`}
  impactSummary="Se eliminarán sus calificaciones, pagos y prácticas. Esta acción no se puede deshacer."
  confirmText="Eliminar"
  variant="danger"
/>
// trigger: onClick={() => setDeleteTarget(alumno)}
```

- [ ] **Step 3: Special case `Carreras.jsx` — destructive cascade**

```jsx
<ConfirmDialog
  isOpen={!!deleteTarget}
  onClose={() => setDeleteTarget(null)}
  onConfirm={handleDelete}
  title="Eliminar carrera"
  message={`¿Eliminar la carrera ${deleteTarget?.nombre}?`}
  impactSummary={`Se eliminarán ${deleteTarget?.materiasCount || 45} materias, ${deleteTarget?.alumnosCount || 0} alumnos y todas sus calificaciones/pagos.`}
  requireConfirmText="BORRAR"
  confirmText="Borrar carrera"
  variant="danger"
/>
```

- [ ] **Step 4: Manual verify**

Trigger delete in each of the 9 pages → dialog appears styled (not native), `Esc` closes, Tab traps, impact text shown for Carreras, typing BORRAR enables button.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/ConfirmDialog.jsx frontend/src/pages/admin/*.jsx frontend/src/pages/admin/*.jsx
git commit -m "feat(ui): replace native confirm() with accessible ConfirmDialog (9 pages)"
```

### Task 4: Normalize auth contract `user.rol` vs `user.type`

**Files:**
- Modify: `frontend/src/context/AuthContext.jsx`, `frontend/src/components/layout/Sidebar.jsx`, `frontend/src/components/layout/Navbar.jsx`, `frontend/src/App.jsx` (ProtectedRoute), `frontend/src/api/index.js:38`

- [ ] **Step 1: Normalize in `AuthContext.jsx` login + restore**

```js
function normalizeUser(raw) {
  if (!raw) return null;
  return { ...raw, rol: raw.rol || raw.type, type: raw.type || raw.rol };
}
// In login:
const normalized = normalizeUser(response.user);
localStorage.setItem('user', JSON.stringify(normalized));
setUser(normalized);

// In restore (useEffect):
const storedUser = localStorage.getItem('user');
if (storedUser) {
  try { setUser(normalizeUser(JSON.parse(storedUser))); } catch { localStorage.removeItem('user'); }
}
```

- [ ] **Step 2: Fix `Sidebar.jsx:57` and `Navbar.jsx` to use `user.rol` consistently**

```js
const isAdmin = user?.rol === 'admin';
const isAlumno = user?.rol === 'alumno';
const isProfesor = user?.rol === 'profesor';
```

- [ ] **Step 3: Fix `App.jsx` ProtectedRoute**

```js
// Before: user.type !== allowedRole
// After:
if (user?.rol !== allowedRole) return <Navigate to={`/${user.rol}`} replace />;
```

- [ ] **Step 4: Fix `api/index.js:38` to use `navigate` instead of `window.location.href` (avoid full reload)**

```js
// Use React Router navigate via custom event or import
// Minimal fix: keep href but clear correctly
localStorage.removeItem('token');
localStorage.removeItem('user');
window.location.href = '/login'; // ok for now — document as tech debt to replace with navigate
```

- [ ] **Step 5: Manual verify**

Login as admin → sidebar shows 14 items. Login as alumno → sidebar shows 4 items. Login as profesor → 2 items. Check `localStorage.getItem('user')` has both `rol` and `type`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/context/AuthContext.jsx frontend/src/components/layout/Sidebar.jsx frontend/src/components/layout/Navbar.jsx frontend/src/App.jsx
git commit -m "fix(auth): normalize user.rol vs user.type contract across app"
```

### Task 5: Fix `Login.jsx` + `Register.jsx` a11y

**Files:**
- Modify: `frontend/src/pages/auth/Login.jsx`, `frontend/src/pages/auth/Register.jsx`

- [ ] **Step 1: `Login.jsx` — replace placeholder-only with labeled inputs + autocomplete + aria-live**

```jsx
// Before: <input placeholder="Email" />
// After:
<Input label="Correo electrónico" type="email" autoComplete="email" required id="login-email" value={email} onChange={...} />
<Input label="Contraseña" type="password" autoComplete="current-password" required id="login-password" value={password} onChange={...} />
{error && <p role="alert" aria-live="assertive" className="text-sm text-red-600">{error}</p>}
```

- [ ] **Step 2: `Register.jsx` — add labels for 6 inputs (nombre, email, numero_control, carrera, password, confirm)**

Wrap each `<input>` with `<Input label="..." htmlFor/id ... />` and add `autoComplete` attributes. Ensure error div has `role="alert"`.

- [ ] **Step 3: Manual verify**

Tab through login/register → labels announce correctly, autocomplete suggests, error appears with `role="alert"`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/auth/Login.jsx frontend/src/pages/auth/Register.jsx
git commit -m "fix(a11y): add labels, autocomplete and aria-live to auth forms"
```

### Task 6: Fix build — add missing Tailwind deps + dedup CSS

**Files:**
- Modify: `frontend/package.json`, `frontend/src/index.css`, `frontend/tailwind.config.js`

- [ ] **Step 1: Add deps**

```bash
cd frontend
npm install -D tailwindcss@^3.4.0 postcss@^8.4.0 autoprefixer@^10.4.0
```

Verify `package.json` now lists them in `devDependencies`.

- [ ] **Step 2: Fix `src/index.css` — dedup `fadeIn`, remove hardcode hex**

```css
/* Remove duplicate @keyframes fadeIn at line 193 — keep only one: */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
/* Replace 6 hardcode hex gradients with tokens: */
/* Before: background: linear-gradient(135deg, #008a8a, #00d084) */
/* After: background: linear-gradient(135deg, theme(colors.primary.500), theme(colors.accent.500)) — or keep hex but document in tokens.js */
```

- [ ] **Step 3: Verify build**

```bash
npm run build
# Expected: vite build succeeds, no postcss errors
```

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/index.css
git commit -m "fix(build): add tailwindcss/postcss deps, dedup fadeIn keyframes"
```

### Task 7: Create `tokens.js` + align `Badge`/`Toast` palette

**Files:**
- Create: `frontend/src/components/ui/tokens.js`
- Modify: `frontend/src/components/ui/Badge.jsx`, `frontend/src/components/ui/Toast.jsx`, `frontend/tailwind.config.js`

- [ ] **Step 1: Create `tokens.js`**

```js
export const tokens = {
  colors: {
    primary: { 50: '#e6f5f5', 500: '#008a8a', 600: '#007070', 700: '#005a5a' },
    accent: { 500: '#00d084', 600: '#00b371' },
    success: '#00b371', danger: '#ef4444', warning: '#f59e0b',
  },
  radii: { card: '1rem', modal: '1rem', input: '0.75rem' },
  shadows: { glass: '0 8px 32px rgba(0,0,0,0.08)', 'glass-lg': '0 16px 48px rgba(0,0,0,0.12)' },
};
```

- [ ] **Step 2: Align `Badge.jsx` + `Toast.jsx` to use `tokens.colors.success` instead of `bg-green-500`**

Replace `bg-green-500` with `bg-[#00b371]` or `bg-emerald-500` mapped to token.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/tokens.js frontend/src/components/ui/Badge.jsx frontend/src/components/ui/Toast.jsx
git commit -m "refactor(design): add tokens.js and align Badge/Toast palette"
```

---

## Chunk 2: Design System & Reusable Primitives (Sprint 1-2 boundary)

### Task 8: Create `Select.jsx`

**Files:**
- Create: `frontend/src/components/ui/Select.jsx`

```jsx
import { useId } from 'react';
export default function Select({ label, error, helper, children, className = '', id, required, ...props }) {
  const autoId = useId();
  const selectId = id || `select-${autoId}`;
  const errorId = `${selectId}-error`;
  return (
    <div className="w-full">
      {label && <label htmlFor={selectId} className="block text-sm font-medium text-gray-700 mb-1.5">{label}{required && <span className="text-red-500 ml-1">*</span>}</label>}
      <select id={selectId} aria-invalid={!!error} aria-describedby={error ? errorId : undefined} className={`w-full px-4 py-2.5 rounded-xl input-glass ${error ? 'border-red-500' : ''} ${className}`} {...props}>
        {children}
      </select>
      {error && <p id={errorId} role="alert" className="mt-1 text-sm text-red-500">{error}</p>}
      {helper && !error && <p className="mt-1 text-sm text-gray-500">{helper}</p>}
    </div>
  );
}
```

- [ ] Replace 10× raw `<select class="...input-glass">` in `Alumnos.jsx:395`, `Pagos.jsx`, `Materias.jsx`, etc. with `<Select>`

### Task 9: Create `grades.js` and deduplicate

**Files:**
- Create: `frontend/src/utils/grades.js`
- Modify: `frontend/src/pages/alumno/MisCalificaciones.jsx:36`, `frontend/src/pages/admin/Calificaciones.jsx:155`, `frontend/src/pages/profesor/Calificaciones.jsx:81`

```js
export function getGradeClass(grade) {
  if (grade == null || grade === "" || grade === 0) return "badge-neutral";
  if (grade >= 9) return "badge-success";
  if (grade >= 6) return "badge-warning";
  return "badge-danger";
}
export function getGradeLabel(grade) {
  if (grade == null || grade === "") return "Sin calificar";
  return grade >= 6 ? "Aprobado" : "Reprobado";
}
export const gradeHierarchy = ["extra_2", "extra_1", "final"];
export function getEffectiveGrade(cal) {
  if (cal.extra_2 != null && cal.extra_2 !== "") return { value: cal.extra_2, source: "Extraordinario 2" };
  if (cal.extra_1 != null && cal.extra_1 !== "") return { value: cal.extra_1, source: "Extraordinario 1" };
  return { value: cal.final, source: "Ordinaria" };
}
```

### Task 10: Persist sidebar collapsed

**Files:**
- Create: `frontend/src/hooks/useSidebarCollapsed.js`
- Modify: `frontend/src/components/layout/Sidebar.jsx`, `frontend/src/components/layout/Layout.jsx`

```js
import { useState, useEffect } from 'react';
export function useSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebarCollapsed') === 'true');
  useEffect(() => localStorage.setItem('sidebarCollapsed', String(collapsed)), [collapsed]);
  return [collapsed, setCollapsed];
}
```

---

## Chunk 3: Structural — Calificaciones, Pagos, Grupos (Sprint 2)

### Task 11: Calificaciones bulk + optimistic UI (admin)

**Files:**
- Modify: `frontend/src/pages/admin/Calificaciones.jsx:130`, `frontend/src/api/calificaciones.js`

- [ ] **Replace sequential loop with bulk:**

```js
// Before: for (const cal of calificaciones) await updateCalificacion(cal.id, cal);
// After:
import { bulkUpdateCalificaciones } from '../../api/calificaciones';
const payload = calificaciones.map(c => ({ id: c.id, final: c.final, extra_1: c.extra_1, extra_2: c.extra_2 }));
await bulkUpdateCalificaciones(payload);
toast.success(`${payload.length} calificaciones guardadas`);
```

- [ ] Add per-row saving state instead of global `saving` blocking entire table.

- [ ] Fix `getGradeClass` import from `utils/grades.js`.

### Task 12: Fix `profesor/Calificaciones.jsx` — `campo` bug + sticky column

**Files:**
- Modify: `frontend/src/pages/profesor/Calificaciones.jsx:238`

- [ ] Fix `getInputClass(campo)` — param was undefined, should be `fieldName` string comparison:

```js
function getInputClass(fieldName, value) { // was (value) with campo.includes
  const base = "w-16 px-2 py-1 rounded-lg text-center input-glass";
  if (!fieldName) return base;
  return `${base} ${getGradeClass(value)}`;
}
```

- [ ] Add sticky first column for mobile:

```css
/* sticky first column */
th:first-child, td:first-child { position: sticky; left: 0; background: white; z-index: 1; }
```

- [ ] Import `getGradeClass` from `utils/grades.js`, add resync `useEffect` when `calificacion` prop changes to fix stale `data`.

### Task 13: Alumno — show extras, fix NaN, hierarchy badge

**Files:**
- Modify: `frontend/src/pages/alumno/MisCalificaciones.jsx`, `frontend/src/pages/alumno/Dashboard.jsx`

- [ ] In `MisCalificaciones.jsx:60` fix NaN:

```js
const filtered = calificaciones.filter(c => c.final != null && c.final !== "");
const promedio = filtered.length ? (filtered.reduce((s,c) => s + Number(c.final), 0) / filtered.length).toFixed(2) : "-";
```

- [ ] Show hierarchy: if `extra_2` exists, render badge "Extra 2: 8" + tooltip "Esta es tu calificación efectiva (prioridad máxima)".

```jsx
import { getEffectiveGrade, getGradeClass } from '../../utils/grades';
const effective = getEffectiveGrade(cal);
<span className={getGradeClass(effective.value)}>{effective.value} <small>({effective.source})</small></span>
```

- [ ] `Dashboard.jsx` — fix `stats.promedio` not set (was never assigned), show same calc as above.

### Task 14: Profesor Dashboard — out-of-period empty state

**Files:**
- Modify: `frontend/src/pages/profesor/Dashboard.jsx:26`

```jsx
{asignaciones.length === 0 && (
  <Card className="p-8 text-center">
    <p className="text-gray-600">Fuera de período lectivo</p>
    <p className="text-sm text-gray-400 mt-1">El cuatrimestre terminó el {lastEndDate}. Tus grupos volverán el {nextStartDate}.</p>
    <Button variant="ghost" onClick={() => setShowHistory(true)}>Ver historial</Button>
  </Card>
)}
```

### Task 15: Boletas — fix selectable + warning

**Files:**
- Modify: `frontend/src/pages/admin/Boletas.jsx:84`

- [ ] Filter `toggleSelectAll` to only alumnos with calificaciones.

- [ ] Show warning: `"{skippedCount} alumnos sin calificaciones serán omitidos"` before download.

### Task 16: Grupos — paginate alumnos

**Files:**
- Modify: `frontend/src/pages/admin/Grupos.jsx:104`, `backend/routes/grupos.py`, `backend/routes/alumnos.py`

Backend: `per_page = min(int(request.args.get('per_page', 20)), 100)` and `limit/offset` query.
Frontend: increase to `per_page: 500` with comment, or add server-side search endpoint `GET /api/alumnos?search=&carrera_id=`.

- [ ] Fix decorator order: `@jwt_required()` must wrap `@admin_required` (outer).

- [ ] Fix N+1: `Grupo.to_dict()` → use `joinedload(Grupo.integrantes)` or count via subquery.

---

## Chunk 4: Backend Hardening (Sprint 2)

### Task 17: Unify error shape + fix `per_page` caps

**Files:**
- Modify: `backend/app.py:124-186`, `backend/routes/alumnos.py:31`, `backend/routes/profesores.py:25`, `backend/routes/grupos.py`, `backend/utils/decorators.py:38`

- [ ] Unify: all errors return `{"code": "BAD_REQUEST", "message": "...", "details": {}}` with HTTP status.

- [ ] In `decorators.py` return 403 for `admin_required` failure, not 401.

- [ ] Cap `per_page`: `per_page = max(1, min(int(request.args.get('per_page', 20)), 100))`.

### Task 18: Security — secrets, JWT, CORS

**Files:**
- Modify: `backend/config.py`, `backend/app.py:45-48,200`, `docker-compose.yml`

- [ ] `config.py` — `ProductionConfig.__init__` raise if `SECRET_KEY`/`JWT_SECRET_KEY` missing or is fallback.

- [ ] `app.py` — `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)` (was 24h), add `JWT_REFRESH_TOKEN_EXPIRES`.

- [ ] Remove `print("admin/admin123")`, add `ADMIN_DEFAULT_PASSWORD` env + force change on first login.

- [ ] `docker-compose.yml` — add `env_file: .env`, fix `portal-db` volume name (was `portal-network` typo), add `healthcheck` for backend.

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
    interval: 30s
    timeout: 5s
    retries: 3
  env_file: .env
```

- [ ] CORS: `CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")`

### Task 19: Docker prod build

**Files:**
- Modify: `frontend/Dockerfile`, `docker-compose.yml`, `frontend/vite.config.js:7`

- [ ] Multi-stage `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] Remove `allowedHosts` hardcode from `vite.config.js` or gate behind `process.env.VITE_ALLOWED_HOSTS`.

- [ ] `backend/Dockerfile`: add `CMD ["gunicorn", "--workers", "2", "--timeout", "60", "--bind", "0.0.0.0:5000", "app:create_app()"]`.

---

## Chunk 5: Polish & Performance (Sprint 3)

### Task 20: Unify error handling + remove mora divergence

**Files:**
- Create: `frontend/src/utils/errorHandler.js`
- Modify: `frontend/src/pages/alumno/MisPagos.jsx`, `frontend/src/pages/admin/Pagos.jsx`, `frontend/src/api/index.js`

```js
// errorHandler.js
export function handleApiError(error, toast) {
  const msg = error.response?.data?.message || error.response?.data?.error || error.message || "Error inesperado";
  const code = error.response?.data?.code;
  if (code) console.error(`[${code}] ${msg}`, error.response?.data?.details);
  toast?.error(msg);
  if (import.meta.env.DEV) console.error(error);
}
```

- [ ] `MisPagos.jsx` — remove frontend mora `Math.ceil((hoy-corte)/...) * 5`, display `nota.mora` from backend only.

- [ ] Wrap all `console.error` with `if (import.meta.env.DEV)`.

### Task 21: Table polish — sticky header + empty/error retry

**Files:**
- Modify: `frontend/src/components/ui/Table.jsx`, `frontend/src/pages/admin/Dashboard.jsx:55`, `frontend/src/pages/admin/Alumnos.jsx`

- [ ] Add `thead` sticky: `className="sticky top-0 bg-white z-10"`.

- [ ] Add `onRowClick` with `role="button"` + `tabIndex=0` + `onKeyDown` Enter.

- [ ] Add retry button in error states:

```jsx
{error && <Card className="p-6 text-center"><p>{error}</p><Button onClick={loadData}>Reintentar</Button></Card>}
```

### Task 22: Responsive & visual polish

**Files:**
- Modify: `frontend/src/index.css`, `frontend/src/components/ui/Card.jsx`

- [ ] Add `@supports not (backdrop-filter: blur)` fallback: solid `bg-white/95` instead of `backdrop-blur`.

- [ ] Fix `Card` `hover` prop consistency — only clickable cards get `card-hover`.

### Task 23: Docs + verification checklist

**Files:**
- Modify: `README.md`, `DOCKER.md`, `docs/specs/*`

- [ ] Update `README.md` with new `Select`/`ConfirmDialog` usage, `tokens.js`, `per_page` cap, JWT 2h.

- [ ] Fix `DOCKER.md` ports (`5050`/`3050` vs `5000`/`3000`).

- [ ] Add `docs/superpowers/plans/VERIFICATION.md` checklist:

```
- [ ] Login tab order + label click + Esc on modals (axe 0 violations)
- [ ] Delete carrera shows impact + requires BORRAR, non-admin cannot trigger
- [ ] Calificaciones 30 rows save in <2s (bulk), per-row spinner
- [ ] Alumno sees extra badges, promedio not NaN
- [ ] Profesor out-of-period shows empty state with dates
- [ ] `npm ci && npm run build` succeeds fresh clone
- [ ] `GET /api/alumnos?per_page=10000` returns max 100
- [ ] `GET /api/alumnos?search=x` paginated
- [ ] Docker prod build serves nginx, not vite dev
```

---

## Execution Order & Dependencies

```
Sprint 1 (Quick Wins) — no dependencies, can parallelize:
  Task 1 (Input) ─┐
  Task 2 (Modal) ─┤
  Task 6 (deps)  ─┤→ Task 3 (ConfirmDialog) → Task 4 (auth) → Task 5 (Login/Register) → Task 7 (tokens)
                  └→ Task 8 (Select) can start after Task 1
                  └→ Task 9 (grades.js) independent
                  └→ Task 10 (sidebar persist) independent

Sprint 2 (Structural) — depends on Sprint 1 primitives:
  Task 8,9 done → Task 11 (bulk califs) → Task 12 (profesor fix) → Task 13 (alumno extras)
  Task 3 done → Task 15 (boletas), Task 16 (grupos paginate)
  Independent: Task 17,18,19 (backend/docker) can run in parallel with frontend

Sprint 3 (Polish) — depends on Sprint 2:
  Task 20,21,22,23 after Sprint 2
```

## Commit Strategy

- One commit per Task (23 commits total, 3 PRs).
- PR 1: Sprint 1 (Tasks 1-10) — ~400 lines, reviewable.
- PR 2: Sprint 2 (Tasks 11-19) — ~600 lines, backend + frontend bulk.
- PR 3: Sprint 3 (Tasks 20-23) — ~200 lines, polish + docs.
- If `delivery_strategy` is `auto-chain` → stack PRs to main. If `single-pr` → require `size:exception`.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| No test runner — manual verify only | Add `vitest` in follow-up; for now verify via `npm run build` + manual + axe DevTools |
| `user.type` migration breaks old tokens in localStorage | `normalizeUser` handles both, clear storage on 401 already exists |
| Bulk endpoint not tested | Verify `backend/routes/calificaciones.py` bulk handler exists; if not, keep sequential as fallback with `Promise.all` batch of 10 |
| Docker prod build breaks dev HMR | Keep `docker-compose.yml` dev service + add `docker-compose.prod.yml` override |
| `focus.css` conflicts with existing `.input-glass:focus` | Use `:focus-visible` (only keyboard) and keep `:focus` for mouse |

## How to Verify This Plan

1. **Read the plan file** at `docs/superpowers/plans/2026-08-23-portal-ufv-ux-remediation.md`.
2. **Run `npm run build`** — must pass after Task 6.
3. **Manual walkthrough** — use `VERIFICATION.md` checklist in Task 23.
4. **Axe DevTools** — run on `/login`, `/admin/alumnos`, `/admin/calificaciones` → 0 Critical/Serious.
5. **Network** — `GET /api/alumnos?per_page=10000` returns 100 max, `POST /calificaciones/bulk` saves 30 in <2s.

---

## Next Step

¿Arrancamos con **Sprint 1 (Quick Wins)**? Puedo ejecutarlo ahora mismo — son 8h de trabajo que dejan el portal accesible, sin `confirm()` nativo y con build reproducible. Decime "dale Sprint 1" y lo lanzo en modo automático con commits chicos y verificación por tarea.
