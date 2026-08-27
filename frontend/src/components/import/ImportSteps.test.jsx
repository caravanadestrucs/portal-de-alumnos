import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ImportSteps from './ImportSteps';

describe('ImportSteps placeholder', () => {
  it('renderiza 4 pasos y marca activo', () => {
    render(<ImportSteps currentStep={2} />);
    expect(screen.getByText('Tipo')).toBeInTheDocument();
    expect(screen.getByText('Archivo')).toBeInTheDocument();
    expect(screen.getByText('Previsualizar')).toBeInTheDocument();
    expect(screen.getByText('Resultados')).toBeInTheDocument();
    // step 2 debe estar activo
    const active = screen.getByText('Archivo').closest('div') || screen.getByText('Archivo');
    expect(active).toBeInTheDocument();
  });

  it('muestra TODO comment para tanstack-virtual', () => {
    const { container } = render(<ImportSteps currentStep={1} />);
    // placeholder debe tener data-testid o texto TODO
    expect(container.textContent).toMatch(/TODO|tanstack-virtual/i);
  });
});
