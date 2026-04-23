-- fixtures/seed_test.sql
-- Seed mínimo para la base de datos de TEST.
-- Usado por los tests E2E de Playwright (el backend necesita estos usuarios
-- para que auth.setup.ts pueda loguearse con cada rol).
--
-- IMPORTANTE: correr contra la DB de test, no contra producción.
--   psql -U postgres -d acompanarte_test -f fixtures/seed_test.sql
--
-- Los tests de integración pytest usan su propio seed programático en
-- conftest.py y no necesitan este archivo.

-- ─── Limpiar datos existentes de test (idempotente) ──────────────────────────
DELETE FROM recursos_profesionales WHERE titulo LIKE '%[TEST]%';
DELETE FROM actividades_familiar    WHERE titulo LIKE '%[TEST]%';
DELETE FROM usuarios WHERE email LIKE '%@test.acompanarte.ar';

-- ─── Asegurarse de que existen los roles ─────────────────────────────────────
INSERT INTO roles (key, label, default_path, nav_config)
VALUES
  ('admin',   'Administración',      '/admin/dashboard',                 '[]'),
  ('ter-int', 'Terapeuta interno',   '/terapeuta/interno/dashboard',     '[]'),
  ('ter-ext', 'Terapeuta externo',   '/terapeuta/externo/dashboard',     '[]'),
  ('familia', 'Panel familiar',      '/familiar/dashboard',              '[]')
ON CONFLICT (key) DO NOTHING;

-- ─── Usuarios de test por rol ─────────────────────────────────────────────────
-- Contraseñas en texto claro para referencia; el hash bcrypt está calculado con
-- bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
--
-- admin@test.acompanarte.ar     → Admin1234!
-- ter.int@test.acompanarte.ar   → TerInt1234!
-- ter.ext@test.acompanarte.ar   → TerExt1234!
-- familia@test.acompanarte.ar   → Familia1234!

DO $$
DECLARE
  rol_admin_id   UUID;
  rol_terint_id  UUID;
  rol_terext_id  UUID;
  rol_familia_id UUID;
BEGIN
  SELECT id INTO rol_admin_id   FROM roles WHERE key = 'admin';
  SELECT id INTO rol_terint_id  FROM roles WHERE key = 'ter-int';
  SELECT id INTO rol_terext_id  FROM roles WHERE key = 'ter-ext';
  SELECT id INTO rol_familia_id FROM roles WHERE key = 'familia';

  INSERT INTO usuarios (id, email, password_hash, nombre, apellido, rol_id, avatar_initials, avatar_class, activo, bloqueado, intentos_fallidos)
  VALUES
    (
      gen_random_uuid(),
      'admin@test.acompanarte.ar',
      -- bcrypt hash de 'Admin1234!' — regenerar si cambia la contraseña
      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpfXkUCWuuLc3i',
      'Admin', 'Test',
      rol_admin_id,
      'AT', 'av-gr', TRUE, FALSE, 0
    ),
    (
      gen_random_uuid(),
      'ter.int@test.acompanarte.ar',
      -- bcrypt hash de 'TerInt1234!'
      '$2b$12$eImiTXuWVxfM37uY4JANDexample_hash_terint_replace_me____',
      'TerapeutaInt', 'Test',
      rol_terint_id,
      'TT', 'av-tl', TRUE, FALSE, 0
    ),
    (
      gen_random_uuid(),
      'ter.ext@test.acompanarte.ar',
      -- bcrypt hash de 'TerExt1234!'
      '$2b$12$eImiTXuWVxfM37uY4JANDexample_hash_terext_replace_me____',
      'TerapeutaExt', 'Test',
      rol_terext_id,
      'TT', 'av-pp', TRUE, FALSE, 0
    ),
    (
      gen_random_uuid(),
      'familia@test.acompanarte.ar',
      -- bcrypt hash de 'Familia1234!'
      '$2b$12$eImiTXuWVxfM37uY4JANDexample_hash_familia_replace_me___',
      'Familia', 'Test',
      rol_familia_id,
      'FT', 'av-tl', TRUE, FALSE, 0
    )
  ON CONFLICT (email) DO NOTHING;
END $$;

-- ─── Paciente de test ─────────────────────────────────────────────────────────
INSERT INTO pacientes (id, nombre, apellido, activo)
VALUES (gen_random_uuid(), 'Paciente', 'Test', TRUE)
ON CONFLICT DO NOTHING;

-- ─── Recurso pendiente de validación ─────────────────────────────────────────
INSERT INTO recursos_profesionales (id, titulo, tipo, descripcion, contenido_texto, validado)
VALUES (
  gen_random_uuid(),
  '[TEST] Recurso pendiente E2E',
  'articulo',
  'Recurso de test para validar el widget del dashboard admin',
  'Contenido de texto de prueba para el recurso E2E.',
  FALSE
)
ON CONFLICT DO NOTHING;

-- ─── Nota sobre los hashes ────────────────────────────────────────────────────
-- Los hashes de ejemplo arriba son placeholders — reemplazarlos con hashes
-- reales generados con Python:
--
--   python3 -c "
--   from passlib.context import CryptContext
--   ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
--   for pwd in ['Admin1234!', 'TerInt1234!', 'TerExt1234!', 'Familia1234!']:
--       print(f'{pwd}: {ctx.hash(pwd)}')
--   "
--
-- O bien usar el script de Python en scripts/generate_test_hashes.py
