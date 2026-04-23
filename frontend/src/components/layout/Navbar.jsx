import { Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth();

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
