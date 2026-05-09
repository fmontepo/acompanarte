// admin/Recursos.jsx
// Panel de administración de la base de conocimiento.
// El admin puede ver todos los recursos (validados y pendientes),
// validarlos para que el Asistente IA los use, desactivarlos,
// y también subir nuevos recursos directamente.

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

const TIPOS_OPCIONES = [
  { val: 'pdf',       label: 'PDF' },
  { val: 'articulo',  label: 'Artículo' },
  { val: 'guia',      label: 'Guía' },
  { val: 'protocolo', label: 'Protocolo' },
]

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
const IcoPlus = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" d="M12 5v14M5 12h14"/>
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

// ─── Modal nuevo recurso ─────────────────────────────────────────────────
const FORM_EMPTY = { titulo: '', tipo: 'pdf', descripcion: '', contenido_texto: '', url_storage: '' }

function ModalNuevoRecurso({ onClose, onGuardado }) {
  const { authFetch } = useAuth()
  const [form, setForm]     = useState(FORM_EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  function set(k, v) { setForm(p => ({ ...p, [k]: v })) }

  async function handleGuardar(e) {
    e.preventDefault()
    if (!form.titulo.trim()) { setError('El título es obligatorio.'); return }
    setSaving(true)
    setError('')
    try {
      const res = await authFetch('/recursos/', {
        method: 'POST',
        body: JSON.stringify({
          titulo:          form.titulo.trim(),
          tipo:            form.tipo,
          descripcion:     form.descripcion.trim() || null,
          contenido_texto: form.contenido_texto.trim() || null,
          url_storage:     form.url_storage.trim() || null,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        onGuardado(normalizeRecurso(data))
        onClose()
      } else {
        const err = await res.json().catch(() => ({}))
        setError(err?.detail ?? 'Error al guardar el recurso.')
      }
    } catch {
      setError('Error de conexión. Intentá de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo" style={{ maxWidth: 540 }}>
        <div className="mh">
          <div className="mt">Nuevo recurso</div>
          <button className="btn btn-g btn-sm" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleGuardar}>
          <div className="mb" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label className="fl">Título <span style={{ color: 'var(--red)' }}>*</span></label>
              <input className="fi" value={form.titulo} onChange={e => set('titulo', e.target.value)}
                placeholder="Ej: Guía de intervención temprana TEA" />
            </div>
            <div>
              <label className="fl">Tipo</label>
              <select className="fi" value={form.tipo} onChange={e => set('tipo', e.target.value)}>
                {TIPOS_OPCIONES.map(t => <option key={t.val} value={t.val}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="fl">Descripción <span className="tm">(opcional)</span></label>
              <textarea className="fi" rows={2} value={form.descripcion}
                onChange={e => set('descripcion', e.target.value)}
                placeholder="Breve descripción del contenido…" />
            </div>
            <div>
              <label className="fl">
                Contenido del recurso{' '}
                <span className="tm">(texto para el Asistente IA)</span>
              </label>
              <textarea className="fi" rows={5} value={form.contenido_texto}
                onChange={e => set('contenido_texto', e.target.value)}
                placeholder="Pegá aquí el texto del documento. Al validar el recurso, se usará para el Asistente IA." />
              <div className="ts tm" style={{ marginTop: 4 }}>
                Al validar el recurso, se generará automáticamente el embedding para RAG.
              </div>
            </div>
            <div>
              <label className="fl">URL del recurso <span className="tm">(opcional)</span></label>
              <input className="fi" value={form.url_storage} onChange={e => set('url_storage', e.target.value)}
                placeholder="https://…" />
            </div>
            {error && <div className="disc disc-rd ts">{error}</div>}
            <div className="disc disc-tl ts" style={{ marginTop: 0 }}>
              El recurso quedará como <strong>pendiente de validación</strong>.
              Podés validarlo desde esta misma pantalla.
            </div>
          </div>
          <div className="mf">
            <button type="button" className="btn btn-s btn-sm" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p btn-sm" disabled={saving}>
              {saving ? 'Guardando…' : 'Agregar recurso'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────
export default function AdminRecursos() {
  const { authFetch } = useAuth()
  const [recursos, setRecursos]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [apiError, setApiError]   = useState('')      // error persistente de carga
  const [filtro, setFiltro]       = useState('todos') // todos | validados | pendientes
  const [busqueda, setBusqueda]   = useState('')
  const [expandido, setExpandido] = useState(null)
  const [verContenido, setVerContenido]   = useState(null)
  const [modalNuevo, setModalNuevo]       = useState(false)
  const [validando, setValidando]         = useState(null)
  const [desactivando, setDesactivando]   = useState(null)
  const [toast, setToast] = useState({ msg: '', ok: true })

  function showToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 3500)
  }

  async function cargar() {
    setLoading(true)
    setApiError('')
    try {
      const res = await authFetch('/recursos/?solo_validados=false')
      if (res.ok) {
        const data = await res.json()
        setRecursos(Array.isArray(data) ? data.map(normalizeRecurso) : [])
      } else {
        const err = await res.json().catch(() => ({}))
        setApiError(err?.detail ?? `Error del servidor (${res.status}). Intentá recargar.`)
        setRecursos([])
      }
    } catch {
      setApiError('No se pudo conectar con el servidor. Verificá la conexión e intentá de nuevo.')
      setRecursos([])
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

  function onRecursoAgregado(recurso) {
    setRecursos(prev => [recurso, ...prev])
    showToast('Recurso agregado. Podés validarlo desde esta pantalla.')
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
            {loading ? 'Cargando…' : apiError ? (
              <span style={{ color: 'var(--red)' }}>Error al cargar</span>
            ) : (
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
        <div className="flex ic g8">
          <button className="btn btn-s btn-sm" onClick={cargar} disabled={loading}>
            ↺ Actualizar
          </button>
          <button
            className="btn btn-p btn-sm flex ic g6"
            onClick={() => setModalNuevo(true)}
          >
            <IcoPlus /> Nuevo recurso
          </button>
        </div>
      </div>

      {/* Error persistente */}
      {apiError && (
        <div className="disc disc-rd" style={{ marginBottom: 20 }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>No se pudieron cargar los recursos</div>
          <div className="ts">{apiError}</div>
          <button className="btn btn-s btn-sm" style={{ marginTop: 10 }} onClick={cargar}>
            Reintentar
          </button>
        </div>
      )}

      {/* Resumen rápido */}
      {!loading && !apiError && (
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

      {/* Buscador + Filtros — siempre visibles */}
      {!apiError && (
        <>
          <div style={{ position: 'relative', marginBottom: 12 }}>
            <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }}>
              <IcoSearch />
            </span>
            <input className="fi" value={busqueda} onChange={e => setBusqueda(e.target.value)}
              placeholder="Buscar por título o descripción…" style={{ paddingLeft: 34 }} />
          </div>

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
        </>
      )}

      {/* Lista / estados */}
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      ) : apiError ? null : filtrados.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📚</div>
          {total === 0 ? (
            <>
              <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
                No hay recursos en la base de conocimiento
              </div>
              <div className="ts" style={{ marginBottom: 16, maxWidth: 360, margin: '0 auto 16px' }}>
                Los terapeutas pueden subir recursos desde su panel de Conocimiento.
                También podés agregar recursos directamente desde acá.
              </div>
              <button className="btn btn-p btn-sm flex ic g6" style={{ margin: '0 auto' }}
                onClick={() => setModalNuevo(true)}>
                <IcoPlus /> Agregar primer recurso
              </button>
            </>
          ) : (
            <>
              <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin resultados</div>
              <div className="ts tm" style={{ marginTop: 4 }}>No hay recursos con el filtro seleccionado.</div>
            </>
          )}
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
      {modalNuevo   && <ModalNuevoRecurso onClose={() => setModalNuevo(false)} onGuardado={onRecursoAgregado} />}
    </div>
  )
}
