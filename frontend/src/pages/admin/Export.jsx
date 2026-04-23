import { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { Download, FileText, Database, FileSpreadsheet } from 'lucide-react';

export default function AdminExport() {
  const [loading, setLoading] = useState(null);

  const handleDownload = async (type) => {
    setLoading(type);
    try {
      const API_URL = import.meta.env.VITE_API_URL || '/api';
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_URL}/export/${type}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Error al descargar');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Get filename from content-disposition or default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `export_${type}_${new Date().toISOString().split('T')[0]}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match) {
          filename = match[1].replace(/['"]/g, '');
        }
      }
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Error al descargar el archivo. Intenta de nuevo.');
      console.error('Download error:', error);
    } finally {
      setLoading(null);
    }
  };

  const exportOptions = [
    {
      id: 'sql',
      title: 'Descargar SQL',
      description: 'Exporta la base de datos completa en formato SQL. Ideal para respaldo o migración.',
      icon: Database,
      color: 'from-blue-500 to-blue-600',
      extension: '.sql',
    },
    {
      id: 'excel',
      title: 'Descargar Excel',
      description: 'Exporta todos los datos en hojas de cálculo de Excel. Incluye alumnos, calificaciones y más.',
      icon: FileSpreadsheet,
      color: 'from-green-500 to-green-600',
      extension: '.xlsx',
    },
  ];

  const tableInfo = [
    'Alumnos',
    'Carreras',
    'Materias',
    'Calificaciones',
    'Pagos (Notas de Remisión)',
    'Prácticas Profesionales',
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Exportar Datos</h1>
        <p className="text-gray-500 mt-1">
          Descarga los datos del sistema en diferentes formatos
        </p>
      </div>

      {/* Export Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {exportOptions.map((option) => {
          const Icon = option.icon;
          return (
            <Card key={option.id} hover className="relative overflow-hidden">
              <div
                className={`absolute top-0 right-0 w-32 h-32 rounded-full bg-gradient-to-br ${option.color} opacity-10 transform translate-x-8 -translate-y-8`}
              />
              <div className="relative">
                <div
                  className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${option.color} flex items-center justify-center shadow-lg mb-4`}
                >
                  <Icon size={32} className="text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">
                  {option.title}
                </h3>
                <p className="text-gray-500 mb-4">{option.description}</p>
                <Button
                  onClick={() => handleDownload(option.id)}
                  loading={loading === option.id}
                  variant="outline"
                  className="w-full"
                >
                  <Download size={18} />
                  {option.title}
                  <span className="text-xs opacity-70 ml-2">
                    ({option.extension})
                  </span>
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Tables Info */}
      <Card title="Tablas Incluidas" subtitle="Datos que se incluirán en la exportación">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {tableInfo.map((table) => (
            <div
              key={table}
              className="flex items-center gap-2 p-3 bg-gray-50 rounded-xl"
            >
              <FileText size={16} className="text-primary-500" />
              <span className="text-sm font-medium text-gray-700">{table}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Info Card */}
      <Card>
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <FileText size={20} className="text-blue-600" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">
              Acerca de las exportaciones
            </h4>
            <p className="text-sm text-gray-500">
              Los archivos SQL pueden ser importados directamente a cualquier base
              de datos MySQL o PostgreSQL. Los archivos Excel contienen hojas
              separadas para cada tabla y pueden ser abiertos en Excel, Google
              Sheets o cualquier otra aplicación de hojas de cálculo.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
