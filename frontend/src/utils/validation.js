const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const NUMERO_CONTROL_REGEX = /^[A-Za-z0-9]{8,14}$/;

export function isValidEmail(value) {
  if (!value || typeof value !== 'string') return false;
  return EMAIL_REGEX.test(value.trim());
}

export function isValidNumeroControl(value) {
  if (!value || typeof value !== 'string') return false;
  return NUMERO_CONTROL_REGEX.test(value.trim());
}

export function getEmailError(value) {
  if (!value) return '';
  return isValidEmail(value) ? '' : 'Formato de email inválido';
}

export function getNumeroControlError(value) {
  if (!value) return '';
  return isValidNumeroControl(value) ? '' : 'Número de control debe tener 8-14 caracteres alfanuméricos';
}
