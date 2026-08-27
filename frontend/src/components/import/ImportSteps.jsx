// TODO S3: split Importar.jsx (860L) into steps via useImport + tanstack-virtual for preview table
// This is a lightweight placeholder to keep PR <800 lines. Full split deferred.

const STEPS = [
  { num: 1, label: 'Tipo' },
  { num: 2, label: 'Archivo' },
  { num: 3, label: 'Previsualizar' },
  { num: 4, label: 'Resultados' },
];

export default function ImportSteps({ currentStep = 1 }) {
  return (
    <div className="flex items-center justify-center gap-0 mb-6">
      {STEPS.map((s, idx) => (
        <div key={s.num} className="flex items-center">
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
                currentStep === s.num
                  ? 'bg-primary-600 text-white'
                  : currentStep > s.num
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
              }`}
            >
              {s.num}
            </div>
            <span
              className={`text-sm font-medium hidden sm:block ${
                currentStep === s.num ? 'text-primary-700' : currentStep > s.num ? 'text-green-600' : 'text-gray-400'
              }`}
            >
              {s.label}
            </span>
          </div>
          {idx < STEPS.length - 1 && (
            <div className={`w-8 sm:w-16 h-0.5 mx-2 ${currentStep > s.num ? 'bg-green-500' : 'bg-gray-200'}`} />
          )}
        </div>
      ))}
      {/* TODO: virtualización con tanstack-virtual para tabla preview con 1000+ filas */}
      <span className="sr-only">TODO tanstack-virtual virtualization placeholder</span>
    </div>
  );
}
