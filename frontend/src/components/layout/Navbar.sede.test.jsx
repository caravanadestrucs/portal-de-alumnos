import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../../context/AuthContext';
import Navbar from './Navbar';

describe('Navbar sede badge/switcher', () => {
  it('muestra badge TEO para sede_admin TEO', async () => {
    useAuth.mockReturnValue({
      user: { nombre: 'Admin TEO', rol: 'admin', role: 'sede_admin', sede_id: 1, sede: { id: 1, codigo: 'TEO', nombre: 'Teotitlan' } },
      isGeneralAdmin: false,
      isSedeAdmin: true,
      sedeId: 1,
      sede: { id: 1, codigo: 'TEO', nombre: 'Teotitlan' },
      role: 'sede_admin',
      logout: vi.fn(),
    });
    render(<Navbar onMenuClick={vi.fn()} />);
    expect(screen.getByTestId('sede-badge')).toBeInTheDocument();
    expect(screen.getByTestId('sede-badge')).toHaveTextContent(/TEO/i);
  });

  it('muestra badge HUA para sede_admin HUA', async () => {
    useAuth.mockReturnValue({
      user: { nombre: 'Admin HUA', rol: 'admin', role: 'sede_admin', sede_id: 2, sede: { id: 2, codigo: 'HUA', nombre: 'Huautla' } },
      isGeneralAdmin: false,
      isSedeAdmin: true,
      sedeId: 2,
      sede: { id: 2, codigo: 'HUA', nombre: 'Huautla' },
      role: 'sede_admin',
      logout: vi.fn(),
    });
    render(<Navbar onMenuClick={vi.fn()} />);
    expect(screen.getByTestId('sede-badge')).toBeInTheDocument();
    expect(screen.getByTestId('sede-badge')).toHaveTextContent(/HUA/i);
  });

  it('muestra badge General para general_admin', async () => {
    useAuth.mockReturnValue({
      user: { nombre: 'Super Admin', rol: 'admin', role: 'general_admin', sede_id: null, sede: null },
      isGeneralAdmin: true,
      isSedeAdmin: false,
      sedeId: null,
      sede: null,
      role: 'general_admin',
      logout: vi.fn(),
    });
    render(<Navbar onMenuClick={vi.fn()} />);
    // should show General or Todos or sin sede filter
    const general = screen.queryByText(/General/i) || screen.queryByText(/Todos/i) || screen.queryByText(/TEO|HUA/i);
    // at least it should not show TEO-specific badge when general
    // but we assert General badge exists
    expect(screen.getByText(/General/i)).toBeInTheDocument();
  });

  it('general_admin ve switcher/select de sede', async () => {
    useAuth.mockReturnValue({
      user: { nombre: 'Super Admin', rol: 'admin', role: 'general_admin', sede_id: null },
      isGeneralAdmin: true,
      isSedeAdmin: false,
      sedeId: null,
      sede: null,
      role: 'general_admin',
      logout: vi.fn(),
    });
    render(<Navbar onMenuClick={vi.fn()} />);
    // switcher could be select or buttons with TEO/HUA options
    const hasSwitcher = screen.queryByRole('combobox') || screen.queryByText(/TEO/) || screen.queryByText(/HUA/) || screen.queryByLabelText(/sede/i);
    expect(hasSwitcher).toBeInTheDocument();
  });
});
