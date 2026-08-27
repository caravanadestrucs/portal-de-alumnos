export function handleApiError(error, toast) {
  const msg = error.response?.data?.message || error.response?.data?.error || error.message || "Error inesperado";
  const code = error.response?.data?.code;
  if (code && import.meta.env.DEV) console.error(`[${code}] ${msg}`, error.response?.data?.details);
  toast?.error(msg);
  if (import.meta.env.DEV) console.error(error);
}
