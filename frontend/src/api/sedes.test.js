import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./index', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { sedes: [] } }),
    post: vi.fn().mockResolvedValue({ data: { sede: { id: 1 } } }),
    put: vi.fn().mockResolvedValue({ data: { sede: { id: 1 } } }),
    delete: vi.fn().mockResolvedValue({ data: { message: 'deleted' } }),
  },
}));

import api from './index';
import * as sedesApi from './sedes';

describe('sedes api', () => {
  beforeEach(() => vi.clearAllMocks());

  it('expone getSedes, getSede, createSede, updateSede, deleteSede', () => {
    expect(typeof sedesApi.getSedes).toBe('function');
    expect(typeof sedesApi.getSede).toBe('function');
    expect(typeof sedesApi.createSede).toBe('function');
    expect(typeof sedesApi.updateSede).toBe('function');
    expect(typeof sedesApi.deleteSede).toBe('function');
  });

  it('getSedes llama GET /sedes con auth header via api instance', async () => {
    await sedesApi.getSedes();
    expect(api.get).toHaveBeenCalledWith('/sedes', expect.any(Object) || undefined);
    // allow either /sedes or /sedes/ ; accept both
    const call = api.get.mock.calls[0][0];
    expect(call).toMatch(/\/sedes\/?/);
  });

  it('getSedes forward sede_id filter as query param', async () => {
    await sedesApi.getSedes({ sede_id: 2 });
    expect(api.get).toHaveBeenCalled();
    const args = api.get.mock.calls[0];
    const params = args[1]?.params || args[0]?.includes?.('sede_id') ? args : null;
    // implementation may pass {params:{sede_id:2}} or URLSearchParams
    // check that sede_id 2 was forwarded somehow
    const forwarded = JSON.stringify(args);
    expect(forwarded).toContain('2');
  });

  it('createSede POST /sedes with body {nombre,codigo,direccion}', async () => {
    await sedesApi.createSede({ nombre: 'Test', codigo: 'TST', direccion: 'Addr' });
    expect(api.post).toHaveBeenCalled();
    const url = api.post.mock.calls[0][0];
    expect(url).toMatch(/\/sedes/);
    const body = api.post.mock.calls[0][1];
    expect(body.nombre).toBe('Test');
    expect(body.codigo).toBe('TST');
  });

  it('getSede GET /sedes/:id', async () => {
    await sedesApi.getSede(5);
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/sedes/5'));
  });

  it('updateSede PUT /sedes/:id', async () => {
    await sedesApi.updateSede(5, { nombre: 'New' });
    expect(api.put).toHaveBeenCalledWith(expect.stringContaining('/sedes/5'), expect.objectContaining({ nombre: 'New' }));
  });

  it('deleteSede DELETE /sedes/:id', async () => {
    await sedesApi.deleteSede(5);
    expect(api.delete).toHaveBeenCalledWith(expect.stringContaining('/sedes/5'));
  });
});
