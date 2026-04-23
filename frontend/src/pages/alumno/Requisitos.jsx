import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import { GraduationCap, CheckCircle, XCircle, Building, Calendar } from 'lucide-react';

export default function Requisitos() {
  const { user } = useAuth();
  const [practicas, setPracticas] = useState([]);

  useEffect(() => {
    // In a real implementation, this would fetch from an API
    // For now, we'll show placeholder data
    setPracticas([
      {
        id: 1,
        numero_practica: 1,
        nombre_empresa: 'Por definir',
        fecha_inicio: null,
        fecha_fin: null,
        reporte_entregado: false,
        validada: false,
        observaciones: null,
      },
      {
        id: 2,
        numero_practica: 2,
        nombre_empresa: 'Por definir',
        fecha_inicio: null,
        fecha_fin: null,
        reporte_entregado: false,
        validada: false,
        observaciones: null,
      },
    ]);
  }, [user]);

  const getStatusIcon = (practica) => {
    if (practica.validada) {
      return <CheckCircle size={24} className="text-green-500" />;
    }
    if (practica.reporte_entregado) {
      return <CheckCircle size={24} className="text-yellow-500" />;
    }
    return <XCircle size={24} className="text-gray-400" />;
  };

  const getStatusText = (practica) => {
    if (practica.validada) {
      return 'Completada y validada';
    }
    if (practica.reporte_entregado) {
      return 'Reporte entregado, en revisión';
    }
    return 'Pendiente de iniciar';
  };

  const getStatusBadge = (practica) => {
    if (practica.validada) {
      return <Badge variant="success">Completada</Badge>;
    }
    if (practica.reporte_entregado) {
      return <Badge variant="warning">En revisión</Badge>;
    }
    return <Badge variant="default">Pendiente</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">
          Requisitos de Titulación
        </h1>
        <p className="text-gray-500 mt-1">
          Prácticas profesionales y requisitos para obtener tu título
        </p>
      </div>

      {/* Info Card */}
      <Card>
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
            <GraduationCap size={24} className="text-purple-600" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">
              Prácticas Profesionales
            </h4>
            <p className="text-sm text-gray-500">
              Para obtener tu título profesional, debes completar dos prácticas
              profesionales en empresas o instituciones autorizadas. Cada práctica
              tiene una duración mínima de 480 horas (3 meses). Asegúrate de
              entregar tu reporte final y solicitar la validación a tiempo.
            </p>
          </div>
        </div>
      </Card>

      {/* Practicas Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {practicas.map((practica) => (
          <Card key={practica.id} className="relative overflow-hidden">
            {/* Status Background */}
            <div
              className={`absolute top-0 right-0 w-32 h-32 rounded-full opacity-10 transform translate-x-8 -translate-y-8 ${
                practica.validada
                  ? 'bg-green-500'
                  : practica.reporte_entregado
                  ? 'bg-yellow-500'
                  : 'bg-gray-400'
              }`}
            />

            <div className="relative">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      practica.validada
                        ? 'bg-green-100'
                        : practica.reporte_entregado
                        ? 'bg-yellow-100'
                        : 'bg-gray-100'
                    }`}
                  >
                    <GraduationCap
                      size={24}
                      className={
                        practica.validada
                          ? 'text-green-600'
                          : practica.reporte_entregado
                          ? 'text-yellow-600'
                          : 'text-gray-400'
                      }
                    />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-800">
                      Práctica Profesional {practica.numero_practica}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(practica)}
                      <span className="text-sm text-gray-500">
                        {getStatusText(practica)}
                      </span>
                    </div>
                  </div>
                </div>
                {getStatusBadge(practica)}
              </div>

              {/* Details */}
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Building
                    size={18}
                    className={
                      practica.nombre_empresa !== 'Por definir'
                        ? 'text-primary-500'
                        : 'text-gray-400'
                    }
                  />
                  <div>
                    <p className="text-xs text-gray-500">Empresa</p>
                    <p className="font-medium text-gray-800">
                      {practica.nombre_empresa}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Calendar size={18} className="text-gray-400" />
                  <div className="flex-1 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500">Fecha Inicio</p>
                      <p className="font-medium text-gray-800">
                        {practica.fecha_inicio
                          ? new Date(practica.fecha_inicio).toLocaleDateString(
                              'es-MX'
                            )
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Fecha Fin</p>
                      <p className="font-medium text-gray-800">
                        {practica.fecha_fin
                          ? new Date(practica.fecha_fin).toLocaleDateString(
                              'es-MX'
                            )
                          : '-'}
                      </p>
                    </div>
                  </div>
                </div>

                {practica.observaciones && (
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Observaciones</p>
                    <p className="text-sm text-gray-700">
                      {practica.observaciones}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Checklist */}
      <Card title="Checklist de Titulación">
        <div className="space-y-3">
          {[
            { label: 'Credenciales completas', done: true },
            { label: 'Servicio social realizado', done: true },
            { label: 'Práctica Profesional 1', done: practicas[0]?.validada || false },
            { label: 'Práctica Profesional 2', done: practicas[1]?.validada || false },
            { label: 'Examen de idiomas (inglés)', done: false },
            { label: 'Documentación completa', done: false },
          ].map((item, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              {item.done ? (
                <CheckCircle size={20} className="text-green-500" />
              ) : (
                <XCircle size={20} className="text-gray-400" />
              )}
              <span
                className={`font-medium ${
                  item.done ? 'text-gray-800' : 'text-gray-500'
                }`}
              >
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Contact Info */}
      <Card>
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <GraduationCap size={20} className="text-primary-600" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">
              ¿Necesitas más información?
            </h4>
            <p className="text-sm text-gray-500">
              Contacta al departamento de Vinculación para resolver dudas sobre
              tus prácticas profesionales o al departamento académico para
              requisites de titulación.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
