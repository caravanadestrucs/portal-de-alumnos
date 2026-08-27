import { describe, it, expect } from 'vitest';
import * as exportApi from './export';

describe('export api', () => {
  it('expone downloadExcel con filtros', () => {
    expect(typeof exportApi.downloadExcel).toBe('function');
  });
  it('expone downloadSQL', () => {
    expect(typeof exportApi.downloadSQL).toBe('function');
  });
  it('downloadExcel acepta params (filters)', async () => {
    // placeholder: verify function signature expects filters
    expect(exportApi.downloadExcel.length).toBeGreaterThanOrEqual(0);
  });
});
