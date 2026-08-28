export function requiresGeneralAdmin(path) {
  if (!path) return false;
  // Only /admin/sedes requires general_admin for write; read is filtered
  // For guard purpose, we treat create/edit of sedes as general-only
  return path.includes('/admin/sedes');
}

export function canAccessAdminRoute(user, path) {
  if (!user) return false;
  const rol = user.rol || user.type || user.user_type;
  if (rol !== 'admin') return false;
  const role = user.role;
  // If no role (legacy admin), treat as general_admin
  if (!role) return true;
  if (requiresGeneralAdmin(path)) {
    return role === 'general_admin';
  }
  // Other admin routes: both general and sede_admin can access (scoped)
  if (path.startsWith('/admin')) {
    return role === 'general_admin' || role === 'sede_admin';
  }
  return true;
}

export function isWikiAdminRoute(path) {
  return path.includes('/admin/wiki');
}

export function isSedeRoute(path) {
  return path.includes('/sedes');
}
