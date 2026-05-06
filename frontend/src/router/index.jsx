import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Layout principal
import AppShell from '../components/layout/AppShell'

// Familia
import FamDashboard    from '../pages/familiar/Dashboard'
import FamMisParientes from '../pages/familiar/MisParientes'
import FamSeguimientos from '../pages/familiar/Seguimientos'
import FamActividades  from '../pages/familiar/Actividades'
import FamAsistente    from '../pages/familiar/Asistente'
import FamAlertas      from '../pages/familiar/Alertas'

// Terapeuta interno
import TerIntDash         from '../pages/terapeuta/interno/Dashboard'
import TerIntRegistros    from '../pages/terapeuta/interno/Registros'
import TerIntActividades  from '../pages/terapeuta/interno/Actividades'
import TerIntConocimiento from '../pages/terapeuta/interno/Conocimiento'
import TerIntAlertas      from '../pages/terapeuta/interno/Alertas'
import TerIntAsistente    from '../pages/terapeuta/interno/Asistente'
import TerIntPacientes    from '../pages/terapeuta/interno/Pacientes'

// Terapeuta externo
import TerExtDash      from '../pages/terapeuta/externo/Dashboard'
import TerExtRegistros from '../pages/terapeuta/externo/Registros'

// Admin
import AdminDash            from '../pages/admin/Dashboard'
import AdminUsuarios        from '../pages/admin/Usuarios'
import AdminAuditoria       from '../pages/admin/Auditoria'
import AdminContactos       from '../pages/admin/ContactosPublicos'
import AdminReglasIA        from '../pages/admin/ReglasIA'

// Auth y errores
import LoginPage        from '../pages/LoginPage'
import OnboardingPage   from '../pages/OnboardingPage'
import NotFound         from '../pages/NotFound'
import AsistentePublico from '../pages/AsistentePublico'

// ─────────────────────────────────────────────────────────────
// ProtectedRoute
// Verifica: 1) sesión activa  2) rol permitido (si se especifica)
// ─────────────────────────────────────────────────────────────
function ProtectedRoute({ allowedRoles }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  // Esperar a que AuthContext termine de validar el token almacenado
  if (isLoading) return null

  if (!user) {
    // Sin sesión → al login, guardando la ruta intentada para redirect post-login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.rol_key)) {
    // Sesión válida pero rol incorrecto → 404
    return <Navigate to="/404" replace />
  }

  return <Outlet />
}

// ─────────────────────────────────────────────────────────────
// PublicRoute
// Si ya hay sesión, redirige a user.default_path (viene del backend).
// Ya no hay ningún mapeo de roles en el frontend.
// ─────────────────────────────────────────────────────────────
function PublicRoute() {
  const { user, isLoading } = useAuth()

  // Esperar a que AuthContext termine de validar el token almacenado
  if (isLoading) return null

  if (user) {
    // default_path viene directamente del backend vía el JWT/login response
    // Ej: '/familiar/dashboard' | '/terapeuta/interno/dashboard' | '/admin/dashboard'
    return <Navigate to={user.default_path} replace />
  }

  return <Outlet />
}

// ─────────────────────────────────────────────────────────────
// AppRouter — árbol de rutas completo
// ─────────────────────────────────────────────────────────────
export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Raíz → login */}
        <Route index element={<Navigate to="/login" replace />} />

        {/* ── Asistente TEA público — sin auth, sin AppShell ── */}
        {/* Accesible para cualquier persona, incluso sin cuenta */}
        <Route path="/asistente" element={<AsistentePublico />} />

        {/* ── Rutas públicas (redirigen si ya hay sesión) ── */}
        <Route element={<PublicRoute />}>
          <Route path="/login"      element={<LoginPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
        </Route>

        {/* ── Familiar ── */}
        <Route element={<ProtectedRoute allowedRoles={['familia']} />}>
          <Route path="/familiar" element={<AppShell />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard"      element={<FamDashboard />} />
            <Route path="mis-parientes" element={<FamMisParientes />} />
            <Route path="seguimientos"  element={<FamSeguimientos />} />
            <Route path="actividades"  element={<FamActividades />} />
            <Route path="asistente"    element={<FamAsistente />} />
            <Route path="alertas"      element={<FamAlertas />} />
          </Route>
        </Route>

        {/* ── Terapeuta interno ── */}
        <Route element={<ProtectedRoute allowedRoles={['ter-int']} />}>
          <Route path="/terapeuta/interno" element={<AppShell />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard"    element={<TerIntDash />} />
            <Route path="pacientes"    element={<TerIntPacientes />} />
            <Route path="registros"    element={<TerIntRegistros />} />
            <Route path="actividades"  element={<TerIntActividades />} />
            <Route path="asistente"    element={<TerIntAsistente />} />
            <Route path="conocimiento" element={<TerIntConocimiento />} />
            <Route path="alertas"      element={<TerIntAlertas />} />
          </Route>
        </Route>

        {/* ── Terapeuta externo ── */}
        <Route element={<ProtectedRoute allowedRoles={['ter-ext']} />}>
          <Route path="/terapeuta/externo" element={<AppShell />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<TerExtDash />} />
            <Route path="registros" element={<TerExtRegistros />} />
          </Route>
        </Route>

        {/* ── Admin ── */}
        <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
          <Route path="/admin" element={<AppShell />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard"  element={<AdminDash />} />
            <Route path="usuarios"   element={<AdminUsuarios />} />
            <Route path="contactos"  element={<AdminContactos />} />
            <Route path="reglas-ia"  element={<AdminReglasIA />} />
            <Route path="auditoria"  element={<AdminAuditoria />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="/404" element={<NotFound />} />
        <Route path="*"    element={<Navigate to="/404" replace />} />

      </Routes>
    </BrowserRouter>
  )
}
