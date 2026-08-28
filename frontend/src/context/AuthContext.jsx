import { createContext, useContext, useState, useEffect } from 'react';
import * as authApi from '../api/auth';

const AuthContext = createContext(null);

export function normalizeUser(raw) {
  if (!raw) return null;
  const rol = raw.rol || raw.type || raw.user_type || null;
  const type = raw.type || raw.user_type || raw.rol || null;
  const user_type = raw.user_type || raw.type || raw.rol || null;
  // role is admin subtype, keep undefined if not present (legacy admin)
  const role = raw.role;
  let sede_id_raw;
  if (raw.sede_id !== undefined) sede_id_raw = raw.sede_id;
  else if (raw.sedeId !== undefined) sede_id_raw = raw.sedeId;
  else if (raw.sede?.id !== undefined) sede_id_raw = raw.sede.id;
  else sede_id_raw = null;
  const normalizedSedeId = sede_id_raw === undefined ? null : sede_id_raw;
  const sede = raw.sede ?? null;
  const base = {
    ...raw,
    rol,
    type,
    user_type,
    sede_id: normalizedSedeId,
    sedeId: normalizedSedeId,
    sede,
  };
  if (role !== undefined) {
    base.role = role;
  } else {
    // ensure role is undefined not null for legacy
    if ('role' in base) delete base.role;
  }
  // preserve sede_id_alias for compat
  base.sede_id_alias = normalizedSedeId;
  return base;
}

export function getSedeId(user) {
  if (!user) return null;
  let v;
  if (user.sede_id !== undefined) v = user.sede_id;
  else if (user.sedeId !== undefined) v = user.sedeId;
  else if (user.sede?.id !== undefined) v = user.sede.id;
  else v = null;
  return v === undefined ? null : v;
}

export function getRole(user) {
  if (!user) return null;
  return user.role ?? null;
}

export function isGeneralAdmin(user) {
  if (!user) return false;
  return user.role === 'general_admin';
}

export function isSedeAdmin(user) {
  if (!user) return false;
  return user.role === 'sede_admin';
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Restore session from localStorage on mount
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (token && storedUser && storedUser !== "undefined") {
      try {
        setUser(normalizeUser(JSON.parse(storedUser)));
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const response = await authApi.login(email, password);
    const { access_token: token, user: userData } = response;

    const normalized = normalizeUser(userData);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(normalized));
    setUser(normalized);

    return normalized;
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  const register = async (userData) => {
    const response = await authApi.register(userData);
    return response;
  };

  const value = {
    user,
    loading,
    login,
    logout,
    register,
    isAdmin: user?.rol === 'admin',
    isAlumno: user?.rol === 'alumno',
    isProfesor: user?.rol === 'profesor',
    isGeneralAdmin: isGeneralAdmin(user),
    isSedeAdmin: isSedeAdmin(user),
    sedeId: getSedeId(user),
    sede: user?.sede ?? null,
    role: getRole(user),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
