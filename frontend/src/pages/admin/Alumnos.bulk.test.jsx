import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../api/alumnos', () => ({
  getAlumnos: vi.fn().mockResolvedValue({ alumnos: [{ id: 1, nombre: 'Ana', apellido_paterno: 'Lopez', email: 'a@test.com', numero_control: '11111111', carrera: { nombre: 'ISC' }, activo: true, carrera_id: 1 }], total: 1, pages: 1 }),
  createAlumno: vi.fn(),
  updateAlumno: vi.fn(),
  deleteAlumno: vi.fn(),
  sendBulkCredentials: vi.fn().mockResolvedValue({ results: [] }),
}));

vi.mock('../../api/carreras', () => ({ getCarreras: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/sedes', () => ({ getSedes: vi.fn().mockResolvedValue({ sedes: [{ id: 1, codigo: 'TEO' }, { id: 2, codigo: 'HUA' }] }) }));
vi.mock('../../context/AuthContext', () => ({ useAuth: () => ({ isGeneralAdmin: true, isSedeAdmin: false }) }));
vi.mock('../../hooks/useFetch', () => ({ useFetch: () => ({ data: [] }) }));

import Alumnos from './Alumnos';

describe('Alumnos bulk wiring', () => {
  it('checkbox por fila + header checkbox y botón disabled si 0', async () => {
    render(<Alumnos />);
    // Wait for data load
    const checkboxes = await screen.findAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThanOrEqual(1);
    const bulkBtn = screen.getByRole('button', { name: /enviar credenciales/i });
    expect(bulkBtn).toBeDisabled();
    expect(bulkBtn).toHaveAttribute('title', expect.stringContaining('Select at least one'));
  });

  it('seleccionar checkbox habilita botón con contador', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<Alumnos />);
    });
    const checkboxes = await screen.findAllByRole('checkbox');
    // second is row checkbox (first is select-all)
    await act(async () => {
      await user.click(checkboxes[1] || checkboxes[0]);
    });
    await waitFor(() => {
      const bulkBtn = screen.getByRole('button', { name: /enviar credenciales \(1\)/i });
      expect(bulkBtn).toBeEnabled();
    });
  });
});
