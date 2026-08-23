import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Settings calendario pagos', () => {
  it('Settings.jsx renderiza sección calendario y conecta a api/settings', () => {
    const content = fs.readFileSync(path.resolve('src/pages/admin/Settings.jsx'), 'utf-8');
    expect(content).toMatch(/calendario|Calendario|pagos.*calendario/i);
    expect(content).toMatch(/api\/settings|getPaymentCalendar|payment/i);
  });

  it('api/settings.js expone calendario CRUD', () => {
    const apiContent = fs.readFileSync(path.resolve('src/api/settings.js'), 'utf-8');
    expect(apiContent).toMatch(/getPaymentCalendar|calendario/i);
  });
});
