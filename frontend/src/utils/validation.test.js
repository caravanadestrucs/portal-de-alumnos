import { describe, it, expect } from 'vitest';
import { isValidEmail, isValidNumeroControl, getEmailError, getNumeroControlError } from './validation';

describe('validation helpers', () => {
  it('isValidEmail returns true for valid email', () => {
    expect(isValidEmail('alumno@ejemplo.com')).toBe(true);
    expect(isValidEmail('TEST@UFV.EDU.MX')).toBe(true);
  });

  it('isValidEmail returns false for invalid email', () => {
    expect(isValidEmail('not-an-email')).toBe(false);
    expect(isValidEmail('a@b')).toBe(false);
    expect(isValidEmail('')).toBe(false);
    expect(isValidEmail('alumno@')).toBe(false);
  });

  it('isValidNumeroControl validates 8-14 alphanumeric', () => {
    expect(isValidNumeroControl('20230001')).toBe(true);
    expect(isValidNumeroControl('A2023001')).toBe(true);
    expect(isValidNumeroControl('12345678')).toBe(true);
  });

  it('isValidNumeroControl rejects invalid', () => {
    expect(isValidNumeroControl('123')).toBe(false);
    expect(isValidNumeroControl('')).toBe(false);
    expect(isValidNumeroControl('abc!1234')).toBe(false);
    expect(isValidNumeroControl('123456789012345')).toBe(false);
  });

  it('getEmailError returns helper vivo message', () => {
    expect(getEmailError('bad')).toBeTruthy();
    expect(getEmailError('bad')).toMatch(/email/i);
    expect(getEmailError('a@b.com')).toBe('');
    expect(getEmailError('')).toBe('');
  });

  it('getNumeroControlError returns helper vivo message', () => {
    expect(getNumeroControlError('123')).toBeTruthy();
    expect(getNumeroControlError('20230001')).toBe('');
    expect(getNumeroControlError('')).toBe('');
  });
});
