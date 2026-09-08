import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../../api/boletas', () => ({
  getAlumnosBoletas: vi.fn().mockResolvedValue({ alumnos: [] }),
  descargarBoleta: vi.fn().mockResolvedValue(undefined),
  descargarBoletasMultiples: vi.fn().mockResolvedValue(undefined),
  previewBoleta: vi.fn().mockResolvedValue({}),
}));
vi.mock('../../api/carreras', () => ({ getCarreras: vi.fn().mockResolvedValue({ carreras: [] }) }));
vi.mock('../../api/periodos', () => ({
  getPeriodos: vi.fn().mockResolvedValue({ periodos: [{ id: 4, nombre: 'Enero-Abril 2026', activa: true }] }),
}));
vi.mock('../../components/ui/Toast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));

import AdminBoletas from './Boletas';
import { getAlumnosBoletas, descargarBoletasMultiples } from '../../api/boletas';

describe('Boletas periodo UI', () => {
  beforeEach(() => vi.clearAllMocks());

  it('selector por defecto Todos y filtrar llama con periodo_id', async () => {
    render(<AdminBoletas />);
    const select = await screen.findByLabelText('Período');
    expect(select.value).toBe('');
    fireEvent.change(select, { target: { value: '4' } });
    await waitFor(() => expect(getAlumnosBoletas).toHaveBeenCalledWith(
      expect.objectContaining({ periodo_id: '4' })));
  });

  it('sin resultados muestra vacio pero la descarga sigue disponible', async () => {
    getAlumnosBoletas.mockResolvedValueOnce({ alumnos: [] });
    render(<AdminBoletas />);
    expect(await screen.findByText('No se encontraron alumnos')).toBeInTheDocument();
    const btn = screen.getByText('Descargar todas');
    expect(btn.disabled).toBe(false);
    fireEvent.click(btn);
    await waitFor(() => expect(descargarBoletasMultiples).not.toHaveBeenCalledWith(
      expect.objectContaining({ periodo_id: expect.anything() })));
  });
});
