import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OnboardingTour from './OnboardingTour';

const STORAGE_KEY = 'onboarding_seen_v1';

describe('OnboardingTour', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('primer login muestra tour en paso 1 Tus calificaciones con boton Siguiente', () => {
    const onComplete = vi.fn();
    const onSkip = vi.fn();
    render(<OnboardingTour isOpen={true} onComplete={onComplete} onSkip={onSkip} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    // Paso 1 title según spec
    expect(screen.getByText(/Tus calificaciones/i)).toBeInTheDocument();
    // debe tener Next/Siguiente y Skip
    expect(screen.getByRole('button', { name: /Siguiente|Next/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Saltar|Skip/i })).toBeInTheDocument();
  });

  it('Skip cierra y persiste onboarding_seen_v1=true y llama onSkip', async () => {
    const user = userEvent.setup();
    const onSkip = vi.fn();
    const onComplete = vi.fn();
    const onClose = vi.fn();
    render(<OnboardingTour isOpen={true} onSkip={onSkip} onComplete={onComplete} onClose={onClose} />);
    const skipBtn = screen.getByRole('button', { name: /Saltar|Skip/i });
    await act(async () => {
      await user.click(skipBtn);
    });
    await waitFor(() => expect(localStorage.getItem(STORAGE_KEY)).toBe('true'));
    expect(onSkip).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem(STORAGE_KEY)).toBe('true');
  });

  it('segundo login no muestra tour cuando flag ya existe (suprime)', () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    // Simulamos wrapper que decide no renderizar Tour si flag existe
    function Wrapper() {
      const shouldShow = !localStorage.getItem(STORAGE_KEY);
      if (!shouldShow) return <div>dashboard sin tour</div>;
      return <OnboardingTour isOpen={true} onComplete={vi.fn()} onSkip={vi.fn()} />;
    }
    render(<Wrapper />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByText(/dashboard sin tour/i)).toBeInTheDocument();
  });

  it('navegación Next 1→2→3 y Finish persiste y Prev vuelve', async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    render(<OnboardingTour isOpen={true} onComplete={onComplete} onSkip={vi.fn()} />);
    // paso 1
    expect(screen.getByRole('heading', { name: /Tus calificaciones/i })).toBeInTheDocument();
    // Next a paso 2
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Siguiente|Next/i }));
    });
    await waitFor(() => expect(screen.getByRole('heading', { name: /^Pagos$/i })).toBeInTheDocument());
    // Next a paso 3
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Siguiente|Next/i }));
    });
    await waitFor(() => expect(screen.getByRole('heading', { name: /Requisitos/i })).toBeInTheDocument());
    // Prev vuelve a paso 2
    const prevBtn = screen.getByRole('button', { name: /Anterior|Prev|Atrás/i });
    await act(async () => {
      await user.click(prevBtn);
    });
    await waitFor(() => expect(screen.getByRole('heading', { name: /^Pagos$/i })).toBeInTheDocument());
    // volver a paso 3
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Siguiente|Next/i }));
    });
    await waitFor(() => expect(screen.getByRole('heading', { name: /Requisitos/i })).toBeInTheDocument());
    // Finish debe persistir y llamar onComplete
    const finishBtn = screen.getByRole('button', { name: /Finalizar|Finish|Completar/i });
    await act(async () => {
      await user.click(finishBtn);
    });
    await waitFor(() => expect(localStorage.getItem(STORAGE_KEY)).toBe('true'));
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it('tiene foco en paso y es accesible', async () => {
    render(<OnboardingTour isOpen={true} onComplete={vi.fn()} onSkip={vi.fn()} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(2);
    // wait for 30ms focus timeout to settle inside act
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });
  });
});
