// playwright.config.ts
// Configuración central de Playwright para Acompañarte.
// Corre contra el frontend en http://localhost:5173 y el backend en :8000.
//
// Uso rápido:
//   npx playwright test                    # todos los specs
//   npx playwright test e2e/auth.spec.ts   # un spec
//   npx playwright test --ui               # modo interactivo
//   npx playwright show-report             # ver último reporte HTML

import { defineConfig, devices } from '@playwright/test';
import path from 'path';

// Carpeta donde Playwright guarda storageState por rol (cookies + localStorage)
export const STORAGE_DIR = path.join(__dirname, '.playwright-state');

// Archivos de estado de sesión reutilizables entre specs
export const AUTH_FILES = {
  admin:   path.join(STORAGE_DIR, 'admin.json'),
  terInt:  path.join(STORAGE_DIR, 'ter-int.json'),
  terExt:  path.join(STORAGE_DIR, 'ter-ext.json'),
  familia: path.join(STORAGE_DIR, 'familia.json'),
};

export default defineConfig({
  // ─── Dónde están los specs ───────────────────────────────────────────────
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',

  // ─── Timeouts ────────────────────────────────────────────────────────────
  timeout: 30_000,          // por test
  expect: { timeout: 5_000 },

  // ─── Ejecución ───────────────────────────────────────────────────────────
  fullyParallel: false,     // false: auth.spec.ts debe correr primero (genera state)
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // ─── Reporter ────────────────────────────────────────────────────────────
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  // ─── Configuración base compartida por todos los proyectos ───────────────
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
  },

  // ─── Proyectos: navegadores / dispositivos ───────────────────────────────
  projects: [
    // 1) Proyecto especial: genera los storageState para todos los roles.
    //    Corre SIEMPRE antes que el resto (no tiene dependencias).
    {
      name: 'setup',
      testMatch: '**/auth.setup.ts',
    },

    // 2) Specs E2E reales — dependen del setup anterior.
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
  ],

  // ─── Servidores opcionales (descomentá si querés arranque automático) ─────
  // webServer: [
  //   {
  //     command: 'cd frontend && npm run dev',
  //     url: 'http://localhost:5173',
  //     reuseExistingServer: !process.env.CI,
  //   },
  //   {
  //     command: 'cd backend && uvicorn app.main:app --reload --port 8000',
  //     url: 'http://localhost:8000/health',
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
});
