import { useState, useEffect } from 'react';
import { getAsignaciones, createAsignacion, updateAsignacion, deleteAsignacion } from '../../api/asignaciones';
import { getProfesores } from '../../api/profesores';
import { getMaterias } from '../../api/materias';
import { getGrupos } from '../../api/grupos';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Plus, Edit, Trash2, Calendar, Users } from 'lucide-react';

export default function AdminAsignaciones() {
  const [asignaciones, setAsignaciones] = useState([]);
  const [profesores, setProfesores] = useState([]);
  const [materias, setMaterias] = useState([]);
  const [grupos, setGrupos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [selectedAsignacion, setSelectedAsignacion] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    profesor_id: '',
    materia_id: '',
    grupo_id: '',
    fecha_inicio: '',
    fecha_fin: '',
    activo: true,
  });
  
  // Filtrado dinámico
  const [selectedGrupoId, setSelectedGrupoId] = useState('');
  const [grupoCarreraId, setGrupoCarreraId] = useState(null);
  
  const [saving, setSaving] = useState(false);
  const [filtroProfesor, setFiltroProfesor] = useState('');
  const [filtroGrupo, setFiltroGrupo] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [asigData, profData, matData, grpData] = await Promise.all([
        getAsignaciones(),
        getProfesores(),
        getMaterias(),
        getGrupos(),
      ]);
      setAsignaciones(asigData || []);
      setProfesores(profData || []);
      setMaterias(matData || []);
      setGrupos(grpData || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Cuando se selecciona un grupo, obtener su carrera_id
  const handleGrupoChange = (grupoId) => {
    setFormData({ ...formData, grupo_id: grupoId, materia_id: '' });
    
    if (grupoId) {
      const grupo = grupos.find(g => g.id === parseInt(grupoId));
      if (grupo) {
        setGrupoCarreraId(grupo.carrera_id);
      }
    } else {
      setGrupoCarreraId(null);
    }
  };

  // Filtrar materias por la carrera del grupo seleccionado
  const materiasFiltradas = grupoCarreraId 
    ? materias.filter(m => m.carrera_id === grupoCarreraId)
    : [];

  const openNewModal = () => {
    setModalMode('create');
    setSelectedAsignacion(null);
    setGrupoCarreraId(null);
    setSelectedGrupoId('');
    
    const today = new Date();
    const nextMonth = new Date(today);
    nextMonth.setMonth(nextMonth.getMonth() + 4);
    
    setFormData({
      profesor_id: '',
      materia_id: '',
      grupo_id: '',
      fecha_inicio: today.toISOString().split('T')[0],
      fecha_fin: nextMonth.toISOString().split('T')[0],
      activo: true,
    });
    setShowModal(true);
  };

  const openEditModal = (asignacion) => {
    setModalMode('edit');
    setSelectedAsignacion(asignacion);
    setFormData({
      profesor_id: asignacion.profesor_id || '',
      materia_id: asignacion.materia_id || '',
      grupo_id: asignacion.grupo_id || '',
      fecha_inicio: asignacion.fecha_inicio || '',
      fecha_fin: asignacion.fecha_fin || '',
      activo: asignacion.activo !== undefined ? asignacion.activo : true,
    });
    // Setear la carrera del grupo para filtrar materias
    if (asignacion.grupo_id) {
      const grupo = grupos.find(g => g.id === asignacion.grupo_id);
      if (grupo) {
        setGrupoCarreraId(grupo.carrera_id);
      }
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedAsignacion(null);
    setGrupoCarreraId(null);
    setSelectedGrupoId('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (modalMode === 'edit' && selectedAsignacion) {
        await updateAsignacion(selectedAsignacion.id, formData);
      } else {
        await createAsignacion(formData);
      }
      closeModal();
      loadData();
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('¿Eliminar esta asignación?')) {
      try {
        await deleteAsignacion(id);
        loadData();
      } catch (error) {
        alert(error.response?.data?.error || 'Error al eliminar');
      }
    }
  };

  // Filtrar asignaciones
  const filteredAsignaciones = asignaciones.filter(a => {
    if (filtroProfesor && a.profesor_id !== parseInt(filtroProfesor)) return false;
    if (filtroGrupo && a.grupo_id !== parseInt(filtroGrupo)) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Asignaciones</h1>
          <p className="text-gray-500 mt-1">
            Asignar profesores a materias y grupos
          </p>
        </div>
        <Button onClick={openNewModal}>
          <Plus size={18} className="mr-2" />
          Nueva Asignación
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Filtrar por profesor
            </label>
            <select
              value={filtroProfesor}
              onChange={(e) => setFiltroProfesor(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="">Todos los profesores</option>
              {profesores.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.titulo} {p.nombre} {p.apellido_paterno}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Filtrar por grupo
            </label>
            <select
              value={filtroGrupo}
              onChange={(e) => setFiltroGrupo(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="">Todos los grupos</option>
              {grupos.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.nombre} - {g.carrera?.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Table */}
      {loading ? (
        <Card className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-500">Cargando asignaciones...</p>
        </Card>
      ) : filteredAsignaciones.length === 0 ? (
        <Card className="text-center py-12">
          <Calendar size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No hay asignaciones registradas</p>
          <p className="text-sm text-gray-400 mt-1">
            Crea la primera asignación para comenzar
          </p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Profesor
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Materia
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Grupo
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Período
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">
                    Puede Editar
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">
                    Estado
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredAsignaciones.map((a) => (
                  <tr key={a.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className="text-gray-800">
                        {a.profesor?.nombre} {a.profesor?.apellido_paterno}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-600">
                        {a.materia?.nombre}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="info">{a.grupo?.nombre}</Badge>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-500">
                        {a.fecha_inicio} - {a.fecha_fin}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={a.puede_editar ? 'success' : 'warning'}>
                        {a.puede_editar ? 'Sí' : 'No'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={a.activo ? 'success' : 'danger'}>
                        {a.activo ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openEditModal(a)}
                          className="p-2 hover:bg-primary-50 rounded-lg"
                        >
                          <Edit size={18} className="text-primary-500" />
                        </button>
                        <button
                          onClick={() => handleDelete(a.id)}
                          className="p-2 hover:bg-red-50 rounded-lg"
                        >
                          <Trash2 size={18} className="text-red-500" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-800">
                {modalMode === 'edit' ? 'Editar Asignación' : 'Nueva Asignación'}
              </h2>
              <button onClick={closeModal} className="p-2 hover:bg-gray-100 rounded-lg">
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* 1. Seleccionar Profesor */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Profesor *
                </label>
                <select
                  required
                  value={formData.profesor_id}
                  onChange={(e) => setFormData({ ...formData, profesor_id: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                >
                  <option value="">Seleccionar profesor</option>
                  {profesores.filter(p => p.activo).map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.titulo} {p.nombre} {p.apellido_paterno}
                    </option>
                  ))}
                </select>
              </div>

              {/* 2. Seleccionar Grupo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Grupo *
                </label>
                <select
                  required
                  value={formData.grupo_id}
                  onChange={(e) => handleGrupoChange(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                >
                  <option value="">Seleccionar grupo</option>
                  {grupos.filter(g => g.activo).map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.nombre} - {g.carrera?.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* 3. Seleccionar Materia (solo de la carrera del grupo) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Materia * 
                  <span className="text-gray-400 text-xs ml-2">
                    (solo materias de la carrera del grupo)
                  </span>
                </label>
                <select
                  required
                  value={formData.materia_id}
                  onChange={(e) => setFormData({ ...formData, materia_id: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  disabled={!formData.grupo_id}
                >
                  <option value="">
                    {formData.grupo_id 
                      ? `${materiasFiltradas.length} materias disponibles` 
                      : 'Selecciona un grupo primero'}
                  </option>
                  {materiasFiltradas.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre} ({m.codigo})
                    </option>
                  ))}
                </select>
              </div>

              {/* Fechas */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Fecha Inicio *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.fecha_inicio}
                    onChange={(e) => setFormData({ ...formData, fecha_inicio: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Fecha Fin *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.fecha_fin}
                    onChange={(e) => setFormData({ ...formData, fecha_fin: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="activo"
                  checked={formData.activo}
                  onChange={(e) => setFormData({ ...formData, activo: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-primary-500"
                />
                <label htmlFor="activo" className="text-sm text-gray-700">
                  Asignación activa
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <Button type="button" variant="ghost" onClick={closeModal}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving ? 'Guardando...' : modalMode === 'edit' ? 'Actualizar' : 'Crear'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}