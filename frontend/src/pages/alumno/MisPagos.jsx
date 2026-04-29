import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import * as pagosApi from '../../api/pagos';
import { CreditCard, CheckCircle, XCircle, DollarSign, Calendar } from 'lucide-react';

export default function MisPagos() {
  const { user } = useAuth();
  const [pagos, setPagos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPagos = async () => {
      setLoading(true);
      try {
        if (user?.id) {
          const data = await pagosApi.getPagosByAlumno(user.id);
          console.log('Pagos data:', data);
          setPagos(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        console.error('Error loading pagos:', error);
        setPagos([]);
      } finally {
        setLoading(false);
      }
    };

    loadPagos();
  }, [user]);

  const totalPagado = pagos
    .filter((p) => p.pagada)
    .reduce((sum, p) => sum + p.monto, 0);

  const totalPendiente = pagos
    .filter((p) => !p.pagada)
    .reduce((sum, p) => sum + p.monto, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Mis Pagos</h1>
        <p className="text-gray-500 mt-1">
          Estado de cuenta y notas de remisión
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="text-center">
          <DollarSign size={28} className="mx-auto text-gray-400 mb-2" />
          <p className="text-sm text-gray-500">Total Pagos</p>
          <p className="text-2xl font-bold text-gray-800">
            {new Intl.NumberFormat('es-MX', {
              style: 'currency',
              currency: 'MXN',
            }).format(totalPagado + totalPendiente)}
          </p>
        </Card>
        <Card className="text-center">
          <CheckCircle size={28} className="mx-auto text-green-500 mb-2" />
          <p className="text-sm text-gray-500">Pagado</p>
          <p className="text-2xl font-bold text-green-600">
            {new Intl.NumberFormat('es-MX', {
              style: 'currency',
              currency: 'MXN',
            }).format(totalPagado)}
          </p>
        </Card>
        <Card className="text-center">
          <XCircle size={28} className="mx-auto text-orange-500 mb-2" />
          <p className="text-sm text-gray-500">Pendiente</p>
          <p className="text-2xl font-bold text-orange-600">
            {new Intl.NumberFormat('es-MX', {
              style: 'currency',
              currency: 'MXN',
            }).format(totalPendiente)}
          </p>
        </Card>
      </div>

      {/* Pagos List */}
      {loading ? (
        <Card className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-500">Cargando pagos...</p>
        </Card>
      ) : pagos.length === 0 ? (
        <Card className="text-center py-12">
          <CreditCard size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No hay notas de remisión registradas</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {pagos.map((pago) => (
            <Card key={pago.id} className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    pago.pagada
                      ? 'bg-green-100 text-green-600'
                      : 'bg-orange-100 text-orange-600'
                  }`}
                >
                  {pago.pagada ? (
                    <CheckCircle size={24} />
                  ) : (
                    <XCircle size={24} />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">
                    {pago.concepto}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar size={14} />
                    <span>
                      Emitida:{' '}
                      {new Date(pago.fecha_emision).toLocaleDateString('es-MX')}
                    </span>
                    {pago.fecha_pago && (
                      <>
                        <span>•</span>
                        <span>
                          Pagada:{' '}
                          {new Date(pago.fecha_pago).toLocaleDateString('es-MX')}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-gray-800">
                  {new Intl.NumberFormat('es-MX', {
                    style: 'currency',
                    currency: 'MXN',
                  }).format(pago.monto)}
                </p>
                <Badge variant={pago.pagada ? 'success' : 'warning'}>
                  {pago.pagada ? 'Pagada' : 'Pendiente'}
                </Badge>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Info */}
      <Card>
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <CreditCard size={20} className="text-blue-600" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">
              Información importante
            </h4>
            <p className="text-sm text-gray-500">
              Si tienes alguna duda sobre tus pagos o necesitas un comprobante,
              contacta al departamento de finanzas. Los pagos pueden tardar 24-48
              horas en reflejarse en el sistema.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
