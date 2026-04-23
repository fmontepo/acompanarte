// tests/e2e/auth.setup.ts
// Proyecto "setup" de Playwright: loguea cada rol UNA VEZ y guarda el
// storageState (token en localStorage). Los demás specs reutilizan esos
// archivos para evitar repetir el login en cada test.
//
// Playwright corre este archivo antes que cualquier spec del proyecto
// "chromium" (ver playwright.config.ts → dependencies: ['setup']).

import { test as setup, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { AUTH_FILES, STORAGE_DIR } from '../../playwright.config';

// ─── Credenciales de test ────────────────────────────────────────────────────
// Deben existir en la base de datos de test (ver fixtures/seed_test.sql).
// Sobreescribibles via variables de entorno para CI.
const USUARIOS_TEST = {
  admin: {
    email:    process.env.TEST_ADMIN_EMAIL    ?? 'admin@test.acompanarte.ar',
    password: process.env.TEST_ADMIN_PASS     ?? 'Admin1234!',
    rolKey:   'admin',
    redirect: '/admin/dashboard',
  },
  terInt: {
    email:    process.env.TEST_TER_INT_EMAIL  ?? 'ter.int@test.acompanarte.ar',
    password: process.env.TEST_TER_INT_PASS   ?? 'TerInt1234!',
    rolKey:   'ter-int',
    redirect: '/terapeuta/interno/dashboard',
  },
  terExt: {
    email:    process.env.TEST_TER_EXT_EMAIL  ?? 'ter.ext@test.acompanarte.ar',
    password: process.env.TEST_TER_EXT_PASS   ?? 'TerExt1234!',
    rolKey:   'ter-ext',
    redirect: '/terapeuta/externo/dashboard',
  },
  familia: {
    email:    process.env.TEST_FAMILIA_EMAIL  ?? 'familia@test.acompanarte.ar',
    password: process.env.TEST_FAMILIA_PASS   ?? 'Familia1234!',
    rolKey:   'familia',
    redirect: '/familiar/dashboard',
  },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function loginAndSave(page: any, creds: typeof USUARIOS_TEST[keyof typeof USUARIOS_TEST], storageFile: string) {
  await page.goto('/login');

  // Esperar que el form esté listo
  await page.waitForSelector('input[type="email"], input[name="email"], input[name="username"]');

  // Completar credenciales
  const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]').first();
  const passInput  = page.locator('input[type="password"]').first();

  await emailInput.fill(creds.email);
  await passInput.fill(creds.password);
  await passInput.press('Enter');

  // Verificar redirect al default_path del rol
  await page.waitForURL(`**${creds.redirect}`, { timeout: 10_000 });

  // Guardar estado de sesión
  fs.mkdirSync(STORAGE_DIR, { recursive: true });
  await page.context().storageState({ path: storageFile });
}

// ─── Tests de setup ───────────────────────────────────────────────────────────

setup('login: admin', async ({ page }) => {
  await loginAndSave(page, USUARIOS_TEST.admin, AUTH_FILES.admin);
});

setup('login: terapeuta interno', async ({ page }) => {
  await loginAndSave(page, USUARIOS_TEST.terInt, AUTH_FILES.terInt);
});

setup('login: terapeuta externo', async ({ page }) => {
  await loginAndSave(page, USUARIOS_TEST.terExt, AUTH_FILES.terExt);
});

setup('login: familia', async ({ page }) => {
  await loginAndSave(page, USUARIOS_TEST.familia, AUTH_FILES.familia);
});
