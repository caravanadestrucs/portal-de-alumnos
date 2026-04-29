import { useState, useEffect } from 'react';
import { getProfesores, createProfesor, updateProfesor, deleteProfesor } from '../../api/profesores';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Plus, Edit, Trash2, UserCheck, Users } from 'lucide-react';

export default function AdminProfesores() {
  const [profesores, setProfesores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [selectedProfesor, setSelectedProfesor] = useState(null);
  const [formData, setFormData] = useState({
    numero_empleado: '',
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    titulo: '',
    email: '',
    password: '',
    activo: true,
  });
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadProfesores();
  }, []);

  const loadProfesores = async () => {
    setLoading(true);
    try {
      const data = await getProfesores();
      setProfesores(data || []);
    } catch (error) {
      console.error('Error loading profesores:', error);
    } finally {
      setLoading(false);
    }
  };

  const openNewModal = () => {
    setModalMode('create');
    setSelectedProfesor(null);
    setFormData({
      numero_empleado: '',
      nombre: '',
      apellido_paterno: '',
      apellido_materno: '',
      titulo: '',
      email: '',
      password: '',
      activo: true,
    });
    setShowModal(true);
  };

  const openEditModal = (profesor) => {
    setModalMode('edit');
    setSelectedProfesor(profesor);
    setFormData({
      numero_empleado: profesor.numero_empleado || '',
      nombre: profesor.nombre || '',
      apellido_paterno: profesor.apellido_paterno || '',
      apellido_materno: profesor.apellido_materno || '',
      titulo: profesor.titulo || '',
      email: profesor.email || '',
      password: '', // No mostrar password
      activo: profesor.activo !== undefined ? profesor.activo : true,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedProfesor(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (modalMode === 'edit' && selectedProfesor) {
        // No enviar password vacío
        const dataToSend = { ...formData };
        if (!dataToSend.password) {
          delete dataToSend.password;
        }
        await updateProfesor(selectedProfesor.id, dataToSend);
      } else {
        await createProfesor(formData);
      }
      closeModal();
      loadProfesores();
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('¿Estás seguro de eliminar este professor?')) {
      try {
        await deleteProfesor(id);
        loadProfesores();
      } catch (error) {
        alert(error.response?.data?.error || 'Error al eliminar');
      }
    }
  };

  // Filtrar profesores
  const filteredProfesores = profesores.filter(p => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      p.nombre?.toLowerCase().includes(search) ||
      p.apellido_paterno?.toLowerCase().includes(search) ||
      p.email?.toLowerCase().includes(search) ||
      p.numero_empleado?.toLowerCase().includes(search)
    );
  });

  const titulos = ['Lic.', 'Ing.', 'Mtro.', 'Mtra.', 'Dr.', 'Dra.', 'PhD'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Profesores</h1>
          <p className="text-gray-500 mt-1">
            Gestión de profesores
          </p>
        </div>
        <Button onClick={openNewModal}>
          <Plus size={18} className="mr-2" />
          Nuevo Profesor
        </Button>
      </div>

      {/* Search */}
      <Card>
        <div className="relative">
          <input
            type="text"
            placeholder="Buscar profesores..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2.5 pl-10 rounded-xl input-glass"
          />
          <Users size={18} className="absolute left-3 top-3 text-gray-400" />
        </div>
      </Card>

      {/* Table */}
      {loading ? (
        <Card className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-500">Cargando profesores...</p>
        </Card>
      ) : filteredProfesores.length === 0 ? (
        <Card className="text-center py-12">
          <Users size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">
            No hay profesores registrados
          </p>
          <p className="text-sm text-gray-400 mt-1">
            Crea el primer profesor para comenzar
          </p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    No. Empleado
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Nombre
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Título
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Email
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
                {filteredProfesores.map((profesor) => (
                  <tr
                    key={profesor.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">
                      <span className="text-gray-800 font-medium">
                        {profesor.numero_empleado}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-800">
                        {profesor.nombre} {profesor.apellido_paterno}{' '}
                        {profesor.apellido_materno}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-600">
                        {profesor.titulo || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-600">
                        {profesor.email}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={profesor.activo ? 'success' : 'danger'}>
                        {profesor.activo ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openEditModal(profesor)}
                          className="p-2 hover:bg-primary-50 rounded-lg transition-colors"
                        >
                          <Edit size={18} className="text-primary-500" />
                        </button>
                        <button
                          onClick={() => handleDelete(profesor.id)}
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

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-800">
                {modalMode === 'edit' ? 'Editar Profesor' : 'Nuevo Profesor'}
              </h2>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Número de Empleado *
                </label>
                <input
                  type="text"
                  required
                  value={formData.numero_empleado}
                  onChange={(e) =>
                    setFormData({ ...formData, numero_empleado: e.target.value })
                  }
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="Ejem: EMP001"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Nombre(s) *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.nombre}
                    onChange={(e) =>
                      setFormData({ ...formData, nombre: e.target.value })
                    }
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                    placeholder="Nombre"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Apellido Paterno *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.apellido_paterno}
                    onChange={(e) =>
                      setFormData({ ...formData, apellido_paterno: e.target.value })
                    }
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Apellido Materno
                  </label>
                  <input
                    type="text"
                    value={formData.apellido_materno}
                    onChange={(e) =>
                      setFormData({ ...formData, apellido_materno: e.target.value })
                    }
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Título
                  </label>
                  <select
                    value={formData.titulo || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, titulo: e.target.value })
                    }
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  >
                    <option value="">Seleccionar</option>
                    {titulos.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Email *
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="correo@universidad.edu.mx"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Contraseña {modalMode === 'edit' ? '(dejar vacío para mantener)' : '*'}
                </label>
                <input
                  type="password"
                  required={modalMode === 'create'}
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="••••••••"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="activo"
                  checked={formData.activo}
                  onChange={(e) =>
                    setFormData({ ...formData, activo: e.target.checked })
                  }
                  className="w-4 h-4 rounded border-gray-300 text-primary-500"
                />
                <label htmlFor="activo" className="text-sm text-gray-700">
                  Profesor activo
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <Button type="button" variant="ghost" onClick={closeModal}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving
                    ? 'Guardando...'
                    : modalMode === 'edit'
                    ? 'Actualizar'
                    : 'Crear'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}