import { createContext, useContext, useState, useCallback, useEffect } from 'react'

// ─────────────────────────────────────────────────────────────
// AuthContext — estado global de sesión
//
// CAMBIO RESPECTO A LA VERSIÓN ANTERIOR:
//   - Se eliminó el objeto ROLES hardcodeado
//   - login() ahora hace fetch a POST /api/v1/auth/login
//   - El backend devuelve { access_token, user } donde user incluye:
//       { id, email, nombre, rol_key, label, default_path,
//         nav_config, avatar_initials, avatar_class, profile_label }
//   - El frontend ya no necesita saber nada sobre roles:
//     sólo renderiza lo que el backend le da
// ─────────────────────────────────────────────────────────────

const AuthContext = createContext(null)

// URL base de la API — leer de variable de entorno Vite
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function AuthProvider({ children }) {
  // user: null cuando no hay sesión
  // user: objeto con todo lo que devolvió el backend cuando sí hay sesión
  const [user, setUser]       = useState(null)
  const [token, setToken]     = useState(null)
  // isLoading: true mientras validamos el token almacenado al inicio.
  // El router no debe tomar decisiones de redirect hasta que sea false.
  const [isLoading, setIsLoading] = useState(true)

  // ── Validar sesión almacenada al montar ─────────────────────
  // Si hay un token en localStorage lo verificamos contra /auth/me.
  // Si el token expiró o es inválido, limpiamos el storage y mostramos login.
  useEffect(() => {
    const storedToken = localStorage.getItem('acompanarte_token')
    const storedUser  = localStorage.getItem('acompanarte_user')

    if (!storedToken || !storedUser) {
      setIsLoading(false)
      return
    }

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${storedToken}` },
    })
      .then(res => {
        if (res.ok) {
          // Token vigente — restaurar sesión
          setToken(storedToken)
          setUser(JSON.parse(storedUser))
        } else {
          // Token expirado o inválido — limpiar storage
          localStorage.removeItem('acompanarte_token')
          localStorage.removeItem('acompanarte_user')
        }
      })
      .catch(() => {
        // Error de red: no podemos validar → limpiar para forzar re-login
        localStorage.removeItem('acompanarte_token')
        localStorage.removeItem('acompanarte_user')
      })
      .finally(() => setIsLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── login ────────────────────────────────────────────────────
  // Devuelve { ok: true } o { ok: false, error: string }
  const login = useCallback(async (email, password) => {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
		body: new URLSearchParams({ username: email.trim().toLowerCase(), password }),
})

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        return {
          ok: false,
          error: body?.detail ?? 'Correo o contraseña incorrectos.',
        }
      }

      // El backend devuelve:
      // {
      //   access_token: string,
      //   token_type: "bearer",
      //   user: {
      //     id, email, nombre, apellido,
      //     rol_key, label, default_path, nav_config,
      //     avatar_initials, avatar_class, profile_label
      //   }
      // }
      const data = await res.json()

      const userData = data.user
      const jwt      = data.access_token

      // Persistir en localStorage para sobrevivir F5
      localStorage.setItem('acompanarte_token', jwt)
      localStorage.setItem('acompanarte_user', JSON.stringify(userData))

      setToken(jwt)
      setUser(userData)

      return { ok: true }

    } catch (err) {
      console.error('[AuthContext] login error:', err)
      return { ok: false, error: 'Error de conexión. Intentá de nuevo.' }
    }
  }, [])

  // ── logout ───────────────────────────────────────────────────
  const logout = useCallback(async () => {
    // Notificar al backend (invalida el token server-side si existe blacklist)
    if (token) {
      fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {}) // fire-and-forget, no bloqueamos el logout local
    }

    localStorage.removeItem('acompanarte_token')
    localStorage.removeItem('acompanarte_user')
    setToken(null)
    setUser(null)
  }, [token])

  // ── hasRole ──────────────────────────────────────────────────
  // Verifica si el usuario tiene uno de los roles indicados.
  // Uso: hasRole('ter-int', 'admin')
  const hasRole = useCallback((...roles) => {
    return user ? roles.includes(user.rol_key) : false
  }, [user])

  // ── authFetch ────────────────────────────────────────────────
  // Wrapper de fetch que inyecta el JWT automáticamente.
  // Uso: authFetch('/api/v1/pacientes')
  const authFetch = useCallback((url, options = {}) => {
    return fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers ?? {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
  }, [token])

  return (
    <AuthContext.Provider value={{ user, token, login, logout, hasRole, authFetch, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook de acceso
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}
