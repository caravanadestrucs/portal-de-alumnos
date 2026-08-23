import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EmptyState from './EmptyState';
import { Search } from 'lucide-react';

describe('EmptyState', () => {
  it('renderiza titulo y descripcion', () => {
    render(<EmptyState icon={Search} title="Sin resultados" description="No hay datos para mostrar" />);
    expect(screen.getByText('Sin resultados')).toBeInTheDocument();
    expect(screen.getByText('No hay datos para mostrar')).toBeInTheDocument();
  });

  it('renderiza icono cuando se provee', () => {
    render(<EmptyState icon={Search} title="Vacío" />);
    // lucide icons render svg
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('muestra accion con label y llama onAction al click', async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    render(<EmptyState title="Sin pagos" actionLabel="Crear pago" onAction={onAction} />);
    const btn = screen.getByRole('button', { name: /Crear pago/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('no muestra boton cuando no hay actionLabel', () => {
    render(<EmptyState title="Vacío" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('actionLabel sin onAction no rompe', () => {
    render(<EmptyState title="Vacío" actionLabel="Acción" />);
    expect(screen.getByRole('button', { name: /Acción/i })).toBeInTheDocument();
  });
});
