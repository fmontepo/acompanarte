import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

// ─── Iconos ────────────────────────────────────────────────────────────
const IcoUsers = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
  </svg>
)
const IcoPaciente = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
  </svg>
)
const IcoTerapeuta = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
  </svg>
)
const IcoActividad = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
  </svg>
)
const IcoArrow = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
  </svg>
)
const IcoAlert = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
  </svg>
)
const IcoCheck = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
  </svg>
)
const IcoLogin = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
  </svg>
)
const IcoPlus = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/>
  </svg>
)
const IcoBook = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
  </svg>
)

const TIPO_LABEL = { pdf: 'PDF', articulo: 'Artículo', guia: 'Guía', protocolo: 'Protocolo' }

// ─── Modal lector de contenido ─────────────────────────────────────────────
function ModalContenidoRecurso({ recurso, onClose }) {
  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo" style={{ maxWidth: 620 }}>
        <div className="mh">
          <div className="flex ic g8">
            <IcoBook />
            <div className="mt" style={{ fontSize: 15 }}>{recurso.titulo}</div>
          </div>
          <button className="btn btn-g btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="mb" style={{ maxHeight: '62vh', overflowY: 'auto' }}>
          {recurso.descripcion && (
            <div className="disc disc-tl txs" style={{ marginBottom: 12 }}>
              {recurso.descripcion}
            </div>
          )}
          {recurso.contenido_texto ? (
            <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text)', whiteSpace: 'pre-wrap' }}>
              {recurso.contenido_texto}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text3)', fontSize: 13, fontStyle: 'italic' }}>
              Este recurso no tiene contenido de texto cargado.
            </div>
          )}
        </div>
        <div className="mf">
          <button className="btn btn-p btn-sm" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  )
}

// ─── Componente StatCard ────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, subColor, accent, onClick }) {
  return (
    <div
      className="stat"
      style={{ cursor: onClick ? 'pointer' : 'default', transition: 'box-shadow 0.15s' }}
      onClick={onClick}
      onMouseEnter={e => onClick && (e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.10)')}
      onMouseLeave={e => onClick && (e.currentTarget.style.boxShadow = '')}
    >
      <div className="flex ic jb mb8">
        <div style={{
          width: 38, height: 38, borderRadius: 9,
          background: accent + '22',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: accent,
        }}>
          {icon}
        </div>
        {onClick && <span style={{ color: 'var(--text3)', display: 'flex' }}><IcoArrow /></span>}
      </div>
      <div className="sn">{value}</div>
      <div className="sl">{label}</div>
      {sub && <div className="sc" style={{ color: subColor ?? 'var(--teal)' }}>{sub}</div>}
    </div>
  )
}

// ─── Componente AuditRow ───────────────────────────────────────────────
function AuditRow({ item }) {
  const esAlerta = item.estado === 'alerta'
  return (
    <div className="flex ic g12" style={{
      padding: '10px 0',
      borderBottom: '1px solid var(--border)',
    }}>
      {/* Ícono tipo */}
      <div style={{
        width: 30, height: 30, borderRadius: 7, flexShrink: 0,
        background: esAlerta ? 'var(--amber2)' : item.tipo === 'login' ? 'var(--teal2)' : 'var(--purple2)',
        color: esAlerta ? 'var(--amber)' : item.tipo === 'login' ? 'var(--teal3)' : 'var(--purple)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {esAlerta ? <IcoAlert /> : item.tipo === 'login' ? <IcoLogin /> : <IcoCheck />}
      </div>

      {/* Descripción */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.accion}
        </div>
        <div className="flex ic g6" style={{ marginTop: 2 }}>
          <span className="txs tm">{item.usuario}</span>
          <span className="txs tm">·</span>
          <span className={`chip ${
            item.rol === 'Familiar' ? 'ch-teal' :
            item.rol === 'Terapeuta Interno' ? 'ch-pp' :
            item.rol === 'Terapeuta Externo' ? 'ch-blu' :
            item.rol === 'Administrador' ? 'ch-am' : 'ch-gray'
          }`}>{item.rol}</span>
        </div>
      </div>

      {/* Hora */}
      <div className="txs tm" style={{ flexShrink: 0 }}>{item.hora}</div>
    </div>
  )
}

// ─── Dashboard principal ────────────────────────────────────────────────
export default function AdminDashboard() {
  const { user, authFetch } = useAuth()
  const navigate = useNavigate()

  const [stats, setStats]             = useState(null)
  const [auditoria, setAuditoria]     = useState([])
  const [recientes, setRecientes]     = useState([])
  const [pendientes, setPendientes]   = useState([])
  const [verContenido, setVerContenido] = useState(null)
  const [validando, setValidando]     = useState(null)
  const [toastMsg, setToastMsg]       = useState('')
  const [loading, setLoading]         = useState(true)

  useEffect(() => {
    async function cargarDatos() {
      setLoading(true)
      try {
        // Endpoint agregado: devuelve stats + recientes en una sola llamada
        const [resDash, resAuditoria] = await Promise.allSettled([
          authFetch('/admin/dashboard'),
          authFetch('/auditoria/?limit=8'),
        ])

        // Dashboard stats
        if (resDash.status === 'fulfilled' && resDash.value.ok) {
          const data = await resDash.value.json()
          const s = data.stats ?? {}
          setStats({
            usuarios:        { total: s.usuarios?.total ?? 0, activos: s.usuarios?.total ?? 0, nuevos_mes: s.usuarios?.nuevos_mes ?? 0 },
            pacientes:       { total: s.pacientes?.total ?? 0, activos: s.pacientes?.activos ?? 0, alta_este_mes: s.pacientes?.alta_este_mes ?? 0 },
            terapeutas:      { total: s.terapeutas?.total ?? 0, internos: s.terapeutas?.internos ?? 0, externos: s.terapeutas?.externos ?? 0 },
            actividades_hoy: s.actividades_hoy ?? 0,
          })
          setPendientes(Array.isArray(data.recursos_pendientes) ? data.recursos_pendientes : [])
          setRecientes(Array.isArray(data.recientes) ? data.recientes.map(u => ({
            id:      u.id,
            nombre:  u.nombre,
            email:   u.email,
            rol:     u.rol_label || u.rol || '—',
            av:      (u.nombre || '?').slice(0, 2).toUpperCase(),
            avClass: 'av-tl',
            fecha:   u.fecha ? new Date(u.fecha).toLocaleString('es-AR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—',
          })) : [])
        } else {
          setStats({ usuarios: {total:0,activos:0,nuevos_mes:0}, pacientes: {total:0,activos:0,alta_este_mes:0}, terapeutas: {total:0,internos:0,externos:0}, actividades_hoy: 0 })
          setRecientes([])
        }

        // Auditoría reciente
        if (resAuditoria.status === 'fulfilled' && resAuditoria.value.ok) {
          const data = await resAuditoria.value.json()
          setAuditoria(Array.isArray(data) ? data.map(e => ({
            id:     e.id,
            tipo:   e.accion || e.tipo || 'create',
            usuario: e.usuario || 'Sistema',
            rol:    e.rol || 'sistema',
            accion: e.desc || e.accion || '',
            hora:   e.timestamp ? _hace(e.timestamp) : '—',
            estado: e.resultado === 'exito' ? 'ok' : 'alerta',
          })) : [])
        } else {
          setAuditoria([])
        }

      } catch {
        setStats({ usuarios: { total: 0, activos: 0, nuevos_mes: 0 }, pacientes: { total: 0, activos: 0, alta_este_mes: 0 }, terapeutas: { total: 0, internos: 0, externos: 0 }, actividades_hoy: 0 })
        setAuditoria([])
        setRecientes([])
      } finally {
        setLoading(false)
      }
    }

    cargarDatos()
  }, [authFetch])

  function _hace(iso) {
    const diff  = Date.now() - new Date(iso).getTime()
    const mins  = Math.floor(diff / 60000)
    const hours = Math.floor(mins / 60)
    const days  = Math.floor(hours / 24)
    if (mins < 60)  return `hace ${mins} min`
    if (hours < 24) return `hace ${hours} h`
    return `hace ${days} día${days > 1 ? 's' : ''}`
  }

  function showToast(msg) {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(''), 2800)
  }

  async function handleValidar(recurso) {
    setValidando(recurso.id)
    try {
      const res = await authFetch(`/recursos/${recurso.id}/validar`, { method: 'POST' })
      if (res.ok) {
        setPendientes(prev => prev.filter(r => r.id !== recurso.id))
        showToast(`"${recurso.titulo}" validado. Ya está disponible para el Asistente IA.`)
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err?.detail ?? 'Error al validar el recurso.')
      }
    } catch {
      showToast('Error de conexión al intentar validar.')
    } finally {
      setValidando(null)
    }
  }

  // ── Skeleton loader ────────────────────────────────────────────────
  if (loading) {
    return (
      <div>
        <div className="g4 mb20">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="stat" style={{ height: 110 }}>
              <div style={{ width: 38, height: 38, borderRadius: 9, background: 'var(--bg)', marginBottom: 12 }} />
              <div style={{ width: '60%', height: 28, borderRadius: 6, background: 'var(--bg)' }} />
              <div style={{ width: '80%', height: 12, borderRadius: 6, background: 'var(--bg)', marginTop: 8 }} />
            </div>
          ))}
        </div>
        <div className="flex ic jb mb12">
          <div style={{ width: 160, height: 18, borderRadius: 5, background: 'var(--bg)' }} />
        </div>
        <div className="card">
          {[...Array(5)].map((_, i) => (
            <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
              <div style={{ width: '75%', height: 14, borderRadius: 5, background: 'var(--bg)' }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ── Render principal ───────────────────────────────────────────────
  const nombre = [user?.nombre, user?.apellido].filter(Boolean).join(' ') || 'Admin'
  const hora   = new Date().getHours()
  const saludo = hora < 13 ? 'Buenos días' : hora < 20 ? 'Buenas tardes' : 'Buenas noches'

  return (
    <div>
      <div className={`toast ${toastMsg ? 'visible' : ''}`}>{toastMsg}</div>
      {verContenido && <ModalContenidoRecurso recurso={verContenido} onClose={() => setVerContenido(null)} />}

      {/* ── Saludo ─────────────────────────────────────────────── */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{saludo}, {nombre} 👋</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            Resumen del sistema · {new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
        </div>
        <div className="flex ic g8">
          <button className="btn btn-s btn-sm" onClick={() => navigate('/admin/auditoria')}>
            Ver auditoría
          </button>
          <button className="btn btn-p btn-sm" onClick={() => navigate('/admin/usuarios')}>
            <IcoPlus /> Nuevo usuario
          </button>
        </div>
      </div>

      {/* ── KPIs ───────────────────────────────────────────────── */}
      <div className="g4 mb20">
        <StatCard
          icon={<IcoUsers />}
          label="Usuarios registrados"
          value={stats.usuarios.total}
          sub={`+${stats.usuarios.nuevos_mes} este mes`}
          accent="var(--teal)"
          onClick={() => navigate('/admin/usuarios')}
        />
        <StatCard
          icon={<IcoPaciente />}
          label="Pacientes activos"
          value={stats.pacientes.activos}
          sub={`${stats.pacientes.total} en total · ${stats.pacientes.alta_este_mes} altas nuevas`}
          accent="var(--purple)"
        />
        <StatCard
          icon={<IcoTerapeuta />}
          label="Terapeutas"
          value={stats.terapeutas.total}
          sub={`${stats.terapeutas.internos} internos · ${stats.terapeutas.externos} externos`}
          accent="var(--amber)"
          subColor="var(--amber)"
        />
        <StatCard
          icon={<IcoActividad />}
          label="Actividades registradas hoy"
          value={stats.actividades_hoy}
          sub="en las últimas 24 hs"
          accent="var(--blue)"
          subColor="var(--blue)"
        />
      </div>

      {/* ── Cuerpo: Auditoría + Panel lateral ─────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16, alignItems: 'start' }}>

        {/* Actividad reciente */}
        <div className="card" style={{ padding: 0 }}>
          <div className="flex ic jb" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Actividad reciente</div>
              <div className="txs tm" style={{ marginTop: 2 }}>Últimas acciones del sistema</div>
            </div>
            <button className="btn btn-g btn-sm" onClick={() => navigate('/admin/auditoria')}>
              Ver todo <IcoArrow />
            </button>
          </div>
          <div style={{ padding: '0 20px' }}>
            {auditoria.length === 0
              ? <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text3)', fontSize: 13 }}>Sin actividad registrada todavía</div>
              : auditoria.map(item => <AuditRow key={item.id} item={item} />)
            }
          </div>
        </div>

        {/* Panel lateral derecho */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Distribución de roles */}
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>Distribución de usuarios</div>
            {(() => {
              const total = stats.usuarios.total || 1
              const rows = [
                { rol: 'Terapeutas Internos', n: stats.terapeutas.internos, color: 'var(--purple)' },
                { rol: 'Terapeutas Externos', n: stats.terapeutas.externos, color: 'var(--amber)' },
                { rol: 'Familiares + Otros',  n: Math.max(0, stats.usuarios.total - stats.terapeutas.total), color: 'var(--teal)' },
              ]
              return rows.map(row => (
                <div key={row.rol} style={{ marginBottom: 12 }}>
                  <div className="flex ic jb" style={{ marginBottom: 5 }}>
                    <span className="ts">{row.rol}</span>
                    <span className="ts f5" style={{ color: row.color }}>{row.n}</span>
                  </div>
                  <div className="pbar">
                    <div className="pf" style={{ width: `${Math.round((row.n / total) * 100)}%`, background: row.color }} />
                  </div>
                </div>
              ))
            })()}
          </div>

          {/* Nuevos usuarios */}
          <div className="card">
            <div className="flex ic jb" style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>Últimos registros</div>
              <button className="btn btn-g btn-xs" onClick={() => navigate('/admin/usuarios')}>
                Ver todos
              </button>
            </div>
            {recientes.length === 0
              ? <div className="txs tm" style={{ textAlign: 'center', padding: '12px 0' }}>Sin registros recientes</div>
              : recientes.map(u => (
                <div key={u.id} className="flex ic g10" style={{ marginBottom: 12 }}>
                  <div className={`av ${u.avClass}`} style={{ width: 32, height: 32, fontSize: 11 }}>
                    {u.av}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="ts f5" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {u.nombre}
                    </div>
                    <div className="txs tm">{u.rol}</div>
                  </div>
                  <div className="txs tm" style={{ flexShrink: 0 }}>{u.fecha}</div>
                </div>
              ))
            }
          </div>

          {/* ── Recursos pendientes de validación ─────────────── */}
          <div className="card">
            <div className="flex ic jb" style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>Base de conocimiento</div>
              {pendientes.length > 0 && (
                <span style={{
                  fontSize: 11, fontWeight: 700, background: 'var(--amber2)',
                  color: 'var(--amber)', borderRadius: 20, padding: '2px 8px',
                }}>
                  {pendientes.length} pendiente{pendientes.length > 1 ? 's' : ''}
                </span>
              )}
            </div>

            {pendientes.length === 0 ? (
              <div className="flex ic g8" style={{ color: 'var(--teal)', fontSize: 12, padding: '8px 0' }}>
                <IcoCheck /> <span>Base de conocimiento al día</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {pendientes.map(r => (
                  <div key={r.id} style={{
                    borderRadius: 8, border: '1px solid var(--border)',
                    padding: '10px 12px', background: 'var(--bg)',
                  }}>
                    <div className="flex ic jb" style={{ marginBottom: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 600,
                        background: 'var(--amber2)', color: 'var(--amber)',
                        borderRadius: 4, padding: '2px 6px' }}>
                        {TIPO_LABEL[r.tipo] ?? r.tipo}
                      </span>
                      {r.subido_en && (
                        <span className="txs tm">
                          {new Date(r.subido_en).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' })}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, lineHeight: 1.3 }}>
                      {r.titulo}
                    </div>
                    <div className="flex ic g6">
                      <button
                        className="btn btn-g btn-xs flex ic g4"
                        onClick={() => setVerContenido(r)}
                        title="Ver contenido del recurso"
                        style={{ fontSize: 11 }}
                      >
                        <IcoBook /> Leer
                      </button>
                      <button
                        className="btn btn-p btn-xs"
                        disabled={validando === r.id}
                        onClick={() => handleValidar(r)}
                        style={{ fontSize: 11 }}
                      >
                        {validando === r.id ? '…' : '✓ Validar'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Acciones rápidas */}
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Acciones rápidas</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button className="btn btn-s btn-sm w100" style={{ justifyContent: 'flex-start' }}
                onClick={() => navigate('/admin/usuarios')}>
                <IcoPlus /> Crear nuevo usuario
              </button>
              <button className="btn btn-s btn-sm w100" style={{ justifyContent: 'flex-start' }}
                onClick={() => navigate('/admin/auditoria')}>
                <IcoActividad /> Ver log de auditoría
              </button>
            </div>
          </div>

        </div>
      </div>

    </div>
  )
}
