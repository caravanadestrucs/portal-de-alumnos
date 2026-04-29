import { useState, useEffect } from 'react';
import { getMaterias, createMateria, updateMateria, deleteMateria } from '../../api/materias';
import { getCarreras } from '../../api/carreras';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { Plus, Edit, Trash2, BookOpen, ChevronLeft, ChevronRight, Search } from 'lucide-react';

const ITEMS_PER_PAGE = 50;

export default function AdminMaterias() {
  const [materias, setMaterias] = useState([]);
  const [carreras, setCarreras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingMateria, setEditingMateria] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    codigo: '',
    creditos: 0,
    carrera_id: '',
  });
  const [saving, setSaving] = useState(false);

  // Filtros y paginación
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroCarrera, setFiltroCarrera] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [materiasData, carrerasData] = await Promise.all([
        getMaterias(),
        getCarreras(),
      ]);
      setMaterias(materiasData || []);
      setCarreras(carrerasData || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filtrar materias
  const filteredMaterias = materias.filter(m => {
    // Filtro por carrera
    if (filtroCarrera && m.carrera_id !== parseInt(filtroCarrera)) {
      return false;
    }
    // Filtro por búsqueda
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        m.nombre?.toLowerCase().includes(search) ||
        m.codigo?.toLowerCase().includes(search)
      );
    }
    return true;
  });

  // Paginación
  const totalPages = Math.ceil(filteredMaterias.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedMaterias = filteredMaterias.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  // Resetear página cuando cambia el filtro
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filtroCarrera]);

  const openNewModal = () => {
    setEditingMateria(null);
    setFormData({
      nombre: '',
      codigo: '',
      creditos: 0,
      carrera_id: carreras.length > 0 ? carreras[0].id : '',
    });
    setShowModal(true);
  };

  const openEditModal = (materia) => {
    setEditingMateria(materia);
    setFormData({
      nombre: materia.nombre || '',
      codigo: materia.codigo || '',
      creditos: materia.creditos || 0,
      carrera_id: materia.carrera_id || '',
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingMateria(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (editingMateria) {
        await updateMateria(editingMateria.id, formData);
      } else {
        await createMateria(formData);
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
    if (confirm('¿Eliminar esta materia?')) {
      try {
        await deleteMateria(id);
        loadData();
      } catch (error) {
        alert(error.response?.data?.error || 'Error al eliminar');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Materias</h1>
          <p className="text-gray-500 mt-1">
            Gestión de materias por carrera
          </p>
        </div>
        <Button onClick={openNewModal}>
          <Plus size={18} className="mr-2" />
          Nueva Materia
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Buscar materia
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar por nombre o código..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2.5 pl-10 rounded-xl input-glass"
              />
              <Search size={18} className="absolute left-3 top-3 text-gray-400" />
            </div>
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

      {/* Info */}
      <div className="text-sm text-gray-500">
        Mostrando {paginatedMaterias.length} de {filteredMaterias.length} materias
        {filtroCarrera && ` (filtrado)`}
      </div>

      {/* Table */}
      {loading ? (
        <Card className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-500">Cargando...</p>
        </Card>
      ) : paginatedMaterias.length === 0 ? (
        <Card className="text-center py-12">
          <BookOpen size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">
            {searchTerm || filtroCarrera ? 'No hay materias que coincidan' : 'No hay materias registradas'}
          </p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Código
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Nombre
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Carrera
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">
                    Créditos
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedMaterias.map((materia) => (
                  <tr
                    key={materia.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">
                      <span className="text-gray-800 font-medium">
                        {materia.codigo}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-800">
                        {materia.nombre}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-600">
                        {materia.carrera?.nombre || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="text-gray-600">
                        {materia.creditos || 0}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openEditModal(materia)}
                          className="p-2 hover:bg-primary-50 rounded-lg"
                        >
                          <Edit size={16} className="text-primary-600" />
                        </button>
                        <button
                          onClick={() => handleDelete(materia.id)}
                          className="p-2 hover:bg-red-50 rounded-lg"
                        >
                          <Trash2 size={16} className="text-red-500" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-500">
                Página {currentPage} de {totalPages}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft size={18} />
                </Button>
                
                {/* Números de página */}
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`w-8 h-8 rounded-lg text-sm ${
                          currentPage === pageNum
                            ? 'bg-primary-500 text-white'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight size={18} />
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-800">
                {editingMateria ? 'Editar Materia' : 'Nueva Materia'}
              </h2>
              <button onClick={closeModal} className="p-2 hover:bg-gray-100 rounded-lg">
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Código *
                </label>
                <input
                  type="text"
                  required
                  value={formData.codigo}
                  onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="Ej: ISC101"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Nombre *
                </label>
                <input
                  type="text"
                  required
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="Nombre de la materia"
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
                  <option value="">Seleccionar</option>
                  {carreras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Créditos
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.creditos}
                  onChange={(e) => setFormData({ ...formData, creditos: parseInt(e.target.value) || 0 })}
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <Button type="button" variant="ghost" onClick={closeModal}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving ? 'Guardando...' : editingMateria ? 'Actualizar' : 'Crear'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}