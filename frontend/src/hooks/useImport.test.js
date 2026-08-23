import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useImport from './useImport';

describe('useImport', () => {
  it('retorna estado inicial', () => {
    const { result } = renderHook(() => useImport());
    expect(result.current.step).toBe(1);
    expect(result.current.tipo).toBe(null);
    expect(result.current.file).toBe(null);
  });

  it('setTipo y setStep funcionan', () => {
    const { result } = renderHook(() => useImport());
    act(() => result.current.setTipo('alumnos'));
    expect(result.current.tipo).toBe('alumnos');
    act(() => result.current.setStep(2));
    expect(result.current.step).toBe(2);
  });

  it('reset vuelve a estado inicial', () => {
    const { result } = renderHook(() => useImport());
    act(() => {
      result.current.setTipo('pagos');
      result.current.setStep(3);
    });
    act(() => result.current.reset());
    expect(result.current.step).toBe(1);
    expect(result.current.tipo).toBe(null);
  });
});
