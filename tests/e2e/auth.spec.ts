// tests/e2e/auth.spec.ts
// Casos cubiertos:
//   CU-PUB-01 — Login con credenciales válidas y redirect al default_path del rol
//   CU-PUB-02 — Credenciales inválidas: error visible, sin redirect
//   CU-PUB-05 — Acceso a ruta protegida sin sesión → redirect a /login (con from)
//   CU-PUB-06 — Acceso a ruta de otro rol → redirect a /404
//
// Este spec corre DESPUÉS de auth.setup.ts (que generó los storageState).
// Para CU-PUB-01 volvemos a loguear en el browser sin storageState previo
// para verificar el flujo completo desde cero.

import { test, expect, type BrowserContext, type Page } from '@playwright/test';
import { AUTH_FILES } from '../../playwright.config';

// ─────────────────────────────────────────────────────────────────────────────
// CU-PUB-01 — Login con credenciales válidas, redirect por rol
// ─────────────────────────────────────────────────────────────────────────────
test.describe('CU-PUB-01 · Login y redirect por rol', () => {
  // Credenciales y destino esperado por rol
  const casos = [
    { rol: 'admin',   email: process.env.TEST_ADMIN_EMAIL   ?? 'admin@test.acompanarte.ar',   pass: process.env.TEST_ADMIN_PASS   ?? 'Admin1234!',   destino: '/admin/dashboard' },
    { rol: 'ter-int', email: process.env.TEST_TER_INT_EMAIL ?? 'ter.int@test.acompanarte.ar', pass: process.env.TEST_TER_INT_PASS ?? 'TerInt1234!',  destino: '/terapeuta/interno/dashboard' },
    { rol: 'ter-ext', email: process.env.TEST_TER_EXT_EMAIL ?? 'ter.ext@test.acompanarte.ar', pass: process.env.TEST_TER_EXT_PASS ?? 'TerExt1234!',  destino: '/terapeuta/externo/dashboard' },
    { rol: 'familia', email: process.env.TEST_FAMILIA_EMAIL ?? 'familia@test.acompanarte.ar', pass: process.env.TEST_FAMILIA_PASS ?? 'Familia1234!', destino: '/familiar/dashboard' },
  ];

  for (const c of casos) {
    test(`rol: ${c.rol} → ${c.destino}`, async ({ page }) => {
      await page.goto('/login');

      // Completar form
      await page.locator('input[type="email"], input[name="email"], input[name="username"]').first().fill(c.email);
      await page.locator('input[type="password"]').first().fill(c.pass);
      await page.locator('input[type="password"]').first().press('Enter');

      // Verificar destino correcto según rol
      await expect(page).toHaveURL(new RegExp(c.destino), { timeout: 10_000 });

      // El dashboard debe renderizar algo útil (no spinner infinito ni 404)
      await expect(page.locator('body')).not.toContainText('404', { timeout: 5_000 });
    });
  }

  test('ya autenticado: /login redirige a default_path', async ({ browser }) => {
    // Usar storageState del admin (ya logueado)
    const ctx = await browser.newContext({ storageState: AUTH_FILES.admin });
    const page = await ctx.newPage();

    await page.goto('/login');

    // PublicRoute debe redirigir al default_path si ya hay sesión
    await expect(page).toHaveURL(/\/admin\/dashboard/, { timeout: 8_000 });
    await ctx.close();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// CU-PUB-02 — Credenciales inválidas
// ─────────────────────────────────────────────────────────────────────────────
test.describe('CU-PUB-02 · Credenciales inválidas', () => {
  test('email inexistente → mensaje de error, sin redirect', async ({ page }) => {
    await page.goto('/login');

    await page.locator('input[type="email"], input[name="email"], input[name="username"]').first().fill('noexiste@test.ar');
    await page.locator('input[type="password"]').first().fill('ContrasenaInvalida!');
    await page.locator('input[type="password"]').first().press('Enter');

    // Debe permanecer en /login
    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 });

    // Debe mostrar algún mensaje de error
    const errorTexts = ['incorrectos', 'inválido', 'error', 'invalid', 'wrong'];
    const bodyText = (await page.locator('body').textContent() ?? '').toLowerCase();
    const hayError = errorTexts.some(t => bodyText.includes(t));
    expect(hayError, 'Se esperaba un mensaje de error en pantalla').toBe(true);
  });

  test('contraseña incorrecta → sin redirect', async ({ page }) => {
    await page.goto('/login');

    // Email existente pero password mal
    await page.locator('input[type="email"], input[name="email"], input[name="username"]').first()
      .fill(process.env.TEST_ADMIN_EMAIL ?? 'admin@test.acompanarte.ar');
    await page.locator('input[type="password"]').first().fill('ContrasenaErronea999!');
    await page.locator('input[type="password"]').first().press('Enter');

    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// CU-PUB-05 — Ruta protegida sin sesión → redirect /login con ?from
// ─────────────────────────────────────────────────────────────────────────────
test.describe('CU-PUB-05 · Sin sesión → redirect a login', () => {
  const rutasProtegidas = [
    '/admin/dashboard',
    '/terapeuta/interno/dashboard',
    '/terapeuta/externo/dashboard',
    '/familiar/dashboard',
    '/admin/usuarios',
  ];

  for (const ruta of rutasProtegidas) {
    test(`${ruta} sin auth → /login`, async ({ page }) => {
      // Acceder sin storageState (contexto limpio, sin token)
      await page.goto(ruta);
      await expect(page).toHaveURL(/\/login/, { timeout: 6_000 });
    });
  }

  test('login guarda la ruta intentada (state.from)', async ({ page }) => {
    // Navegar directo al dashboard del admin sin sesión
    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/login/, { timeout: 6_000 });

    // Loguear como admin
    await page.locator('input[type="email"], input[name="email"], input[name="username"]').first()
      .fill(process.env.TEST_ADMIN_EMAIL ?? 'admin@test.acompanarte.ar');
    await page.locator('input[type="password"]').first()
      .fill(process.env.TEST_ADMIN_PASS ?? 'Admin1234!');
    await page.locator('input[type="password"]').first().press('Enter');

    // Tras login, debe volver a /admin/dashboard (o al menos al área admin)
    await expect(page).toHaveURL(/\/admin/, { timeout: 10_000 });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// CU-PUB-06 — Rol incorrecto → /404
// ─────────────────────────────────────────────────────────────────────────────
test.describe('CU-PUB-06 · Rol incorrecto → /404', () => {
  test('familiar intenta acceder a /admin/dashboard → 404', async ({ browser }) => {
    const ctx = await browser.newContext({ storageState: AUTH_FILES.familia });
    const page = await ctx.newPage();

    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/404/, { timeout: 6_000 });
    await ctx.close();
  });

  test('ter-ext intenta acceder a /admin/usuarios → 404', async ({ browser }) => {
    const ctx = await browser.newContext({ storageState: AUTH_FILES.terExt });
    const page = await ctx.newPage();

    await page.goto('/admin/usuarios');
    await expect(page).toHaveURL(/\/404/, { timeout: 6_000 });
    await ctx.close();
  });

  test('ter-int intenta acceder a /familiar/dashboard → 404', async ({ browser }) => {
    const ctx = await browser.newContext({ storageState: AUTH_FILES.terInt });
    const page = await ctx.newPage();

    await page.goto('/familiar/dashboard');
    await expect(page).toHaveURL(/\/404/, { timeout: 6_000 });
    await ctx.close();
  });
});
