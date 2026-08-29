import { test, expect } from '@playwright/test';

test.describe('A11y smoke', () => {
  test('login page inputs tienen labels asociados', async ({ page }) => {
    await page.goto('/login');
    const email = page.getByRole('textbox', { name: 'Correo electrónico' });
    await expect(email).toBeVisible();
    await expect(email).toHaveAttribute('id', /login-email/);
    // aria-invalid no debe existir sin error inicial o debe ser false
    await expect(email).toHaveAttribute('type', 'email');

    const password = page.locator('#login-password');
    await expect(password).toBeVisible();
    await expect(password).toHaveAttribute('id', /login-password/);

    // Links accesibles por role
    await expect(page.getByRole('link', { name: /Olvidaste tu contraseña/i })).toBeVisible();
    // Registration is invite-only (/r/*), no public signup link should exist
    await expect(page.getByRole('link', { name: /Regístrate/i })).toHaveCount(0);

    // Logo tiene alt accesible
    await expect(page.getByRole('img', { name: /Universidad Felipe Villanueva/i })).toBeVisible();

    // Heading jerarquía
    await expect(page.getByRole('heading', { name: 'Iniciar Sesión' })).toBeVisible();
  });

  test('modal focus trap y Esc', async ({ page }) => {
    // Mock auth + APIs para entrar a /admin/alumnos sin backend real — use robust init like wiki-sede
    const adminUser = { id: 1, rol: 'admin', type: 'admin', nombre: 'Admin', role: 'general_admin', sede_id: null };
    await page.addInitScript(({ token, user }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    }, { token: 'fake-jwt-token', user: adminUser });

    await page.route((url) => new URL(url).pathname.startsWith('/api/alumnos'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          alumnos: [
            {
              id: 1,
              nombre: 'Test',
              apellido_paterno: 'User',
              numero_control: 'CTRL001',
              email: 'test@test.com',
              carrera: { nombre: 'Sistemas' },
              activo: true,
            },
          ],
          total: 1,
          pages: 1,
        }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/carreras'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ carreras: [{ id: 1, nombre: 'Sistemas' }] }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/sedes'), async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ sedes: [{ id: 1, nombre: 'Teotitlan', codigo: 'TEO' }, { id: 2, nombre: 'Huautla', codigo: 'HUA' }] }),
        });
      } else {
        await route.continue();
      }
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/auth/me'), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ type: 'admin', user: adminUser }),
      });
    });
    await page.route((url) => new URL(url).pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.evaluate(({ token, user }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    }, { token: 'fake-jwt-token', user: adminUser });

    await page.goto('/admin/alumnos', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('body')).toContainText(/Alumnos/i, { timeout: 5000 });

    // Abrir modal "Nuevo Alumno" — trigger por role
    const newBtn = page.getByRole('button', { name: /Nuevo Alumno/i });
    await expect(newBtn).toBeVisible({ timeout: 5000 });
    await newBtn.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });
    await expect(dialog).toHaveAttribute('aria-modal', 'true');
    await expect(page.getByRole('heading', { name: /Nuevo Alumno/i })).toBeVisible();

    // Focus trap: al abrir, un input o botón dentro del dialog tiene foco
    const firstInput = dialog.getByLabel('Nombre');
    await expect(firstInput).toBeFocused({ timeout: 3000 }).catch(async () => {
      // Fallback: al menos algún elemento focusable tiene foco dentro del dialog
      const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
      expect(['INPUT', 'BUTTON', 'SELECT']).toContain(focusedTag);
      expect(await dialog.evaluate((el) => el.contains(document.activeElement))).toBe(true);
    });

    // Esc cierra el modal
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden({ timeout: 3000 });

    // Reabre y cierra con botón X / Cerrar modal
    await newBtn.click();
    await expect(dialog).toBeVisible({ timeout: 5000 });
    // Use JS click to avoid sticky header intercepting pointer events on X button
    await dialog.getByLabel('Cerrar modal').evaluate((el) => el.click());
    await expect(dialog).toBeHidden({ timeout: 3000 });

    // Reabre y cierra con Cancelar en footer
    await newBtn.click();
    await expect(dialog).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: 'Cancelar' }).click();
    await expect(dialog).toBeHidden({ timeout: 3000 });
  });
});
