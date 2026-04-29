import { useState, useEffect } from 'react';
import { useFetch } from '../../hooks/useFetch';
import { getAlumnos, createAlumno, updateAlumno, deleteAlumno } from '../../api/alumnos';
import { getCarreras } from '../../api/carreras';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Badge from '../../components/ui/Badge';
import { Plus, Search, Edit, Trash2, UserPlus } from 'lucide-react';

export default function AdminAlumnos() {
  const { data: alumnos, loading, refetch } = useFetch(getAlumnos);
  const { data: carreras } = useFetch(getCarreras);

  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAlumno, setEditingAlumno] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    email: '',
    numero_control: '',
    password: '',
    carrera_id: '',
  });
  const [saving, setSaving] = useState(false);

  const filteredAlumnos = Array.isArray(alumnos)
    ? alumnos.filter((alumno) => {
        const fullName = `${alumno.nombre} ${alumno.apellido_paterno} ${alumno.apellido_materno}`.toLowerCase();
        return (
          fullName.includes(searchTerm.toLowerCase()) ||
          alumno.numero_control?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          alumno.email?.toLowerCase().includes(searchTerm.toLowerCase())
        );
      })
    : [];

  const columns = [
    {
      key: 'numero_control',
      header: 'No. Control',
      width: '120px',
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (row) =>
        `${row.nombre} ${row.apellido_paterno} ${row.apellido_materno || ''}`.trim(),
    },
    {
      key: 'email',
      header: 'Email',
    },
    {
      key: 'carrera',
      header: 'Carrera',
      render: (row) => row.carrera?.nombre || '-',
    },
    {
      key: 'activo',
      header: 'Estado',
      render: (row) => (
        <Badge variant={row.activo ? 'success' : 'danger'}>
          {row.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
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
    setEditingAlumno(null);
    setFormData({
      nombre: '',
      apellido_paterno: '',
      apellido_materno: '',
      email: '',
      numero_control: '',
      password: '',
      carrera_id: '',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (alumno) => {
    setEditingAlumno(alumno);
    setFormData({
      nombre: alumno.nombre,
      apellido_paterno: alumno.apellido_paterno,
      apellido_materno: alumno.apellido_materno || '',
      email: alumno.email,
      numero_control: alumno.numero_control,
      password: '',
      carrera_id: alumno.carrera_id || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (editingAlumno) {
        const { password, ...updateData } = formData;
        await updateAlumno(editingAlumno.id, updateData);
      } else {
        await createAlumno(formData);
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
    if (confirm('¿Estás seguro de eliminar este alumno?')) {
      try {
        await deleteAlumno(id);
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
          <h1 className="text-3xl font-bold text-gray-800">Alumnos</h1>
          <p className="text-gray-500 mt-1">
            Gestionar alumnos registrados
          </p>
        </div>
        <Button onClick={openNewModal}>
          <UserPlus size={18} />
          Nuevo Alumno
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por nombre, número de control o email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-12 pr-4 py-3 rounded-xl input-glass"
        />
      </div>

      {/* Table */}
      <Table
        columns={columns}
        data={filteredAlumnos}
        loading={loading}
        emptyMessage="No hay alumnos registrados"
      />

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingAlumno ? 'Editar Alumno' : 'Nuevo Alumno'}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSubmit} loading={saving}>
              {editingAlumno ? 'Guardar Cambios' : 'Crear Alumno'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Nombre"
              name="nombre"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              required
            />
            <Input
              label="Apellido Paterno"
              name="apellido_paterno"
              value={formData.apellido_paterno}
              onChange={(e) => setFormData({ ...formData, apellido_paterno: e.target.value })}
              required
            />
          </div>

          <Input
            label="Apellido Materno"
            name="apellido_materno"
            value={formData.apellido_materno}
            onChange={(e) => setFormData({ ...formData, apellido_materno: e.target.value })}
          />

          <Input
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />

          <Input
            label="Número de Control"
            name="numero_control"
            value={formData.numero_control}
            onChange={(e) => setFormData({ ...formData, numero_control: e.target.value })}
            required
          />

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

          {!editingAlumno ? (
            <Input
              label="Contraseña"
              name="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              helper="Mínimo 6 caracteres"
            />
          ) : (
            <div className="space-y-2">
              <Input
                label="Nueva Contraseña (dejar vacío para mantener la actual)"
                name="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                helper="Mínimo 6 caracteres"
              />
              <button
                type="button"
                onClick={() => {
                  const newPassword = Math.random().toString(36).slice(-6);
                  setFormData({ ...formData, password: newPassword });
                }}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                🔄 Generar contraseña aleatoria
              </button>
            </div>
          )}
        </form>
      </Modal>
    </div>
  );
}
