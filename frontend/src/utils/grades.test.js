import { describe, it, expect } from 'vitest';
import { getGradeClass, getGradeLabel, getEffectiveGrade, gradeHierarchy } from './grades';

describe('getGradeClass', () => {
  it('retorna badge-neutral para null/"" /0 /NaN', () => {
    expect(getGradeClass(null)).toBe('badge-neutral');
    expect(getGradeClass(undefined)).toBe('badge-neutral');
    expect(getGradeClass('')).toBe('badge-neutral');
    expect(getGradeClass(0)).toBe('badge-neutral');
    expect(getGradeClass('0')).toBe('badge-neutral');
    expect(getGradeClass(NaN)).toBe('badge-neutral');
    expect(getGradeClass('abc')).toBe('badge-neutral');
  });

  it('retorna badge-success para >=9', () => {
    expect(getGradeClass(9)).toBe('badge-success');
    expect(getGradeClass(9.5)).toBe('badge-success');
    expect(getGradeClass(10)).toBe('badge-success');
  });

  it('retorna badge-warning para 8-8.9', () => {
    expect(getGradeClass(8)).toBe('badge-warning');
    expect(getGradeClass(8.5)).toBe('badge-warning');
    expect(getGradeClass(8.9)).toBe('badge-warning');
  });

  it('retorna badge-danger para <8 y >0', () => {
    expect(getGradeClass(7.9)).toBe('badge-danger');
    expect(getGradeClass(5)).toBe('badge-danger');
    expect(getGradeClass(6)).toBe('badge-danger');
    expect(getGradeClass(0.1)).toBe('badge-danger');
    expect(getGradeClass(1)).toBe('badge-danger');
  });

  it('maneja strings numéricos', () => {
    expect(getGradeClass('9')).toBe('badge-success');
    expect(getGradeClass('8.5')).toBe('badge-warning');
    expect(getGradeClass('7')).toBe('badge-danger');
    expect(getGradeClass('10')).toBe('badge-success');
  });
});

describe('getGradeLabel', () => {
  it('retorna Sin calificar para null o string vacio', () => {
    expect(getGradeLabel(null)).toBe('Sin calificar');
    expect(getGradeLabel(undefined)).toBe('Sin calificar');
    expect(getGradeLabel('')).toBe('Sin calificar');
  });

  it('retorna Aprobado para >=8', () => {
    expect(getGradeLabel(8)).toBe('Aprobado');
    expect(getGradeLabel(9)).toBe('Aprobado');
    expect(getGradeLabel('8.5')).toBe('Aprobado');
  });

  it('retorna Reprobado para <8', () => {
    expect(getGradeLabel(7.9)).toBe('Reprobado');
    expect(getGradeLabel(5)).toBe('Reprobado');
    expect(getGradeLabel(0)).toBe('Reprobado');
  });
});

describe('getEffectiveGrade', () => {
  it('prioriza extra_2 sobre extra_1 y final', () => {
    const cal = { final: 5, extra_1: 7, extra_2: 9 };
    expect(getEffectiveGrade(cal)).toEqual({ value: 9, source: 'Extraordinario 2' });
  });

  it('prioriza extra_1 si no hay extra_2', () => {
    const cal = { final: 5, extra_1: 8, extra_2: null };
    expect(getEffectiveGrade(cal)).toEqual({ value: 8, source: 'Extraordinario 1' });
    expect(getEffectiveGrade({ final: 5, extra_1: 8 })).toEqual({ value: 8, source: 'Extraordinario 1' });
  });

  it('usa final si no hay extras', () => {
    expect(getEffectiveGrade({ final: 7 })).toEqual({ value: 7, source: 'Ordinaria' });
    expect(getEffectiveGrade({ final: null })).toEqual({ value: null, source: 'Ordinaria' });
  });

  it('soporta calificacion_final alias', () => {
    expect(getEffectiveGrade({ calificacion_final: 6 })).toEqual({ value: 6, source: 'Ordinaria' });
    expect(getEffectiveGrade({ calificacionFinal: 6 })).toEqual({ value: 6, source: 'Ordinaria' });
    // precedencia de calificacion_final sobre final
    expect(getEffectiveGrade({ calificacion_final: 9, final: 5 })).toEqual({ value: 9, source: 'Ordinaria' });
  });

  it('retorna null si cal es null/undefined', () => {
    expect(getEffectiveGrade(null)).toEqual({ value: null, source: 'Ordinaria' });
    expect(getEffectiveGrade(undefined)).toEqual({ value: null, source: 'Ordinaria' });
  });

  it('ignora extras con valor 0 o vacio', () => {
    expect(getEffectiveGrade({ final: 6, extra_1: 0, extra_2: '' })).toEqual({ value: 6, source: 'Ordinaria' });
    expect(getEffectiveGrade({ final: 6, extra_1: '', extra_2: 0 })).toEqual({ value: 6, source: 'Ordinaria' });
  });
});

describe('gradeHierarchy', () => {
  it('es ["extra_2","extra_1","final"]', () => {
    expect(gradeHierarchy).toEqual(['extra_2', 'extra_1', 'final']);
  });
});
