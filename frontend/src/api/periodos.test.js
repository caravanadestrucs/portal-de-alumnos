import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./index', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { periodos: [] } }),
    post: vi.fn().mockResolvedValue({ data: { periodo: { id: 1 } } }),
    put: vi.fn().mockResolvedValue({ data: { periodo: { id: 1 } } }),
    delete: vi.fn().mockResolvedValue({ data: { message: 'Período desactivado' } }),
  },
}));

import api from './index';
import * as periodosApi from './periodos';

describe('periodos api', () => {
  beforeEach(() => vi.clearAllMocks());

  it('expone getPeriodos, createPeriodo, updatePeriodo, deletePeriodo', () => {
    expect(typeof periodosApi.getPeriodos).toBe('function');
    expect(typeof periodosApi.createPeriodo).toBe('function');
    expect(typeof periodosApi.updatePeriodo).toBe('function');
    expect(typeof periodosApi.deletePeriodo).toBe('function');
  });

  it('getPeriodos llama GET /periodos', async () => {
    await periodosApi.getPeriodos();
    expect(api.get).toHaveBeenCalledWith('/periodos', expect.any(Object));
    expect(api.get.mock.calls[0][0]).toMatch(/\/periodos\/?/);
  });

  it('createPeriodo POST /periodos con el nombre', async () => {
    await periodosApi.createPeriodo({ nombre: 'Regular' });
    expect(api.post).toHaveBeenCalledWith(expect.stringContaining('/periodos'), expect.objectContaining({ nombre: 'Regular' }));
  });

  it('updatePeriodo PUT /periodos/:id', async () => {
    await periodosApi.updatePeriodo(5, { nombre: 'Nuevo' });
    expect(api.put).toHaveBeenCalledWith(expect.stringContaining('/periodos/5'), expect.objectContaining({ nombre: 'Nuevo' }));
  });

  it('deletePeriodo DELETE /periodos/:id', async () => {
    await periodosApi.deletePeriodo(5);
    expect(api.delete).toHaveBeenCalledWith(expect.stringContaining('/periodos/5'));
  });
});
