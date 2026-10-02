import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../api/periodos', () => ({
  getPeriodos: vi.fn().mockResolvedValue({ periodos: [
    { id: 1, nombre: 'Enero-Abril 2026', fecha_inicio: '2026-01-01', fecha_fin: '2026-04-30', activa: true },
    { id: 2, nombre: 'Regular', fecha_inicio: null, fecha_fin: null, activa: false },
  ] }),
  createPeriodo: vi.fn().mockResolvedValue({ periodo: { id: 3, nombre: 'Nuevo' } }),
  updatePeriodo: vi.fn().mockResolvedValue({ periodo: { id: 1, nombre: 'Updated' } }),
  deletePeriodo: vi.fn().mockResolvedValue({ message: 'deleted' }),
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isGeneralAdmin: true, user: { role: 'general_admin' } }),
}));

import Periodos from './Periodos';

describe('Periodos CRUD', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renderiza titulo y tabla con los periodos', async () => {
    await act(async () => {
      render(<Periodos />);
    });
    expect(await screen.findByRole('heading', { name: /Periodos/i })).toBeInTheDocument();
    expect(await screen.findByText('Enero-Abril 2026')).toBeInTheDocument();
    expect(screen.getByText('Regular')).toBeInTheDocument();
    expect(screen.getByText('Sí')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });

  it('tiene boton Nuevo Periodo y abre modal crear', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<Periodos />);
    });
    const btn = await screen.findByRole('button', { name: /Nuevo Periodo/i });
    expect(btn).toBeInTheDocument();
    await act(async () => {
      await user.click(btn);
    });
    expect(await screen.findByRole('heading', { name: /Crear Periodo/i })).toBeInTheDocument();
  });

  it('muestra - para fechas vacias (Regular)', async () => {
    await act(async () => {
      render(<Periodos />);
    });
    await screen.findByText('Regular');
    // Regular no tiene fechas: ambas celdas se muestran como '-'
    expect(screen.getAllByText('-').length).toBeGreaterThanOrEqual(2);
  });

  it('editar abre modal con valores precargados', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<Periodos />);
    });
    await screen.findByText('Enero-Abril 2026');
    const editButtons = screen.getAllByTitle('Editar');
    await act(async () => {
      await user.click(editButtons[0]);
    });
    expect(await screen.findByRole('heading', { name: /Editar Periodo/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/)).toHaveValue('Enero-Abril 2026');
    expect(screen.getByLabelText(/Fecha inicio/)).toHaveValue('2026-01-01');
    expect(screen.getByLabelText(/Fecha fin/)).toHaveValue('2026-04-30');
    expect(screen.getByLabelText(/Activa/)).toBeChecked();
  });
});