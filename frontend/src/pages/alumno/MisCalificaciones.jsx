import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import * as api from '../../api/alumnos';
import { BookOpen, TrendingUp } from 'lucide-react';

export default function MisCalificaciones() {
  const { user } = useAuth();
  const [calificaciones, setCalificaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [periodo, setPeriodo] = useState('todos');
  const [anio, setAnio] = useState('todos');

  useEffect(() => {
    const loadCalificaciones = async () => {
      setLoading(true);
      try {
        const data = await api.getAlumnos().catch(() => []);
        // For now, show empty state - real implementation would call user-specific endpoint
        setCalificaciones([]);
      } catch (error) {
        console.error('Error loading calificaciones:', error);
        setCalificaciones([]);
      } finally {
        setLoading(false);
      }
    };

    loadCalificaciones();
  }, [user]);

  const getGradeClass = (grade) => {
    if (grade === null || grade === undefined) return 'grade-pending';
    if (grade >= 13) return 'grade-approved';
    return 'grade-failed';
  };

  const getGradeText = (grade) => {
    if (grade === null || grade === undefined) return 'Sin calificar';
    return grade >= 13 ? 'Aprobado' : 'Reprobado';
  };

  // Calculate stats
  const totalMaterias = calificaciones.length;
  const materiasAprobadas = calificaciones.filter(c => c.calificacion_final >= 13).length;
  const promedio = calificaciones.length > 0
    ? calificaciones.reduce((sum, c) => sum + (c.calificacion_final || 0), 0) / calificaciones.length
    : null;

  const filteredCalificaciones = calificaciones.filter(c => {
    if (periodo !== 'todos' && c.periodo !== periodo) return false;
    if (anio !== 'todos' && c.anio !== parseInt(anio)) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Mis Calificaciones</h1>
        <p className="text-gray-500 mt-1">
          Historial académico completo
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="text-center">
          <BookOpen size={28} className="mx-auto text-primary-500 mb-2" />
          <p className="text-sm text-gray-500">Total Materias</p>
          <p className="text-2xl font-bold text-gray-800">{totalMaterias}</p>
        </Card>
        <Card className="text-center">
          <TrendingUp size={28} className="mx-auto text-green-500 mb-2" />
          <p className="text-sm text-gray-500">Aprobadas</p>
          <p className="text-2xl font-bold text-green-600">{materiasAprobadas}</p>
        </Card>
        <Card className="text-center">
          <TrendingUp size={28} className="mx-auto text-accent-500 mb-2" />
          <p className="text-sm text-gray-500">Promedio</p>
          <p className="text-2xl font-bold text-gray-800">
            {promedio ? promedio.toFixed(1) : '-'}
          </p>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Período
            </label>
            <select
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="todos">Todos los períodos</option>
              <option value="2026-1">2026-1</option>
              <option value="2025-2">2025-2</option>
              <option value="2025-1">2025-1</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Año
            </label>
            <select
              value={anio}
              onChange={(e) => setAnio(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="todos">Todos los años</option>
              <option value="2026">2026</option>
              <option value="2025">2025</option>
              <option value="2024">2024</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Table */}
      {loading ? (
        <Card className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-500">Cargando calificaciones...</p>
        </Card>
      ) : filteredCalificaciones.length === 0 ? (
        <Card className="text-center py-12">
          <BookOpen size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">
            No hay calificaciones registradas
          </p>
          <p className="text-sm text-gray-400 mt-1">
            Las calificaciones aparecerán cuando el departamento académico las registre
          </p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Materia
                  </th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">
                    Período
                  </th>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <th
                      key={n}
                      className="text-center py-3 px-2 font-semibold text-gray-700 w-10"
                    >
                      A{n}
                    </th>
                  ))}
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">
                    P1
                  </th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">
                    P2
                  </th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">
                    Final
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredCalificaciones.map((cal) => (
                  <tr
                    key={cal.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">
                      <span className="font-medium text-gray-800">
                        {cal.materia?.nombre || 'Materia'}
                      </span>
                      <span className="text-gray-400 text-sm ml-2">
                        ({cal.materia?.codigo})
                      </span>
                    </td>
                    <td className="text-center py-3 px-2 text-gray-600">
                      {cal.periodo} {cal.anio}
                    </td>
                    {[1, 2, 3, 4, 5].map((n) => (
                      <td key={n} className="text-center py-3 px-2">
                        <span
                          className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${
                            cal[`asistencia_${n}`]
                              ? 'bg-green-100 text-green-600'
                              : 'bg-red-100 text-red-400'
                          }`}
                        >
                          {cal[`asistencia_${n}`] ? '✓' : '✗'}
                        </span>
                      </td>
                    ))}
                    <td className={`text-center py-3 px-2 font-medium ${getGradeClass(cal.practica_1)}`}>
                      {cal.practica_1 ?? '-'}
                    </td>
                    <td className={`text-center py-3 px-2 font-medium ${getGradeClass(cal.practica_2)}`}>
                      {cal.practica_2 ?? '-'}
                    </td>
                    <td className="text-center py-3 px-2">
                      <span
                        className={`inline-block px-3 py-1 rounded-lg font-bold ${getGradeClass(
                          cal.calificacion_final
                        )}`}
                      >
                        {cal.calificacion_final ?? '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 mt-4 pt-4 border-t border-gray-200 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Asistencia:</span>
              <span className="w-5 h-5 rounded bg-green-100 text-green-600 flex items-center justify-center text-xs">✓</span>
              <span className="text-gray-400">Presente</span>
              <span className="w-5 h-5 rounded bg-red-100 text-red-400 flex items-center justify-center text-xs ml-2">✗</span>
              <span className="text-gray-400">Ausente</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
