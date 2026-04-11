-- ================================================================
-- acompañarte — Migración: roles + reestructura usuarios
-- Archivo: migrations/003_roles_y_usuarios.sql
--
-- QUÉ HACE:
--   1. Crea la tabla `roles` con su data inicial (4 roles)
--   2. Agrega columnas nuevas a `usuarios`:
--        rol_id, avatar_initials, avatar_class, profile_label
--   3. Migra los valores existentes de `rol` VARCHAR → `rol_id` FK
--   4. Elimina la columna `rol` ya obsoleta
--   5. Agrega índices necesarios
--
-- GARANTÍAS:
--   - Todas las operaciones en una sola transacción (ROLLBACK automático si algo falla)
--   - Datos existentes en `usuarios.rol` se migran, no se pierden
--   - Las demás tablas no se tocan
--
-- CÓMO EJECUTAR:
--   psql -U acompanarte_user -d acompanarte_db -f migrations/003_roles_y_usuarios.sql
-- ================================================================

BEGIN;

-- ────────────────────────────────────────────────────────────────
-- 1. CREAR TABLA roles
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key          VARCHAR(32)  NOT NULL UNIQUE,
    label        VARCHAR(100) NOT NULL,
    default_path VARCHAR(200) NOT NULL,
    nav_config   JSONB        NOT NULL DEFAULT '[]',
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  roles              IS 'Roles de acceso al sistema. Desacopla permisos del modelo usuario.';
COMMENT ON COLUMN roles.key          IS 'Clave técnica: familia | ter-int | ter-ext | admin';
COMMENT ON COLUMN roles.default_path IS 'Ruta React inicial tras el login';
COMMENT ON COLUMN roles.nav_config   IS 'Estructura del sidebar: [{section, items:[{id,icon,label,badge?}]}]';


-- ────────────────────────────────────────────────────────────────
-- 2. INSERTAR LOS 4 ROLES INICIALES
-- ────────────────────────────────────────────────────────────────
INSERT INTO roles (key, label, default_path, nav_config) VALUES

('familia',
 'Panel familiar',
 '/familiar/dashboard',
 '[
   {"section": "Principal", "items": [
     {"id": "dashboard",    "icon": "home",       "label": "Panel de inicio"},
     {"id": "seguimientos", "icon": "clipboard",  "label": "Seguimientos"},
     {"id": "actividades",  "icon": "target",     "label": "Actividades"}
   ]},
   {"section": "Herramientas", "items": [
     {"id": "asistente",    "icon": "bot",        "label": "Asistente IA"},
     {"id": "alertas",      "icon": "bell",       "label": "Alertas", "badge": 1}
   ]}
 ]'
),

('ter-int',
 'Terapeuta interno',
 '/terapeuta/interno/dashboard',
 '[
   {"section": "Principal", "items": [
     {"id": "ter-int-dash",        "icon": "home",      "label": "Panel de inicio"},
     {"id": "ter-int-registros",   "icon": "pencil",    "label": "Registros"},
     {"id": "ter-int-actividades", "icon": "clipboard", "label": "Actividades"}
   ]},
   {"section": "Herramientas", "items": [
     {"id": "ter-int-conocimiento", "icon": "book",  "label": "Base de conocimiento"},
     {"id": "alertas",              "icon": "bell",  "label": "Alertas", "badge": 2}
   ]}
 ]'
),

('ter-ext',
 'Terapeuta externo',
 '/terapeuta/externo/dashboard',
 '[
   {"section": "Principal", "items": [
     {"id": "ter-ext-dash",      "icon": "home",   "label": "Panel de inicio"},
     {"id": "ter-ext-registros", "icon": "pencil", "label": "Mis registros"}
   ]}
 ]'
),

('admin',
 'Administración',
 '/admin/dashboard',
 '[
   {"section": "Sistema", "items": [
     {"id": "admin-dash",      "icon": "home",       "label": "Panel de inicio"},
     {"id": "admin-usuarios",  "icon": "users",      "label": "Terapeutas"},
     {"id": "admin-auditoria", "icon": "bar-chart",  "label": "Auditoría"}
   ]}
 ]'
)

ON CONFLICT (key) DO NOTHING;  -- idempotente: si ya existen, no falla


-- ────────────────────────────────────────────────────────────────
-- 3. AGREGAR COLUMNAS NUEVAS A usuarios
-- ────────────────────────────────────────────────────────────────

-- 3a. FK a roles (inicialmente nullable para poder poblarla antes de
--     aplicar el constraint NOT NULL)
ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS rol_id        UUID        REFERENCES roles(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS avatar_initials VARCHAR(4) NULL,
    ADD COLUMN IF NOT EXISTS avatar_class    VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS profile_label   VARCHAR(200) NULL;

COMMENT ON COLUMN usuarios.rol_id          IS 'FK a roles.id — reemplaza la columna rol VARCHAR';
COMMENT ON COLUMN usuarios.avatar_initials IS 'Iniciales para el avatar: ML | AG | LR...';
COMMENT ON COLUMN usuarios.avatar_class    IS 'Clase CSS del avatar: av-tl | av-pp | av-gr...';
COMMENT ON COLUMN usuarios.profile_label   IS 'Texto descriptivo del perfil visible en la app';


-- ────────────────────────────────────────────────────────────────
-- 4. MIGRAR DATOS: usuarios.rol → usuarios.rol_id
-- Cubre los valores conocidos del ENUM anterior.
-- Cualquier valor no reconocido queda con rol_id = NULL
-- (visible en la verificación del paso siguiente).
-- ────────────────────────────────────────────────────────────────
UPDATE usuarios u
SET    rol_id = r.id
FROM   roles r
WHERE  r.key = u.rol           -- 'familia'
   AND u.rol = 'familia';

UPDATE usuarios u
SET    rol_id = r.id
FROM   roles r
WHERE  r.key = u.rol
   AND u.rol = 'ter-int';

UPDATE usuarios u
SET    rol_id = r.id
FROM   roles r
WHERE  r.key = u.rol
   AND u.rol = 'ter-ext';

UPDATE usuarios u
SET    rol_id = r.id
FROM   roles r
WHERE  r.key = u.rol
   AND u.rol = 'admin';


-- ────────────────────────────────────────────────────────────────
-- 4b. VERIFICACIÓN — aborta si quedaron filas sin migrar
-- ────────────────────────────────────────────────────────────────
DO $$
DECLARE
    sin_rol INTEGER;
BEGIN
    SELECT COUNT(*) INTO sin_rol
    FROM usuarios
    WHERE rol_id IS NULL;

    IF sin_rol > 0 THEN
        RAISE EXCEPTION
            'Migración abortada: % usuario(s) quedaron sin rol_id. '
            'Revisá los valores de la columna "rol" antes de continuar.',
            sin_rol;
    END IF;
END;
$$;


-- ────────────────────────────────────────────────────────────────
-- 5. HACER rol_id NOT NULL ahora que todos los registros están migrados
-- ────────────────────────────────────────────────────────────────
ALTER TABLE usuarios
    ALTER COLUMN rol_id SET NOT NULL;


-- ────────────────────────────────────────────────────────────────
-- 6. ELIMINAR LA COLUMNA rol OBSOLETA
-- ────────────────────────────────────────────────────────────────
ALTER TABLE usuarios
    DROP COLUMN IF EXISTS rol;


-- ────────────────────────────────────────────────────────────────
-- 7. ÍNDICES
-- ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_roles_key
    ON roles(key);

CREATE INDEX IF NOT EXISTS idx_roles_activo
    ON roles(activo)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_usuarios_rol_id
    ON usuarios(rol_id);

-- Índice compuesto: filtros frecuentes en el panel de admin
CREATE INDEX IF NOT EXISTS idx_usuarios_rol_activo
    ON usuarios(rol_id, activo);


-- ────────────────────────────────────────────────────────────────
-- 8. CONFIRMAR
-- ────────────────────────────────────────────────────────────────
COMMIT;

-- ────────────────────────────────────────────────────────────────
-- VERIFICACIÓN POST-MIGRACIÓN (ejecutar manualmente si querés confirmar)
-- ────────────────────────────────────────────────────────────────
-- SELECT r.key, COUNT(u.id) AS usuarios
-- FROM   roles r
-- LEFT   JOIN usuarios u ON u.rol_id = r.id
-- GROUP  BY r.key
-- ORDER  BY r.key;
