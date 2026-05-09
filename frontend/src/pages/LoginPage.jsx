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

const IcoHeart = () => (
  <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth="2">
    <path strokeLinecap="round"
      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
  </svg>
)

const ROLES = [
  { key: 'familia',  icon: '👨‍👩‍👧', label: 'Familia' },
  { key: 'ter-int',  icon: '👩‍⚕️',  label: 'Ter. Interno' },
  { key: 'ter-ext',  icon: '🩺',    label: 'Ter. Externo' },
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
    const from = location.state?.from?.pathname
    navigate(from && from !== '/login' ? from : result.defaultPath ?? '/', { replace: true })
  }

  return (
    <div className="login-page">
      <div className="login-card">

        {/* ── Panel izquierdo ── */}
        <div className="login-left">
          <div className="login-left-brand">
            <div className="lico"><IcoHeart /></div>
            <div className="login-left-title">acompañarte</div>
            <div className="login-left-sub">
              Plataforma de acompañamiento<br />familiar · TEA
            </div>
          </div>

          <div className="login-assist-wrap">
            <div className="login-assist-label">Acceso público · sin cuenta</div>
            <button
              type="button"
              className="login-assist-btn"
              onClick={() => navigate('/asistente')}
            >
              <IcoBot />
              Consultar al Asistente TEA — sin registrarse
            </button>
          </div>
        </div>

        {/* ── Panel derecho — formulario ── */}
        <div className="login-right">
          <div className="login-right-title">Ingresá a tu cuenta</div>
          <div className="login-right-sub">Seleccioná tu perfil y completá tus datos</div>

          <form onSubmit={handleLogin} autoComplete="off" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {/* Traps autocomplete */}
            <input type="text"     style={{ display: 'none' }} aria-hidden="true" readOnly />
            <input type="password" style={{ display: 'none' }} aria-hidden="true" readOnly />

            {/* Selector de rol */}
            <div>
              <div className="fl mb8" style={{ fontSize: 12 }}>Ingresar como</div>
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
              <label className="fl" style={{ fontSize: 12 }}>Correo electrónico</label>
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
              <label className="fl" style={{ fontSize: 12 }}>Contraseña</label>
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
              style={{ padding: '10px', marginTop: 2 }}
              disabled={loading}
            >
              {loading ? 'Ingresando…' : 'Ingresar al sistema'}
            </button>

            {/* Onboarding */}
            <button
              type="button"
              className="btn btn-g btn-full"
              style={{ fontSize: 12 }}
              onClick={() => navigate('/onboarding')}
            >
              ¿Sin cuenta? Registrarse como familiar
            </button>

            {/* Nota de seguridad */}
            <div className="txs tm" style={{ textAlign: 'center', marginTop: 2 }}>
              Sistema protegido · TLS 1.3 · Datos cifrados AES-256
            </div>
          </form>
        </div>

      </div>
    </div>
  )
}
