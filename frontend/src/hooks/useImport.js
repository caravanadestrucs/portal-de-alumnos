import { useState, useCallback } from 'react';

// Stub hook for Importar split prep
// TODO S3: extract logic from Importar.jsx (860L) into this hook
// and wire tanstack-virtual for preview table virtualization
export default function useImport() {
  const [step, setStep] = useState(1);
  const [tipo, setTipo] = useState(null);
  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [result, setResult] = useState(null);

  const reset = useCallback(() => {
    setStep(1);
    setTipo(null);
    setFile(null);
    setPreviewData(null);
    setResult(null);
  }, []);

  return {
    step,
    setStep,
    tipo,
    setTipo,
    file,
    setFile,
    previewData,
    setPreviewData,
    result,
    setResult,
    reset,
  };
}
