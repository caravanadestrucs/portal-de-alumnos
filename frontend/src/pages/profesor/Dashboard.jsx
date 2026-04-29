import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getAsignacionesActuales } from '../../api/asignaciones';
import Card from '../../components/ui/Card';
import { BookOpen, Users, Calendar, Edit } from 'lucide-react';

export default function ProfesorDashboard() {
  const { user } = useAuth();
  const [asignaciones, setAsignaciones] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      if (!user?.id) return;
      
      setLoading(true);
      try {
        const data = await getAsignacionesActuales(user.id);
        // API returns { profesor, asignaciones: [], total, hoy }
        setAsignaciones(data.asignaciones || []);
      } catch (error) {
        console.error('Error loading:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user?.id]);

  // Get stats
  const totalAlumnos = asignaciones.reduce((sum, a) => sum + (a.grupo?.total_integrantes || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">
          Bienvenido, {user?.nombre}
        </h1>
        <p className="text-gray-500 mt-1">
          Panel de control del profesor
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="text-center">
          <BookOpen size={28} className="mx-auto text-primary-500 mb-2" />
          <p className="text-sm text-gray-500">Materias Asignadas</p>
          <p className="text-2xl font-bold text-gray-800">{asignaciones.length}</p>
        </Card>
        <Card className="text-center">
          <Users size={28} className="mx-auto text-green-500 mb-2" />
          <p className="text-sm text-gray-500">Total Alumnos</p>
          <p className="text-2xl font-bold text-gray-800">{totalAlumnos}</p>
        </Card>
        <Card className="text-center">
          <Calendar size={28} className="mx-auto text-accent-500 mb-2" />
          <p className="text-sm text-gray-500">Período Actual</p>
          <p className="text-lg font-bold text-gray-800">
            {new Date().toLocaleDateString('es-MX', { month: 'long', year: 'numeric' })}
          </p>
        </Card>
      </div>

      {/* Mis Asignaciones */}
      <Card>
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          Mis Asignaciones Activas
        </h2>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          </div>
        ) : asignaciones.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No tienes asignaciones activas en este período
          </div>
        ) : (
          <div className="space-y-4">
            {asignaciones.map((asig) => (
              <div 
                key={asig.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <h3 className="font-bold text-gray-800">
                    {asig.materia?.nombre}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Grupo {asig.grupo?.nombre} • {asig.grupo?.carrera?.nombre}
                  </p>
                  <div className="text-xs text-gray-400 mt-1">
                    <span className={asig.puede_editar ? 'text-green-600' : 'text-red-600'}>
                      {asig.puede_editar ? '✓ Puede editar calificaciones' : '✗ Período cerrado'}
                    </span>
                    <span className="ml-2">
                      ({asig.fecha_inicio} - {asig.fecha_fin})
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-primary-600">
                    {asig.grupo?.total_integrantes || 0}
                  </p>
                  <p className="text-xs text-gray-500">alumnos</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Info */}
      <Card className="bg-blue-50 border border-blue-200">
        <div className="flex items-start gap-3">
          <Edit size={20} className="text-blue-600 mt-1" />
          <div>
            <h3 className="font-bold text-blue-800">Sobre editar calificaciones</h3>
            <p className="text-sm text-blue-700 mt-1">
              Solo puedes editar calificaciones cuando el período de la asignación esté activo.
              El período se define en la fecha_inicio y fecha_fin de cada asignación.
              Una vez pasado el período, las calificaciones se bloquean automáticamente.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}