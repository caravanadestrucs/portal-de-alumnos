import { Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useState, useEffect } from 'react';

export default function Navbar({ onMenuClick }) {
  const { user, logout, isGeneralAdmin, isSedeAdmin, sede, sedeId } = useAuth();
  const isAdmin = user?.rol === 'admin';
  const isAlumno = user?.rol === 'alumno';
  const isProfesor = user?.rol === 'profesor';

  const [activeSede, setActiveSede] = useState(() => {
    return localStorage.getItem('activeSede') || 'all';
  });

  useEffect(() => {
    localStorage.setItem('activeSede', activeSede);
    window.dispatchEvent(new CustomEvent('sede-change', { detail: activeSede }));
  }, [activeSede]);

  const sedeCode = sede?.codigo || (sedeId === 1 ? 'TEO' : sedeId === 2 ? 'HUA' : null);
  const sedeLabel = sede?.nombre || (sedeCode === 'TEO' ? 'Teotitlan' : sedeCode === 'HUA' ? 'Huautla' : '');

  return (
    <header className="sticky top-0 z-30 glass mb-6">
      <div className="flex items-center justify-between px-4 py-3 lg:px-8">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-primary-100 transition-colors"
          >
            <Menu size={24} className="text-primary-600" />
          </button>
          <h1 className="text-xl font-bold text-primary-700 lg:text-2xl">
            Universidad Felipe Villanueva
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {/* Sede badge */}
          {isAdmin && (
            <div className="flex items-center gap-2">
              {isSedeAdmin && sedeCode && (
                <span data-testid="sede-badge" className="px-3 py-1 rounded-full text-xs font-bold bg-primary-100 text-primary-700 border border-primary-200">
                  {sedeCode} {sedeLabel && `— ${sedeLabel}`}
                </span>
              )}
              {isGeneralAdmin && (
                <>
                  <span data-testid="sede-badge" className="px-3 py-1 rounded-full text-xs font-bold bg-accent-100 text-accent-700 border border-accent-200">
                    General
                  </span>
                  <select
                    aria-label="sede switcher"
                    data-testid="sede-switcher"
                    value={activeSede}
                    onChange={(e) => setActiveSede(e.target.value)}
                    className="text-xs border border-gray-300 rounded-lg px-2 py-1 bg-white"
                  >
                    <option value="all">Todas las sedes</option>
                    <option value="1">TEO — Teotitlan</option>
                    <option value="2">HUA — Huautla</option>
                  </select>
                </>
              )}
              {isGeneralAdmin && !sede && (
                <span className="hidden sm:inline text-xs text-gray-500">Todas</span>
              )}
            </div>
          )}

          <div className="hidden sm:flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold">
              {user?.nombre?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="font-medium text-gray-800">
                {user?.nombre || 'Usuario'}
              </p>
              <p className="text-sm text-gray-500 capitalize">{user?.rol || 'user'}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
