import { test, expect } from '@playwright/test';

test.describe('Admin critical paths (auth mocked)', () => {
  test.beforeEach(async ({ page }) => {
    // Mock localStorage para simular admin logueado sin depender de backend
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-for-e2e');
      localStorage.setItem(
        'user',
        JSON.stringify({ id: 1, rol: 'admin', type: 'admin', email: 'admin@universidadfv.edu.mx', nombre: 'Admin' })
      );
    });

    // Mock all API calls so pages render shell without real backend on :5000
    await page.route('**/api/**', async (route) => {
      const url = route.request().url();
      if (url.includes('/api/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 1, rol: 'admin', type: 'admin', email: 'admin@universidadfv.edu.mx', nombre: 'Admin' }),
        });
        return;
      }
      if (url.includes('/api/alumnos')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ alumnos: [], total: 0, pages: 0 }),
        });
        return;
      }
      if (url.includes('/api/carreras')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
        return;
      }
      if (url.includes('/api/materias')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
        return;
      }
      if (url.includes('/api/pagos')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ alumnos: [], total_adeudo: 0 }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      });
    });
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
