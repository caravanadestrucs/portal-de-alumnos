import { useState, useRef, useCallback } from 'react';
import { previewImport, executeImport } from '../../api/imports';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import { useToast } from '../../components/ui/Toast';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  ArrowLeft,
  ArrowRight,
  Users,
  CreditCard,
  BookOpen,
  Building2,
} from 'lucide-react';

// ── Constants ──────────────────────────────────────────────

const TIPOS = [
  {
    id: 'alumnos',
    label: 'Alumnos',
    icon: Users,
    description: 'Importar alumnos con datos personales, número de control y contraseñas',
  },
  {
    id: 'calificaciones',
    label: 'Calificaciones',
    icon: FileSpreadsheet,
    description: 'Importar calificaciones por alumno, materia, periodo y año',
  },
  {
    id: 'pagos',
    label: 'Pagos',
    icon: CreditCard,
    description: 'Importar notas de remisión con concepto, monto y fechas',
  },
  {
    id: 'carreras',
    label: 'Carreras',
    icon: Building2,
    description: 'Importar carreras con código, nombre y descripción',
  },
  {
    id: 'materias',
    label: 'Materias',
    icon: BookOpen,
    description: 'Importar materias con código, nombre, carrera y créditos',
  },
];

const ALLOWED_EXTENSIONS = ['.csv', '.xlsx'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const STEPS = [
  { num: 1, label: 'Tipo' },
  { num: 2, label: 'Archivo' },
  { num: 3, label: 'Previsualizar' },
  { num: 4, label: 'Resultados' },
];

// ── Helpers ────────────────────────────────────────────────

function formatColumnName(name) {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());
}

// ── Component ──────────────────────────────────────────────

export default function AdminImportar() {
  const [step, setStep] = useState(1);
  const [tipo, setTipo] = useState(null);
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const toast = useToast();

  // ── Reset ────────────────────────────────────────────────

  const reset = useCallback(() => {
    setStep(1);
    setTipo(null);
    setFile(null);
    setFileError(null);
    setPreviewData(null);
    setLoading(false);
    setExecuting(false);
    setResult(null);
    setApiError(null);
  }, []);

  // ── File validation (client-side) ────────────────────────

  const validateFile = (f) => {
    if (!f) return 'No se seleccionó ningún archivo';
    const name = f.name.toLowerCase();
    const ext = '.' + name.split('.').pop();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return 'Formato no soportado. Solo se aceptan archivos .csv y .xlsx';
    }
    if (f.size > MAX_FILE_SIZE) {
      return 'El archivo excede el límite de 10MB';
    }
    return null;
  };

  const handleFileSelect = (f) => {
    const err = validateFile(f);
    if (err) {
      setFileError(err);
      setFile(null);
    } else {
      setFileError(null);
      setFile(f);
    }
  };

  // ── Drag & drop handlers ─────────────────────────────────

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFileSelect(f);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInputChange = (e) => {
    const f = e.target.files?.[0];
    if (f) handleFileSelect(f);
  };

  // ── Navigation ───────────────────────────────────────────

  const goToStep2 = () => {
    if (!tipo) return;
    setApiError(null);
    setStep(2);
  };

  const goBackToStep2 = () => {
    setApiError(null);
    setStep(2);
  };

  // ── Preview API call ─────────────────────────────────────

  const handlePreview = async () => {
    if (!file || !tipo || fileError) return;
    setLoading(true);
    setApiError(null);
    try {
      const data = await previewImport(file, tipo);
      setPreviewData(data);
      setStep(3);
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        (err.code === 'ECONNABORTED'
          ? 'La solicitud tardó demasiado. Intenta con un archivo más pequeño.'
          : 'Error de conexión. Intenta de nuevo.');
      setApiError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // ── Execute API call ─────────────────────────────────────

  const handleExecute = async () => {
    if (!file || !tipo) return;
    setExecuting(true);
    setApiError(null);
    try {
      const data = await executeImport(file, tipo);
      setResult(data);
      setStep(4);
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        (err.code === 'ECONNABORTED'
          ? 'El archivo es demasiado grande o el servidor está ocupado.'
          : 'Error de conexión. Intenta de nuevo.');
      setApiError(msg);
      toast.error(msg);
    } finally {
      setExecuting(false);
    }
  };

  // ── Download passwords CSV (client-side) ─────────────────

  const downloadPasswordsCSV = () => {
    if (!result?.generated_passwords?.length) return;
    const headers = 'numero_control,password';
    const rows = result.generated_passwords
      .map((p) => `${p.numero_control},${p.password}`)
      .join('\n');
    const csv = `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `contrasenas_${tipo}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // ── Render: Step Indicator ───────────────────────────────

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((s, idx) => (
        <div key={s.num} className="flex items-center">
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors shrink-0 ${
                step === s.num
                  ? 'bg-primary-600 text-white shadow-md'
                  : step > s.num
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
              }`}
            >
              {step > s.num ? <CheckCircle size={16} /> : s.num}
            </div>
            <span
              className={`text-sm font-medium hidden sm:block ${
                step === s.num
                  ? 'text-primary-700'
                  : step > s.num
                    ? 'text-green-600'
                    : 'text-gray-400'
              }`}
            >
              {s.label}
            </span>
          </div>
          {idx < STEPS.length - 1 && (
            <div
              className={`w-8 sm:w-16 h-0.5 mx-2 ${
                step > s.num ? 'bg-green-500' : 'bg-gray-200'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );

  // ── Render: Step 1 — Select Type ─────────────────────────

  const renderStep1 = () => (
    <div className="space-y-6">
      <p className="text-gray-500 text-center">
        Seleccioná el tipo de datos que querés importar
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {TIPOS.map((t) => {
          const Icon = t.icon;
          const isSelected = tipo === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTipo(t.id)}
              className={`relative p-6 rounded-2xl text-left transition-all duration-200 ${
                isSelected
                  ? 'ring-2 ring-primary-500 bg-primary-50 shadow-lg scale-[1.02]'
                  : 'glass card-hover'
              }`}
            >
              <div
                className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors ${
                  isSelected
                    ? 'bg-primary-600 text-white'
                    : 'bg-primary-100 text-primary-600'
                }`}
              >
                <Icon size={28} />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">
                {t.label}
              </h3>
              <p className="text-sm text-gray-500">{t.description}</p>
            </button>
          );
        })}
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={goToStep2} disabled={!tipo} size="lg">
          Siguiente
          <ArrowRight size={18} />
        </Button>
      </div>
    </div>
  );

  // ── Render: Step 2 — Upload File ─────────────────────────

  const renderStep2 = () => (
    <div className="space-y-6">
      <p className="text-gray-500 text-center">
        Subí un archivo CSV o XLSX (máximo 10MB)
      </p>

      {/* Drag & drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
          dragOver
            ? 'border-primary-500 bg-primary-50'
            : file
              ? 'border-green-400 bg-green-50'
              : fileError
                ? 'border-red-400 bg-red-50'
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {file ? (
          <div className="space-y-3">
            <FileSpreadsheet size={48} className="mx-auto text-green-500" />
            <div>
              <p className="text-lg font-semibold text-gray-800">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setFileError(null);
              }}
              className="text-sm text-red-500 hover:text-red-600 underline"
            >
              Quitar archivo
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload size={48} className="mx-auto text-gray-400" />
            <div>
              <p className="text-lg font-semibold text-gray-700">
                Arrastrá tu archivo aquí o hacé clic para seleccionar
              </p>
              <p className="text-sm text-gray-400 mt-1">
                CSV o XLSX &mdash; Máximo 10MB
              </p>
            </div>
          </div>
        )}

        {/* File error message */}
        {fileError && (
          <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-2 text-red-500 text-sm">
            <AlertCircle size={16} />
            <span>{fileError}</span>
          </div>
        )}
      </div>

      {/* API error banner */}
      {apiError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2">
          <AlertCircle size={18} className="text-red-500 mt-0.5 shrink-0" />
          <p className="text-sm text-red-700">{apiError}</p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-4">
        <Button variant="secondary" onClick={() => setStep(1)}>
          <ArrowLeft size={18} />
          Atrás
        </Button>
        <Button
          onClick={handlePreview}
          disabled={!file || !!fileError}
          loading={loading}
          size="lg"
        >
          Previsualizar
          <ArrowRight size={18} />
        </Button>
      </div>
    </div>
  );

  // ── Render: Step 3 — Preview ─────────────────────────────

  const renderStep3 = () => {
    if (!previewData) return null;

    const { columns, rows_preview, total_rows, importable, warnings } = previewData;
    const errorCount = rows_preview.filter((r) => !r.valid).length;

    return (
      <div className="space-y-6">
        {/* Summary bar */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 p-4 bg-gray-50 rounded-xl">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <FileSpreadsheet size={18} className="text-primary-500" />
            <span className="font-medium">{file?.name}</span>
          </div>
          <span className="text-gray-300 hidden sm:inline">|</span>
          <span className="text-sm text-gray-600">
            <strong>{total_rows}</strong> filas totales
          </span>
          <span className="text-gray-300 hidden sm:inline">|</span>
          <span className="text-sm text-gray-600">
            <strong>{columns.length}</strong> columna{columns.length !== 1 ? 's' : ''}
          </span>
          {errorCount > 0 && (
            <>
              <span className="text-gray-300 hidden sm:inline">|</span>
              <span className="flex items-center gap-1 text-sm text-red-600">
                <XCircle size={16} />
                <strong>{errorCount}</strong> fila{errorCount !== 1 ? 's' : ''} con errores
              </span>
            </>
          )}
        </div>

        {/* Warnings */}
        {warnings?.length > 0 && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
            <div className="flex items-start gap-2">
              <AlertCircle size={18} className="text-yellow-600 mt-0.5 shrink-0" />
              <div className="text-sm text-yellow-700">
                {warnings.map((w, i) => (
                  <p key={i}>{w}</p>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Preview table */}
        <div className="glass rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gradient-to-r from-primary-500 to-accent-500">
                  <th className="px-4 py-3 text-left text-white font-semibold whitespace-nowrap w-14">
                    #
                  </th>
                  <th className="px-4 py-3 text-center text-white font-semibold whitespace-nowrap w-20">
                    Estado
                  </th>
                  {columns.map((col) => (
                    <th
                      key={col}
                      className="px-4 py-3 text-left text-white font-semibold whitespace-nowrap"
                    >
                      {formatColumnName(col)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows_preview.map((row) => {
                  const rowErrors = row.errors || [];
                  const isValid = row.valid;
                  return (
                    <tr
                      key={row.row}
                      className={`border-b border-gray-100 transition-colors ${
                        isValid
                          ? 'bg-white hover:bg-gray-50'
                          : 'bg-red-50 hover:bg-red-100'
                      }`}
                    >
                      <td className="px-4 py-3 text-gray-500 font-mono text-xs">
                        {row.row}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {isValid ? (
                          <CheckCircle size={18} className="text-green-500 mx-auto" />
                        ) : (
                          <div className="relative inline-flex group">
                            <XCircle size={18} className="text-red-500 cursor-help" />
                            {rowErrors.length > 0 && (
                              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-10">
                                <p className="font-semibold mb-1 text-gray-200">
                                  Errores fila {row.row}:
                                </p>
                                {rowErrors.map((e, i) => (
                                  <p key={i} className="text-red-300">
                                    <strong>{e.field}</strong>: {e.message}
                                  </p>
                                ))}
                                <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                      {columns.map((col) => {
                        const cellError = rowErrors.find((e) => e.field === col);
                        return (
                          <td
                            key={col}
                            className={`px-4 py-3 max-w-[220px] truncate ${
                              cellError
                                ? 'text-red-600 font-medium'
                                : 'text-gray-700'
                            }`}
                            title={row.data[col] != null ? String(row.data[col]) : ''}
                          >
                            {row.data[col] != null ? row.data[col] : ''}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Error details list */}
        {errorCount > 0 && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
            <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
              <AlertCircle size={18} />
              Detalles de errores por fila
            </h4>
            <div className="space-y-3 text-sm text-red-700">
              {rows_preview
                .filter((r) => !r.valid)
                .map((row) => (
                  <div key={row.row}>
                    <p className="font-medium mb-0.5">Fila {row.row}:</p>
                    <ul className="ml-5 list-disc space-y-0.5">
                      {row.errors.map((e, i) => (
                        <li key={i}>
                          <strong className="text-red-800">{e.field}</strong>:{' '}
                          {e.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* API error banner */}
        {apiError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2">
            <AlertCircle size={18} className="text-red-500 mt-0.5 shrink-0" />
            <p className="text-sm text-red-700">{apiError}</p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-4">
          <Button variant="secondary" onClick={goBackToStep2}>
            <ArrowLeft size={18} />
            Atrás
          </Button>
          <Button
            onClick={handleExecute}
            disabled={importable === false}
            loading={executing}
            size="lg"
            title={
              importable === false
                ? 'No se puede importar debido a errores estructurales en el archivo'
                : undefined
            }
          >
            {executing ? 'Importando...' : `Importar ${total_rows} registro${total_rows !== 1 ? 's' : ''}`}
            <ArrowRight size={18} />
          </Button>
        </div>
      </div>
    );
  };

  // ── Render: Step 4 — Results ─────────────────────────────

  const renderStep4 = () => {
    if (!result) return null;

    const isSuccess = result.status === 'success';
    const hasPasswords = result.generated_passwords?.length > 0;
    const hasErrors = result.errors?.length > 0;

    return (
      <div className="space-y-6">
        {isSuccess && !hasErrors ? (
          <>
            {/* ── Success Banner ── */}
            <div className="text-center py-8">
              <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <CheckCircle size={48} className="text-green-500" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Importación completada
              </h2>
              <p className="text-lg text-gray-600">
                <strong className="text-green-600">{result.imported}</strong>{' '}
                registro{result.imported !== 1 ? 's' : ''} importado
                {result.imported !== 1 ? 's' : ''} exitosamente
              </p>

              {result.details && (
                <div className="flex justify-center gap-6 mt-4 text-sm text-gray-500">
                  {result.details.alumnos_importados > 0 && (
                    <span>
                      Alumnos: <strong>{result.details.alumnos_importados}</strong>
                    </span>
                  )}
                  {result.details.calificaciones_creadas > 0 && (
                    <span>
                      Calificaciones creadas:{' '}
                      <strong>{result.details.calificaciones_creadas}</strong>
                    </span>
                  )}
                  {result.details.calificaciones_actualizadas > 0 && (
                    <span>
                      Calificaciones actualizadas:{' '}
                      <strong>{result.details.calificaciones_actualizadas}</strong>
                    </span>
                  )}
                  {result.details.pagos_creados > 0 && (
                    <span>
                      Pagos: <strong>{result.details.pagos_creados}</strong>
                    </span>
                  )}
                  {result.details.carreras_importadas > 0 && (
                    <span>
                      Carreras: <strong>{result.details.carreras_importadas}</strong>
                    </span>
                  )}
                  {result.details.materias_importadas > 0 && (
                    <span>
                      Materias: <strong>{result.details.materias_importadas}</strong>
                    </span>
                  )}
                  {result.created !== undefined && result.created > 0 && (
                    <span>
                      Creados: <strong>{result.created}</strong>
                    </span>
                  )}
                  {result.updated !== undefined && result.updated > 0 && (
                    <span>
                      Actualizados: <strong>{result.updated}</strong>
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* ── Passwords Table ── */}
            {hasPasswords && (
              <Card title="Contraseñas generadas" subtitle="Estas contraseñas se asignaron a los nuevos alumnos">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-2.5 text-left text-gray-600 font-medium">
                          Número de Control
                        </th>
                        <th className="px-4 py-2.5 text-left text-gray-600 font-medium">
                          Contraseña
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.generated_passwords.map((p) => (
                        <tr key={p.numero_control} className="border-t border-gray-100">
                          <td className="px-4 py-2.5 font-mono text-gray-700">
                            {p.numero_control}
                          </td>
                          <td className="px-4 py-2.5 font-mono text-gray-700">
                            {p.password}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4">
                  <Button onClick={downloadPasswordsCSV} variant="outline">
                    <Download size={18} />
                    Descargar CSV
                  </Button>
                </div>
              </Card>
            )}
          </>
        ) : (
          <>
            {/* ── Error Banner ── */}
            <div className="text-center py-8">
              <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                <XCircle size={48} className="text-red-500" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Error en la importación
              </h2>
              <p className="text-gray-600">
                {hasErrors
                  ? 'La importación no se completó debido a errores en los datos.'
                  : 'Ocurrió un error al procesar la importación.'}
              </p>
              {result.error_count && (
                <p className="text-sm text-gray-500 mt-1">
                  Se encontraron <strong>{result.error_count}</strong> error
                  {result.error_count !== 1 ? 'es' : ''}
                </p>
              )}
            </div>

            {/* ── Error Table ── */}
            {hasErrors && (
              <div className="glass rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gradient-to-r from-red-500 to-red-600">
                        <th className="px-4 py-3 text-left text-white font-semibold w-16">
                          Fila
                        </th>
                        <th className="px-4 py-3 text-left text-white font-semibold">
                          Campo
                        </th>
                        <th className="px-4 py-3 text-left text-white font-semibold">
                          Valor
                        </th>
                        <th className="px-4 py-3 text-left text-white font-semibold">
                          Error
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.errors.map((err, i) => (
                        <tr
                          key={i}
                          className="border-b border-gray-100 bg-white hover:bg-red-50 transition-colors"
                        >
                          <td className="px-4 py-3 font-mono text-gray-600 text-xs">
                            {err.row}
                          </td>
                          <td className="px-4 py-3 font-medium text-gray-700">
                            {err.field}
                          </td>
                          <td className="px-4 py-3 font-mono text-gray-500 text-xs max-w-[200px] truncate">
                            {err.value != null ? String(err.value) : '-'}
                          </td>
                          <td className="px-4 py-3 text-red-600">
                            {err.message}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ── Rollback Info ── */}
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
              <div className="flex items-start gap-2">
                <AlertCircle size={18} className="text-yellow-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-yellow-700">
                    <strong>No se realizaron cambios en la base de datos.</strong>{' '}
                    La importación requiere que todas las filas sean válidas. Corregí
                    los errores e intentá de nuevo.
                  </p>
                  {result.total_rows && (
                    <p className="text-sm text-yellow-600 mt-1">
                      {result.imported || 0} de {result.total_rows} filas procesadas
                      correctamente antes del error.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Import another file button */}
        <div className="flex justify-center pt-4">
          <Button onClick={reset} size="lg">
            Importar otro archivo
          </Button>
        </div>
      </div>
    );
  };

  // ── Main Render ──────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Importar Datos</h1>
        <p className="text-gray-500 mt-1">
          Importación masiva de datos desde archivos CSV o XLSX
        </p>
      </div>

      {/* Step indicator */}
      {renderStepIndicator()}

      {/* Content */}
      <Card>
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
        {step === 4 && renderStep4()}
      </Card>
    </div>
  );
}
