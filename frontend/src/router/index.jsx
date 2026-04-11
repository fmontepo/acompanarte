import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Layout principal
import AppShell from '../components/layout/AppShell'

// Familia
import FamDashboard    from '../pages/familiar/Dashboard'
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

// Terapeuta externo
import TerExtDash      from '../pages/terapeuta/externo/Dashboard'
import TerExtRegistros from '../pages/terapeuta/externo/Registros'

// Admin
import AdminDash      from '../pages/admin/Dashboard'
import AdminUsuarios  from '../pages/admin/Usuarios'
import AdminAuditoria from '../pages/admin/Auditoria'

// Auth y errores
import LoginPage      from '../pages/LoginPage'
import OnboardingPage from '../pages/OnboardingPage'
import NotFound       from '../pages/NotFound'

// ─────────────────────────────────────────────────────────────
// ProtectedRoute
// Verifica: 1) sesión activa  2) rol permitido (si se especifica)
// ─────────────────────────────────────────────────────────────
function ProtectedRoute({ allowedRoles }) {
  const { user } = useAuth()
  const location = useLocation()

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
  const { user } = useAuth()

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

        {/* ── Rutas públicas ── */}
        <Route element={<PublicRoute />}>
          <Route path="/login"      element={<LoginPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
        </Route>

        {/* ── Familiar ── */}
        <Route element={<ProtectedRoute allowedRoles={['familia']} />}>
          <Route path="/familiar" element={<AppShell />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard"    element={<FamDashboard />} />
            <Route path="seguimientos" element={<FamSeguimientos />} />
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
            <Route path="registros"    element={<TerIntRegistros />} />
            <Route path="actividades"  element={<TerIntActividades />} />
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
