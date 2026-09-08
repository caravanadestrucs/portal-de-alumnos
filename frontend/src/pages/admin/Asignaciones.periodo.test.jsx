import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../../api/asignaciones', () => ({
  getAsignaciones: vi.fn().mockResolvedValue([]),
  createAsignacion: vi.fn().mockResolvedValue({}),
  updateAsignacion: vi.fn().mockResolvedValue({}),
  deleteAsignacion: vi.fn().mockResolvedValue({}),
}));
vi.mock('../../api/profesores', () => ({ getProfesores: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/materias', () => ({ getMaterias: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/grupos', () => ({ getGrupos: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/periodos', () => ({
  getPeriodos: vi.fn().mockResolvedValue({ periodos: [
    { id: 1, nombre: 'Enero-Abril 2026', activa: true },
    { id: 2, nombre: 'Viejo', activa: false },
  ] }),
}));
vi.mock('../../components/ui/Toast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));

import AdminAsignaciones from './Asignaciones';
import { getAsignaciones, createAsignacion } from '../../api/asignaciones';

describe('Asignaciones periodo UI', () => {
  beforeEach(() => vi.clearAllMocks());

  it('el dropdown de crear muestra nombres y crear sin periodo no envia', async () => {
    render(<AdminAsignaciones />);
    fireEvent.click(await screen.findByText('Nueva Asignación'));
    expect(await screen.findByText('Enero-Abril 2026')).toBeInTheDocument();
    expect(screen.queryByText('Viejo')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Crear'));
    await waitFor(() => expect(createAsignacion).not.toHaveBeenCalled());
  });

  it('la tabla muestra Sin periodo ante periodo_id null', async () => {
    getAsignaciones.mockResolvedValueOnce([{ id: 7, profesor_id: 1, materia_id: 1, grupo_id: 1,
      fecha_inicio: '2026-01-01', fecha_fin: '2026-04-30',
      periodo_id: null, periodo_nombre: 'Sin periodo', puede_editar: true, activo: true }]);
    render(<AdminAsignaciones />);
    expect(await screen.findByText('Sin periodo')).toBeInTheDocument();
    expect(screen.getByText('Período')).toBeInTheDocument();
    expect(screen.getByText('Fechas')).toBeInTheDocument();
  });
});
