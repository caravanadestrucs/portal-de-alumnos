import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import { getCalificacionesByAlumno } from '../../api/calificaciones';
import { BookOpen, TrendingUp } from 'lucide-react';

export default function MisCalificaciones() {
  const { user } = useAuth();
  const [calificaciones, setCalificaciones] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCalificaciones = async () => {
      if (!user || !user.id) {
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const data = await getCalificacionesByAlumno(user.id).catch(() => []);
        setCalificaciones(data);
      } catch (error) {
        console.error('Error loading calificaciones:', error);
        setCalificaciones([]);
      } finally {
        setLoading(false);
      }
    };

    loadCalificaciones();
  }, [user]);

  // Escala 0-10, aprobado >= 7
  const getGradeClass = (grade) => {
    if (grade === null || grade === undefined || grade === 0) return 'text-gray-400';
    if (grade >= 6) return 'text-green-600 font-bold';
    return 'text-red-500';
  };

  // Obtener la calificación final (Extra tiene prioridad sobre Final)
  const getCalificacionFinal = (cal) => {
    if (cal.extra_2 && cal.extra_2 > 0) return cal.extra_2;
    if (cal.extra_1 && cal.extra_1 > 0) return cal.extra_1;
    return cal.calificacion_final;
  };

  const getEstado = (cal) => {
    const final = getCalificacionFinal(cal);
    if (!final || final === 0) return { text: 'Sin calificar', variant: 'default' };
    return final >= 7 
      ? { text: 'Aprobado', variant: 'success' }
      : { text: 'Reprobado', variant: 'danger' };
  };

  // Calculate stats
  const totalMaterias = calificaciones.length;
  const promedio = calificaciones.length > 0
    ? calificaciones.reduce((sum, c) => sum + (getCalificacionFinal(c) || 0), 0) / calificaciones.filter(c => getCalificacionFinal(c) > 0).length
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Mis Calificaciones</h1>
        <p className="text-gray-500 mt-1">
          Historial académico - Escala 0-10 (mínimo 7 para aprobar)
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
          <TrendingUp size={28} className="mx-auto text-accent-500 mb-2" />
          <p className="text-sm text-gray-500">Promedio</p>
          <p className={`text-2xl font-bold ${promedio ? getGradeClass(promedio) : 'text-gray-400'}`}>
            {promedio ? promedio.toFixed(1) : '-'}
          </p>
        </Card>
        <Card className="text-center">
          <TrendingUp size={28} className="mx-auto text-green-500 mb-2" />
          <p className="text-sm text-gray-500">Aprobadas</p>
          <p className="text-2xl font-bold text-green-600">
            {calificaciones.filter(c => getCalificacionFinal(c) >= 7).length}
          </p>
        </Card>
      </div>

      {/* Calificaciones Table */}
      <Card>
        <h2 className="text-xl font-bold text-gray-800 mb-4">Detalle por Materia</h2>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          </div>
        ) : calificaciones.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No tienes calificaciones registradas
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Materia</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">A1</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">A2</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">A3</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">A4</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">A5</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">P1</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">P2</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">Calif. Final</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700">Estado</th>
                </tr>
              </thead>
              <tbody>
                {calificaciones.map((cal) => {
                  const final = getCalificacionFinal(cal);
                  const estado = getEstado(cal);
                  return (
                    <tr key={cal.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <span className="font-medium text-gray-800">
                          {cal.materia?.nombre || 'Materia'}
                        </span>
                        <span className="text-gray-400 text-sm ml-2">
                          ({cal.materia?.codigo})
                        </span>
                      </td>
                      {[1, 2, 3, 4, 5].map((n) => (
                        <td key={n} className="text-center py-3 px-2">
                          <span className={cal[`asistencia_${n}`] === 1 ? 'text-green-600' : 'text-gray-300'}>
                            {cal[`asistencia_${n}`] === 1 ? '✓' : '✗'}
                          </span>
                        </td>
                      ))}
                      <td className={`text-center py-3 px-2 ${getGradeClass(cal.practica_1)}`}>
                        {cal.practica_1 || '-'}
                      </td>
                      <td className={`text-center py-3 px-2 ${getGradeClass(cal.practica_2)}`}>
                        {cal.practica_2 || '-'}
                      </td>
                      <td className={`text-center py-3 px-2 font-bold ${getGradeClass(final)}`}>
                        {final || '-'}
                      </td>
                      <td className="text-center py-3 px-2">
                        <Badge variant={estado.variant}>
                          {estado.text}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}