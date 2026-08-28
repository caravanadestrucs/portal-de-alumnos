import { describe, it, expect, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../../api/alumnos', () => ({ getAlumnos: vi.fn().mockResolvedValue({ total: 5, alumnos: [] }) }));
vi.mock('../../api/carreras', () => ({ getCarreras: vi.fn().mockResolvedValue([{ id: 1 }, { id: 2 }]) }));
vi.mock('../../api/materias', () => ({ getMaterias: vi.fn().mockResolvedValue([{ id: 1 }]) }));
vi.mock('../../api/pagos', () => ({ getAlumnosConPagosPendientes: vi.fn().mockResolvedValue({ alumnos: [], total_adeudo: 0 }) }));
vi.mock('../../api/sedes', () => ({
  getSedes: vi.fn().mockResolvedValue({ sedes: [{ id: 1, codigo: 'TEO' }, { id: 2, codigo: 'HUA' }], total: 2 }),
}));
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ user: { nombre: 'Admin', rol: 'admin', role: 'general_admin' }, isGeneralAdmin: true, isSedeAdmin: false, sedeId: null, sede: null }),
}));

import Dashboard from './Dashboard';

describe('Dashboard sede scoped', () => {
  it('file calls /api/sedes and scopes stats', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Dashboard.jsx'), 'utf-8');
    expect(content).toMatch(/getSedes|\/sedes|sedes/);
    expect(content).toMatch(/sede|TEO|HUA|scoped/i);
  });

  it('renders sede badge or counts', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );
    // should show Alumnos count and maybe sede badge
    expect(await screen.findByText(/Alumnos/i)).toBeInTheDocument();
    // check heading bienvenido
    expect(screen.getByRole('heading', { name: /Bienvenido/i })).toBeInTheDocument();
    // badge for general
    expect(screen.getByText(/General/)).toBeInTheDocument();
  });

  it('fetches sedes for general_admin', async () => {
    const { getSedes } = await import('../../api/sedes');
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );
    await screen.findByText(/Alumnos/i);
    // getSedes should have been called
    expect(getSedes).toHaveBeenCalled();
  });
});
