import { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';

const MOCK_ITEMS = [
  { id: 1, label: 'Alumnos', path: '/admin/alumnos' },
  { id: 2, label: 'Pagos', path: '/admin/pagos' },
  { id: 3, label: 'Grupos', path: '/admin/grupos' },
  { id: 4, label: 'Materias', path: '/admin/materias' },
  { id: 5, label: 'Calificaciones', path: '/admin/calificaciones' },
];

export default function GlobalSearch() {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const filtered = query
    ? MOCK_ITEMS.filter((i) => i.label.toLowerCase().includes(query.toLowerCase()))
    : [];

  return (
    <div className="relative w-full max-w-md">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          placeholder="Buscar... Cmd+K"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2 rounded-xl input-glass text-sm"
          aria-label="Buscador global"
        />
      </div>
      {query && (
        <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          {filtered.length > 0 ? (
            filtered.map((item) => (
              <div key={item.id} className="px-4 py-2 hover:bg-gray-50 text-sm text-gray-700">
                {item.label}
              </div>
            ))
          ) : (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">Sin resultados</div>
          )}
        </div>
      )}
    </div>
  );
}
