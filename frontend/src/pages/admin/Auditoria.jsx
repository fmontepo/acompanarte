import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Iconos ──────────────────────────────────────────────────────────────
const IcoSearch = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="M21 21l-4.35-4.35"/>
  </svg>
)
const IcoDownload = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
  </svg>
)
const IcoFilter = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
  </svg>
)
const IcoRefresh = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
  </svg>
)

// ─── Mock data ───────────────────────────────────────────────────────────
const TIPOS = [
  { key: 'login',    label: 'Login',     chipClass: 'ch-teal', color: 'var(--teal)' },
  { key: 'logout',   label: 'Logout',    chipClass: 'ch-gray', color: 'var(--text3)' },
  { key: 'create',   label: 'Creación',  chipClass: 'ch-pp',   color: 'var(--purple)' },
  { key: 'update',   label: 'Edición',   chipClass: 'ch-blu',  color: 'var(--blue)' },
  { key: 'delete',   label: 'Baja',      chipClass: 'ch-rd',   color: 'var(--red)' },
  { key: 'alert',    label: 'Alerta',    chipClass: 'ch-am',   color: 'var(--amber)' },
  { key: 'ia',       label: 'IA',        chipClass: 'ch-pp',   color: 'var(--purple)' },
]

const ROL_CHIPS = {
  admin:    'ch-am',
  familia:  'ch-teal',
  'ter-int':'ch-pp',
  'ter-ext':'ch-blu',
  sistema:  'ch-gray',
}
const ROL_LABELS = {
  admin:    'Administrador',
  familia:  'Familiar',
  'ter-int':'Terapeuta Int.',
  'ter-ext':'Terapeuta Ext.',
  sistema:  'Sistema',
}

function generarMock() {
  const acciones = [
    { tipo: 'login',   usuario: 'María González',   rol: 'familia',  desc: 'Inicio de sesión exitoso' },
    { tipo: 'login',   usuario: 'Dr. Luis Herrera', rol: 'ter-int',  desc: 'Inicio de sesión exitoso' },
    { tipo: 'create',  usuario: 'Dr. Luis Herrera', rol: 'ter-int',  desc: 'Registro de seguimiento creado para paciente #3' },
    { tipo: 'update',  usuario: 'Fernando Montepó', rol: 'admin',    desc: 'Usuario jorge.fernandez@mail.com actualizado' },
    { tipo: 'alert',   usuario: 'Sistema',           rol: 'sistema',  desc: 'Alerta de inactividad: paciente #7 sin registros en 7 días' },
    { tipo: 'create',  usuario: 'Fernando Montepó', rol: 'admin',    desc: 'Usuario ana.torres@mail.com creado con rol Familiar' },
    { tipo: 'ia',      usuario: 'Carlos Méndez',    rol: 'familia',  desc: 'Consulta al asistente IA — sesión iniciada' },
    { tipo: 'logout',  usuario: 'Silvia Suárez',    rol: 'ter-ext',  desc: 'Cierre de sesión' },
    { tipo: 'create',  usuario: 'Dr. Luis Herrera', rol: 'ter-int',  desc: 'Nueva actividad asignada: Ejercicio de respiración' },
    { tipo: 'alert',   usuario: 'Sistema',           rol: 'sistema',  desc: 'Consentimiento vencido: familiar #3 — requiere renovación' },
    { tipo: 'update',  usuario: 'Patricia Ruiz',    rol: 'ter-int',  desc: 'Registro de seguimiento #12 editado' },
    { tipo: 'login',   usuario: 'Ana Torres',       rol: 'familia',  desc: 'Inicio de sesión exitoso' },
    { tipo: 'delete',  usuario: 'Fernando Montepó', rol: 'admin',    desc: 'Usuario roberto.castro@terapeutas.com desactivado' },
    { tipo: 'ia',      usuario: 'María González',   rol: 'familia',  desc: 'Consulta al asistente IA — 3 mensajes intercambiados' },
    { tipo: 'create',  usuario: 'Patricia Ruiz',    rol: 'ter-int',  desc: 'Progreso de actividad registrado para paciente #5' },
    { tipo: 'login',   usuario: 'Carlos Méndez',    rol: 'familia',  desc: 'Inicio de sesión exitoso' },
    { tipo: 'update',  usuario: 'Fernando Montepó', rol: 'admin',    desc: 'Permisos de seguimiento actualizados para paciente #2' },
    { tipo: 'alert',   usuario: 'Sistema',           rol: 'sistema',  desc: 'Intento de acceso fallido: usuario desconocido (3 intentos)' },
    { tipo: 'logout',  usuario: 'Dr. Luis Herrera', rol: 'ter-int',  desc: 'Cierre de sesión' },
    { tipo: 'create',  usuario: 'Fernando Montepó', rol: 'admin',    desc: 'Nuevo terapeuta externo registrado: r.castro@terapeutas.com' },
  ]
  const now = Date.now()
  return acciones.map((a, i) => ({
    id: i + 1,
    ...a,
    ip: `192.168.1.${10 + i}`,
    timestamp: new Date(now - i * 23 * 60 * 1000).toISOString(),
  }))
}

const MOCK_LOGS = generarMock()

function formatFechaHora(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

function getTipoMeta(key) {
  return TIPOS.find(t => t.key === key) ?? { key, label: key, chipClass: 'ch-gray', color: 'var(--text3)' }
}

// ─── Página ──────────────────────────────────────────────────────────────
export default function AdminAuditoria() {
  const { authFetch } = useAuth()

  const [logs, setLogs]           = useState([])
  const [loading, setLoading]     = useState(true)
  const [busqueda, setBusqueda]   = useState('')
  const [filtroTipo, setFiltroTipo] = useState('todos')
  const [filtroRol, setFiltroRol] = useState('todos')
  const [pagina, setPagina]       = useState(1)
  const POR_PAGINA = 10

  // Backend devuelve accion="login|create|…" y tipo=recurso_tipo ("usuario", "sesion"…)
  // El frontend usa `tipo` como el tipo de acción → mapeamos accion → tipo
  function normalizeLog(l) {
    return {
      ...l,
      tipo: l.accion || l.tipo || 'create',   // accion tiene el valor correcto (login, create, etc.)
      desc: l.desc || l.accion || '',
      ip:   l.ip   || l.ip_origen || '—',
    }
  }

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/auditoria/?limit=100')
        if (res.ok) {
          const data = await res.json()
          const norm = Array.isArray(data) ? data.map(normalizeLog) : []
          setLogs(norm)
        } else {
          setLogs([])
        }
      } catch {
        setLogs(MOCK_LOGS)  // error de red → mock
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [authFetch])

  // Filtrado
  const filtrados = useMemo(() => {
    let list = [...logs]
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase()
      list = list.filter(l =>
        l.usuario?.toLowerCase().includes(q) ||
        l.desc?.toLowerCase().includes(q) ||
        l.ip?.includes(q)
      )
    }
    if (filtroTipo !== 'todos') list = list.filter(l => l.tipo === filtroTipo)
    if (filtroRol  !== 'todos') list = list.filter(l => l.rol  === filtroRol)
    return list
  }, [logs, busqueda, filtroTipo, filtroRol])

  // Paginación
  const totalPags = Math.ceil(filtrados.length / POR_PAGINA)
  const pagActual = filtrados.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA)

  function cambiarFiltro() { setPagina(1) }

  // Exportar CSV simple
  function exportarCSV() {
    const cols = ['ID', 'Fecha', 'Tipo', 'Usuario', 'Rol', 'Descripción', 'IP']
    const rows = filtrados.map(l => [
      l.id, formatFechaHora(l.timestamp), getTipoMeta(l.tipo).label,
      l.usuario, ROL_LABELS[l.rol] ?? l.rol, `"${l.desc}"`, l.ip
    ])
    const csv = [cols, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = `auditoria_${new Date().toISOString().slice(0,10)}.csv`
    a.click(); URL.revokeObjectURL(url)
  }

  // Estadísticas rápidas
  const stats = useMemo(() => ({
    logins:   logs.filter(l => l.tipo === 'login').length,
    alertas:  logs.filter(l => l.tipo === 'alert').length,
    creaciones: logs.filter(l => l.tipo === 'create').length,
    total:    logs.length,
  }), [logs])

  return (
    <div>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Auditoría del sistema</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            Registro completo de actividad · {logs.length} eventos
          </div>
        </div>
        <div className="flex ic g8">
          <button className="btn btn-s btn-sm" onClick={() => { setLoading(true); setTimeout(() => setLoading(false), 500) }}>
            <IcoRefresh /> Actualizar
          </button>
          <button className="btn btn-s btn-sm" onClick={exportarCSV}>
            <IcoDownload /> Exportar CSV
          </button>
        </div>
      </div>

      {/* ── KPIs rápidos ────────────────────────────────────────── */}
      <div className="g4 mb20">
        {[
          { label: 'Eventos totales',  value: stats.total,      color: 'var(--teal)',   bg: 'var(--teal2)' },
          { label: 'Inicios de sesión',value: stats.logins,     color: 'var(--blue)',   bg: 'var(--blue2)' },
          { label: 'Creaciones',       value: stats.creaciones, color: 'var(--purple)', bg: 'var(--purple2)' },
          { label: 'Alertas del sistema', value: stats.alertas, color: 'var(--amber)',  bg: 'var(--amber2)' },
        ].map(s => (
          <div key={s.label} className="stat">
            <div className="sn" style={{ color: s.color }}>{s.value}</div>
            <div className="sl">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Filtros ─────────────────────────────────────────────── */}
      <div className="card mb16" style={{ padding: '12px 16px' }}>
        <div className="flex ic g10" style={{ flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: '1 1 220px', minWidth: 180 }}>
            <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }}>
              <IcoSearch />
            </span>
            <input className="fi" value={busqueda}
              onChange={e => { setBusqueda(e.target.value); cambiarFiltro() }}
              placeholder="Buscar por usuario, descripción o IP…"
              style={{ paddingLeft: 32, fontSize: 13 }} />
          </div>
          <select className="fs" value={filtroTipo}
            onChange={e => { setFiltroTipo(e.target.value); cambiarFiltro() }}
            style={{ width: 'auto', minWidth: 150, fontSize: 13 }}>
            <option value="todos">Todos los tipos</option>
            {TIPOS.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
          </select>
          <select className="fs" value={filtroRol}
            onChange={e => { setFiltroRol(e.target.value); cambiarFiltro() }}
            style={{ width: 'auto', minWidth: 160, fontSize: 13 }}>
            <option value="todos">Todos los roles</option>
            {Object.entries(ROL_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          {(busqueda || filtroTipo !== 'todos' || filtroRol !== 'todos') && (
            <button className="btn btn-g btn-sm" onClick={() => { setBusqueda(''); setFiltroTipo('todos'); setFiltroRol('todos'); setPagina(1) }}>
              Limpiar filtros
            </button>
          )}
        </div>
      </div>

      {/* ── Tabla ───────────────────────────────────────────────── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando registros…</div>
        ) : filtrados.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
            <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin resultados</div>
            <div className="ts tm" style={{ marginTop: 4 }}>No hay eventos que coincidan con los filtros aplicados.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Fecha y hora', 'Tipo', 'Usuario', 'Descripción', 'IP'].map(h => (
                    <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11,
                      fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase',
                      letterSpacing: '0.06em', background: 'var(--bg)', whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pagActual.map((log, idx) => {
                  const tipo = getTipoMeta(log.tipo)
                  return (
                    <tr key={log.id} style={{
                      borderBottom: idx < pagActual.length - 1 ? '1px solid var(--border)' : 'none',
                      background: log.tipo === 'alert' ? 'rgba(186,117,23,0.04)' :
                                  log.tipo === 'delete' ? 'rgba(163,45,45,0.03)' : undefined,
                    }}>
                      <td style={{ padding: '11px 14px', fontSize: 12, color: 'var(--text3)', whiteSpace: 'nowrap' }}>
                        {formatFechaHora(log.timestamp)}
                      </td>
                      <td style={{ padding: '11px 14px' }}>
                        <span className={`chip ${tipo.chipClass}`}>{tipo.label}</span>
                      </td>
                      <td style={{ padding: '11px 14px' }}>
                        <div style={{ fontSize: 13, fontWeight: 500 }}>{log.usuario}</div>
                        <span className={`chip txs ${ROL_CHIPS[log.rol] ?? 'ch-gray'}`} style={{ marginTop: 3 }}>
                          {ROL_LABELS[log.rol] ?? log.rol}
                        </span>
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: 13, color: 'var(--text2)', maxWidth: 380 }}>
                        {log.desc}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: 12, color: 'var(--text3)', fontFamily: 'var(--font-mono, monospace)' }}>
                        {log.ip}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginación */}
        {!loading && totalPags > 1 && (
          <div className="flex ic jb" style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', background: 'var(--bg)' }}>
            <span className="txs tm">
              Mostrando {(pagina - 1) * POR_PAGINA + 1}–{Math.min(pagina * POR_PAGINA, filtrados.length)} de {filtrados.length} eventos
            </span>
            <div className="flex ic g6">
              <button className="btn btn-s btn-xs" disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>
                ← Anterior
              </button>
              {[...Array(totalPags)].map((_, i) => (
                <button key={i}
                  className={`btn btn-xs ${pagina === i + 1 ? 'btn-p' : 'btn-s'}`}
                  onClick={() => setPagina(i + 1)}>
                  {i + 1}
                </button>
              ))}
              <button className="btn btn-s btn-xs" disabled={pagina === totalPags} onClick={() => setPagina(p => p + 1)}>
                Siguiente →
              </button>
            </div>
          </div>
        )}
        {!loading && filtrados.length > 0 && totalPags <= 1 && (
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)',
            background: 'var(--bg)', fontSize: 12, color: 'var(--text3)' }}>
            {filtrados.length} eventos
          </div>
        )}
      </div>

    </div>
  )
}
