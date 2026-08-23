import { useState, useEffect, useRef } from 'react';
import * as alumnosApi from '../../api/alumnos';
import * as calificacionesApi from '../../api/calificaciones';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';
import { Save, User, BookOpen, Search, X } from 'lucide-react';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { getGradeClass, getEffectiveGrade } from '../../utils/grades';

export default function AdminCalificaciones() {
  const toast = useToast();
  const [selectedAlumno, setSelectedAlumno] = useState(null);
  const [calificaciones, setCalificaciones] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Autocomplete state
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const searchRef = useRef(null);

  useEffect(() => {
    if (selectedAlumno) {
      loadCalificaciones();
    }
  }, [selectedAlumno]);

  // Debounced search
  useEffect(() => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const data = await alumnosApi.getAlumnos({ search: searchTerm, per_page: 10 });
        setSearchResults(data.alumnos || []);
        setShowSuggestions(true);
      } catch (error) {
        console.error('Error searching alumnos:', error);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Cerrar sugerencias al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

  const handleSelectSuggestion = (alumno) => {
    setSelectedAlumno(alumno);
    setSearchTerm(`${alumno.nombre} ${alumno.apellido_paterno} ${alumno.apellido_materno || ''}`.trim());
    setShowSuggestions(false);
    setHighlightedIndex(-1);
  };

  const handleClear = () => {
    setSelectedAlumno(null);
    setSearchTerm('');
    setSearchResults([]);
    setCalificaciones([]);
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions || searchResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev < searchResults.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev > 0 ? prev - 1 : searchResults.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < searchResults.length) {
          handleSelectSuggestion(searchResults[highlightedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowSuggestions(false);
        break;
    }
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
      // SAFE bulk prep: bulk endpoint may not exist yet (backend currently exposes POST /calificaciones/bulk)
      // Keep sequential loop as fallback — do NOT remove until bulk is verified.
      // Bulk option (comentada) para migración futura:
      // try {
      //   const payload = calificaciones.map(c => ({
      //     id: c.id,
      //     alumno_id: c.alumno_id,
      //     materia_id: c.materia_id,
      //     asistencia_1: c.asistencia_1,
      //     asistencia_2: c.asistencia_2,
      //     asistencia_3: c.asistencia_3,
      //     asistencia_4: c.asistencia_4,
      //     asistencia_5: c.asistencia_5,
      //     practica_1: c.practica_1,
      //     practica_2: c.practica_2,
      //     extra_1: c.extra_1,
      //     extra_2: c.extra_2,
      //     calificacion_final: c.calificacion_final,
      //   }));
      //   await calificacionesApi.bulkUpdateCalificaciones(payload);
      //   toast.success(`${payload.length} calificaciones guardadas`);
      //   return;
      // } catch (bulkError) {
      //   console.warn('Bulk no disponible, fallback a secuencial:', bulkError?.response?.status);
      // }

      // Fallback secuencial — con try/catch por lote para no perder todo si una falla
      let successCount = 0;
      let failCount = 0;
      for (const cal of calificaciones) {
        try {
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
          successCount++;
        } catch (rowError) {
          console.error(`Error guardando calificacion ${cal.id}:`, rowError);
          failCount++;
        }
      }
      if (failCount === 0) {
        toast.success(`${successCount} calificaciones guardadas exitosamente`);
      } else if (successCount > 0) {
        toast.success(`${successCount} guardadas, ${failCount} con error`);
      } else {
        throw new Error('No se pudo guardar ninguna calificación');
      }
    } catch (error) {
      toast.error(error.response?.data?.message || error.message || 'Error al guardar');
    } finally {
      setSaving(false);
    }
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

      {/* Buscador de alumnos */}
      <Card>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          Buscar Alumno
        </label>
        <div className="relative" ref={searchRef}>
          <div className="relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por nombre o número de control..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setShowSuggestions(true);
                if (selectedAlumno) {
                  setSelectedAlumno(null);
                  setCalificaciones([]);
                }
              }}
              onFocus={() => {
                if (searchTerm.trim()) setShowSuggestions(true);
              }}
              onKeyDown={handleKeyDown}
              className="w-full pl-12 pr-10 py-2.5 rounded-xl input-glass"
            />
            {searchTerm && (
              <button
                onClick={handleClear}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={18} />
              </button>
            )}
          </div>

          {searchLoading && (
            <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 p-4 text-center">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary-500 border-t-transparent mx-auto"></div>
            </div>
          )}

          {showSuggestions && !searchLoading && searchResults.length > 0 && (
            <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
              {searchResults.map((alumno, index) => (
                <button
                  key={alumno.id}
                  onClick={() => handleSelectSuggestion(alumno)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  className={`w-full flex items-center gap-3 p-3 transition-colors text-left ${
                    index === highlightedIndex ? 'bg-primary-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <User size={18} className="text-gray-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 truncate">
                      {alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno || ''}
                    </p>
                    <p className="text-sm text-gray-500">{alumno.numero_control}</p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {showSuggestions && !searchLoading && searchTerm.trim() && searchResults.length === 0 && (
            <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 p-4 text-center">
              <p className="text-gray-400 text-sm">No se encontraron alumnos</p>
            </div>
          )}
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
            <Card>
              <TableSkeleton rows={5} columns={10} />
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
                  <span className="text-gray-500">Aprobado (≥8)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded grade-failed"></div>
                  <span className="text-gray-500">Reprobado (&lt;8)</span>
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
