import { useState } from 'react';
import { useFetch } from '../../hooks/useFetch';
import * as alumnosApi from '../../api/alumnos';
import { getPagosByAlumno, createPago, togglePagoStatus, deletePago } from '../../api/pagos';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { Plus, CheckCircle, XCircle, DollarSign, Trash2 } from 'lucide-react';

export default function AdminPagos() {
  const { data: alumnos } = useFetch(alumnosApi.getAlumnos);

  const [selectedAlumno, setSelectedAlumno] = useState(null);
  const [pagos, setPagos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    concepto: '',
    monto: '',
    fecha_emision: new Date().toISOString().split('T')[0],
  });

  const handleAlumnoChange = async (e) => {
    const alumnoId = parseInt(e.target.value);
    const alumno = alumnos?.find((a) => a.id === alumnoId);
    setSelectedAlumno(alumno || null);

    if (alumno) {
      setLoading(true);
      try {
        const data = await getPagosByAlumno(alumnoId);
        setPagos(data || []);
      } catch (error) {
        console.error('Error loading pagos:', error);
        setPagos([]);
      } finally {
        setLoading(false);
      }
    } else {
      setPagos([]);
    }
  };

  const togglePagoStatus = async (pago) => {
    try {
      await togglePagoStatus(pago.id);
      setPagos((prev) =>
        prev.map((p) =>
          p.id === pago.id ? { ...p, pagada: !p.pagada } : p
        )
      );
    } catch (error) {
      alert('Error al actualizar el estado del pago');
    }
  };

  const handleDeletePago = async (pago) => {
    const confirmacion = window.confirm(
      `¿Estás seguro de eliminar la nota de remisión "${pago.concepto}"?\n\nMonto: $${pago.monto}\n\nEsta acción no se puede deshacer.`
    );
    
    if (confirmacion) {
      try {
        await deletePago(pago.id);
        setPagos((prev) => prev.filter((p) => p.id !== pago.id));
      } catch (error) {
        alert('Error al eliminar el pago');
      }
    }
  };

  const handleCreatePago = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const newPago = await createPago({
        ...formData,
        monto: parseFloat(formData.monto),
        alumno_id: selectedAlumno.id,
      });
      setPagos((prev) => [...prev, newPago]);
      setIsModalOpen(false);
      setFormData({
        concepto: '',
        monto: '',
        fecha_emision: new Date().toISOString().split('T')[0],
      });
    } catch (error) {
      alert(error.response?.data?.error || 'Error al crear el pago');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const totalPendiente = pagos
    .filter((p) => !p.pagada)
    .reduce((sum, p) => sum + p.monto, 0);

  const totalPagado = pagos
    .filter((p) => p.pagada)
    .reduce((sum, p) => sum + p.monto, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Pagos</h1>
        <p className="text-gray-500 mt-1">
          Gestionar notas de remisión
        </p>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Seleccionar Alumno
            </label>
            <select
              value={selectedAlumno?.id || ''}
              onChange={handleAlumnoChange}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            >
              <option value="">-- Seleccionar --</option>
              {Array.isArray(alumnos) &&
                alumnos.map((alumno) => (
                  <option key={alumno.id} value={alumno.id}>
                    {alumno.numero_control} - {alumno.nombre}{' '}
                    {alumno.apellido_paterno}
                  </option>
                ))}
            </select>
          </div>

          {selectedAlumno && (
            <div className="flex items-end">
              <Button onClick={() => setIsModalOpen(true)}>
                <Plus size={18} />
                Nueva Nota
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Stats */}
      {selectedAlumno && pagos.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="text-center">
            <DollarSign size={32} className="mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-500">Total Pagos</p>
            <p className="text-2xl font-bold text-gray-800">
              {formatCurrency(totalPagado + totalPendiente)}
            </p>
          </Card>
          <Card className="text-center">
            <CheckCircle size={32} className="mx-auto text-green-500 mb-2" />
            <p className="text-sm text-gray-500">Pagado</p>
            <p className="text-2xl font-bold text-green-600">
              {formatCurrency(totalPagado)}
            </p>
          </Card>
          <Card className="text-center">
            <XCircle size={32} className="mx-auto text-orange-500 mb-2" />
            <p className="text-sm text-gray-500">Pendiente</p>
            <p className="text-2xl font-bold text-orange-600">
              {formatCurrency(totalPendiente)}
            </p>
          </Card>
        </div>
      )}

      {/* Table */}
      {selectedAlumno ? (
        loading ? (
          <Card className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
            <p className="mt-4 text-gray-500">Cargando pagos...</p>
          </Card>
        ) : pagos.length === 0 ? (
          <Card className="text-center py-12">
            <DollarSign size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">
              No hay notas de remisión para este alumno
            </p>
          </Card>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Fecha Emisión</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Concepto</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Monto</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Estado</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Fecha Pago</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {pagos.map((pago) => (
                    <tr key={pago.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-700">
                        {formatDate(pago.fecha_emision)}
                      </td>
                      <td className="py-3 px-4 font-medium text-gray-800">
                        {pago.concepto}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-gray-800">
                        {formatCurrency(pago.monto)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge variant={pago.pagada ? 'success' : 'warning'}>
                          {pago.pagada ? 'Pagada' : 'Pendiente'}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-center text-gray-500">
                        {pago.fecha_pago ? (
                          <span className="text-green-600 font-medium">
                            {formatDate(pago.fecha_pago)}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => togglePagoStatus(pago)}
                            className={`p-2 rounded-lg transition-colors ${
                              pago.pagada
                                ? 'hover:bg-orange-50 text-orange-500'
                                : 'hover:bg-green-50 text-green-500'
                            }`}
                            title={pago.pagada ? 'Marcar como pendiente' : 'Marcar como pagada'}
                          >
                            {pago.pagada ? <XCircle size={18} /> : <CheckCircle size={18} />}
                          </button>
                          <button
                            onClick={() => handleDeletePago(pago)}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors text-red-500"
                            title="Eliminar pago"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )
      ) : (
        <Card className="text-center py-12">
          <DollarSign size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">
            Selecciona un alumno para ver sus pagos
          </p>
        </Card>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div 
          style={{ 
            display: 'flex',
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
              maxWidth: '450px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
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
                Nueva Nota de Remisión
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                style={{ padding: '8px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleCreatePago}>
              <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '6px' }}>
                    Concepto *
                  </label>
                  <input
                    type="text"
                    value={formData.concepto}
                    onChange={(e) => setFormData({ ...formData, concepto: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      border: '1px solid #d1d5db',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                    placeholder="Ej: Colegiatura Marzo 2026"
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '6px' }}>
                    Monto *
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.monto}
                    onChange={(e) => setFormData({ ...formData, monto: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      border: '1px solid #d1d5db',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '6px' }}>
                    Fecha de Emisión *
                  </label>
                  <input
                    type="date"
                    value={formData.fecha_emision}
                    onChange={(e) => setFormData({ ...formData, fecha_emision: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      border: '1px solid #d1d5db',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  />
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
                  onClick={() => setIsModalOpen(false)}
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
                  {saving ? 'Creando...' : 'Crear Nota'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
