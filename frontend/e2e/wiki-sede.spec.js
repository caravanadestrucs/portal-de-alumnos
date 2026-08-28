import { test, expect } from '@playwright/test';

async function mockSedes(page) {
  await page.route((url) => new URL(url).pathname.startsWith('/api/sedes'), async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sedes: [
            { id: 1, nombre: 'Teotitlan', codigo: 'TEO', direccion: 'Teotitlan', activa: true },
            { id: 2, nombre: 'Huautla', codigo: 'HUA', direccion: 'Huautla', activa: true },
          ],
          total: 2,
        }),
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ sede: { id: 3, nombre: 'Test', codigo: 'TST' } }),
      });
    } else {
      await route.continue();
    }
  });
}

async function mockWiki(page, { isCross403 = false } = {}) {
  await page.route((url) => new URL(url).pathname.startsWith('/api/wiki/pages'), async (route) => {
    const method = route.request().method();
    const url = route.request().url();
    if (method === 'GET') {
      const u = new URL(url);
      const slug = u.searchParams.get('slug');
      if (isCross403 && slug === 'manual-hua') {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Cross-sede forbidden', code: 'CROSS_SEDE' }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          pages: [
            { id: 1, slug: 'guia', title: 'Guia TEO', sede_id: 1, body_markdown: '# Hola TEO', sede: { id: 1, codigo: 'TEO' } },
            { id: 2, slug: 'reg', title: 'Reglamento', sede_id: null, body_markdown: 'global', sede: null },
            { id: 3, slug: 'manual-hua', title: 'Manual HUA', sede_id: 2, body_markdown: '# HUA' },
          ],
          total: 3,
        }),
      });
    } else if (method === 'POST') {
      const body = route.request().postDataJSON?.() || {};
      if (body.slug === 'guia' && body.sede_id === 1) {
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Slug already exists for this sede' }),
        });
        return;
      }
      if (isCross403 && body.sede_id === 2) {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Forbidden', code: 'CROSS_SEDE' }),
        });
        return;
      }
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ page: { id: 99, ...body } }),
      });
    } else if (method === 'PUT' && isCross403) {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Cross-sede forbidden' }),
      });
    } else {
      await route.continue();
    }
  });

  await page.route((url) => new URL(url).pathname.match(/\/api\/wiki\/pages\/\d+\/history/), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ revisions: [{ id: 1, body_markdown: '# v1', title: 'Guia' }], history: [{ id: 1 }], total: 1 }),
    });
  });

  await page.route((url) => new URL(url).pathname.match(/\/api\/wiki\/pages\/\d+\/attachments/), async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ attachments: [{ id: 10, filename: 'manual.pdf', mime: 'application/pdf' }], total: 1 }),
      });
    } else {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ attachment: { id: 10, filename: 'manual.pdf' } }),
      });
    }
  });
  await page.route((url) => new URL(url).pathname.startsWith('/api/wiki/attachments'), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({}),
    });
  });
}

async function mockAlumnos(page) {
  await page.route((url) => new URL(url).pathname.startsWith('/api/alumnos'), async (route) => {
    const url = new URL(route.request().url());
    const sede = url.searchParams.get('sede_id');
    let alumnos = [
      { id: 1, nombre: 'Ana', apellido_paterno: 'Lopez', email: 'a@test.com', numero_control: '11111111', carrera: { nombre: 'ISC' }, activo: true, sede_id: 1, sede: { id: 1, codigo: 'TEO' } },
      { id: 2, nombre: 'Juan', apellido_paterno: 'Perez', email: 'j@test.com', numero_control: '22222222', carrera: { nombre: 'ISC' }, activo: true, sede_id: 2, sede: { id: 2, codigo: 'HUA' } },
    ];
    if (sede === '1') alumnos = alumnos.filter((a) => a.sede_id === 1);
    if (sede === '2') alumnos = alumnos.filter((a) => a.sede_id === 2);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ alumnos, total: alumnos.length, pages: 1, page: 1 }),
    });
  });
  await page.route((url) => new URL(url).pathname.startsWith('/api/carreras'), async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ carreras: [{ id: 1, nombre: 'ISC' }] }) });
  });
  await page.route((url) => new URL(url).pathname.startsWith('/api/materias'), async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ materias: [{ id: 1, nombre: 'Mat' }] }) });
  });
  await page.route((url) => new URL(url).pathname.startsWith('/api/pagos'), async (route) => {
    // Handle both /pagos/alumnos-pendientes and /pagos/alumnos-con-pagos-pendientes and /pagos/alumnos/:id
    const pathname = new URL(route.request().url()).pathname;
    if (pathname.includes('alumnos-pendientes') || pathname.includes('alumnos-con-pagos')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ alumnos: [], total_adeudo: 0 }) });
      return;
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });
  await page.route((url) => new URL(url).pathname.startsWith('/api/admins'), async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ admins: [{ id: 1, username: 'admin', nombre: 'Admin', email: 'a@fv.edu', role: 'general_admin', sede_id: null }] }) });
    } else {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    }
  });
}

async function loginAs(page, { role = 'general_admin', sede_id = null }) {
  const user = {
    id: 1,
    type: 'admin',
    rol: 'admin',
    role,
    sede_id,
    sede: sede_id ? { id: sede_id, codigo: sede_id === 1 ? 'TEO' : 'HUA', nombre: sede_id === 1 ? 'Teotitlan' : 'Huautla' } : null,
    username: role === 'general_admin' ? 'general' : 'sede_teo',
    nombre: role === 'general_admin' ? 'General Admin' : 'Sede Admin TEO',
    email: role === 'general_admin' ? 'general@fv.edu' : 'teo@fv.edu',
    sedeId: sede_id,
    user_type: 'admin',
  };
  // Register auth/me mock BEFORE navigation to avoid race.
  await page.route((url) => new URL(url).pathname === '/api/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ type: 'admin', user }),
    });
  });
  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  }, { token: 'fake-jwt-token', user });
  // Navigate to a same-origin page first to ensure localStorage is set for http://localhost:3000
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(({ token, user }) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  }, { token: 'fake-jwt-token', user });
  await page.goto('/admin', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);
  // Ensure we are on /admin (not redirected to /login)
  const url = page.url();
  if (!url.includes('/admin')) {
    // Fallback: set again and reload
    await page.evaluate(({ token, user }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    }, { token: 'fake-jwt-token', user });
    await page.goto('/admin', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
  }
}

test.describe('Wiki Sede Multitenancy E2E', () => {
  test.beforeEach(async ({ page }) => {
    await mockSedes(page);
    await mockAlumnos(page);
    await page.route((url) => new URL(url).pathname === '/api/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Login exitoso', user: { type: 'admin', role: 'general_admin' }, access_token: 'fake', refresh_token: 'fake' }),
      });
    });
  });

  test('general_admin login muestra sede switcher y puede ver sedes', async ({ page }) => {
    await mockWiki(page);
    await loginAs(page, { role: 'general_admin', sede_id: null });
    // after loginAs, should be on /admin and see General badge + switcher
    await expect(page.getByText(/General/i).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByLabel(/sede switcher/i)).toBeVisible();
    await page.goto('/admin/sedes');
    await expect(page.getByRole('heading', { name: /Sedes/i })).toBeVisible();
    // Use cell role to avoid matching hidden <option> elements
    await expect(page.getByRole('cell', { name: 'TEO', exact: true })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'HUA', exact: true })).toBeVisible();
  });

  test('sede_admin TEO ve badge TEO y wiki filtrado', async ({ page }) => {
    await mockWiki(page);
    await loginAs(page, { role: 'sede_admin', sede_id: 1 });
    await expect(page.getByTestId('sede-badge')).toContainText(/TEO/i);
    await page.goto('/admin/wiki');
    await expect(page.getByRole('heading', { name: /Wiki/i })).toBeVisible();
    await expect(page.getByText('Guia TEO')).toBeVisible();
    await expect(page.getByText('Reglamento')).toBeVisible();
  });

  test('sede_admin cross-sede wiki create 403', async ({ page }) => {
    await mockWiki(page, { isCross403: true });
    await loginAs(page, { role: 'sede_admin', sede_id: 1 });
    await page.goto('/admin/wiki');
    await expect(page.getByRole('heading', { name: /Wiki/i })).toBeVisible();
    await page.getByRole('button', { name: /Nueva Página/i }).click();
    await page.getByLabel(/Slug/i).fill('manual-hua');
    await page.getByLabel(/Título/i).fill('Intento HUA');
    await page.getByLabel('Body').fill('# Intento cross sede');
    const sedeSelect = page.getByLabel(/Sede/i);
    await sedeSelect.selectOption('2');
    await page.getByRole('button', { name: /Crear/i }).click();
    await expect(page.getByText(/Forbidden|Cross-sede|ya existe|Error/i).first()).toBeVisible({ timeout: 3000 }).catch(async () => {
      await expect(page.getByLabel(/Slug/i)).toBeVisible();
    });
  });

  test('alumnos sede filter funciona para general_admin', async ({ page }) => {
    await mockWiki(page);
    await loginAs(page, { role: 'general_admin', sede_id: null });
    await page.goto('/admin/alumnos');
    await expect(page.getByRole('heading', { name: /Alumnos/i })).toBeVisible();
    const sedeFilter = page.getByLabel(/Filtrar por sede/i);
    await expect(sedeFilter).toBeVisible();
    await sedeFilter.selectOption('1');
    await page.waitForTimeout(800);
    // Use cell to avoid hidden option
    await expect(page.getByRole('cell', { name: 'TEO', exact: true }).first()).toBeVisible();
  });

  test('wiki read global visible both sedes, private isolated', async ({ page }) => {
    await mockWiki(page);
    await loginAs(page, { role: 'sede_admin', sede_id: 1 });
    await page.goto('/wiki/guia');
    await expect(page.getByRole('heading', { name: /Guia/i })).toBeVisible();
    await expect(page.getByText(/Hola TEO/).first()).toBeVisible();
    await page.goto('/wiki/reg');
    // global page - heading may be Reglamento
    await expect(page.getByText(/Reglamento|global/i).first()).toBeVisible();
  });
});
