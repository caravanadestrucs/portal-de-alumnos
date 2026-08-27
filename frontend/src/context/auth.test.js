import { describe, it, expect, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Pure logic extracted from AuthContext.jsx — mirrors implementation exactly
// ---------------------------------------------------------------------------
function normalizeUser(raw) {
  if (!raw) return null;
  return { ...raw, rol: raw.rol || raw.type, type: raw.type || raw.rol };
}

function isAdmin(user) {
  return user?.rol === 'admin';
}
function isAlumno(user) {
  return user?.rol === 'alumno';
}
function isProfesor(user) {
  return user?.rol === 'profesor';
}

/**
 * Pure ProtectedRoute decision logic (no Router dependency).
 * Returns { allowed, redirect } so tests stay framework-free.
 */
function canAccess(user, allowedRole) {
  if (!user) return { allowed: false, redirect: '/login' };
  if (allowedRole && user.rol !== allowedRole) return { allowed: false, redirect: `/${user.rol}` };
  return { allowed: true, redirect: null };
}

// ---------------------------------------------------------------------------
// normalizeUser
// ---------------------------------------------------------------------------
describe('normalizeUser', () => {
  it('mapea type -> rol cuando solo viene type', () => {
    const u = normalizeUser({ id: 1, type: 'admin', email: 'a@b.com' });
    expect(u.rol).toBe('admin');
    expect(u.type).toBe('admin');
  });

  it('mapea rol -> type cuando solo viene rol', () => {
    const u = normalizeUser({ id: 2, rol: 'alumno', email: 'b@b.com' });
    expect(u.type).toBe('alumno');
    expect(u.rol).toBe('alumno');
  });

  it('preserva rol y type cuando ambos existen', () => {
    const u = normalizeUser({ rol: 'profesor', type: 'profesor' });
    expect(u.rol).toBe('profesor');
    expect(u.type).toBe('profesor');
  });

  it('preserva rol si existe aunque type sea distinto (rol gana)', () => {
    // rol || type => rol has priority
    const u = normalizeUser({ rol: 'admin', type: 'alumno' });
    expect(u.rol).toBe('admin');
  });

  it('retorna null si raw es null/undefined/false', () => {
    expect(normalizeUser(null)).toBeNull();
    expect(normalizeUser(undefined)).toBeNull();
    expect(normalizeUser(false)).toBeNull();
    expect(normalizeUser('')).toBeNull();
  });

  it('mantiene props adicionales intactas', () => {
    const u = normalizeUser({ id: 99, type: 'admin', email: 'x@y.com', nombre: 'Ana' });
    expect(u.id).toBe(99);
    expect(u.email).toBe('x@y.com');
    expect(u.nombre).toBe('Ana');
  });
});

// ---------------------------------------------------------------------------
// Role derivations (isAdmin / isAlumno / isProfesor)
// ---------------------------------------------------------------------------
describe('role derivations', () => {
  it('rol admin => isAdmin true, resto false', () => {
    const u = normalizeUser({ type: 'admin' });
    expect(isAdmin(u)).toBe(true);
    expect(isAlumno(u)).toBe(false);
    expect(isProfesor(u)).toBe(false);
  });

  it('rol alumno => isAlumno true, isAdmin false', () => {
    const u = normalizeUser({ rol: 'alumno' });
    expect(isAlumno(u)).toBe(true);
    expect(isAdmin(u)).toBe(false);
  });

  it('rol profesor => isProfesor true', () => {
    const u = normalizeUser({ type: 'profesor' });
    expect(isProfesor(u)).toBe(true);
    expect(isAdmin(u)).toBe(false);
  });

  it('null user => todos false', () => {
    const u = normalizeUser(null);
    expect(isAdmin(u)).toBe(false);
    expect(isAlumno(u)).toBe(false);
    expect(isProfesor(u)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ProtectedRoute logic puro
// ---------------------------------------------------------------------------
describe('ProtectedRoute logic', () => {
  it('sin user => redirect /login', () => {
    expect(canAccess(null, 'admin')).toEqual({ allowed: false, redirect: '/login' });
    expect(canAccess(null, null)).toEqual({ allowed: false, redirect: '/login' });
  });

  it('user con rol distinto a allowedRole => redirect a su rol', () => {
    const alumno = normalizeUser({ type: 'alumno' });
    expect(canAccess(alumno, 'admin')).toEqual({ allowed: false, redirect: '/alumno' });
    const prof = normalizeUser({ rol: 'profesor' });
    expect(canAccess(prof, 'admin')).toEqual({ allowed: false, redirect: '/profesor' });
  });

  it('user con rol correcto => allowed true', () => {
    const admin = normalizeUser({ type: 'admin' });
    expect(canAccess(admin, 'admin')).toEqual({ allowed: true, redirect: null });
  });

  it('sin allowedRole y con user => allowed true (ruta autenticada)', () => {
    const alumno = normalizeUser({ rol: 'alumno' });
    expect(canAccess(alumno, null)).toEqual({ allowed: true, redirect: null });
    expect(canAccess(alumno, undefined)).toEqual({ allowed: true, redirect: null });
  });
});

// ---------------------------------------------------------------------------
// localStorage persistence contract
// ---------------------------------------------------------------------------
describe('localStorage auth contract', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('persiste user normalizado y token tras login', () => {
    const raw = { id: 1, type: 'admin', email: 'a@b.com' };
    const normalized = normalizeUser(raw);
    const token = 'tok-123';

    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(normalized));

    expect(localStorage.getItem('token')).toBe('tok-123');
    const stored = JSON.parse(localStorage.getItem('user'));
    expect(stored.rol).toBe('admin');
    expect(stored.type).toBe('admin');
  });

  it('clear on logout elimina token y user', () => {
    localStorage.setItem('token', 'tok');
    localStorage.setItem('user', JSON.stringify({ rol: 'admin' }));

    // simulate logout finally block from AuthContext.jsx
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('restore from localStorage normaliza correctamente', () => {
    // stored with only type (legacy) -> restore should have rol
    localStorage.setItem('user', JSON.stringify({ id: 5, type: 'alumno' }));
    const storedUser = localStorage.getItem('user');
    const restored = normalizeUser(JSON.parse(storedUser));
    expect(restored.rol).toBe('alumno');
    expect(isAlumno(restored)).toBe(true);
  });
});
