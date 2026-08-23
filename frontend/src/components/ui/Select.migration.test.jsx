import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Select migration', () => {
  it('Grupos.jsx usa <Select> en lugar de <select> nativo para carrera', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Grupos.jsx'), 'utf-8');
    // debe contener <Select label="Carrera" y no <select requerido...carrera
    const hasSelectComponent = content.includes('<Select') && content.includes('Carrera');
    const rawSelectCount = (content.match(/<select/g) || []).length;
    // tras migración, debe quedar 0 selects nativos en el modal (solo filtro ya migrado)
    expect(hasSelectComponent).toBe(true);
    expect(rawSelectCount).toBe(0);
  });

  it('Asignaciones.jsx usa <Select> en modal (al menos 2 migrados)', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Asignaciones.jsx'), 'utf-8');
    const selectUsages = (content.match(/<Select/g) || []).length;
    const rawSelects = (content.match(/<select/g) || []).length;
    // debe tener al menos 4 Select (2 filtros + 2 modal) y máximo 1 raw restante
    expect(selectUsages).toBeGreaterThanOrEqual(4);
    expect(rawSelects).toBeLessThanOrEqual(1);
  });
});
