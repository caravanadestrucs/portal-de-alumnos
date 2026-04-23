import { useState } from 'react';
import { useFetch } from '../../hooks/useFetch';
import * as api from '../../api/materias';
import * as carrerasApi from '../../api/carreras';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import { Plus, Edit, Trash2, BookOpen } from 'lucide-react';

export default function AdminMaterias() {
  const { data: materias, loading, refetch } = useFetch(api.getMaterias);
  const { data: carreras } = useFetch(carrerasApi.getCarreras);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMateria, setEditingMateria] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    codigo: '',
    creditos: 0,
    carrera_id: '',
  });
  const [saving, setSaving] = useState(false);

  const columns = [
    {
      key: 'codigo',
      header: 'Código',
      width: '100px',
    },
    {
      key: 'nombre',
      header: 'Nombre',
    },
    {
      key: 'creditos',
      header: 'Créditos',
      width: '100px',
      render: (row) => row.creditos || '-',
    },
    {
      key: 'carrera',
      header: 'Carrera',
      render: (row) => row.carrera?.nombre || '-',
    },
    {
      key: 'actions',
      header: 'Acciones',
      width: '150px',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              openEditModal(row);
            }}
            className="p-2 hover:bg-primary-50 rounded-lg transition-colors"
          >
            <Edit size={16} className="text-primary-600" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(row.id);
            }}
            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Trash2 size={16} className="text-red-500" />
          </button>
        </div>
      ),
    },
  ];

  const openNewModal = () => {
    setEditingMateria(null);
    setFormData({
      nombre: '',
      codigo: '',
      creditos: 0,
      carrera_id: '',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (materia) => {
    setEditingMateria(materia);
    setFormData({
      nombre: materia.nombre,
      codigo: materia.codigo,
      creditos: materia.creditos || 0,
      carrera_id: materia.carrera_id || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (editingMateria) {
        await api.updateMateria(editingMateria.id, formData);
      } else {
        await api.createMateria(formData);
      }
      setIsModalOpen(false);
      refetch();
    } catch (error) {
      alert(error.response?.data?.message || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('¿Estás seguro de eliminar esta materia?')) {
      try {
        await api.deleteMateria(id);
        refetch();
      } catch (error) {
        alert(error.response?.data?.message || 'Error al eliminar');
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
            Gestionar materias por carrera
          </p>
        </div>
        <Button onClick={openNewModal}>
          <Plus size={18} />
          Nueva Materia
        </Button>
      </div>

      {/* Table */}
      <Table
        columns={columns}
        data={materias || []}
        loading={loading}
        emptyMessage="No hay materias registradas"
      />

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingMateria ? 'Editar Materia' : 'Nueva Materia'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSubmit} loading={saving}>
              {editingMateria ? 'Guardar Cambios' : 'Crear Materia'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nombre"
            name="nombre"
            value={formData.nombre}
            onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Código"
              name="codigo"
              value={formData.codigo}
              onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
              required
              helper="Ej: MAT-101"
            />

            <Input
              label="Créditos"
              name="creditos"
              type="number"
              min="0"
              value={formData.creditos}
              onChange={(e) => setFormData({ ...formData, creditos: parseInt(e.target.value) || 0 })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Carrera
            </label>
            <select
              name="carrera_id"
              value={formData.carrera_id}
              onChange={(e) => setFormData({ ...formData, carrera_id: e.target.value })}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
              required
            >
              <option value="">Seleccionar carrera</option>
              {Array.isArray(carreras) &&
                carreras.map((carrera) => (
                  <option key={carrera.id} value={carrera.id}>
                    {carrera.nombre}
                  </option>
                ))}
            </select>
          </div>
        </form>
      </Modal>
    </div>
  );
}
