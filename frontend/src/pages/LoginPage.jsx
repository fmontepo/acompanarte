import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const IcoBot = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <path strokeLinecap="round" d="M12 11V7m-4 4V9a4 4 0 018 0v2"/>
    <circle cx="9" cy="16" r="1" fill="currentColor"/>
    <circle cx="15" cy="16" r="1" fill="currentColor"/>
  </svg>
)

// ─── Roles disponibles para seleccionar ───────────────────────────
const ROLES = [
  { key: 'familia',  icon: '👨‍👩‍👧', label: 'Familia' },
  { key: 'ter-int',  icon: '👩‍⚕️',  label: 'Terapeuta Interno' },
  { key: 'ter-ext',  icon: '🩺',    label: 'Terapeuta Externo' },
  { key: 'admin',    icon: '🔐',    label: 'Admin' },
]


export default function LoginPage() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const location  = useLocation()

  const [selectedRole, setSelectedRole] = useState('familia')
  const [email,        setEmail]        = useState('')
  const [password,     setPassword]     = useState('')
  const [error,        setError]        = useState('')
  const [loading,      setLoading]      = useState(false)
  const [showPass,     setShowPass]     = useState(false)

  // Cambio de rol → limpia campos y error
  function handleRoleSelect(key) {
    setSelectedRole(key)
    setEmail('')
    setPassword('')
    setError('')
  }

  async function handleLogin(e) {
    e.preventDefault()
    if (!email || !password) {
      setError('Completá el correo y la contraseña.')
      return
    }
    setError('')
    setLoading(true)

    const result = await login(email, password)
    setLoading(false)

    if (!result.ok) {
      setError(result.error)
      return
    }

    // Redirigir a la ruta que intentaba acceder, o al default_path del rol
    const from = location.state?.from?.pathname
    navigate(from && from !== '/login' ? from : result.defaultPath ?? '/', { replace: true })
  }

  function handleOnboarding() {
    navigate('/onboarding')
  }

  return (
    <div className="login-page">
      <div className="login-card">

        {/* Logo */}
        <div className="login-logo">
          <div className="lico">
            <svg width="26" height="26" fill="none" viewBox="0 0 24 24"
              stroke="white" strokeWidth="2">
              <path strokeLinecap="round"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
            acompañarte
          </h1>
          <div className="txs tm">
            Plataforma de acompañamiento familiar · TEA
          </div>
        </div>

        <form onSubmit={handleLogin} autoComplete="off" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Inputs trampa: engañan al navegador para que no rellene los campos reales */}
          <input type="text"     style={{ display: 'none' }} aria-hidden="true" readOnly />
          <input type="password" style={{ display: 'none' }} aria-hidden="true" readOnly />

          {/* Selector de rol */}
          <div>
            <div className="fl mb8">Ingresar como</div>
            <div className="role-sel">
              {ROLES.map(r => (
                <div
                  key={r.key}
                  className={`rbtn${selectedRole === r.key ? ' sel' : ''}`}
                  onClick={() => handleRoleSelect(r.key)}
                >
                  <span className="ric">{r.icon}</span>
                  {r.label}
                </div>
              ))}
            </div>
          </div>

          {/* Email */}
          <div className="fg">
            <label className="fl">Correo electrónico</label>
            <input
              className="fi"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="tu@correo.com"
              autoComplete="off"
              required
            />
          </div>

          {/* Contraseña */}
          <div className="fg">
            <label className="fl">Contraseña</label>
            <div style={{ position: 'relative' }}>
              <input
                className="fi"
                type={showPass ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
                required
                style={{ paddingRight: 40 }}
              />
              <button
                type="button"
                onClick={() => setShowPass(v => !v)}
                style={{
                  position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text3)', padding: 2, lineHeight: 1,
                }}
                tabIndex={-1}
                aria-label={showPass ? 'Ocultar contraseña' : 'Ver contraseña'}
              >
                {showPass ? (
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path strokeLinecap="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="disc disc-rd txs">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 8v4m0 4h.01"/>
              </svg>
              {error}
            </div>
          )}

          {/* Botón login */}
          <button
            type="submit"
            className="btn btn-p btn-full"
            style={{ padding: '10px', marginTop: 4 }}
            disabled={loading}
          >
            {loading ? 'Ingresando…' : 'Ingresar al sistema'}
          </button>

          {/* Onboarding */}
          <button
            type="button"
            className="btn btn-g btn-full"
            style={{ fontSize: 12 }}
            onClick={handleOnboarding}
          >
            ¿Sin cuenta? Registrarse como familiar
          </button>

          {/* Nota de seguridad */}
          <div className="txs tm" style={{ textAlign: 'center' }}>
            Sistema protegido · TLS 1.3 · Datos cifrados AES-256
          </div>

          {/* Separador — acceso al Asistente público */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14, marginTop: 2 }}>
            <div className="txs" style={{ color: 'var(--text2)', textAlign: 'center', marginBottom: 8 }}>
              ¿Tenés dudas sobre el desarrollo de tu hijo?
            </div>
            <button
              type="button"
              className="btn btn-full"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
                background: 'var(--teal)', color: '#fff', fontWeight: 600,
                border: 'none', padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
              }}
              onClick={() => navigate('/asistente')}
            >
              <IcoBot />
              Consultar al Asistente TEA — sin registrarse
            </button>
          </div>

        </form>
      </div>
    </div>
  )
}
