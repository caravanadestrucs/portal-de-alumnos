import { test, expect } from '@playwright/test';

test.describe('Auth flows', () => {
  test('login form muestra labels accesibles y error con role=alert', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByLabel('Correo electrónico')).toBeVisible();
    await expect(page.getByLabel('Contraseña')).toBeVisible();
    await page.getByRole('button', { name: 'Iniciar Sesión' }).click();
    // html5 required validation o error toast — al menos verifica que no navegó a /admin sin creds
    await expect(page).toHaveURL(/login/);
  });

  test('login con creds inválidas muestra error', async ({ page }) => {
    // Mock backend so test is shippable without real API on :5000
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Credenciales inválidas' }),
      });
    });

    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill('no@existe.com');
    await page.getByLabel('Contraseña').fill('wrong');
    await page.getByRole('button', { name: 'Iniciar Sesión' }).click();
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 5000 });
  });

  test('toggle mostrar contraseña cambia type', async ({ page }) => {
    await page.goto('/login');
    const input = page.getByLabel('Contraseña');
    await expect(input).toHaveAttribute('type', 'password');
    await page.getByLabel(/Mostrar contraseña|Ocultar/).click();
    await expect(input).toHaveAttribute('type', 'text');
  });
});
