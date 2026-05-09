import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Iconos ─────────────────────────────────────────────────────────────
const IcoSearch = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="M21 21l-4.35-4.35"/>
  </svg>
)
const IcoPlus = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 4v16m8-8H4"/>
  </svg>
)
const IcoEdit = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
  </svg>
)
const IcoToggle = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
  </svg>
)
const IcoUnlock = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path strokeLinecap="round" d="M7 11V7a5 5 0 019.9-1"/>
  </svg>
)
const IcoCopy = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <rect x="9" y="9" width="13" height="13" rx="2"/>
    <path strokeLinecap="round" d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
  </svg>
)
const IcoClose = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12"/>
  </svg>
)
const IcoChevron = ({ dir = 'down' }) => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"
    style={{ transform: dir === 'up' ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}>
    <path strokeLinecap="round" d="M19 9l-7 7-7-7"/>
  </svg>
)

// ─── Constantes ──────────────────────────────────────────────────────────
const ROLES = [
  { key: 'admin',   label: 'Administrador',      chipClass: 'ch-am',   avClass: 'av-am' },
  { key: 'familia', label: 'Familiar',            chipClass: 'ch-teal', avClass: 'av-tl' },
  { key: 'ter-int', label: 'Terapeuta Interno',   chipClass: 'ch-pp',   avClass: 'av-pp' },
  { key: 'ter-ext', label: 'Terapeuta Externo',   chipClass: 'ch-blu',  avClass: 'av-bu' },
]

// Badge de estado — prioridad: Bloqueado > Inactivo > Activo
function getEstadoBadge(u) {
  if (u.bloqueado) return { cls: 'ch-rd', label: 'Bloqueado' }
  if (!u.activo)   return { cls: 'ch-gray', label: 'Inactivo' }
  return { cls: 'ch-teal', label: 'Activo' }
}

const MOCK_USUARIOS = [
  { id: 1,  nombre: 'Fernando',  apellido: 'Montepó',  email: 'fmontepo@gmail.com',      rol_key: 'admin',   activo: true,  bloqueado: false, ultimo_acceso: '2026-04-14T09:30:00', fecha_alta: '2026-01-01' },
  { id: 2,  nombre: 'María',     apellido: 'González', email: 'maria.g@mail.com',         rol_key: 'familia', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-14T08:12:00', fecha_alta: '2026-02-10' },
  { id: 3,  nombre: 'Luis',      apellido: 'Herrera',  email: 'l.herrera@clinica.com',    rol_key: 'ter-int', activo: true,  bloqueado: true,  ultimo_acceso: '2026-04-13T17:45:00', fecha_alta: '2026-01-15' },
  { id: 4,  nombre: 'Ana',       apellido: 'Torres',   email: 'ana.torres@mail.com',      rol_key: 'familia', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-14T10:05:00', fecha_alta: '2026-03-22' },
  { id: 5,  nombre: 'Carlos',    apellido: 'Méndez',   email: 'carlos.m@mail.com',        rol_key: 'familia', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-12T14:20:00', fecha_alta: '2026-02-28' },
  { id: 6,  nombre: 'Silvia',    apellido: 'Suárez',   email: 's.suarez@terapeutas.com',  rol_key: 'ter-ext', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-13T09:00:00', fecha_alta: '2026-01-20' },
  { id: 7,  nombre: 'Jorge',     apellido: 'Fernández',email: 'jorge.fernandez@mail.com', rol_key: 'familia', activo: false, bloqueado: false, ultimo_acceso: '2026-03-30T11:10:00', fecha_alta: '2026-03-01' },
  { id: 8,  nombre: 'Patricia',  apellido: 'Ruiz',     email: 'p.ruiz@clinica.com',       rol_key: 'ter-int', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-11T16:30:00', fecha_alta: '2026-01-15' },
  { id: 9,  nombre: 'Roberto',   apellido: 'Castro',   email: 'r.castro@terapeutas.com',  rol_key: 'ter-ext', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-10T10:00:00', fecha_alta: '2026-02-05' },
  { id: 10, nombre: 'Elena',     apellido: 'Morales',  email: 'elena.m@mail.com',         rol_key: 'familia', activo: true,  bloqueado: false, ultimo_acceso: '2026-04-09T08:45:00', fecha_alta: '2026-03-15' },
]

function getRolMeta(key) {
  return ROLES.find(r => r.key === key) ?? { key, label: key, chipClass: 'ch-gray', avClass: 'av-gr' }
}
function getInitials(nombre, apellido) {
  return ((nombre?.[0] ?? '') + (apellido?.[0] ?? '')).toUpperCase() || '?'
}
function formatFecha(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
function formatHace(iso) {
  if (!iso) return '—'
  const diff  = Date.now() - new Date(iso).getTime()
  const mins  = Math.floor(diff / 60000)
  const hours = Math.floor(mins / 60)
  const days  = Math.floor(hours / 24)
  if (mins < 60)  return `hace ${mins} min`
  if (hours < 24) return `hace ${hours} h`
  return `hace ${days} día${days > 1 ? 's' : ''}`
}

// ─── Modal Crear / Editar ────────────────────────────────────────────────
function ModalUsuario({ usuario, onClose, onSave }) {
  const [form, setForm] = useState({
    nombre:   usuario?.nombre   ?? '',
    apellido: usuario?.apellido ?? '',
    email:    usuario?.email    ?? '',
    rol_key:  usuario?.rol_key  ?? 'familia',
    activo:   usuario?.activo   ?? true,
    password: '',
  })
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const isEdit = !!usuario

  function handleChange(e) {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.nombre.trim() || !form.email.trim()) { setError('Nombre y correo son obligatorios.'); return }
    if (!isEdit) {
      if (!form.password.trim()) { setError('La contraseña es obligatoria para usuarios nuevos.'); return }
      if (form.password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return }
      if (!/[A-Z]/.test(form.password)) { setError('La contraseña debe contener al menos una letra mayúscula.'); return }
      if (!/\d/.test(form.password)) { setError('La contraseña debe contener al menos un número.'); return }
    }
    setSaving(true)
    await onSave(form)
    setSaving(false)
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">{isEdit ? 'Editar usuario' : 'Nuevo usuario'}</div>
          <button className="btn btn-g btn-sm" onClick={onClose}><IcoClose /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb">
            <div className="fr2">
              <div className="fg">
                <label className="fl">Nombre *</label>
                <input className="fi" name="nombre" value={form.nombre} onChange={handleChange} placeholder="Ej: María" />
              </div>
              <div className="fg">
                <label className="fl">Apellido</label>
                <input className="fi" name="apellido" value={form.apellido} onChange={handleChange} placeholder="Ej: González" />
              </div>
            </div>
            <div className="fg">
              <label className="fl">Correo electrónico *</label>
              <input className="fi" name="email" type="email" value={form.email} onChange={handleChange}
                placeholder="usuario@mail.com" disabled={isEdit} />
              {isEdit && <span className="txs tm">El correo no puede modificarse una vez creado.</span>}
            </div>
            <div className="fg">
              <label className="fl">Rol *</label>
              <select className="fs" name="rol_key" value={form.rol_key} onChange={handleChange}>
                {ROLES.map(r => <option key={r.key} value={r.key}>{r.label}</option>)}
              </select>
            </div>
            {!isEdit && (
              <div className="fg">
                <label className="fl">Contraseña *</label>
                <div style={{ position: 'relative' }}>
                  <input className="fi" name="password" type={showPass ? 'text' : 'password'} value={form.password}
                    onChange={handleChange} placeholder="Mínimo 8 caracteres" style={{ paddingRight: 40 }} />
                  <button
                    type="button"
                    onClick={() => setShowPass(v => !v)}
                    style={{
                      position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--text3)', padding: 2, lineHeight: 1,
                    }}
                    tabIndex={-1}
                    aria-label={showPass ? 'Ocultar' : 'Ver contraseña'}
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
                <span className="txs tm">Mínimo 8 caracteres, una mayúscula y un número. Ej: <em>Acmp2024!</em></span>
              </div>
            )}
            {isEdit && (
              <div className="flex ic g8" style={{ padding: '10px 14px', background: 'var(--bg)', borderRadius: 7, border: '1px solid var(--border)' }}>
                <input type="checkbox" id="activo" name="activo" checked={form.activo}
                  onChange={handleChange} style={{ width: 15, height: 15, accentColor: 'var(--teal)' }} />
                <label htmlFor="activo" style={{ fontSize: 13, cursor: 'pointer' }}>Usuario activo</label>
              </div>
            )}
            {error && <div className="disc disc-rd txs">{error}</div>}
          </div>
          <div className="mf">
            <button type="button" className="btn btn-s" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving}>
              {saving ? 'Guardando…' : isEdit ? 'Guardar cambios' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Modal Contraseña Temporal (resultado de desbloqueo) ─────────────────
function ModalPassTemporal({ usuario, password, onClose }) {
  const [copiado, setCopiado] = useState(false)

  function copiar() {
    navigator.clipboard.writeText(password).then(() => {
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    })
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">Usuario desbloqueado</div>
          <button className="btn btn-g btn-sm" onClick={onClose}><IcoClose /></button>
        </div>
        <div className="mb">
          <div className="disc disc-tl txs" style={{ marginBottom: 16 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
              <path strokeLinecap="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>
              <strong>{usuario.nombre} {usuario.apellido}</strong> fue desbloqueado y reactivado.
              Compartí la siguiente contraseña temporal con el usuario para que pueda ingresar.
            </span>
          </div>
          <div className="fg">
            <label className="fl">Contraseña temporal</label>
            <div className="flex ic g8">
              <input
                className="fi"
                value={password}
                readOnly
                style={{ fontFamily: 'monospace', fontSize: 16, fontWeight: 700, letterSpacing: 2, flex: 1 }}
              />
              <button className="btn btn-s btn-sm" onClick={copiar} style={{ flexShrink: 0 }}>
                <IcoCopy /> {copiado ? 'Copiado' : 'Copiar'}
              </button>
            </div>
          </div>
          <div className="disc disc-am txs" style={{ marginTop: 8 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
              <path strokeLinecap="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            El usuario deberá cambiar su contraseña al ingresar. Esta contraseña no volverá a mostrarse.
          </div>
        </div>
        <div className="mf">
          <button className="btn btn-p" onClick={onClose}>Entendido</button>
        </div>
      </div>
    </div>
  )
}

// ─── Página principal ────────────────────────────────────────────────────
export default function AdminUsuarios() {
  const { authFetch } = useAuth()

  const [usuarios, setUsuarios]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [busqueda, setBusqueda]   = useState('')
  const [filtroRol, setFiltroRol] = useState('todos')
  const [filtroAct, setFiltroAct] = useState('todos')
  const [sortCol, setSortCol]     = useState('nombre')
  const [sortDir, setSortDir]     = useState('asc')
  const [modal, setModal]         = useState(null)   // { modo: 'crear'|'editar'|'pass-temp', usuario?, password? }
  const [toast, setToast]         = useState({ msg: '', ok: true })

  // Normaliza el objeto usuario del backend al shape esperado por la tabla
  function normalizeUser(u) {
    return {
      ...u,
      rol_key:       u.rol_key ?? u.rol ?? 'familia',
      fecha_alta:    u.fecha_alta   ?? u.creado_en,
      ultimo_acceso: u.ultimo_acceso ?? u.ultimo_login,
      bloqueado:     u.bloqueado ?? false,
    }
  }

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/usuarios/')
        if (res.ok) {
          const data = await res.json()
          const norm = Array.isArray(data) ? data.map(normalizeUser) : []
          setUsuarios(norm)
        } else {
          setUsuarios([])
        }
      } catch {
        setUsuarios(MOCK_USUARIOS)
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [authFetch])

  function showToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 2800)
  }

  async function handleSave(form) {
    if (modal.modo === 'crear') {
      try {
        const res = await authFetch('/usuarios/', {
          method: 'POST',
          body: JSON.stringify({
            nombre:   form.nombre,
            apellido: form.apellido,
            email:    form.email,
            rol:      form.rol_key,
            password: form.password,
          }),
        })
        if (res.ok) {
          const nuevo = normalizeUser(await res.json())
          setUsuarios(u => [nuevo, ...u])
          showToast('Usuario creado correctamente.')
          setModal(null)
        } else {
          const err = await res.json().catch(() => ({}))
          const msg = Array.isArray(err.detail)
            ? err.detail.map(e => e.msg).join('. ')
            : (err.detail ?? 'Error al crear el usuario.')
          showToast(msg, false)
        }
      } catch {
        showToast('Error de conexión.', false)
      }
    } else {
      try {
        const res = await authFetch(`/usuarios/${modal.usuario.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            nombre:   form.nombre,
            apellido: form.apellido,
            rol:      form.rol_key,
            activo:   form.activo,
          }),
        })
        if (res.ok) {
          const actualizado = normalizeUser(await res.json())
          setUsuarios(u => u.map(x => x.id === modal.usuario.id ? actualizado : x))
          showToast('Cambios guardados correctamente.')
          setModal(null)
        } else {
          const err = await res.json().catch(() => ({}))
          const msg = Array.isArray(err.detail)
            ? err.detail.map(e => e.msg).join('. ')
            : (err.detail ?? 'Error al guardar los cambios.')
          showToast(msg, false)
        }
      } catch {
        showToast('Error de conexión.', false)
      }
    }
  }

  async function toggleActivo(id) {
    const u = usuarios.find(x => x.id === id)
    if (!u) return
    setUsuarios(prev => prev.map(x => x.id === id ? { ...x, activo: !x.activo } : x))
    try {
      const res = await authFetch(`/usuarios/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ activo: !u.activo }),
      })
      if (res.ok) {
        const actualizado = normalizeUser(await res.json())
        setUsuarios(prev => prev.map(x => x.id === id ? actualizado : x))
        showToast(u.activo ? 'Usuario desactivado.' : 'Usuario activado.')
      } else {
        const err = await res.json().catch(() => ({}))
        setUsuarios(prev => prev.map(x => x.id === id ? { ...x, activo: u.activo } : x))
        showToast(err.detail ?? 'Error al cambiar el estado del usuario.', false)
      }
    } catch {
      setUsuarios(prev => prev.map(x => x.id === id ? { ...x, activo: u.activo } : x))
      showToast('Error de conexión.', false)
    }
  }

  async function desbloquear(id) {
    try {
      const res = await authFetch(`/usuarios/${id}/desbloquear`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        const actualizado = normalizeUser({ ...data })
        setUsuarios(prev => prev.map(x => x.id === id ? { ...x, ...actualizado } : x))
        setModal({ modo: 'pass-temp', usuario: actualizado, password: data.password_temporal })
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err.detail ?? 'Error al desbloquear el usuario.', false)
      }
    } catch {
      showToast('Error de conexión.', false)
    }
  }

  function handleSort(col) {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
  }

  const nActivos    = usuarios.filter(u => u.activo && !u.bloqueado).length
  const nInactivos  = usuarios.filter(u => !u.activo && !u.bloqueado).length
  const nBloqueados = usuarios.filter(u => u.bloqueado).length

  const filtrados = useMemo(() => {
    let list = [...usuarios]
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase()
      list = list.filter(u =>
        u.nombre?.toLowerCase().includes(q) ||
        u.apellido?.toLowerCase().includes(q) ||
        u.email?.toLowerCase().includes(q)
      )
    }
    if (filtroRol !== 'todos')       list = list.filter(u => u.rol_key === filtroRol)
    if (filtroAct === 'activos')     list = list.filter(u => u.activo && !u.bloqueado)
    if (filtroAct === 'inactivos')   list = list.filter(u => !u.activo && !u.bloqueado)
    if (filtroAct === 'bloqueados')  list = list.filter(u => u.bloqueado)
    list.sort((a, b) => {
      let va = '', vb = ''
      if (sortCol === 'nombre') { va = `${a.nombre} ${a.apellido}`; vb = `${b.nombre} ${b.apellido}` }
      if (sortCol === 'email')  { va = a.email; vb = b.email }
      if (sortCol === 'rol')    { va = a.rol_key; vb = b.rol_key }
      if (sortCol === 'acceso') { va = a.ultimo_acceso ?? ''; vb = b.ultimo_acceso ?? '' }
      return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
    })
    return list
  }, [usuarios, busqueda, filtroRol, filtroAct, sortCol, sortDir])

  function Th({ col, children }) {
    const active = sortCol === col
    return (
      <th onClick={() => handleSort(col)} style={{
        cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
        padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600,
        color: active ? 'var(--teal3)' : 'var(--text3)',
        textTransform: 'uppercase', letterSpacing: '0.06em',
        background: active ? 'var(--teal2)' : 'var(--bg)',
      }}>
        <span className="flex ic g4">{children}{active && <IcoChevron dir={sortDir === 'asc' ? 'up' : 'down'} />}</span>
      </th>
    )
  }

  return (
    <div>
      <div className={`toast ${toast.msg ? 'visible' : ''} ${!toast.ok ? 'error' : ''}`}>{toast.msg}</div>

      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Usuarios</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {usuarios.length} registrados · {nActivos} activos · {nInactivos} inactivos
            {nBloqueados > 0 && <span style={{ color: 'var(--rd)', fontWeight: 600 }}> · {nBloqueados} bloqueados</span>}
          </div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => setModal({ modo: 'crear', usuario: null })}>
          <IcoPlus /> Nuevo usuario
        </button>
      </div>

      <div className="card mb16" style={{ padding: '12px 16px' }}>
        <div className="flex ic g10" style={{ flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: '1 1 220px', minWidth: 180 }}>
            <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }}>
              <IcoSearch />
            </span>
            <input className="fi" value={busqueda} onChange={e => setBusqueda(e.target.value)}
              placeholder="Buscar por nombre o correo…" style={{ paddingLeft: 32, fontSize: 13 }} />
          </div>
          <select className="fs" value={filtroRol} onChange={e => setFiltroRol(e.target.value)}
            style={{ width: 'auto', minWidth: 160, flex: '0 0 auto', fontSize: 13 }}>
            <option value="todos">Todos los roles</option>
            {ROLES.map(r => <option key={r.key} value={r.key}>{r.label}</option>)}
          </select>
          <div className="flex ic g6" style={{ flex: '0 0 auto' }}>
            {[
              { val: 'todos',      label: `Todos (${usuarios.length})` },
              { val: 'activos',    label: `Activos (${nActivos})` },
              { val: 'inactivos',  label: `Inactivos (${nInactivos})` },
              { val: 'bloqueados', label: `Bloqueados (${nBloqueados})` },
            ].map(op => (
              <button key={op.val}
                className={`btn btn-sm ${filtroAct === op.val ? 'btn-p' : 'btn-s'}`}
                onClick={() => setFiltroAct(op.val)}>
                {op.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando usuarios…</div>
        ) : filtrados.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
            <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin resultados</div>
            <div className="ts tm" style={{ marginTop: 4 }}>Probá con otros filtros o términos de búsqueda.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <Th col="nombre">Usuario</Th>
                  <Th col="email">Correo</Th>
                  <Th col="rol">Rol</Th>
                  <Th col="acceso">Último acceso</Th>
                  <th style={{ padding: '10px 14px', fontSize: 11, fontWeight: 600, color: 'var(--text3)',
                    textTransform: 'uppercase', letterSpacing: '0.06em', background: 'var(--bg)', textAlign: 'center' }}>
                    Estado
                  </th>
                  <th style={{ padding: '10px 14px', background: 'var(--bg)', width: 100 }} />
                </tr>
              </thead>
              <tbody>
                {filtrados.map((u, idx) => {
                  const rol    = getRolMeta(u.rol_key)
                  const estado = getEstadoBadge(u)
                  const esActivo = u.activo && !u.bloqueado
                  return (
                    <tr key={u.id} style={{
                      borderBottom: idx < filtrados.length - 1 ? '1px solid var(--border)' : 'none',
                      background: u.bloqueado
                        ? 'rgba(220,38,38,0.04)'
                        : !u.activo
                          ? 'rgba(0,0,0,0.015)'
                          : undefined,
                    }}>
                      <td style={{ padding: '12px 14px' }}>
                        <div className="flex ic g10">
                          <div className={`av ${rol.avClass}`} style={{ width: 32, height: 32, fontSize: 11, opacity: esActivo ? 1 : 0.5 }}>
                            {getInitials(u.nombre, u.apellido)}
                          </div>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 500, color: esActivo ? 'var(--text)' : 'var(--text3)' }}>
                              {u.nombre} {u.apellido}
                            </div>
                            <div className="txs tm">Alta: {formatFecha(u.fecha_alta)}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '12px 14px', fontSize: 13, color: 'var(--text2)' }}>{u.email}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span className={`chip ${rol.chipClass}`}>{rol.label}</span>
                      </td>
                      <td style={{ padding: '12px 14px', fontSize: 13, color: 'var(--text3)' }}>
                        {formatHace(u.ultimo_acceso)}
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                        <span className={`chip ${estado.cls}`}>{estado.label}</span>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                        <div className="flex ic g4" style={{ justifyContent: 'flex-end' }}>
                          <button className="btn btn-g btn-xs" title="Editar"
                            onClick={() => setModal({ modo: 'editar', usuario: u })}>
                            <IcoEdit />
                          </button>
                          {u.bloqueado ? (
                            /* Botón Desbloquear — solo visible cuando está bloqueado */
                            <button className="btn btn-am btn-xs" title="Desbloquear y generar nueva contraseña"
                              onClick={() => desbloquear(u.id)}>
                              <IcoUnlock />
                            </button>
                          ) : (
                            /* Botón Activar / Desactivar — solo cuando no está bloqueado */
                            <button className={`btn btn-xs ${u.activo ? 'btn-rd' : 'btn-am'}`}
                              title={u.activo ? 'Desactivar' : 'Activar'}
                              onClick={() => toggleActivo(u.id)}>
                              <IcoToggle />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        {!loading && filtrados.length > 0 && (
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)',
            background: 'var(--bg)', fontSize: 12, color: 'var(--text3)' }}>
            Mostrando {filtrados.length} de {usuarios.length} usuarios
          </div>
        )}
      </div>

      {modal?.modo === 'crear' && (
        <ModalUsuario usuario={null} onClose={() => setModal(null)} onSave={handleSave} />
      )}
      {modal?.modo === 'editar' && (
        <ModalUsuario usuario={modal.usuario} onClose={() => setModal(null)} onSave={handleSave} />
      )}
      {modal?.modo === 'pass-temp' && (
        <ModalPassTemporal usuario={modal.usuario} password={modal.password} onClose={() => setModal(null)} />
      )}
    </div>
  )
}
