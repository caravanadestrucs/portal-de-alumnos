import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getMisAsignaciones, getGrupoCalificaciones, updateCalificacionProfesor } from '../../api/profesor';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Save, BookOpen, Users, AlertCircle, CheckCircle } from 'lucide-react';

export default function ProfesorCalificaciones() {
  const { user } = useAuth();
  const [asignaciones, setAsignaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsignacion, setSelectedAsignacion] = useState(null);
  const [alumnos, setAlumnos] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadAsignaciones();
  }, [user?.id]);

  const loadAsignaciones = async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      const data = await getMisAsignaciones(user.id);
      setAsignaciones(data.asignaciones || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAlumnos = async (asignacion) => {
    try {
      const data = await getGrupoCalificaciones(asignacion.id);
      setAlumnos(data.alumnos || []);
      setSelectedAsignacion(asignacion);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleSave = async (alumnoId, califData) => {
    if (!selectedAsignacion) return;
    
    setSaving(true);
    try {
      await updateCalificacionProfesor(selectedAsignacion.id, {
        alumno_id: alumnoId,
        calificacion: califData
      });
      // Recargar
      await loadAlumnos(selectedAsignacion);
    } catch (error) {
      alert('Error al guardar: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const getGradeClass = (grade) => {
    if (grade === null || grade === undefined || grade === 0) return 'text-gray-400';
    if (grade >= 7) return 'text-green-600 font-bold';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Calificaciones</h1>
        <p className="text-gray-500 mt-1">
          Gestiona las calificaciones de tus alumnos
        </p>
      </div>

      {/* Selector de asignación */}
      <Card>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Seleccionar Materia y Grupo
        </label>
        <select
          value={selectedAsignacion?.id || ''}
          onChange={(e) => {
            const asig = asignaciones.find(a => a.id === parseInt(e.target.value));
            if (asig) loadAlumnos(asig);
          }}
          className="w-full px-4 py-2.5 rounded-xl input-glass"
          disabled={loading}
        >
          <option value="">-- Seleccionar --</option>
          {asignaciones.map((a) => (
            <option key={a.id} value={a.id}>
              {a.materia?.nombre} - Grupo {a.grupo?.nombre} ({a.grupo?.carrera?.nombre})
            </option>
          ))}
        </select>
      </Card>

      {/* Tabla de alumnos */}
      {selectedAsignacion && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                {selectedAsignacion.materia?.nombre}
              </h2>
              <p className="text-sm text-gray-500">
                Grupo {selectedAsignacion.grupo?.nombre} • {selectedAsignacion.grupo?.carrera?.nombre}
              </p>
            </div>
            
            {/* Estado del periodo */}
            <Badge variant={selectedAsignacion.puede_editar ? 'success' : 'danger'}>
              {selectedAsignacion.puede_editar 
                ? '✓ Período activo - puede editar' 
                : '✗ Período cerrado'}
            </Badge>
          </div>

          {/* Info de periodo */}
          {!selectedAsignacion.puede_editar && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertCircle size={18} className="text-red-600" />
              <span className="text-sm text-red-700">
                El período de edición terminó ({selectedAsignacion.fecha_fin}). 
                No puedes modificar las calificaciones.
              </span>
            </div>
          )}

          {/* Lista de alumnos */}
          {alumnos.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No hay alumnos en este grupo
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-2 font-semibold text-gray-700">Alumno</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">A1</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">A2</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">A3</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">A4</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">A5</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">P1</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">P2</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">Ext1</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">Ext2</th>
                    <th className="text-center py-3 px-2 font-semibold text-gray-700">Final</th>
                  </tr>
                </thead>
                <tbody>
                  {alumnos.map(({ alumno, calificacion, puede_editar }) => (
                    <AlumnoRow
                      key={alumno.id}
                      alumno={alumno}
                      calificacion={calificacion}
                      puedeEditar={puede_editar && selectedAsignacion.puede_editar}
                      onSave={(data) => handleSave(alumno.id, data)}
                      saving={saving}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Promedio del grupo */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              Total de alumnos: {alumnos.length}
            </p>
          </div>
        </Card>
      )}

      {/* Loading */}
      {loading && (
        <Card className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
        </Card>
      )}
    </div>
  );
}

// Componente para cada fila de alumno
function AlumnoRow({ alumno, calificacion, puedeEditar, onSave, saving }) {
  const [data, setData] = useState({
    asistencia_1: calificacion?.asistencia_1 ?? null,
    asistencia_2: calificacion?.asistencia_2 ?? null,
    asistencia_3: calificacion?.asistencia_3 ?? null,
    asistencia_4: calificacion?.asistencia_4 ?? null,
    asistencia_5: calificacion?.asistencia_5 ?? null,
    practica_1: calificacion?.practica_1 ?? null,
    practica_2: calificacion?.practica_2 ?? null,
    calificacion_final: calificacion?.calificacion_final ?? null,
  });
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = (campo, valor) => {
    setData({ ...data, [campo]: valor === '' ? null : valor });
    setHasChanges(true);
  };

  const handleGuardar = () => {
    onSave(data);
    setHasChanges(false);
  };

  const getInputClass = (valor) => {
    if (valor === null || valor === undefined || valor === '') return 'text-gray-400';
    const val = parseFloat(valor);
    if (isNaN(val)) return 'text-gray-400';
    if (campo.includes('asistencia_')) {
      return val === 1 ? 'text-green-600' : 'text-red-500';
    }
    return val >= 13 ? 'text-green-600 font-bold' : 'text-red-500';
  };

  return (
    <tr className="border-b border-gray-100">
      <td className="py-2 px-2">
        <div>
          <p className="font-medium text-gray-800">
            {alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno}
          </p>
          <p className="text-xs text-gray-500">{alumno.numero_control}</p>
        </div>
      </td>
      {['asistencia_1', 'asistencia_2', 'asistencia_3', 'asistencia_4', 'asistencia_5'].map(campo => (
        <td key={campo} className="text-center py-2 px-1">
          {puedeEditar ? (
            <input
              type="checkbox"
              checked={data[campo] === 1}
              onChange={(e) => handleChange(campo, e.target.checked ? 1 : 0)}
              className="w-5 h-5 accent-primary-500"
              disabled={!puedeEditar}
            />
          ) : (
            <span className={data[campo] === 1 ? 'text-green-600' : 'text-gray-300'}>
              {data[campo] === 1 ? '✓' : '✗'}
            </span>
          )}
        </td>
      ))}
      {['practica_1', 'practica_2', 'extra_1', 'extra_2', 'calificacion_final'].map(campo => (
        <td key={campo} className="text-center py-2 px-1">
          {puedeEditar ? (
            <input
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={data[campo] ?? ''}
              onChange={(e) => handleChange(campo, e.target.value)}
              className="w-14 px-1 py-1 text-center rounded border border-gray-300 text-sm"
              disabled={!puedeEditar}
            />
          ) : (
            <span className="text-sm font-medium">
              {data[campo] ?? '-'}
            </span>
          )}
        </td>
      ))}
      <td className="py-2 px-2 text-center">
        {hasChanges && puedeEditar && (
          <button
            onClick={handleGuardar}
            disabled={saving}
            className="px-2 py-1 bg-primary-500 text-white rounded text-sm hover:bg-primary-600"
          >
            <Save size={14} />
          </button>
        )}
      </td>
    </tr>
  );
}