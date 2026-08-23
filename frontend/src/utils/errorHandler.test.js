import { describe, it, expect, vi } from 'vitest';
import { handleApiError } from './errorHandler';

describe('handleApiError', () => {
  it('usa message de response.data.message', () => {
    const toast = { error: vi.fn() };
    handleApiError({ response: { data: { message: 'fail' } } }, toast);
    expect(toast.error).toHaveBeenCalledWith('fail');
  });

  it('fallback a error field', () => {
    const toast = { error: vi.fn() };
    handleApiError({ response: { data: { error: 'error field msg' } } }, toast);
    expect(toast.error).toHaveBeenCalledWith('error field msg');
  });

  it('fallback a error.message', () => {
    const toast = { error: vi.fn() };
    handleApiError({ message: 'network fail' }, toast);
    expect(toast.error).toHaveBeenCalledWith('network fail');
  });

  it('fallback a "Error inesperado"', () => {
    const toast = { error: vi.fn() };
    handleApiError({}, toast);
    expect(toast.error).toHaveBeenCalledWith('Error inesperado');
  });

  it('no crashea si toast es undefined', () => {
    expect(() => handleApiError({ message: 'oops' }, undefined)).not.toThrow();
    expect(() => handleApiError({ response: { data: { message: 'fail' } } })).not.toThrow();
    expect(() => handleApiError({}, null)).not.toThrow();
  });
});
