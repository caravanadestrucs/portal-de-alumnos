import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('App lazy loading', () => {
  it('usa React.lazy para Importar y Boletas', () => {
    const content = fs.readFileSync(path.resolve('src/App.jsx'), 'utf-8');
    expect(content).toMatch(/React\.lazy|lazy\(/);
    expect(content).toMatch(/Importar/);
    expect(content).toMatch(/Boletas/);
    expect(content).toMatch(/Suspense/);
  });

  it('tiene comentario tanstack-virtual', () => {
    const content = fs.readFileSync(path.resolve('src/App.jsx'), 'utf-8');
    expect(content).toMatch(/tanstack-virtual|virtualizaci/i);
  });
});
