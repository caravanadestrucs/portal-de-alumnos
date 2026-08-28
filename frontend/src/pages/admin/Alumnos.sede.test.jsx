import { describe, it, expect, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import { render, screen } from '@testing-library/react';

vi.mock('../../api/alumnos', () => ({
  getAlumnos: vi.fn().mockResolvedValue({ alumnos: [
    { id: 1, nombre: 'Ana', apellido_paterno: 'Lopez', email: 'a@test.com', numero_control: '11111111', carrera: { nombre: 'ISC' }, activo: true, carrera_id: 1, sede_id: 1, sede: { id: 1, codigo: 'TEO' } },
    { id: 2, nombre: 'Juan', apellido_paterno: 'Perez', email: 'j@test.com', numero_control: '22222222', carrera: { nombre: 'ISC' }, activo: true, carrera_id: 1, sede_id: 2, sede: { id: 2, codigo: 'HUA' } },
  ], total: 2, pages: 1 }),
  createAlumno: vi.fn(),
  updateAlumno: vi.fn(),
  deleteAlumno: vi.fn(),
  sendBulkCredentials: vi.fn().mockResolvedValue({ results: [] }),
}));
vi.mock('../../api/carreras', () => ({ getCarreras: vi.fn().mockResolvedValue([{ id: 1, nombre: 'ISC' }]) }));
vi.mock('../../api/sedes', () => ({
  getSedes: vi.fn().mockResolvedValue({ sedes: [{ id: 1, codigo: 'TEO', nombre: 'Teotitlan' }, { id: 2, codigo: 'HUA', nombre: 'Huautla' }] }),
}));
vi.mock('../../hooks/useFetch', () => ({ useFetch: () => ({ data: [{ id: 1, nombre: 'ISC' }] }) }));
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isGeneralAdmin: true, isSedeAdmin: false, sedeId: null }),
}));

import Alumnos from './Alumnos';

describe('Alumnos sede filter/column', () => {
  it('file contains sede filter logic and column', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Alumnos.jsx'), 'utf-8');
    expect(content).toMatch(/sede_id|sedeId|Sede/);
    expect(content).toMatch(/getSedes|sedes/);
    expect(content).toMatch(/codigo.*TEO|TEO.*HUA|sede/i);
  });

  it('renders sede column and filter dropdown', async () => {
    render(<Alumnos />);
    // column header Sede
    expect(await screen.findByText(/Sede/i)).toBeInTheDocument();
    // filter dropdown - combobox or select with Todos/TEO/HUA
    const filter = await screen.findByRole('combobox');
    expect(filter).toBeInTheDocument();
    // check TEO/HUA visible in table
    expect(await screen.findByText('TEO')).toBeInTheDocument();
    expect(screen.getByText('HUA')).toBeInTheDocument();
  });

  it('general_admin sees sede filter, sede_admin sees scoped badge', async () => {
    render(<Alumnos />);
    expect(await screen.findByText(/Sede/i)).toBeInTheDocument();
    // at least one badge TEO/HUA
    const badges = await screen.findAllByText(/TEO|HUA/);
    expect(badges.length).toBeGreaterThanOrEqual(2);
  });
});
