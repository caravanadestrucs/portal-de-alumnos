import { useState, useEffect } from 'react';
import { getCarreras, createCarrera, updateCarrera, deleteCarrera } from '../../api/carreras';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import { Plus, Edit, Trash2, GraduationCap } from 'lucide-react';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';

export default function AdminCarreras() {
  const [carreras, setCarreras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [selectedCarrera, setSelectedCarrera] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    codigo: '',
    descripcion: '',
    activa: true,
  });
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  useEffect(() => {
    loadCarreras();
  }, []);

  const loadCarreras = async () => {
    setLoading(true);
    try {
      const data = await getCarreras();
      setCarreras(data || []);
    } catch (error) {
      console.error('Error loading carreras:', error);
      toast.error('Error al cargar carreras');
    } finally {
      setLoading(false);
    }
  };

  const openNewModal = () => {
    setModalMode('create');
    setSelectedCarrera(null);
    setFormData({ nombre: '', codigo: '', descripcion: '', activa: true });
    setShowModal(true);
  };

  const openEditModal = (carrera) => {
    setModalMode('edit');
    setSelectedCarrera(carrera);
    setFormData({
      nombre: carrera.nombre || '',
      codigo: carrera.codigo || '',
      descripcion: carrera.descripcion || '',
      activa: carrera.activa !== undefined ? carrera.activa : true,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedCarrera(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (modalMode === 'edit' && selectedCarrera) {
        await updateCarrera(selectedCarrera.id, formData);
        toast.success('Carrera actualizada exitosamente');
      } else {
        await createCarrera(formData);
        toast.success('Carrera creada exitosamente');
      }
      closeModal();
      loadCarreras();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteCarrera(deleteTarget.id);
      toast.success('Carrera eliminada exitosamente');
      setDeleteTarget(null);
      loadCarreras();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al eliminar');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Carreras</h1>
          <p className="text-gray-500 mt-1">
            Gestionar carreras disponibles
          </p>
        </div>
        <Button onClick={openNewModal}>
          <Plus size={18} />
          Nueva Carrera
        </Button>
      </div>

      {/* Table */}
      <Card>
        {loading ? (
          <TableSkeleton rows={8} columns={5} />
        ) : carreras.length === 0 ? (
          <div className="text-center py-12">
            <GraduationCap size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 mb-4">No hay carreras registradas</p>
            <Button onClick={openNewModal} variant="primary">
              <Plus size={18} />
              Crear primera carrera
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Código</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Nombre</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Descripción</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Estado</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {carreras.map((carrera) => (
                  <tr key={carrera.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{carrera.codigo}</td>
                    <td className="py-3 px-4 font-medium text-gray-800">{carrera.nombre}</td>
                    <td className="py-3 px-4 text-gray-500 text-sm">{carrera.descripcion || '-'}</td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={carrera.activa ? 'success' : 'danger'}>
                        {carrera.activa ? 'Activa' : 'Inactiva'}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openEditModal(carrera)}
                          className="p-2 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200"
                          title="Editar"
                        >
                          <Edit size={16} className="text-blue-600" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(carrera)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
                          title="Eliminar"
                          aria-label={`Eliminar carrera ${carrera.nombre}`}
                        >
                          <Trash2 size={16} className="text-red-600" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal */}
      <Modal
        isOpen={showModal}
        onClose={closeModal}
        title={modalMode === 'edit' ? 'Editar Carrera' : 'Nueva Carrera'}
        footer={
          <>
            <Button type="button" variant="outline" onClick={closeModal}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" loading={saving} form="carrera-form">
              {modalMode === 'edit' ? 'Guardar Cambios' : 'Crear Carrera'}
            </Button>
          </>
        }
      >
        <form id="carrera-form" onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre *
            </label>
            <input
              type="text"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Ej: Ingeniería en Sistemas"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Código *
            </label>
            <input
              type="text"
              value={formData.codigo}
              onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Ej: ING-SIS"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              value={formData.descripcion}
              onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              placeholder="Descripción de la carrera..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="activa"
              checked={formData.activa}
              onChange={(e) => setFormData({ ...formData, activa: e.target.checked })}
              className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="activa" className="text-sm font-medium text-gray-700">
              Carrera activa
            </label>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Eliminar carrera"
        message={deleteTarget ? `¿Eliminar la carrera ${deleteTarget.nombre}?` : '¿Eliminar esta carrera?'}
        impactSummary={
          deleteTarget
            ? `Se eliminarán ${deleteTarget.materiasCount ?? 45} materias, ${deleteTarget.alumnosCount ?? 0} alumnos y todas sus calificaciones/pagos asociados. Esta acción no se puede deshacer.`
            : 'Se eliminarán materias, alumnos y todas sus calificaciones/pagos asociados. Esta acción no se puede deshacer.'
        }
        requireConfirmText="BORRAR"
        confirmText="Borrar carrera"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
