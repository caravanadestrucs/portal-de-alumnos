import { useState, useEffect } from 'react';
import { getGrupos, createGrupo, updateGrupo, deleteGrupo, getIntegrantes, addIntegrante, removeIntegrante } from '../../api/grupos';
import { getCarreras } from '../../api/carreras';
import { getAlumnos } from '../../api/alumnos';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Plus, Edit, Trash2, Users, UserPlus, UserMinus, Search } from 'lucide-react';

export default function AdminGrupos() {
  const [grupos, setGrupos] = useState([]);
  const [carreras, setCarreras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showIntegrantesModal, setShowIntegrantesModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [selectedGrupo, setSelectedGrupo] = useState(null);
  const [integrantes, setIntegrantes] = useState([]);
  const [formData, setFormData] = useState({
    nombre: '',
    carrera_id: '',
    activo: true,
  });
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroCarrera, setFiltroCarrera] = useState('');
  
  // Para agregar integrantes
  const [alumnos, setAlumnos] = useState([]);
  const [busquedaAlumno, setBusquedaAlumno] = useState('');
  const [resultadosBusqueda, setResultadosBusqueda] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [integranteSaving, setIntegranteSaving] = useState(false);

  useEffect(() => {
    loadGrupos();
    loadCarreras();
  }, []);

  const loadGrupos = async () => {
    setLoading(true);
    try {
      const data = await getGrupos();
      setGrupos(data || []);
    } catch (error) {
      console.error('Error loading grupos:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCarreras = async () => {
    try {
      const data = await getCarreras();
      setCarreras(data || []);
    } catch (error) {
      console.error('Error loading carreras:', error);
    }
  };

  const loadIntegrantes = async (grupoId) => {
    try {
      const data = await getIntegrantes(grupoId);
      setIntegrantes(data || []);
    } catch (error) {
      console.error('Error loading integrantes:', error);
    }
  };

  const openNewModal = () => {
    setModalMode('create');
    setSelectedGrupo(null);
    setFormData({
      nombre: '',
      carrera_id: carreras.length > 0 ? carreras[0].id : '',
      activo: true,
    });
    setShowModal(true);
  };

  const openEditModal = (grupo) => {
    setModalMode('edit');
    setSelectedGrupo(grupo);
    setFormData({
      nombre: grupo.nombre || '',
      carrera_id: grupo.carrera_id || '',
      activo: grupo.activo !== undefined ? grupo.activo : true,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedGrupo(null);
  };

  const openIntegrantes = async (grupo) => {
    setSelectedGrupo(grupo);
    await loadIntegrantes(grupo.id);
    try {
      const data = await getAlumnos();
      setAlumnos(data || []);
    } catch (error) {
      console.error('Error loading alumnos:', error);
    }
    setBusquedaAlumno('');
    setResultadosBusqueda([]);
    setShowIntegrantesModal(true);
  };

  const closeIntegrantesModal = () => {
    setShowIntegrantesModal(false);
    setSelectedGrupo(null);
    setIntegrantes([]);
    setShowDropdown(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (modalMode === 'edit' && selectedGrupo) {
        await updateGrupo(selectedGrupo.id, formData);
      } else {
        await createGrupo(formData);
      }
      closeModal();
      loadGrupos();
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('¿Estás seguro de eliminar este grupo?')) {
      try {
        await deleteGrupo(id);
        loadGrupos();
      } catch (error) {
        alert(error.response?.data?.error || 'Error al eliminar');
      }
    }
  };

  // Buscador dinámico de alumnos - solo de la carrera del grupo
  const handleBusquedaChange = (e) => {
    const query = e.target.value;
    setBusquedaAlumno(query);
    
    if (query.length >= 2 && selectedGrupo) {
      // Filtrar alumnos que ya NO están en el grupo Y sean de la carrera del grupo
      const yaEnGrupo = integrantes.map(i => i.alumno_id);
      const carreraIdDelGrupo = selectedGrupo.carrera_id;
      
      const filtered = alumnos.filter(a => 
        !yaEnGrupo.includes(a.id) &&  // No esté ya en el grupo
        a.carrera_id === carreraIdDelGrupo &&  // Sea de la misma carrera
        (
          a.nombre?.toLowerCase().includes(query.toLowerCase()) ||
          a.apellido_paterno?.toLowerCase().includes(query.toLowerCase()) ||
          a.numero_control?.toLowerCase().includes(query.toLowerCase()) ||
          a.email?.toLowerCase().includes(query.toLowerCase())
        )
      ).slice(0, 10); // Máximo 10 resultados
      
      setResultadosBusqueda(filtered);
      setShowDropdown(true);
    } else {
      setShowDropdown(false);
    }
  };

  const seleccionarAlumno = async (alumno) => {
    setIntegranteSaving(true);
    try {
      await addIntegrante(selectedGrupo.id, parseInt(alumno.id));
      await loadIntegrantes(selectedGrupo.id);
      setBusquedaAlumno('');
      setResultadosBusqueda([]);
      setShowDropdown(false);
    } catch (error) {
      alert(error.response?.data?.error || 'Error al agregar integrante');
    } finally {
      setIntegranteSaving(false);
    }
  };

  const handleRemoveIntegrante = async (alumnoId) => {
    if (!confirm('¿Remover este alumno del grupo?')) return;
    try {
      await removeIntegrante(selectedGrupo.id, alumnoId);
      await loadIntegrantes(selectedGrupo.id);
    } catch (error) {
      alert(error.response?.data?.error || 'Error al remover');
    }
  };

  // Filtrar grupos
  const filteredGrupos = grupos.filter(g => {
    if (!searchTerm && !filtroCarrera) return true;
    if (filtroCarrera && g.carrera_id !== parseInt(filtroCarrera)) return false;
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return g.nombre?.toLowerCase().includes(search);
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Grupos</h1>
          <p className="text-gray-500 mt-1">
            Gestión de grupos y sus integrantes
          </p>
        </div>
        <Button onClick={openNewModal}>
          <Plus size={18} className="mr-2" />
          Nuevo Grupo
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Buscar grupo
            </label>
            <input
              type="text"
              placeholder="Buscar por nombre..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Filtrar por carrera
            </label>
            <select
              value={filtroCarrera}
              onChange={(e) => setFiltroCarrera(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="">Todas las carreras</option>
              {carreras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
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
          <p className="mt-4 text-gray-500">Cargando grupos...</p>
        </Card>
      ) : filteredGrupos.length === 0 ? (
        <Card className="text-center py-12">
          <Users size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No hay grupos registrados</p>
          <p className="text-sm text-gray-400 mt-1">
            Crea el primer grupo para comenzar
          </p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Grupo
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Carrera
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">
                    Integrantes
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
                {filteredGrupos.map((grupo) => (
                  <tr
                    key={grupo.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">
                      <span className="font-medium text-gray-800">
                        {grupo.nombre}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-600">
                        {grupo.carrera?.nombre || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant="info">
                        {grupo.total_integrantes || 0}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={grupo.activo ? 'success' : 'danger'}>
                        {grupo.activo ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openIntegrantes(grupo)}
                          className="p-2 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Ver integrantes"
                        >
                          <Users size={18} className="text-blue-500" />
                        </button>
                        <button
                          onClick={() => openEditModal(grupo)}
                          className="p-2 hover:bg-primary-50 rounded-lg transition-colors"
                        >
                          <Edit size={18} className="text-primary-500" />
                        </button>
                        <button
                          onClick={() => handleDelete(grupo.id)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors"
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

      {/* Modal Grupo */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-800">
                {modalMode === 'edit' ? 'Editar Grupo' : 'Nuevo Grupo'}
              </h2>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Nombre del Grupo *
                </label>
                <input
                  type="text"
                  required
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="Ej: A, B, 1-A"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Carrera *
                </label>
                <select
                  required
                  value={formData.carrera_id}
                  onChange={(e) => setFormData({ ...formData, carrera_id: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                >
                  <option value="">Seleccionar carrera</option>
                  {carreras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
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
                  Grupo activo
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

      {/* Modal Integrantes con buscador dinámico */}
      {showIntegrantesModal && selectedGrupo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-800">
                Integrantes - Grupo {selectedGrupo.nombre}
              </h2>
              <button onClick={closeIntegrantesModal} className="p-2 hover:bg-gray-100 rounded-lg">
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Buscador dinámico */}
              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Buscar y agregar alumno
                </label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Buscar por nombre, número de control o email..."
                    value={busquedaAlumno}
                    onChange={handleBusquedaChange}
                    onFocus={() => busquedaAlumno.length >= 2 && setShowDropdown(true)}
                    className="w-full px-4 py-2.5 pl-10 rounded-xl input-glass"
                  />
                  <Search size={18} className="absolute left-3 top-3 text-gray-400" />
                </div>
                
                {/* Dropdown de resultados */}
                {showDropdown && resultadosBusqueda.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {resultadosBusqueda.map((alumno) => (
                      <button
                        key={alumno.id}
                        onClick={() => seleccionarAlumno(alumno)}
                        disabled={integranteSaving}
                        className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b border-gray-100 last:border-b-0"
                      >
                        <div>
                          <p className="font-medium text-gray-800">
                            {alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno}
                          </p>
                          <p className="text-sm text-gray-500">
                            {alumno.numero_control} • {alumno.email}
                          </p>
                        </div>
                        <UserPlus size={18} className="text-green-500" />
                      </button>
                    ))}
                  </div>
                )}
                {showDropdown && busquedaAlumno.length >= 2 && resultadosBusqueda.length === 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center text-gray-500">
                    No se encontraron alumnos
                  </div>
                )}
              </div>

              {/* Lista de integrantes */}
              <div className="space-y-2">
                {integrantes.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">
                    No hay integrantes en este grupo
                  </p>
                ) : (
                  <>
                    <h3 className="font-medium text-gray-700">
                      Lista de integrantes ({integrantes.length})
                    </h3>
                    {integrantes.map((i) => (
                      <div
                        key={i.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-800">
                            {i.alumno?.nombre} {i.alumno?.apellido_paterno}
                          </p>
                          <p className="text-sm text-gray-500">
                            {i.alumno?.numero_control}
                          </p>
                        </div>
                        <button
                          onClick={() => handleRemoveIntegrante(i.alumno_id)}
                          className="p-2 hover:bg-red-50 rounded-lg"
                        >
                          <UserMinus size={18} className="text-red-500" />
                        </button>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}