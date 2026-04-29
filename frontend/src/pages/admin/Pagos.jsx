import { useState, useEffect, useRef } from 'react';
import { useFetch } from '../../hooks/useFetch';
import * as alumnosApi from '../../api/alumnos';
import { getPagosByAlumno, getAlumnosConPagosPendientes, createPago, togglePagoStatus, deletePago } from '../../api/pagos';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { useToast } from '../../components/ui/Toast';
import { Plus, CheckCircle, XCircle, DollarSign, Trash2, AlertTriangle, Search, User, ArrowLeft } from 'lucide-react';

export default function AdminPagos() {
  const { data: alumnos } = useFetch(alumnosApi.getAlumnos);
  const toast = useToast();
  const [pagosPendientesData, setPagosPendientesData] = useState(null);
  const [loadingPendientes, setLoadingPendientes] = useState(true);
  
  const [selectedAlumno, setSelectedAlumno] = useState(null);
  const [pagos, setPagos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const searchRef = useRef(null);
  
  const [formData, setFormData] = useState({
    concepto: '',
    monto: '',
    fecha_emision: new Date().toISOString().split('T')[0],
    fecha_corte: '',
  });

  // Cargar lista de alumnos con pagos pendientes
  useEffect(() => {
    const loadPendientes = async () => {
      try {
        const data = await getAlumnosConPagosPendientes();
        setPagosPendientesData(data);
      } catch (error) {
        console.error('Error loading pagos pendientes:', error);
      } finally {
        setLoadingPendientes(false);
      }
    };
    loadPendientes();
  }, []);

  // Cerrar sugerencias al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filtrar sugerencias del buscador
  const sugerencias = (alumnos || [])
    .filter(a => {
      if (!searchTerm) return false;
      const term = searchTerm.toLowerCase();
      return (
        a.nombre?.toLowerCase().includes(term) ||
        a.apellido_paterno?.toLowerCase().includes(term) ||
        a.numero_control?.toLowerCase().includes(term) ||
        (a.email || '').toLowerCase().includes(term)
      );
    })
    .slice(0, 8);

  const handleSelectSuggestion = (alumno) => {
    selectAlumno(alumno);
    setSearchTerm('');
    setShowSuggestions(false);
  };

  const selectAlumno = async (alumno) => {
    setSelectedAlumno(alumno);
    setLoading(true);
    try {
      const data = await getPagosByAlumno(alumno.id);
      setPagos(data.notas || []);
    } catch (error) {
      console.error('Error loading pagos:', error);
      toast.error('Error al cargar pagos');
      setPagos([]);
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    setSelectedAlumno(null);
    setPagos([]);
    getAlumnosConPagosPendientes().then(setPagosPendientesData);
  };

  const togglePagoStatusHandler = async (pago) => {
    setUpdatingId(pago.id);
    try {
      const result = await togglePagoStatus(pago.id);
      // Actualizar el pago en la lista local con los datos del servidor
      setPagos(prev => prev.map(p => p.id === pago.id ? result.nota : p));
      // Recargar lista de pendientes
      const data = await getAlumnosConPagosPendientes();
      setPagosPendientesData(data);
      toast.success(result.message);
    } catch (error) {
      console.error('Error updating pago:', error);
      toast.error('Error al actualizar el pago');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDeletePago = async (pago) => {
    if (!confirm(`¿Eliminar "${pago.concepto}"?\n\nMonto: $${pago.monto}\n\nEsta acción no se puede deshacer.`)) return;
    
    try {
      await deletePago(pago.id);
      setPagos(prev => prev.filter(p => p.id !== pago.id));
      const data = await getAlumnosConPagosPendientes();
      setPagosPendientesData(data);
      toast.success('Nota eliminada correctamente');
    } catch (error) {
      toast.error('Error al eliminar el pago');
    }
  };

  const handleCreatePago = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const newPago = await createPago({
        concepto: formData.concepto,
        monto: parseFloat(formData.monto),
        fecha_emision: formData.fecha_emision,
        fecha_corte: formData.fecha_corte || null,
        alumno_id: selectedAlumno.id,
      });
      setPagos(prev => [...prev, newPago]);
      setIsModalOpen(false);
      setFormData({
        concepto: '',
        monto: '',
        fecha_emision: new Date().toISOString().split('T')[0],
        fecha_corte: '',
      });
      const data = await getAlumnosConPagosPendientes();
      setPagosPendientesData(data);
      toast.success('Nota de remisión creada');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al crear el pago');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('es-MX', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const calcularMora = (pago) => {
    if (!pago.fecha_corte || pago.pagada) return 0;
    const hoy = new Date();
    const fechaCorte = new Date(pago.fecha_corte);
    if (hoy > fechaCorte) {
      const dias = Math.ceil((hoy - fechaCorte) / (1000 * 60 * 60 * 24));
      return dias * 5;
    }
    return 0;
  };

  const totalPendiente = pagos.filter((p) => !p.pagada).reduce((sum, p) => sum + p.monto + calcularMora(p), 0);
  const totalPagado = pagos.filter((p) => p.pagada).reduce((sum, p) => sum + p.monto, 0);
  const moraTotal = pagos.filter((p) => !p.pagada).reduce((sum, p) => sum + calcularMora(p), 0);

  const alumnosDeudores = pagosPendientesData?.alumnos?.filter(a => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      a.nombre?.toLowerCase().includes(term) ||
      a.numero_control?.toLowerCase().includes(term) ||
      a.carrera?.toLowerCase().includes(term)
    );
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          {selectedAlumno && (
            <button onClick={goBack} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
          )}
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              {selectedAlumno ? `Pagos - ${selectedAlumno.nombre || selectedAlumno.nombre_completo}` : 'Pagos'}
            </h1>
            <p className="text-gray-500 mt-1">
              {selectedAlumno 
                ? `${selectedAlumno.numero_control} • ${selectedAlumno.carrera || selectedAlumno.carrera?.nombre || ''}`
                : 'Gestionar notas de remisión'
              }
            </p>
          </div>
        </div>
        {selectedAlumno && (
          <Button onClick={() => setIsModalOpen(true)}><Plus size={18} /> Nueva Nota</Button>
        )}
      </div>

      {/* Buscador */}
      <Card>
        <div className="relative" ref={searchRef}>
          <div className="relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={selectedAlumno ? 'Cambiar alumno...' : 'Buscar alumno por nombre o número de control...'}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              className="w-full pl-12 pr-4 py-3 rounded-xl input-glass"
            />
          </div>
          
          {showSuggestions && sugerencias.length > 0 && (
            <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
              {sugerencias.map((alumno) => (
                <button
                  key={alumno.id}
                  onClick={() => handleSelectSuggestion(alumno)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors text-left"
                >
                  <User size={18} className="text-gray-400" />
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">
                      {alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno || ''}
                    </p>
                    <p className="text-sm text-gray-500">{alumno.numero_control}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Lista de Deudores */}
      {!selectedAlumno && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-800">Alumnos con Pagos Pendientes</h2>
            <span className="text-sm text-gray-500">
              {pagosPendientesData?.total_alumnos || 0} alumnos • {formatCurrency(pagosPendientesData?.total_adeudo || 0)} total
            </span>
          </div>

          {loadingPendientes ? (
            <Card className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-500">Cargando...</p>
            </Card>
          ) : alumnosDeudores.length === 0 ? (
            <Card className="text-center py-12">
              <DollarSign size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No hay alumnos con pagos pendientes</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {alumnosDeudores.map((alumno) => (
                <Card key={alumno.id} className="hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center">
                        <User size={24} className="text-orange-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{alumno.nombre}</p>
                        <p className="text-sm text-gray-500">{alumno.numero_control} • {alumno.carrera}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {alumno.num_notas} nota{alumno.num_notas !== 1 ? 's' : ''} pendiente{alumno.num_notas !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-orange-600">{formatCurrency(alumno.total_pendiente)}</p>
                        {alumno.mora_total > 0 && (
                          <p className="text-xs text-red-500">+ {formatCurrency(alumno.mora_total)} mora</p>
                        )}
                        {alumno.tiene_mora && <Badge variant="danger">Con mora</Badge>}
                      </div>
                      <Button size="sm" onClick={() => {
                        selectAlumno({
                          id: alumno.id,
                          nombre: alumno.nombre,
                          numero_control: alumno.numero_control,
                          carrera: alumno.carrera,
                          nombre_completo: alumno.nombre,
                        });
                      }}>
                        Ver Pagos
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Detalle de Pagos */}
      {selectedAlumno && (
        <>
          {pagos.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="text-center">
                <DollarSign size={32} className="mx-auto text-gray-400 mb-2" />
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-2xl font-bold text-gray-800">{formatCurrency(totalPagado + totalPendiente)}</p>
              </Card>
              <Card className="text-center">
                <CheckCircle size={32} className="mx-auto text-green-500 mb-2" />
                <p className="text-sm text-gray-500">Pagado</p>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPagado)}</p>
              </Card>
              <Card className="text-center">
                <XCircle size={32} className="mx-auto text-orange-500 mb-2" />
                <p className="text-sm text-gray-500">Pendiente</p>
                <p className="text-2xl font-bold text-orange-600">{formatCurrency(totalPendiente - moraTotal)}</p>
              </Card>
              <Card className="text-center">
                <AlertTriangle size={32} className={`mx-auto mb-2 ${moraTotal > 0 ? 'text-red-500' : 'text-gray-400'}`} />
                <p className="text-sm text-gray-500">Mora (5$/día)</p>
                <p className={`text-2xl font-bold ${moraTotal > 0 ? 'text-red-600' : 'text-gray-600'}`}>{formatCurrency(moraTotal)}</p>
              </Card>
            </div>
          )}

          {loading ? (
            <Card className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-500">Cargando pagos...</p>
            </Card>
          ) : pagos.length === 0 ? (
            <Card className="text-center py-12">
              <DollarSign size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No hay notas de remisión para este alumno</p>
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
                      <th className="text-center py-3 px-4 font-semibold text-gray-700">Fecha Corte</th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-700">Estado</th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-700">Fecha Pago</th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pagos.map((pago) => {
                      const mora = calcularMora(pago);
                      return (
                        <tr key={pago.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-gray-700">{formatDate(pago.fecha_emision)}</td>
                          <td className="py-3 px-4">
                            <div className="font-medium text-gray-800">{pago.concepto}</div>
                            {mora > 0 && (
                              <div className="text-xs text-red-500 flex items-center gap-1 mt-1">
                                <AlertTriangle size={12} />
                                Mora: {formatCurrency(mora)} ({Math.ceil(mora / 5)} días)
                              </div>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="font-semibold text-gray-800">{formatCurrency(pago.monto)}</div>
                            {mora > 0 && <div className="text-xs text-red-500 font-medium">+{formatCurrency(mora)}</div>}
                            {mora > 0 && <div className="text-sm font-bold text-red-600">Total: {formatCurrency(pago.monto + mora)}</div>}
                          </td>
                          <td className="py-3 px-4 text-center text-gray-500">
                            {pago.fecha_corte ? (
                              <span className={new Date() > new Date(pago.fecha_corte) && !pago.pagada ? 'text-red-600 font-medium' : ''}>
                                {formatDate(pago.fecha_corte)}
                              </span>
                            ) : '-'}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Badge variant={pago.pagada ? 'success' : 'warning'}>
                              {pago.pagada ? 'Pagada' : 'Pendiente'}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-center text-gray-500">
                            {pago.fecha_pago ? <span className="text-green-600 font-medium">{formatDate(pago.fecha_pago)}</span> : '-'}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => togglePagoStatusHandler(pago)}
                                disabled={updatingId === pago.id}
                                className={`p-2 rounded-lg transition-colors ${
                                  pago.pagada 
                                    ? 'hover:bg-orange-50 text-orange-500' 
                                    : 'hover:bg-green-50 text-green-500'
                                } ${updatingId === pago.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                                title={pago.pagada ? 'Marcar pendiente' : 'Marcar pagada'}
                              >
                                {updatingId === pago.id ? (
                                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                  pago.pagada ? <XCircle size={18} /> : <CheckCircle size={18} />
                                )}
                              </button>
                              <button
                                onClick={() => handleDeletePago(pago)}
                                className="p-2 hover:bg-red-50 rounded-lg transition-colors text-red-500"
                                title="Eliminar"
                              >
                                <Trash2 size={18} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Modal Nueva Nota */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-bold text-gray-800">Nueva Nota de Remisión</h2>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-lg">✕</button>
            </div>
            <form onSubmit={handleCreatePago} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Concepto *</label>
                <input
                  type="text"
                  value={formData.concepto}
                  onChange={(e) => setFormData({ ...formData, concepto: e.target.value })}
                  required
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="Ej: Colegiatura Marzo 2026"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monto *</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.monto}
                  onChange={(e) => setFormData({ ...formData, monto: e.target.value })}
                  required
                  className="w-full px-4 py-2.5 rounded-xl input-glass"
                  placeholder="0.00"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Emisión *</label>
                  <input
                    type="date"
                    value={formData.fecha_emision}
                    onChange={(e) => setFormData({ ...formData, fecha_emision: e.target.value })}
                    required
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Corte</label>
                  <input
                    type="date"
                    value={formData.fecha_corte}
                    onChange={(e) => setFormData({ ...formData, fecha_corte: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl input-glass"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500">* Después de la fecha de corte se aplican $5 MXN/día de mora</p>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
                <Button type="submit" loading={saving}>{saving ? 'Creando...' : 'Crear Nota'}</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}