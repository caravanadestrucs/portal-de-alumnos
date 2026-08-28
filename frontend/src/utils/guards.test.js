import { describe, it, expect } from 'vitest';

// Pure guard helpers to mirror ProtectedRoute logic
// Will be imported from App.jsx or a utils file after implementation
// For RED phase, we test helpers that do not exist yet

import { canAccessAdminRoute, requiresGeneralAdmin } from './guards';

describe('guards sede RBAC', () => {
  it('general_admin puede acceder a /admin/sedes', () => {
    const user = { rol: 'admin', role: 'general_admin', sede_id: null };
    expect(canAccessAdminRoute(user, '/admin/sedes')).toBe(true);
    expect(requiresGeneralAdmin('/admin/sedes')).toBe(true);
  });

  it('sede_admin NO puede acceder a /admin/sedes (403)', () => {
    const user = { rol: 'admin', role: 'sede_admin', sede_id: 1 };
    expect(canAccessAdminRoute(user, '/admin/sedes')).toBe(false);
  });

  it('sede_admin puede acceder a /admin/wiki', () => {
    const user = { rol: 'admin', role: 'sede_admin', sede_id: 1 };
    expect(canAccessAdminRoute(user, '/admin/wiki')).toBe(true);
    expect(requiresGeneralAdmin('/admin/wiki')).toBe(false);
  });

  it('alumno NO puede acceder a admin routes', () => {
    const user = { rol: 'alumno' };
    expect(canAccessAdminRoute(user, '/admin/alumnos')).toBe(false);
    expect(canAccessAdminRoute(user, '/admin/sedes')).toBe(false);
  });

  it('general_admin puede acceder a todas las rutas admin', () => {
    const user = { rol: 'admin', role: 'general_admin', sede_id: null };
    expect(canAccessAdminRoute(user, '/admin/alumnos')).toBe(true);
    expect(canAccessAdminRoute(user, '/admin/wiki')).toBe(true);
    expect(canAccessAdminRoute(user, '/admin/sedes')).toBe(true);
  });

  it('sede_admin puede acceder a /admin/alumnos (scoped)', () => {
    const user = { rol: 'admin', role: 'sede_admin', sede_id: 1 };
    expect(canAccessAdminRoute(user, '/admin/alumnos')).toBe(true);
  });
});
