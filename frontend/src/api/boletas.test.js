import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./index', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { alumnos: [] } }),
  },
}));

import api from './index';
import { getAlumnosBoletas, descargarBoleta, descargarBoletasMultiples } from './boletas';

describe('boletas api periodo filter', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getAlumnosBoletas reenvia periodo_id como query param', async () => {
    await getAlumnosBoletas({ periodo_id: 3 });
    expect(api.get).toHaveBeenCalledWith('/boletas/alumnos', { params: { periodo_id: 3 } });
  });

  it('las descargas nunca envian periodo_id', () => {
    expect(descargarBoleta.toString()).not.toContain('periodo_id');
    expect(descargarBoletasMultiples.toString()).not.toContain('periodo_id');
  });
});
