import { describe, it, expect, vi } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConfirmDialog from './ConfirmDialog';

describe('ConfirmDialog', () => {
  it('no renderiza cuando isOpen false', () => {
    render(<ConfirmDialog isOpen={false} onClose={vi.fn()} onConfirm={vi.fn()} />);
    expect(screen.queryByText('¿Estás seguro?')).not.toBeInTheDocument();
  });

  it('renderiza title/message/impact cuando open', () => {
    render(
      <ConfirmDialog
        isOpen
        title="Eliminar alumno"
        message="Se borrará el registro"
        impactSummary="Se eliminarán 3 materias"
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />
    );
    expect(screen.getByText('Eliminar alumno')).toBeInTheDocument();
    expect(screen.getByText('Se borrará el registro')).toBeInTheDocument();
    expect(screen.getByText('Se eliminarán 3 materias')).toBeInTheDocument();
  });

  it('botón Confirmar disabled si requireConfirmText no coincide', async () => {
    const user = userEvent.setup();
    render(<ConfirmDialog isOpen requireConfirmText="BORRAR" onClose={vi.fn()} onConfirm={vi.fn()} />);
    const confirmBtn = screen.getByRole('button', { name: 'Confirmar' });
    expect(confirmBtn).toBeDisabled();
    await act(async () => {
      await user.type(screen.getByPlaceholderText('BORRAR'), 'BORRAR');
    });
    await waitFor(() => expect(screen.getByRole('button', { name: 'Confirmar' })).toBeEnabled());
  });

  it('mantiene disabled si el texto no coincide exactamente', async () => {
    const user = userEvent.setup();
    render(<ConfirmDialog isOpen requireConfirmText="BORRAR" onClose={vi.fn()} onConfirm={vi.fn()} />);
    await act(async () => {
      await user.type(screen.getByPlaceholderText('BORRAR'), 'borrar');
    });
    await waitFor(() => expect(screen.getByRole('button', { name: 'Confirmar' })).toBeDisabled());
  });

  it('llama onConfirm al click', async () => {
    const user = userEvent.setup();
    const fn = vi.fn();
    render(<ConfirmDialog isOpen onConfirm={fn} onClose={vi.fn()} />);
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Confirmar/i }));
    });
    expect(fn).toHaveBeenCalledOnce();
  });

  it('llama onClose al click en Cancelar', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<ConfirmDialog isOpen onClose={onClose} onConfirm={vi.fn()} />);
    await act(async () => {
      await user.click(screen.getByRole('button', { name: 'Cancelar' }));
    });
    expect(onClose).toHaveBeenCalledOnce();
  });
});
