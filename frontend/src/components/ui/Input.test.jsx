import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Input from './Input';

describe('Input', () => {
  it('asocia label con input via htmlFor/id', () => {
    render(<Input label="Email" />);
    const input = screen.getByLabelText('Email');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('id');
    const label = document.querySelector('label');
    expect(label).toHaveAttribute('for', input.id);
  });

  it('muestra error con role=alert', () => {
    render(<Input label="Email" error="Requerido" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Requerido');
  });

  it('aria-invalid cuando hay error', () => {
    render(<Input label="Email" error="x" />);
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true');
  });

  it('muestra helper cuando no hay error', () => {
    render(<Input label="Email" helper="Formato: nombre@ejemplo.com" />);
    expect(screen.getByText('Formato: nombre@ejemplo.com')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('no muestra helper cuando hay error', () => {
    render(<Input label="Email" helper="Ayuda" error="Requerido" />);
    expect(screen.queryByText('Ayuda')).not.toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('id custom se usa', () => {
    render(<Input label="Email" id="custom-id" />);
    expect(screen.getByLabelText('Email')).toHaveAttribute('id', 'custom-id');
  });
});
