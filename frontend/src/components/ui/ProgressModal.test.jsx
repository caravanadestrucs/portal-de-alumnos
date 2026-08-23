import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProgressModal from './ProgressModal';

describe('ProgressModal', () => {
  it('no renderiza cuando isOpen false', () => {
    render(<ProgressModal isOpen={false} items={[]} onClose={vi.fn()} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument;
    // alternative query
    expect(document.body.textContent).not.toContain('Progreso');
  });

  it('muestra lista con ✓/✗ y barra x/y', () => {
    const items = [
      { id: 1, email: 'a@test.com', status: 'sent' },
      { id: 2, email: 'b@test.com', status: 'failed', error: 'SMTP timeout' },
      { id: 3, email: 'c@test.com', status: 'sent' },
    ];
    render(<ProgressModal isOpen items={items} onClose={vi.fn()} onRetryFailed={vi.fn()} />);
    expect(screen.getAllByText(/2\/3|2 de 3/i).length).toBeGreaterThan(0);
    // sent rows have check, failed have cross
    expect(screen.getByText('a@test.com')).toBeInTheDocument();
    expect(screen.getByText('b@test.com')).toBeInTheDocument();
    // badge status
    expect(screen.getAllByText(/sent|enviado|✓/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/failed|fall/i).length).toBeGreaterThan(0);
  });

  it('botón Reintentar fallidos solo llama con ids failed', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    const items = [
      { id: 7, email: 'a@test.com', status: 'sent' },
      { id: 12, email: 'b@test.com', status: 'failed' },
    ];
    render(<ProgressModal isOpen items={items} onRetryFailed={onRetry} onClose={vi.fn()} />);
    const btn = screen.getByRole('button', { name: /reintentar/i });
    expect(btn).toBeEnabled();
    await user.click(btn);
    expect(onRetry).toHaveBeenCalledOnce();
    // should have been called with failed ids
    const arg = onRetry.mock.calls[0][0];
    expect(arg).toContain(12);
    expect(arg).not.toContain(7);
  });

  it('is accessible con aria-live', () => {
    const items = [{ id: 1, email: 'a@test.com', status: 'sent' }];
    const { container } = render(<ProgressModal isOpen items={items} onClose={vi.fn()} />);
    expect(container.querySelector('[aria-live]')).not.toBeNull();
  });
});
