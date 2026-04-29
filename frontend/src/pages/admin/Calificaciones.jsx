import { useState, useEffect } from 'react';
import { useFetch } from '../../hooks/useFetch';
import * as alumnosApi from '../../api/alumnos';
import * as calificacionesApi from '../../api/calificaciones';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Save, User, BookOpen } from 'lucide-react';

export default function AdminCalificaciones() {
  const { data: alumnos } = useFetch(alumnosApi.getAlumnos);

  const [selectedAlumno, setSelectedAlumno] = useState(null);
  const [calificaciones, setCalificaciones] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (selectedAlumno) {
      loadCalificaciones();
    }
  }, [selectedAlumno]);

  const loadCalificaciones = async () => {
    setLoading(true);
    try {
      const data = await calificacionesApi.getCalificacionesByAlumno(selectedAlumno.id);
      setCalificaciones(data || []);
    } catch (error) {
      console.error('Error loading calificaciones:', error);
      setCalificaciones([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAlumnoChange = (e) => {
    const alumnoId = parseInt(e.target.value);
    const alumno = alumnos?.find((a) => a.id === alumnoId);
    setSelectedAlumno(alumno || null);
  };

  const handleCalificacionChange = (calificacionId, field, value) => {
    setCalificaciones((prev) =>
      prev.map((c) =>
        c.id === calificacionId ? { ...c, [field]: value } : c
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      for (const cal of calificaciones) {
        await calificacionesApi.updateCalificacion(cal.id, {
          asistencia_1: cal.asistencia_1,
          asistencia_2: cal.asistencia_2,
          asistencia_3: cal.asistencia_3,
          asistencia_4: cal.asistencia_4,
          asistencia_5: cal.asistencia_5,
          practica_1: cal.practica_1,
          practica_2: cal.practica_2,
          extra_1: cal.extra_1,
          extra_2: cal.extra_2,
          calificacion_final: cal.calificacion_final,
        });
      }
      alert('Calificaciones guardadas exitosamente');
    } catch (error) {
      alert(error.response?.data?.message || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const getGradeClass = (grade) => {
    if (grade === null || grade === undefined || grade === 0) return 'text-gray-400';
    if (grade >= 6) return 'text-green-600 font-bold';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Calificaciones</h1>
        <p className="text-gray-500 mt-1">
          Gestionar calificaciones de alumnos
        </p>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Seleccionar Alumno
            </label>
            <select
              value={selectedAlumno?.id || ''}
              onChange={handleAlumnoChange}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="">-- Seleccionar --</option>
              {Array.isArray(alumnos) &&
                alumnos.map((alumno) => (
                  <option key={alumno.id} value={alumno.id}>
                    {alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno} ({alumno.numero_control})
                  </option>
                ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Calificaciones Table */}
      {selectedAlumno && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <User size={20} className="text-primary-500" />
              <span className="font-medium text-gray-700">
                {selectedAlumno.nombre} {selectedAlumno.apellido_paterno}{' '}
                {selectedAlumno.apellido_materno}
              </span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-500">
                {selectedAlumno.carrera?.nombre}
              </span>
            </div>
            <Button onClick={handleSave} loading={saving}>
              <Save size={18} />
              Guardar Cambios
            </Button>
          </div>

          {loading ? (
            <Card className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-500">Cargando calificaciones...</p>
            </Card>
          ) : calificaciones.length === 0 ? (
            <Card className="text-center py-12">
              <BookOpen size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">
                No hay materias asignadas para este alumno
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
                      {[1, 2, 3, 4, 5].map((n) => (
                        <th
                          key={n}
                          className="text-center py-3 px-2 font-semibold text-gray-700 w-12"
                        >
                          A{n}
                        </th>
                      ))}
                      <th className="text-center py-3 px-2 font-semibold text-gray-700 w-20">
                        Prác. 1
                      </th>
                      <th className="text-center py-3 px-2 font-semibold text-gray-700 w-20">
                        Prác. 2
                      </th>
                      <th className="text-center py-3 px-2 font-semibold text-gray-700 w-20">
                        Extra 1
                      </th>
                      <th className="text-center py-3 px-2 font-semibold text-gray-700 w-20">
                        Extra 2
                      </th>
                      <th className="text-center py-3 px-2 font-semibold text-gray-700 w-20">
                        Final
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {calificaciones.map((cal) => (
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
                            <input
                              type="checkbox"
                              checked={cal[`asistencia_${n}`] === 1}
                              onChange={(e) =>
                                handleCalificacionChange(
                                  cal.id,
                                  `asistencia_${n}`,
                                  e.target.checked ? 1 : 0
                                )
                              }
                              className="w-5 h-5 rounded border-gray-300 text-primary-600"
                            />
                          </td>
                        ))}
                        <td className="text-center py-3 px-2">
                          <input
                            type="number"
                            min="0"
                            max="10"
                            value={cal.practica_1 || ''}
                            onChange={(e) =>
                              handleCalificacionChange(
                                cal.id,
                                'practica_1',
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className={`w-16 text-center px-2 py-1 rounded-lg input-glass ${getGradeClass(
                              cal.practica_1
                            )}`}
                          />
                        </td>
                        <td className="text-center py-3 px-2">
                          <input
                            type="number"
                            min="0"
                            max="10"
                            value={cal.practica_2 || ''}
                            onChange={(e) =>
                              handleCalificacionChange(
                                cal.id,
                                'practica_2',
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className={`w-16 text-center px-2 py-1 rounded-lg input-glass ${getGradeClass(
                              cal.practica_2
                            )}`}
                          />
                        </td>
                        <td className="text-center py-3 px-2">
                          <input
                            type="number"
                            min="0"
                            max="10"
                            value={cal.extra_1 || ''}
                            onChange={(e) =>
                              handleCalificacionChange(
                                cal.id,
                                'extra_1',
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className={`w-16 text-center px-2 py-1 rounded-lg input-glass ${getGradeClass(
                              cal.extra_1
                            )}`}
                          />
                        </td>
                        <td className="text-center py-3 px-2">
                          <input
                            type="number"
                            min="0"
                            max="10"
                            value={cal.extra_2 || ''}
                            onChange={(e) =>
                              handleCalificacionChange(
                                cal.id,
                                'extra_2',
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className={`w-16 text-center px-2 py-1 rounded-lg input-glass ${getGradeClass(
                              cal.extra_2
                            )}`}
                          />
                        </td>
                        <td className="text-center py-3 px-2">
                          <input
                            type="number"
                            min="0"
                            max="10"
                            value={cal.calificacion_final || ''}
                            onChange={(e) =>
                              handleCalificacionChange(
                                cal.id,
                                'calificacion_final',
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className={`w-16 text-center px-2 py-1 rounded-lg input-glass font-bold ${getGradeClass(
                              cal.calificacion_final
                            )}`}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-6 mt-4 pt-4 border-t border-gray-200 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-gray-200"></div>
                  <span className="text-gray-500">Sin calificar</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded grade-approved"></div>
                  <span className="text-gray-500">Aprobado (≥13)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded grade-failed"></div>
                  <span className="text-gray-500">Reprobado (&lt;13)</span>
                </div>
              </div>
            </Card>
          )}
        </>
      )}

      {!selectedAlumno && (
        <Card className="text-center py-12">
          <User size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">
            Selecciona un alumno para ver sus calificaciones
          </p>
        </Card>
      )}
    </div>
  );
}
