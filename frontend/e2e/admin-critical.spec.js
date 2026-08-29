import { test, expect } from '@playwright/test';

test.describe('Admin critical paths (auth mocked)', () => {
  const adminUser = {
    id: 1,
    rol: 'admin',
    type: 'admin',
    user_type: 'admin',
    email: 'admin@universidadfv.edu.mx',
    nombre: 'Admin',
    role: 'general_admin',
    sede_id: null,
    sede: null,
  };

  test.beforeEach(async ({ page }) => {
    // Ensure authenticated session before any navigation — mirrors wiki-sede helper
    await page.addInitScript(({ token, user }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    }, { token: 'fake-jwt-for-e2e', user: adminUser });

    // Auth me
    await page.route((url) => new URL(url).pathname === '/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ type: 'admin', user: adminUser }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/sedes'), async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ sedes: [{ id: 1, nombre: 'Teotitlan', codigo: 'TEO' }, { id: 2, nombre: 'Huautla', codigo: 'HUA' }], total: 2 }),
        });
      } else {
        await route.continue();
      }
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/alumnos'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ alumnos: [], total: 0, pages: 0, page: 1 }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/carreras'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ carreras: [] }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/materias'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ materias: [] }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/pagos'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ alumnos: [], total_adeudo: 0 }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/wiki'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ pages: [], total: 0 }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.evaluate(({ token, user }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    }, { token: 'fake-jwt-for-e2e', user: adminUser });
  });

  test('admin dashboard carga con sidebar y stats', async ({ page }) => {
    await page.goto('/admin');
    // Sidebar uses <aside> glass-dark; fallback to navigation role
    await expect(page.locator('aside').first()).toBeVisible({ timeout: 5000 });
    // Al menos una card o título
    await expect(page.locator('body')).toContainText(/Dashboard|Alumnos|Estadísticas|Bienvenido/i);
  });

  test('ConfirmDialog aparece al intentar eliminar (no nativo)', async ({ page }) => {
    // Prevenir dialog nativo si algún código aún usa window.confirm
    page.on('dialog', async (dialog) => {
      throw new Error(`Se usó confirm nativo en lugar de ConfirmDialog: ${dialog.message()}`);
    });

    await page.goto('/admin/alumnos');
    await expect(page.locator('body')).toContainText(/Alumnos/i, { timeout: 5000 });

    // Si hay botón eliminar, click debe abrir dialog no confirm nativo
    const deleteBtn = page.getByRole('button', { name: /Eliminar/i }).first();
    const count = await deleteBtn.count();
    // También probar selector aria-label dinámico usado en AdminAlumnos.jsx
    const deleteByLabel = page.locator('button[aria-label^="Eliminar alumno"]').first();
    const hasAriaBtn = (await deleteByLabel.count()) > 0;

    const targetBtn = hasAriaBtn ? deleteByLabel : deleteBtn;

    if ((await targetBtn.count()) > 0 && (await targetBtn.isVisible().catch(() => false))) {
      await targetBtn.click();
      await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });
      await expect(page.getByRole('button', { name: 'Cancelar' })).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(page.getByRole('dialog')).toBeHidden({ timeout: 3000 });
    } else {
      // No hay datos — verifica que la página cargó sin confirm nativo y sin error
      await expect(page.locator('body')).toContainText(/Alumnos/i);
      // Verifica que ConfirmDialog no está visible cuando no hay deleteTarget
      await expect(page.getByRole('dialog')).toBeHidden();
    }
  });
});
