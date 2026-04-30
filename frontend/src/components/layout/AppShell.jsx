import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Iconos SVG inline — sin dependencia externa ──────────────────
const ICONS = {
  home: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
    </svg>
  ),
  clipboard: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
    </svg>
  ),
  target: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/>
      <circle cx="12" cy="12" r="2"/>
    </svg>
  ),
  bot: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="10" rx="2"/>
      <path strokeLinecap="round" d="M12 11V7m-4 4V9a4 4 0 018 0v2"/>
      <circle cx="9" cy="16" r="1" fill="currentColor"/>
      <circle cx="15" cy="16" r="1" fill="currentColor"/>
    </svg>
  ),
  bell: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round"
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
    </svg>
  ),
  pencil: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
    </svg>
  ),
  book: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
    </svg>
  ),
  users: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round"
        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
    </svg>
  ),
  'bar-chart': (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
    </svg>
  ),
  mail: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
  ),
  shield: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
    </svg>
  ),
}

// Mapeo de screen id → ruta React Router
const SCREEN_TO_PATH = {
  // familia
  'dashboard':              '/familiar/dashboard',
  'seguimientos':           '/familiar/seguimientos',
  'actividades':            '/familiar/actividades',
  'asistente':              '/familiar/asistente',
  'alertas':                '/familiar/alertas',
  // ter-int
  'ter-int-dash':           '/terapeuta/interno/dashboard',
  'ter-int-registros':      '/terapeuta/interno/registros',
  'ter-int-actividades':    '/terapeuta/interno/actividades',
  'ter-int-asistente':      '/terapeuta/interno/asistente',
  'ter-int-conocimiento':   '/terapeuta/interno/conocimiento',
  // ter-ext
  'ter-ext-dash':           '/terapeuta/externo/dashboard',
  'ter-ext-registros':      '/terapeuta/externo/registros',
  // admin
  'admin-dash':             '/admin/dashboard',
  'admin-usuarios':         '/admin/usuarios',
  'admin-contactos':        '/admin/contactos',
  'admin-reglas':           '/admin/reglas-ia',
  'admin-auditoria':        '/admin/auditoria',
}

// Ruta compartida entre roles
function resolveAlertPath(rolKey) {
  const map = {
    familia:   '/familiar/alertas',
    'ter-int': '/terapeuta/interno/alertas',
  }
  return map[rolKey] ?? '/familiar/alertas'
}

export default function AppShell() {
  const { user, logout, authFetch } = useAuth()
  const navigate  = useNavigate()
  const location  = useLocation()
  const [openModal, setOpenModal] = useState(null) // 'perfil'
  const [alertBadge, setAlertBadge] = useState(0)

  // Carga el conteo real de alertas para mostrar en el badge del sidebar
  useEffect(() => {
    if (!user) return
    const rolesConAlertas = ['ter-int', 'familia']
    if (!rolesConAlertas.includes(user.rol_key)) return

    authFetch('/api/v1/alertas/?solo_pendientes=true&limit=50')
      .then(res => res.ok ? res.json() : [])
      .then(data => setAlertBadge(Array.isArray(data) ? data.length : 0))
      .catch(() => setAlertBadge(0))
  }, [user, authFetch])

  if (!user) return null

  // ── Fecha actual ────────────────────────────────────────────────
  const fecha = new Date().toLocaleDateString('es-AR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })

  // ── Título del topbar según ruta activa ─────────────────────────
  function getTitleFromPath() {
    const path = location.pathname
    const allItems = user.nav_config.flatMap(s => s.items)
    const current = allItems.find(item => {
      const itemPath = item.id === 'alertas'
        ? resolveAlertPath(user.rol_key)
        : SCREEN_TO_PATH[item.id]
      return itemPath && path.startsWith(itemPath)
    })
    return current?.label ?? 'Panel'
  }

  // ── Navegar desde el sidebar ────────────────────────────────────
  function handleNav(itemId) {
    const path = itemId === 'alertas'
      ? resolveAlertPath(user.rol_key)
      : SCREEN_TO_PATH[itemId]
    if (path) navigate(path)
  }

  // ── ¿Item activo? ───────────────────────────────────────────────
  function isActive(itemId) {
    const path = itemId === 'alertas'
      ? resolveAlertPath(user.rol_key)
      : SCREEN_TO_PATH[itemId]
    return path ? location.pathname.startsWith(path) : false
  }

  // ── ¿Hay alertas? (dot rojo en el bell) ────────────────────────
  const hasAlerts = alertBadge > 0

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">

      {/* ── SIDEBAR ─────────────────────────────────────────────── */}
      <aside className="sidebar">

        {/* Logo */}
        <div className="sb-logo">
          <div className="logo-row">
            <div className="logo-ico">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"
                stroke="white" strokeWidth="2.5">
                <path strokeLinecap="round"
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
            </div>
            <div>
              <div className="logo-tx">acompañarte</div>
              {/* label viene de la tabla roles vía el backend */}
              <div className="logo-su">{user.label}</div>
            </div>
          </div>
        </div>

        {/* Navegación — construida 100% desde user.nav_config */}
        <nav className="sb-nav">
          {user.nav_config.map(section => (
            <div key={section.section} className="nav-sec">
              <div className="nav-lbl">{section.section}</div>
              {section.items.map(item => (
                <div
                  key={item.id}
                  className={`nav-it${isActive(item.id) ? ' on' : ''}`}
                  onClick={() => handleNav(item.id)}
                >
                  <span className="ico" style={{ fontSize: 16 }}>
                    {ICONS[item.icon] ?? item.icon}
                  </span>
                  {item.label}
                  {item.id === 'alertas' && alertBadge > 0 && (
                    <span className="nbadge">{alertBadge}</span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </nav>

        {/* Usuario */}
        <div className="sb-user" onClick={() => setOpenModal('perfil')}>
          <div className={`av ${user.avatar_class ?? 'av-tl'}`}>
            {user.avatar_initials ?? '?'}
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>
              {[user.nombre, user.apellido].filter(Boolean).join(' ') || user.email}
            </div>
            <div className="txs tm">{user.profile_label ?? user.label}</div>
          </div>
        </div>

      </aside>

      {/* ── COLUMNA PRINCIPAL ────────────────────────────────────── */}
      <div className="main-col">

        {/* Topbar */}
        <div className="topbar">
          <div>
            <div className="tb-title">{getTitleFromPath()}</div>
            <div className="tb-sub">{fecha}</div>
          </div>
          <div className="flex ic g8">
            {/* Campana de alertas */}
            {hasAlerts && (
              <div
                className="notif"
                onClick={() => handleNav('alertas')}
                title="Alertas"
              >
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24"
                  stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round"
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
                </svg>
                <div className="ndot" />
              </div>
            )}
            <button className="btn btn-s btn-sm" onClick={handleLogout}>
              Salir
            </button>
          </div>
        </div>

        {/* Contenido — cada página hija se renderiza acá */}
        <div className="content">
          <Outlet />
        </div>

      </div>

      {/* ── MODAL PERFIL ─────────────────────────────────────────── */}
      {openModal === 'perfil' && (
        <div className="ov open" onClick={e => e.target === e.currentTarget && setOpenModal(null)}>
          <div className="mo">
            <div className="mh">
              <div className="mt">Mi perfil</div>
              <button className="btn btn-g btn-ico btn-sm"
                onClick={() => setOpenModal(null)}>✕</button>
            </div>
            <div className="mb">
              <div style={{ textAlign: 'center', marginBottom: 4 }}>
                <div className={`av av-lg ${user.avatar_class ?? 'av-tl'}`}
                  style={{ margin: '0 auto 10px' }}>
                  {user.avatar_initials ?? '?'}
                </div>
                <div style={{ fontSize: 16, fontWeight: 600 }}>
                  {[user.nombre, user.apellido].filter(Boolean).join(' ') || user.email}
                </div>
                <div className="ts tm">{user.profile_label ?? user.label}</div>
              </div>
              <div className="divider" />
              <div className="fg">
                <label className="fl">Correo electrónico</label>
                <input className="fi" value={user.email} readOnly />
              </div>
              <div className="disc disc-tl txs">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                  <path strokeLinecap="round"
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                Rol: {user.label}
              </div>
            </div>
            <div className="mf">
              <button className="btn btn-s" onClick={() => setOpenModal(null)}>
                Cerrar
              </button>
              <button className="btn btn-rd btn-sm" onClick={handleLogout}>
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
