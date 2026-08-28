import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../api/sedes', () => ({
  getSedes: vi.fn().mockResolvedValue({ sedes: [
    { id: 1, nombre: 'Teotitlan', codigo: 'TEO', direccion: 'Addr TEO', activa: true },
    { id: 2, nombre: 'Huautla', codigo: 'HUA', direccion: 'Addr HUA', activa: true },
  ], total: 2 }),
  createSede: vi.fn().mockResolvedValue({ sede: { id: 3, codigo: 'NEW' } }),
  updateSede: vi.fn().mockResolvedValue({ sede: { id: 1, nombre: 'Updated' } }),
  deleteSede: vi.fn().mockResolvedValue({ message: 'deleted' }),
  getSede: vi.fn(),
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isGeneralAdmin: true, user: { role: 'general_admin' } }),
}));

import Sedes from './Sedes';

describe('Sedes CRUD', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renderiza titulo y tabla con sedes TEO/HUA', async () => {
    await act(async () => {
      render(<Sedes />);
    });
    expect(await screen.findByRole('heading', { name: /Sedes/i })).toBeInTheDocument();
    expect(await screen.findByText('TEO')).toBeInTheDocument();
    expect(await screen.findByText('HUA')).toBeInTheDocument();
    expect(screen.getByText(/Teotitlan/)).toBeInTheDocument();
  });

  it('tiene boton Nuevo y abre modal crear', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<Sedes />);
    });
    const btn = await screen.findByRole('button', { name: /Nueva Sede/i });
    expect(btn).toBeInTheDocument();
    await act(async () => {
      await user.click(btn);
    });
    expect(await screen.findByRole('heading', { name: /Crear Sede/i })).toBeInTheDocument();
  });

  it('muestra codigo, nombre, direccion y acciones', async () => {
    await act(async () => {
      render(<Sedes />);
    });
    await screen.findByText('TEO');
    await waitFor(() => expect(screen.getByText(/Direccion|Dirección/i) || screen.getByText(/Addr TEO/)).toBeInTheDocument());
    // at least one edit/delete button
    const edits = screen.getAllByRole('button');
    expect(edits.length).toBeGreaterThan(2);
  });

  it('filtra solo propias si es sede_admin? General ve todas', async () => {
    await act(async () => {
      render(<Sedes />);
    });
    await screen.findByText('TEO');
    // general should see both
    expect(screen.getByText('TEO')).toBeInTheDocument();
    expect(screen.getByText('HUA')).toBeInTheDocument();
  });
});
