import { describe, it, expect } from 'vitest';

// Pure helpers extracted to mirror AuthContext.jsx implementation
// We will import normalizeUser and derived helpers from AuthContext after implementation
// For RED phase, these imports will fail (file missing exports), proving TDD

import { normalizeUser, getSedeId, isGeneralAdmin, isSedeAdmin, getRole } from './AuthContext.jsx';

describe('AuthContext sede RBAC', () => {
  it('normalizeUser preserves role and sede_id from backend (general_admin NULL)', () => {
    const raw = { id: 1, type: 'admin', role: 'general_admin', sede_id: null, sede: null, email: 'g@fv.edu' };
    const u = normalizeUser(raw);
    expect(u.role).toBe('general_admin');
    expect(u.sede_id).toBeNull();
    expect(u.sedeId).toBeNull();
    expect(u.rol).toBe('admin');
    expect(u.type).toBe('admin');
  });

  it('normalizeUser maps sede_admin with sede_id and sede object, dual type/user_type', () => {
    const raw = { id: 2, type: 'admin', user_type: 'admin', role: 'sede_admin', sede_id: 1, sede: { id: 1, codigo: 'TEO' }, email: 's@fv.edu' };
    const u = normalizeUser(raw);
    expect(u.role).toBe('sede_admin');
    expect(u.sede_id).toBe(1);
    expect(u.sedeId).toBe(1);
    expect(u.sede.codigo).toBe('TEO');
    expect(u.rol).toBe('admin');
  });

  it('normalizeUser handles legacy without role (defaults)', () => {
    const u = normalizeUser({ id: 3, rol: 'admin', email: 'legacy@fv.edu' });
    // legacy admin without role should still have rol admin but role undefined
    expect(u.rol).toBe('admin');
    expect(u.role).toBeUndefined();
    expect(u.sede_id).toBeNull();
  });

  it('normalizeUser handles alumno with type dual and preserves sede null', () => {
    const u = normalizeUser({ id: 10, rol: 'alumno', type: 'alumno' });
    expect(u.rol).toBe('alumno');
    expect(u.type).toBe('alumno');
    expect(u.role).toBeUndefined();
  });

  it('isGeneralAdmin true only for general_admin role', () => {
    expect(isGeneralAdmin({ role: 'general_admin' })).toBe(true);
    expect(isGeneralAdmin({ role: 'sede_admin' })).toBe(false);
    expect(isGeneralAdmin({ rol: 'admin' })).toBe(false);
    expect(isGeneralAdmin(null)).toBe(false);
  });

  it('isSedeAdmin true only for sede_admin', () => {
    expect(isSedeAdmin({ role: 'sede_admin' })).toBe(true);
    expect(isSedeAdmin({ role: 'general_admin' })).toBe(false);
    expect(isSedeAdmin(null)).toBe(false);
  });

  it('getSedeId returns sede_id or sedeId or sede.id or null with normalization', () => {
    expect(getSedeId({ sede_id: 1 })).toBe(1);
    expect(getSedeId({ sedeId: 2 })).toBe(2);
    expect(getSedeId({ sede: { id: 3 } })).toBe(3);
    expect(getSedeId({ sede_id: null, sede: null })).toBeNull();
    expect(getSedeId(null)).toBeNull();
    expect(getSedeId({})).toBeNull();
  });

  it('getRole returns role or null', () => {
    expect(getRole({ role: 'general_admin' })).toBe('general_admin');
    expect(getRole({ role: 'sede_admin' })).toBe('sede_admin');
    expect(getRole({})).toBeNull();
    expect(getRole(null)).toBeNull();
  });

  it('normalizeUser dual sede_id and sedeId both present gives precedence to sede_id', () => {
    const u = normalizeUser({ id: 5, type: 'admin', role: 'sede_admin', sede_id: 1, sedeId: 2 });
    expect(u.sede_id).toBe(1);
    expect(u.sedeId).toBe(1);
  });
});
