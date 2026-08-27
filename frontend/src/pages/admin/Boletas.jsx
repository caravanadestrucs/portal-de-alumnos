import { useState, useEffect, useCallback } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';
import { Download, FileText, Search, Loader2, CheckSquare, Square, DownloadCloud } from 'lucide-react';
import { getAlumnosBoletas, descargarBoleta, descargarBoletasMultiples, previewBoleta } from '../../api/boletas';
import { getCarreras } from '../../api/carreras';

export default function AdminBoletas() {
  const toast = useToast();
  const [alumnos, setAlumnos] = useState([]);
  const [carreras, setCarreras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState({});
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [filters, setFilters] = useState({ carrera_id: '', search: '' });
  const [preview, setPreview] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const loadCarreras = async () => {
    try {
      const res = await getCarreras();
      setCarreras(res.carreras || []);
    } catch {
      // ignore
    }
  };

  const loadAlumnos = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.carrera_id) params.carrera_id = filters.carrera_id;
      if (filters.search) params.search = filters.search;
      const res = await getAlumnosBoletas(params);
      setAlumnos(res.alumnos || []);
    } catch (error) {
      toast.error('Error al cargar alumnos');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadCarreras();
  }, []);

  useEffect(() => {
    loadAlumnos();
  }, [loadAlumnos]);

  const handleDownload = async (alumnoId) => {
    setDownloading((prev) => ({ ...prev, [alumnoId]: true }));
    try {
      await descargarBoleta(alumnoId);
      toast.success('Boleta descargada exitosamente');
    } catch (error) {
      toast.error('Error al descargar boleta');
    } finally {
      setDownloading((prev) => ({ ...prev, [alumnoId]: false }));
    }
  };

  // --- Task 15: selectable logic — solo alumnos con calificaciones deben ser seleccionables/descargables ---
  // Fuente de verdad: alumno.calificaciones_count > 0 (viene del backend getAlumnosBoletas)
  // Fallback: si existe alumno.tieneCalificaciones o alumno.calificaciones?.length > 0 también cuenta
  const isSelectable = (a) => {
    if (typeof a.calificaciones_count === 'number') return a.calificaciones_count > 0;
    if (typeof a.tieneCalificaciones === 'boolean') return a.tieneCalificaciones;
    if (Array.isArray(a.calificaciones)) return a.calificaciones.length > 0;
    // Si no hay flag discriminador, se asume selectable para no bloquear — el warning genérico se mostrará igual
    return true;
  };
  const selectableAlumnos = alumnos.filter(isSelectable);
  const skippedCount = alumnos.length - selectableAlumnos.length;
  const selectableIds = selectableAlumnos.map((a) => a.id);
  const allSelectableSelected = selectableAlumnos.length > 0 && selectableIds.every((id) => selectedIds.has(id));

  const handleDownloadAll = async () => {
    // Si hay selección explícita, filtrar solo los seleccionables
    let idsToDownload;
    if (selectedIds.size > 0) {
      idsToDownload = Array.from(selectedIds).filter((id) =>
        selectableAlumnos.some((a) => a.id === id)
      );
      if (idsToDownload.length === 0) {
        toast.error('Los alumnos seleccionados no tienen calificaciones para generar boleta');
        return;
      }
      if (idsToDownload.length < selectedIds.size) {
        toast.error(`${selectedIds.size - idsToDownload.length} alumnos sin calificaciones serán omitidos`);
      }
    } else {
      idsToDownload = selectableIds;
    }

    if (idsToDownload.length === 0) {
      toast.error('No hay alumnos con calificaciones para descargar');
      return;
    }

    setDownloading((prev) => ({ ...prev, all: true }));
    try {
      await descargarBoletasMultiples(idsToDownload);
      toast.success(`${idsToDownload.length} boletas descargadas`);
    } catch (error) {
      toast.error('Error al descargar boletas');
    } finally {
      setDownloading((prev) => ({ ...prev, all: false }));
    }
  };

  const toggleSelect = (id) => {
    const alumno = alumnos.find((a) => a.id === id);
    if (alumno && !isSelectable(alumno)) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    // Task 15: solo selecciona alumnos con calificaciones
    if (allSelectableSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(selectableIds));
    }
  };

  const handlePreview = async (alumnoId) => {
    try {
      const res = await previewBoleta(alumnoId);
      setPreview(res);
      setShowPreview(true);
    } catch (error) {
      toast.error('Error al obtener vista previa');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Boletas de Calificaciones</h1>
          <p className="text-gray-500 mt-1">
            Genera y descarga boletas de calificaciones para los alumnos
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={toggleSelectAll}
            disabled={selectableAlumnos.length === 0}
            title={skippedCount > 0 ? `${skippedCount} sin calificaciones serán omitidos` : undefined}
          >
            {allSelectableSelected ? <CheckSquare size={18} /> : <Square size={18} />}
            {selectedIds.size > 0
              ? `Seleccionados ${selectedIds.size}`
              : 'Seleccionar todos'}
          </Button>
          <Button
            onClick={handleDownloadAll}
            loading={downloading.all}
            disabled={selectableAlumnos.length === 0}
          >
            <DownloadCloud size={18} />
            {selectedIds.size > 0
              ? `Descargar ${selectedIds.size} boletas`
              : 'Descargar todas'}
          </Button>
        </div>
      </div>
      {/* Task 15 warning: alumnos sin calificaciones */}
      {skippedCount > 0 && !loading && alumnos.length > 0 && (
        <p className="text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
          {skippedCount} alumno{skippedCount !== 1 ? 's' : ''} sin calificaciones {skippedCount !== 1 ? 'serán omitidos' : 'será omitido'} al descargar
        </p>
      )}
      {selectedIds.size > 0 && skippedCount > 0 && (
        <p className="text-sm text-amber-600">
          {skippedCount} alumnos sin calificaciones serán omitidos
        </p>
      )}

      {/* Filters */}
      <Card>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Carrera</label>
            <select
              value={filters.carrera_id}
              onChange={(e) => setFilters((prev) => ({ ...prev, carrera_id: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            >
              <option value="">Todas las carreras</option>
              {carreras.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Buscar alumno</label>
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Nombre, apellido o matrícula..."
                value={filters.search}
                onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Preview Modal */}
      {showPreview && preview && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={() => setShowPreview(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Vista previa de Boleta</h2>
              <button onClick={() => setShowPreview(false)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-xs text-gray-500">Alumno</p>
                  <p className="font-medium">{preview.alumno.nombre_completo}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Matrícula</p>
                  <p className="font-medium">{preview.alumno.numero_control || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Carrera</p>
                  <p className="font-medium">{preview.alumno.carrera}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Promedio</p>
                  <p className="font-medium text-lg">{preview.promedio}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                {preview.materias_aprobadas} de {preview.total_materias} materias aprobadas
              </p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Materia</th>
                    <th className="text-center py-2">Calificación</th>
                    <th className="text-center py-2">Periodo</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.calificaciones.map((c, i) => (
                    <tr key={i} className="border-b border-gray-100">
                      <td className="py-2">{c.materia}</td>
                      <td className="py-2 text-center font-medium">{c.calificacion}</td>
                      <td className="py-2 text-center text-gray-500">{c.periodo} {c.anio}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" onClick={() => setShowPreview(false)}>Cerrar</Button>
              <Button onClick={() => handleDownload(preview.alumno.id)}>
                <Download size={18} />
                Descargar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Alumnos list */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={32} className="animate-spin text-primary-500" />
          </div>
        ) : alumnos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText size={48} className="mx-auto mb-3 text-gray-300" />
            <p>No se encontraron alumnos</p>
            <p className="text-sm mt-1">Los alumnos deben tener calificaciones registradas para generar boletas</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 w-10">
                    <input
                      type="checkbox"
                      checked={allSelectableSelected}
                      onChange={toggleSelectAll}
                      disabled={selectableAlumnos.length === 0}
                      title={selectableAlumnos.length === 0 ? 'No hay alumnos con calificaciones' : skippedCount > 0 ? `${skippedCount} sin calificaciones excluidos` : undefined}
                      className="rounded border-gray-300 disabled:opacity-40"
                    />
                  </th>
                  <th className="text-left py-3 px-3">Matrícula</th>
                  <th className="text-left py-3 px-3">Nombre</th>
                  <th className="text-left py-3 px-3">Carrera</th>
                  <th className="text-center py-3 px-3">Califs.</th>
                  <th className="text-right py-3 px-3">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {alumnos.map((alumno) => (
                  <tr key={alumno.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(alumno.id)}
                        onChange={() => toggleSelect(alumno.id)}
                        disabled={!isSelectable(alumno)}
                        title={!isSelectable(alumno) ? 'Sin calificaciones — no seleccionable' : undefined}
                        className="rounded border-gray-300 disabled:opacity-40 disabled:cursor-not-allowed"
                      />
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-600">{alumno.numero_control || '—'}</td>
                    <td className="py-3 px-3 font-medium">{alumno.nombre_completo}</td>
                    <td className="py-3 px-3 text-gray-600">{alumno.carrera_nombre}</td>
                    <td className="py-3 px-3 text-center">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                        alumno.calificaciones_count > 0
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }`}>
                        {alumno.calificaciones_count}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex gap-1 justify-end">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handlePreview(alumno.id)}
                          title="Vista previa"
                          disabled={alumno.calificaciones_count === 0}
                        >
                          <FileText size={16} />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownload(alumno.id)}
                          loading={downloading[alumno.id]}
                          disabled={alumno.calificaciones_count === 0}
                        >
                          <Download size={16} />
                          Descargar
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
