import { useState, useEffect } from 'react';
import { getCarreras, createCarrera, updateCarrera, deleteCarrera } from '../../api/carreras';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Plus, Edit, Trash2, GraduationCap } from 'lucide-react';

export default function AdminCarreras() {
  const [carreras, setCarreras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [selectedCarrera, setSelectedCarrera] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    codigo: '',
    descripcion: '',
    activa: true,
  });
  const [saving, setSaving] = useState(false);

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
    } finally {
      setLoading(false);
    }
  };

  const openNewModal = () => {
    setModalMode('create');
    setSelectedCarrera(null);
    setFormData({
      nombre: '',
      codigo: '',
      descripcion: '',
      activa: true,
    });
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
      } else {
        await createCarrera(formData);
      }
      closeModal();
      loadCarreras();
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('¿Estás seguro de eliminar esta carrera?')) {
      try {
        await deleteCarrera(id);
        loadCarreras();
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
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
            <p className="mt-4 text-gray-500">Cargando...</p>
          </div>
        ) : carreras.length === 0 ? (
          <div className="text-center py-12">
            <GraduationCap size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No hay carreras registradas</p>
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
                          onClick={() => handleDelete(carrera.id)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
                          title="Eliminar"
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

      {/* MODAL - Siempre renderizado pero oculto con CSS */}
      <div 
        style={{ 
          display: showModal ? 'flex' : 'none',
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.5)',
          zIndex: 9999,
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px'
        }}
      >
        <div 
          style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '500px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: 'bold', color: '#1f2937', margin: 0 }}>
              {modalMode === 'edit' ? 'Editar Carrera' : 'Nueva Carrera'}
            </h2>
            <button
              onClick={closeModal}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Nombre */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '6px' }}>
                  Nombre *
                </label>
                <input
                  type="text"
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #d1d5db',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                  placeholder="Ej: Ingeniería en Sistemas"
                />
              </div>

              {/* Código */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '6px' }}>
                  Código *
                </label>
                <input
                  type="text"
                  value={formData.codigo}
                  onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #d1d5db',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                  placeholder="Ej: ING-SIS"
                />
              </div>

              {/* Descripción */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '6px' }}>
                  Descripción
                </label>
                <textarea
                  value={formData.descripcion}
                  onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    border: '1px solid #d1d5db',
                    fontSize: '14px',
                    outline: 'none',
                    resize: 'none'
                  }}
                  placeholder="Descripción de la carrera..."
                />
              </div>

              {/* Checkbox activa */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="activa"
                  checked={formData.activa}
                  onChange={(e) => setFormData({ ...formData, activa: e.target.checked })}
                  style={{ width: '18px', height: '18px' }}
                />
                <label htmlFor="activa" style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                  Carrera activa
                </label>
              </div>
            </div>

            {/* Footer */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              gap: '12px',
              padding: '16px 24px',
              borderTop: '1px solid #e5e7eb',
              backgroundColor: '#f9fafb'
            }}>
              <button
                type="button"
                onClick={closeModal}
                style={{
                  padding: '10px 20px',
                  borderRadius: '10px',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  color: '#374151',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={saving}
                style={{
                  padding: '10px 20px',
                  borderRadius: '10px',
                  border: 'none',
                  background: saving ? '#9ca3af' : 'linear-gradient(135deg, #008a8a 0%, #00d084 100%)',
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: saving ? 'not-allowed' : 'pointer'
                }}
              >
                {saving ? 'Guardando...' : (modalMode === 'edit' ? 'Guardar Cambios' : 'Crear Carrera')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
