import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'fs';
import path from 'path';

vi.mock('../../api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { admins: [{ id: 1, username: 'admin', nombre: 'Admin', email: 'a@fv.edu', role: 'general_admin', sede_id: null }] } }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

vi.mock('../../api/sedes', () => ({
  getSedes: vi.fn().mockResolvedValue({ sedes: [{ id: 1, codigo: 'TEO', nombre: 'Teotitlan' }, { id: 2, codigo: 'HUA', nombre: 'Huautla' }] }),
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, rol: 'admin', role: 'general_admin' }, isGeneralAdmin: true }),
}));

import Admins from './Admins';

describe('Admins role/sede picker', () => {
  it('file contains role and sede picker logic', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Admins.jsx'), 'utf-8');
    expect(content).toMatch(/role|general_admin|sede_admin/);
    expect(content).toMatch(/sede_id|sedeId|getSedes/);
  });

  it('renders role select and sede select for general_admin', async () => {
    await act(async () => {
      render(<Admins />);
    });
    const newBtn = await screen.findByRole('button', { name: /Nuevo Administrador/i });
    await act(async () => {
      await userEvent.setup().click(newBtn);
    });
    expect(await screen.findByLabelText(/Rol/i)).toBeInTheDocument();
    expect(screen.getAllByText(/general_admin/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/sede_admin/i).length).toBeGreaterThanOrEqual(1);
  });

  it('sede select shows TEO/HUA options', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<Admins />);
    });
    const newBtn = await screen.findByRole('button', { name: /Nuevo Administrador/i });
    await act(async () => {
      await user.click(newBtn);
    });
    const roleSelect = await screen.findByLabelText(/Rol/i);
    await act(async () => {
      await user.selectOptions(roleSelect, 'sede_admin');
    });
    await waitFor(async () => {
      expect((await screen.findAllByText(/TEO/)).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/HUA/).length).toBeGreaterThanOrEqual(1);
    });
  });
});
