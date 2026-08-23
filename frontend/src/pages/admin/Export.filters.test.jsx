import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Export filters', () => {
  it('Export.jsx tiene filtros y usa api/export', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Export.jsx'), 'utf-8');
    expect(content).toMatch(/api\/export|downloadExcel|downloadSQL/);
    // debe tener al menos un filtro (carrera, periodo o similar)
    expect(content).toMatch(/filtro|filter|Select|carrera|periodo/i);
  });
});
