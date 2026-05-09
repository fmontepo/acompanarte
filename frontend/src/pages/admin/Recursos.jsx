// admin/Recursos.jsx
// Panel de administración de la base de conocimiento.
// El admin puede ver todos los recursos (validados y pendientes),
// validarlos para que el Asistente IA los use, y desactivarlos.

import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

const TIPO_LABEL = {
  pdf:       'PDF',
  articulo:  'Artículo',
  guia:      'Guía',
  protocolo: 'Protocolo',
}

const CAT_COLORS = {
  PDF:       'ch-rd',
  Artículo:  'ch-blu',
  Guía:      'ch-teal',
  Protocolo: 'ch-pp',
}

function normalizeRecurso(r) {
  const categoria = TIPO_LABEL[r.tipo] ?? r.tipo ?? 'Recurso'
  const fecha = r.subido_en
    ? new Date(r.subido_en).toLocaleDateString('es-AR', { year: 'numeric', month: '2-digit', day: '2-digit' })
    : '—'
  return {
    id:              r.id,
    titulo:          r.titulo,
    categoria,
    resumen:         r.descripcion || '',
    contenido_texto: r.contenido_texto || '',
    fecha,
    validado:        r.validado ?? false,
    url:             r.url_storage ?? null,
  }
}

// ─── Íconos ───────────────────────────────────────────────────────────────
const IcoStar = () => (
  <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
)
const IcoTrash = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
  </svg>
)
const IcoBook = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
  </svg>
)
const IcoSearch = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="M21 21l-4.35-4.35"/>
  </svg>
)

// ─── Modal contenido ─────────────────────────────────────────────────────
function ModalContenido({ recurso, onClose }) {
  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo" style={{ maxWidth: 640 }}>
        <div className="mh">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <IcoBook />
            <div className="mt" style={{ fontSize: 15 }}>{recurso.titulo}</div>
          </div>
          <button className="btn btn-g btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="mb" style={{ maxHeight: '65vh', overflowY: 'auto' }}>
          {recurso.contenido_texto ? (
            <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text)', whiteSpace: 'pre-wrap' }}>
              {recurso.contenido_texto}
            </div>
          ) : (
            <div className="disc disc-tl txs" style={{ textAlign: 'center', padding: '32px 0' }}>
              Este recurso no tiene contenido de texto cargado.
            </div>
          )}
        </div>
        <div className="mf">
          {recurso.url && (
            <a href={recurso.url} target="_blank" rel="noopener noreferrer" className="btn btn-s btn-sm">
              Ver recurso externo →
            </a>
          )}
          <button className="btn btn-p btn-sm" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────
export default function AdminRecursos() {
  const { authFetch } = useAuth()
  const [recursos, setRecursos]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [filtro, setFiltro]       = useState('todos')   // todos | validados | pendientes
  const [busqueda, setBusqueda]   = useState('')
  const [expandido, setExpandido] = useState(null)
  const [verContenido, setVerContenido] = useState(null)
  const [validando, setValidando] = useState(null)
  const [desactivando, setDesactivando] = useState(null)
  const [toast, setToast]         = useState({ msg: '', ok: true })

  function showToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 3000)
  }

  async function cargar() {
    setLoading(true)
    try {
      const res = await authFetch('/recursos/?solo_validados=false')
      if (res.ok) {
        const data = await res.json()
        setRecursos(Array.isArray(data) ? data.map(normalizeRecurso) : [])
      } else {
        setRecursos([])
      }
    } catch {
      setRecursos([])
      showToast('Error al cargar los recursos.', false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  async function handleValidar(id, e) {
    e.stopPropagation()
    setValidando(id)
    const recurso = recursos.find(r => r.id === id)
    const tieneContenido = !!(recurso?.contenido_texto)
    try {
      const res = await authFetch(`/recursos/${id}/validar`, { method: 'POST' })
      if (res.ok) {
        setRecursos(prev => prev.map(r => r.id === id ? { ...r, validado: true } : r))
        showToast(
          tieneContenido
            ? 'Recurso validado. El embedding se está generando en segundo plano.'
            : 'Recurso validado y disponible para el equipo.'
        )
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err?.detail ?? 'Error al validar el recurso.', false)
      }
    } catch {
      showToast('Error de conexión.', false)
    } finally {
      setValidando(null)
    }
  }

  async function handleDesactivar(id, e) {
    e.stopPropagation()
    if (!window.confirm('¿Desactivar este recurso? Dejará de estar disponible para el Asistente IA.')) return
    setDesactivando(id)
    try {
      const res = await authFetch(`/recursos/${id}`, { method: 'DELETE' })
      if (res.ok || res.status === 204) {
        setRecursos(prev => prev.filter(r => r.id !== id))
        showToast('Recurso desactivado.')
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err?.detail ?? 'Error al desactivar.', false)
      }
    } catch {
      showToast('Error de conexión.', false)
    } finally {
      setDesactivando(null)
    }
  }

  const total     = recursos.length
  const validados = recursos.filter(r => r.validado).length
  const pendientes = total - validados

  const filtrados = recursos.filter(r => {
    const q = busqueda.toLowerCase()
    const matchQ = !q || r.titulo.toLowerCase().includes(q) || r.resumen.toLowerCase().includes(q)
    const matchF = filtro === 'todos' || (filtro === 'validados' ? r.validado : !r.validado)
    return matchQ && matchF
  })

  return (
    <div>
      <div className={`toast ${toast.msg ? 'visible' : ''} ${!toast.ok ? 'error' : ''}`}>{toast.msg}</div>

      {/* Header */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Base de conocimiento</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {loading ? 'Cargando…' : (
              <>
                {total} recursos · {validados} validados
                {pendientes > 0 && (
                  <span style={{ color: 'var(--amber)', marginLeft: 6 }}>
                    · {pendientes} pendiente{pendientes !== 1 ? 's' : ''}
                  </span>
                )}
              </>
            )}
          </div>
        </div>
        <button className="btn btn-s btn-sm" onClick={cargar}>↺ Actualizar</button>
      </div>

      {/* Resumen rápido */}
      {!loading && (
        <div className="flex g10 mb20" style={{ flexWrap: 'wrap' }}>
          {[
            { label: 'Total',      val: total,     color: 'var(--text)' },
            { label: 'Validados',  val: validados,  color: 'var(--teal)' },
            { label: 'Pendientes', val: pendientes, color: 'var(--amber)' },
          ].map(s => (
            <div key={s.label} className="card" style={{ padding: '10px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.val}</div>
              <div className="txs" style={{ color: 'var(--text2)' }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Buscador */}
      <div style={{ position: 'relative', marginBottom: 12 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }}>
          <IcoSearch />
        </span>
        <input className="fi" value={busqueda} onChange={e => setBusqueda(e.target.value)}
          placeholder="Buscar por título o descripción…" style={{ paddingLeft: 34 }} />
      </div>

      {/* Filtros */}
      <div className="flex ic g8 mb20" style={{ flexWrap: 'wrap' }}>
        {[
          { val: 'todos',      label: `Todos (${total})` },
          { val: 'pendientes', label: `Pendientes (${pendientes})` },
          { val: 'validados',  label: `Validados (${validados})` },
        ].map(f => (
          <button key={f.val} className={`btn btn-sm ${filtro === f.val ? 'btn-p' : 'btn-s'}`}
            onClick={() => setFiltro(f.val)}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Lista */}
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      ) : filtrados.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📚</div>
          <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin recursos</div>
          <div className="ts tm" style={{ marginTop: 4 }}>No hay recursos con el filtro seleccionado.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtrados.map(r => (
            <div key={r.id} className="card"
              style={{
                borderLeft: `4px solid ${r.validado ? 'var(--teal)' : 'var(--amber)'}`,
                borderRadius: '0 var(--radius) var(--radius) 0',
              }}>
              <div className="flex ic jb">
                <div className="flex ic g10" style={{ flex: 1, minWidth: 0 }}>
                  {/* Botón ver contenido */}
                  <button
                    onClick={() => setVerContenido(r)}
                    title={r.contenido_texto ? 'Ver contenido del recurso' : 'Sin contenido de texto'}
                    style={{
                      width: 34, height: 34, borderRadius: 8, border: 'none', cursor: 'pointer',
                      background: r.validado ? 'var(--teal2)' : 'var(--bg2)',
                      color: r.validado ? 'var(--teal)' : 'var(--text3)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                    <IcoBook />
                  </button>

                  <div style={{ minWidth: 0 }}>
                    <div className="flex ic g6" style={{ fontSize: 14, fontWeight: 600 }}>
                      {r.validado && (
                        <span style={{ color: 'var(--amber)', flexShrink: 0 }} title="Recurso validado">
                          <IcoStar />
                        </span>
                      )}
                      <span>{r.titulo}</span>
                    </div>
                    <div className="flex ic g6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                      <span className={`chip ${CAT_COLORS[r.categoria] ?? 'ch-gray'}`}>{r.categoria}</span>
                      {r.validado
                        ? <span className="chip ch-teal">Validado</span>
                        : <span className="chip ch-am">Pendiente validación</span>
                      }
                      <span className="txs tm">{r.fecha}</span>
                    </div>
                  </div>
                </div>

                {/* Acciones */}
                <div className="flex ic g6" style={{ flexShrink: 0, marginLeft: 8 }}>
                  {!r.validado && (
                    <button
                      className="btn btn-sm"
                      style={{ background: 'var(--teal)', color: '#fff', border: 'none' }}
                      disabled={validando === r.id}
                      onClick={e => handleValidar(r.id, e)}
                      title="Validar recurso para el Asistente IA">
                      {validando === r.id ? 'Validando…' : '✓ Validar'}
                    </button>
                  )}
                  <button
                    className="btn btn-s btn-sm"
                    style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
                    disabled={desactivando === r.id}
                    onClick={e => handleDesactivar(r.id, e)}
                    title="Desactivar recurso">
                    <IcoTrash />
                  </button>
                  <button
                    style={{ background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--text3)', fontSize: 20, lineHeight: 1, padding: '0 4px' }}
                    onClick={() => setExpandido(expandido === r.id ? null : r.id)}
                    title={expandido === r.id ? 'Ocultar descripción' : 'Ver descripción'}>
                    {expandido === r.id ? '−' : '+'}
                  </button>
                </div>
              </div>

              {expandido === r.id && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                  <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55 }}>
                    {r.resumen || <span style={{ color: 'var(--text3)', fontStyle: 'italic' }}>Sin descripción.</span>}
                  </div>
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noopener noreferrer"
                      className="btn btn-s btn-sm" style={{ display: 'inline-block', marginTop: 10 }}>
                      Ver recurso externo →
                    </a>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {verContenido && <ModalContenido recurso={verContenido} onClose={() => setVerContenido(null)} />}
    </div>
  )
}
