import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GlobalSearch from './GlobalSearch';

describe('GlobalSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renderiza input buscador placeholder Cmd+K', () => {
    render(<GlobalSearch />);
    expect(screen.getByPlaceholderText(/Buscar.*Cmd\+K|Cmd\+K.*Buscar/i)).toBeInTheDocument();
  });

  it('muestra mock resultados al escribir', async () => {
    const user = userEvent.setup();
    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText(/Buscar/i);
    await act(async () => {
      await user.type(input, 'alumno');
    });
    await waitFor(() => expect(screen.getByText(/Alumnos/i)).toBeInTheDocument());
  });

  it('Cmd+K abre buscador (focus)', async () => {
    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText(/Buscar/i);
    await act(async () => {
      const event = new KeyboardEvent('keydown', { key: 'k', metaKey: true });
      window.dispatchEvent(event);
    });
    await waitFor(() => expect(document.activeElement).toBe(input));
  });

  it('filtra resultados mock al escribir query diferente', async () => {
    const user = userEvent.setup();
    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText(/Buscar/i);
    await act(async () => {
      await user.type(input, 'pago');
    });
    await waitFor(() => expect(screen.getByText(/Pagos/i)).toBeInTheDocument());
  });

  it('muestra mensaje sin resultados cuando query no matchea', async () => {
    const user = userEvent.setup();
    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText(/Buscar/i);
    await act(async () => {
      await user.type(input, 'zzzzzz');
    });
    await waitFor(() => expect(screen.getByText(/Sin resultados/i)).toBeInTheDocument());
  });
});
