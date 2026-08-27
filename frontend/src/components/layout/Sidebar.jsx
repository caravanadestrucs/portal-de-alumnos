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
  ChevronLeft,
  ChevronRight,
  Upload,
  Settings,
  FileDown,
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
  { path: '/admin/importar', icon: Upload, label: 'Importar' },
  { path: '/admin/boletas', icon: FileDown, label: 'Boletas' },
  { path: '/admin/admins', icon: UserCheck, label: 'Administradores' },
  { path: '/admin/configuracion', icon: Settings, label: 'Configuración' },
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

export default function Sidebar({ isOpen, setIsOpen, collapsed, onToggleCollapse }) {
  const location = useLocation();
  const { user, logout } = useAuth();
  const isAdmin = user?.rol === 'admin';
  const isAlumno = user?.rol === 'alumno';
  const isProfesor = user?.rol === 'profesor';

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
        className={`fixed top-0 left-0 z-50 h-full glass-dark transition-all duration-300 flex flex-col ${
          collapsed ? 'w-20' : 'w-64'
        } ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 shrink-0">
          <Link to={defaultPath} className="flex items-center gap-2 min-w-0">
            <img src="/logo.png" alt="FV Logo" className="w-10 h-10 shrink-0" />
            <span className={`text-white font-bold text-lg truncate ${
              collapsed ? 'hidden' : 'block'
            }`}>Portal FV</span>
          </Link>
          <button
            onClick={() => setIsOpen(false)}
            className="lg:hidden text-white hover:text-primary-300 shrink-0"
          >
            <X size={24} />
          </button>
        </div>

        {/* Navigation — scrollable */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
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
                } ${collapsed ? 'justify-center px-2' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <Icon size={20} className="shrink-0" />
                <span className={`${collapsed ? 'hidden' : 'block'}`}>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Desktop collapse toggle */}
        <button
          onClick={onToggleCollapse}
          className="hidden lg:flex absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full shadow-md items-center justify-center hover:bg-gray-100 transition-colors z-10"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        {/* User info & logout — fixed at bottom */}
        <div className="shrink-0 p-4 border-t border-white/10">
          <div className={`flex items-center gap-3 mb-3 ${collapsed ? 'justify-center' : ''}`}>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold shrink-0">
              {user?.nombre?.charAt(0) || 'U'}
            </div>
            <div className={`flex-1 min-w-0 ${collapsed ? 'hidden' : 'block'}`}>
              <p className="text-white font-medium truncate text-sm">
                {user?.nombre || 'Usuario'}
              </p>
              <p className="text-white/60 text-xs capitalize">{user?.rol || 'user'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className={`flex items-center gap-2 w-full px-4 py-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors ${
              collapsed ? 'justify-center px-2' : ''
            }`}
            title={collapsed ? 'Cerrar Sesión' : undefined}
          >
            <LogOut size={18} className="shrink-0" />
            <span className={`${collapsed ? 'hidden' : 'block'}`}>Cerrar Sesión</span>
          </button>
        </div>
      </aside>
    </>
  );
}
