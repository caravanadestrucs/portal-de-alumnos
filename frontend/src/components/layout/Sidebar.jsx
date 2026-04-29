import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  BookOpen,
  FileText,
  CreditCard,
  Download,
  LogOut,
  Menu,
  X,
  UserCheck,
  FolderCog,
  ClipboardList,
} from 'lucide-react';

const adminNavItems = [
  { path: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/admin/alumnos', icon: Users, label: 'Alumnos' },
  { path: '/admin/carreras', icon: GraduationCap, label: 'Carreras' },
  { path: '/admin/materias', icon: BookOpen, label: 'Materias' },
  { path: '/admin/calificaciones', icon: FileText, label: 'Calificaciones' },
  { path: '/admin/pagos', icon: CreditCard, label: 'Pagos' },
  { path: '/admin/profesores', icon: UserCheck, label: 'Profesores' },
  { path: '/admin/grupos', icon: FolderCog, label: 'Grupos' },
  { path: '/admin/asignaciones', icon: ClipboardList, label: 'Asignaciones' },
  { path: '/admin/admins', icon: UserCheck, label: 'Administradores' },
  { path: '/admin/requisitos', icon: GraduationCap, label: 'Requisitos' },
  { path: '/admin/exportar', icon: Download, label: 'Exportar' },
];

const alumnoNavItems = [
  { path: '/alumno', icon: LayoutDashboard, label: 'Inicio' },
  { path: '/alumno/calificaciones', icon: FileText, label: 'Calificaciones' },
  { path: '/alumno/pagos', icon: CreditCard, label: 'Pagos' },
  { path: '/alumno/requisitos', icon: GraduationCap, label: 'Requisitos' },
];

const profesorNavItems = [
  { path: '/profesor', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/profesor/calificaciones', icon: FileText, label: 'Calificaciones' },
];

export default function Sidebar({ isOpen, setIsOpen }) {
  const location = useLocation();
  const { user, logout, isAdmin, isProfesor } = useAuth();

  const navItems = isAdmin ? adminNavItems : isProfesor ? profesorNavItems : alumnoNavItems;
  const defaultPath = isAdmin ? '/admin' : isProfesor ? '/profesor' : '/alumno';

  const handleLogout = async () => {
    await logout();
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 glass-dark transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <Link to={defaultPath} className="flex items-center gap-2">
            <img src="/logo.png" alt="FV Logo" className="w-10 h-10" />
            <span className="text-white font-bold text-lg hidden lg:block">Portal FV</span>
          </Link>
          <button
            onClick={() => setIsOpen(false)}
            className="lg:hidden text-white hover:text-primary-300"
          >
            <X size={24} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`sidebar-item flex items-center gap-3 px-4 py-3 rounded-xl text-white ${
                  isActive ? 'active' : ''
                }`}
              >
                <Icon size={20} />
                <span className={`${isOpen ? 'block' : 'hidden'} lg:block`}>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User info & logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold">
              {user?.nombre?.charAt(0) || 'U'}
            </div>
            <div className="hidden lg:block flex-1 min-w-0">
              <p className="text-white font-medium truncate">
                {user?.nombre || 'Usuario'}
              </p>
              <p className="text-white/60 text-sm capitalize">{user?.rol || 'user'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-4 py-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span className="hidden lg:block">Cerrar Sesión</span>
          </button>
        </div>
      </aside>
    </>
  );
}
