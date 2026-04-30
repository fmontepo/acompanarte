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

const MOCK_USUARIOS = [
  { id: 1,  nombre: 'Fernando',  apellido: 'Montepó',  email: 'fmontepo@gmail.com',      rol_key: 'admin',   activo: true,  ultimo_acceso: '2026-04-14T09:30:00', fecha_alta: '2026-01-01' },
  { id: 2,  nombre: 'María',     apellido: 'González', email: 'maria.g@mail.com',         rol_key: 'familia', activo: true,  ultimo_acceso: '2026-04-14T08:12:00', fecha_alta: '2026-02-10' },
  { id: 3,  nombre: 'Luis',      apellido: 'Herrera',  email: 'l.herrera@clinica.com',    rol_key: 'ter-int', activo: true,  ultimo_acceso: '2026-04-13T17:45:00', fecha_alta: '2026-01-15' },
  { id: 4,  nombre: 'Ana',       apellido: 'Torres',   email: 'ana.torres@mail.com',      rol_key: 'familia', activo: true,  ultimo_acceso: '2026-04-14T10:05:00', fecha_alta: '2026-03-22' },
  { id: 5,  nombre: 'Carlos',    apellido: 'Méndez',   email: 'carlos.m@mail.com',        rol_key: 'familia', activo: true,  ultimo_acceso: '2026-04-12T14:20:00', fecha_alta: '2026-02-28' },
  { id: 6,  nombre: 'Silvia',    apellido: 'Suárez',   email: 's.suarez@terapeutas.com',  rol_key: 'ter-ext', activo: true,  ultimo_acceso: '2026-04-13T09:00:00', fecha_alta: '2026-01-20' },
  { id: 7,  nombre: 'Jorge',     apellido: 'Fernández',email: 'jorge.fernandez@mail.com', rol_key: 'familia', activo: false, ultimo_acceso: '2026-03-30T11:10:00', fecha_alta: '2026-03-01' },
  { id: 8,  nombre: 'Patricia',  apellido: 'Ruiz',     email: 'p.ruiz@clinica.com',       rol_key: 'ter-int', activo: true,  ultimo_acceso: '2026-04-11T16:30:00', fecha_alta: '2026-01-15' },
  { id: 9,  nombre: 'Roberto',   apellido: 'Castro',   email: 'r.castro@terapeutas.com',  rol_key: 'ter-ext', activo: true,  ultimo_acceso: '2026-04-10T10:00:00', fecha_alta: '2026-02-05' },
  { id: 10, nombre: 'Elena',     apellido: 'Morales',  email: 'elena.m@mail.com',         rol_key: 'familia', activo: true,  ultimo_acceso: '2026-04-09T08:45:00', fecha_alta: '2026-03-15' },
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
  const isEdit = !!usuario

  function handleChange(e) {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.nombre.trim() || !form.email.trim()) { setError('Nombre y correo son obligatorios.'); return }
    if (!isEdit && !form.password.trim()) { setError('La contraseña es obligatoria para usuarios nuevos.'); return }
    setSaving(true)
    await new Promise(r => setTimeout(r, 600))
    setSaving(false)
    onSave(form)
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
                <input className="fi" name="password" type="password" value={form.password}
                  onChange={handleChange} placeholder="Mínimo 8 caracteres" />
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
  const [modal, setModal]         = useState(null)
  const [toast, setToast]         = useState('')

  // Normaliza el objeto usuario del backend al shape esperado por la tabla
  function normalizeUser(u) {
    return {
      ...u,
      rol_key:      u.rol_key ?? u.rol ?? 'familia',   // backend devuelve "rol", frontend usa "rol_key"
      fecha_alta:   u.fecha_alta   ?? u.creado_en,     // backend devuelve "creado_en"
      ultimo_acceso: u.ultimo_acceso ?? u.ultimo_login, // backend devuelve "ultimo_login"
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
        setUsuarios(MOCK_USUARIOS)  // error de red → mock
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [authFetch])

  function showToast(msg) {
    setToast(msg)
    setTimeout(() => setToast(''), 2800)
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
            rol:      form.rol_key,   // backend espera 'rol', no 'rol_key'
            password: form.password,
          }),
        })
        if (res.ok) {
          const nuevo = normalizeUser(await res.json())
          setUsuarios(u => [nuevo, ...u])
          showToast('Usuario creado correctamente.')
        } else {
          const err = await res.json().catch(() => ({}))
          showToast(err.detail ?? 'Error al crear el usuario.')
          return
        }
      } catch {
        showToast('Error de conexión.')
        return
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
        } else {
          const err = await res.json().catch(() => ({}))
          showToast(err.detail ?? 'Error al guardar los cambios.')
          return
        }
      } catch {
        showToast('Error de conexión.')
        return
      }
    }
    setModal(null)
  }

  async function toggleActivo(id) {
    const u = usuarios.find(x => x.id === id)
    if (!u) return
    // Actualización optimista
    setUsuarios(prev => prev.map(x => x.id === id ? { ...x, activo: !x.activo } : x))
    try {
      const res = await authFetch(`/usuarios/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ activo: !u.activo }),
      })
      if (res.ok) {
        showToast(u.activo ? 'Usuario desactivado.' : 'Usuario activado.')
      } else {
        // Revertir si falla
        setUsuarios(prev => prev.map(x => x.id === id ? { ...x, activo: u.activo } : x))
        showToast('Error al cambiar el estado del usuario.')
      }
    } catch {
      setUsuarios(prev => prev.map(x => x.id === id ? { ...x, activo: u.activo } : x))
      showToast('Error de conexión.')
    }
  }

  function handleSort(col) {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
  }

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
    if (filtroRol !== 'todos')     list = list.filter(u => u.rol_key === filtroRol)
    if (filtroAct === 'activos')   list = list.filter(u => u.activo)
    if (filtroAct === 'inactivos') list = list.filter(u => !u.activo)
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

  const nActivos   = usuarios.filter(u => u.activo).length
  const nInactivos = usuarios.filter(u => !u.activo).length

  return (
    <div>
      <div className={`toast ${toast ? 'visible' : ''}`}>{toast}</div>

      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Usuarios</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {usuarios.length} registrados · {nActivos} activos · {nInactivos} inactivos
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
              { val: 'todos',     label: `Todos (${usuarios.length})` },
              { val: 'activos',   label: `Activos (${nActivos})` },
              { val: 'inactivos', label: `Inactivos (${nInactivos})` },
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
                  <th style={{ padding: '10px 14px', background: 'var(--bg)', width: 80 }} />
                </tr>
              </thead>
              <tbody>
                {filtrados.map((u, idx) => {
                  const rol = getRolMeta(u.rol_key)
                  return (
                    <tr key={u.id} style={{
                      borderBottom: idx < filtrados.length - 1 ? '1px solid var(--border)' : 'none',
                      background: !u.activo ? 'rgba(0,0,0,0.015)' : undefined,
                    }}>
                      <td style={{ padding: '12px 14px' }}>
                        <div className="flex ic g10">
                          <div className={`av ${rol.avClass}`} style={{ width: 32, height: 32, fontSize: 11, opacity: u.activo ? 1 : 0.5 }}>
                            {getInitials(u.nombre, u.apellido)}
                          </div>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 500, color: u.activo ? 'var(--text)' : 'var(--text3)' }}>
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
                        <span className={`chip ${u.activo ? 'ch-teal' : 'ch-gray'}`}>
                          {u.activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                        <div className="flex ic g4" style={{ justifyContent: 'flex-end' }}>
                          <button className="btn btn-g btn-xs" title="Editar"
                            onClick={() => setModal({ modo: 'editar', usuario: u })}>
                            <IcoEdit />
                          </button>
                          <button className={`btn btn-xs ${u.activo ? 'btn-rd' : 'btn-am'}`}
                            title={u.activo ? 'Desactivar' : 'Activar'}
                            onClick={() => toggleActivo(u.id)}>
                            <IcoToggle />
                          </button>
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

      {modal && (
        <ModalUsuario usuario={modal.usuario} onClose={() => setModal(null)} onSave={handleSave} />
      )}
    </div>
  )
}
