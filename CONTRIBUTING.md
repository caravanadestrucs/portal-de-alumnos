# Contributing — Portal de Alumnos

## Comandos de test

### Backend (Flask)
```bash
cd backend
python -m pytest -v --tb=short          # todos los tests
python -m pytest tests/test_send_credentials.py -v
python -m pytest --cov --cov-report=term-missing
```

### Frontend (Vite + Vitest + Playwright)
```bash
cd frontend
npm run test              # vitest run (unit + integration)
npm run test:watch        # watch mode
npm run test:coverage     # con coverage
npm run e2e               # Playwright e2e
npx playwright test --ui  # UI mode
```

### Verificación completa (S3-ready)
```bash
# desde raíz
npm run test --prefix frontend
python -m pytest backend/tests -v
npm run build --prefix frontend   # vite build debe pasar sin errores
```

## Flujo de trabajo
- Stack: Flask + React (Vite 5, Tailwind 3.4, SQLAlchemy)
- Branch: stacked PRs `portal-20-mejoras-bulk-email` → S1 bulk, S2 onboarding+graph, S3 restantes
- Commits: `feat(search):`, `feat(empty):`, `feat(validation):`, `chore(dx):` por work unit
- PR límite: <800 líneas. Si supera, usar `auto-chain stacked-to-main`.

## Estructura de tests (strict TDD)
- Para cada feature: RED (test que falla) → GREEN (mínimo código) → TRIANGULATE → REFACTOR
- Capas: unit (vitest/pytest) > integration (@testing-library) > e2e (Playwright)
- Archivos: `*.test.jsx`, `*.test.js` colocados junto al componente.

## Notas S3
- `CORS_ORIGINS` env ya configurado en `backend/config.py`
- `joinedload` N+1 fix en `backend/routes/grupos.py`
- `Select` migración: usar `frontend/src/components/ui/Select.jsx` en lugar de `<select class="input-glass">`
- `axe-core` placeholder en `frontend/src/utils/a11y.js` — TODO instalar `axe-core` real.
- Import/perf: `useImport` stub + `ImportSteps` placeholder + `React.lazy` para `Importar`/`Boletas` + comentario `tanstack-virtual`.
