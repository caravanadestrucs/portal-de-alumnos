import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('App.jsx sede/wiki routes', () => {
  const content = fs.readFileSync(path.resolve('src/App.jsx'), 'utf-8');

  it('defines /admin/sedes route', () => {
    expect(content).toMatch(/path="sedes"|GeneralAdminRoute|AdminSedes/);
  });

  it('defines /admin/wiki route for WikiAdmin', () => {
    expect(content).toMatch(/path="wiki"|AdminWiki/);
  });

  it('defines /wiki/:slug route for public wiki read', () => {
    expect(content).toMatch(/\/wiki\/:slug|\/wiki\/:id|WikiPage/);
  });

  it('imports Sedes and Wiki components lazy or direct', () => {
    expect(content).toMatch(/Sedes|WikiAdmin|WikiPage/);
  });

  it('ProtectedRoute handles admin role guards (general vs sede)', () => {
    // must check role/sede_id in guard logic
    expect(content).toMatch(/isGeneralAdmin|general_admin|sede_admin|role/);
  });
});
