import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

const MOCK = [
  { id: 1, titulo: 'Técnicas de redirección en TEA', categoria: 'Guía', resumen: 'Estrategias basadas en evidencia para manejar episodios de agitación.', tags: [], fecha: '2025-11', destacado: true, url: null, validado: true },
  { id: 2, titulo: 'Comunicación efectiva con el familiar cuidador', categoria: 'Artículo', resumen: 'Guía para establecer comunicación clara y empática con los familiares.', tags: [], fecha: '2025-10', destacado: true, url: null, validado: true },
  { id: 3, titulo: 'Ejercicios cognitivos adaptados por nivel', categoria: 'Guía', resumen: 'Banco de actividades cognitivas clasificadas por nivel de soporte.', tags: [], fecha: '2025-09', destacado: false, url: null, validado: false },
]

const TIPO_LABEL = {
  pdf:       'PDF',
  articulo:  'Artículo',
  guia:      'Guía',
  protocolo: 'Protocolo',
}

const TIPO_OPCIONES = [
  { value: 'guia',      label: 'Guía clínica' },
  { value: 'articulo',  label: 'Artículo' },
  { value: 'protocolo', label: 'Protocolo' },
  { value: 'pdf',       label: 'PDF / Documento' },
]

const CAT_COLORS = {
  PDF:       'ch-rd',
  Artículo:  'ch-blu',
  Guía:      'ch-teal',
  Protocolo: 'ch-pp',
}

function normalizeRecurso(r) {
  const categoria = TIPO_LABEL[r.tipo] ?? r.tipo ?? 'Recurso'
  const fecha = r.subido_en
    ? new Date(r.subido_en).toLocaleDateString('es-AR', { year: 'numeric', month: '2-digit' }).split('/').reverse().join('-')
    : '—'
  return {
    id:              r.id,
    titulo:          r.titulo,
    categoria,
    resumen:         r.descripcion || '',
    contenido_texto: r.contenido_texto || '',
    tags:            [],
    fecha,
    destacado:       r.validado ?? false,
    validado:        r.validado ?? false,
    url:             r.url_storage ?? null,
  }
}

// ─── Íconos ───────────────────────────────────────────────────────────────
const IcoSearch = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="M21 21l-4.35-4.35"/>
  </svg>
)
const IcoBook = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
  </svg>
)
const IcoStar = () => (
  <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
)

// ─── Modal nuevo recurso ──────────────────────────────────────────────────
function ModalNuevoRecurso({ onClose, onSave }) {
  const [form, setForm] = useState({
    titulo: '', descripcion: '', tipo: 'guia',
    url_storage: '', contenido_texto: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  function set(field, value) {
    setForm(f => ({ ...f, [field]: value }))
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.titulo.trim()) { setError('El título es obligatorio.'); return }
    setSaving(true)
    await onSave({
      titulo:          form.titulo.trim(),
      descripcion:     form.descripcion.trim() || null,
      tipo:            form.tipo,
      url_storage:     form.url_storage.trim() || null,
      contenido_texto: form.contenido_texto.trim() || null,
    })
    setSaving(false)
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">Nuevo recurso</div>
          <button className="btn btn-g btn-sm" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb">
            <div className="fg">
              <label className="fl">Título *</label>
              <input className="fi" value={form.titulo}
                onChange={e => set('titulo', e.target.value)}
                placeholder="Ej: Guía de intervención en crisis conductual" />
            </div>
            <div className="fg">
              <label className="fl">Tipo de material</label>
              <select className="fs" value={form.tipo} onChange={e => set('tipo', e.target.value)}>
                {TIPO_OPCIONES.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div className="fg">
              <label className="fl">Descripción <span className="tm">(breve resumen)</span></label>
              <textarea className="fi fta" rows={2} value={form.descripcion}
                onChange={e => set('descripcion', e.target.value)}
                placeholder="Breve descripción del contenido y su utilidad clínica…" />
            </div>
            <div className="fg">
              <label className="fl">
                Contenido del recurso{' '}
                <span className="tm">(texto para el Asistente IA)</span>
              </label>
              <textarea className="fi fta" rows={5} value={form.contenido_texto}
                onChange={e => set('contenido_texto', e.target.value)}
                placeholder="Pegá aquí el texto del artículo, guía o protocolo. Este contenido genera el embedding que permite al Asistente IA responder consultas basándose en este material…" />
              <div className="txs tm" style={{ marginTop: 4 }}>
                Al validar el recurso, se generará automáticamente el embedding para RAG.
              </div>
            </div>
            <div className="fg">
              <label className="fl">URL del recurso <span className="tm">(opcional)</span></label>
              <input className="fi" value={form.url_storage}
                onChange={e => set('url_storage', e.target.value)}
                placeholder="https://… o ruta interna al archivo" />
            </div>
            <div className="disc disc-tl txs">
              El material quedará como <strong>pendiente de validación</strong> hasta que un terapeuta interno lo apruebe. Solo los recursos validados alimentan el Asistente IA.
            </div>
            {error && <div className="disc disc-rd txs">{error}</div>}
          </div>
          <div className="mf">
            <button type="button" className="btn btn-s" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving || !form.titulo.trim()}>
              {saving ? 'Guardando…' : 'Agregar recurso'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Modal lector de contenido_texto ─────────────────────────────────────
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
            <div style={{
              fontSize: 13, lineHeight: 1.7, color: 'var(--text)',
              whiteSpace: 'pre-wrap', fontFamily: 'inherit',
            }}>
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
            <a href={recurso.url} target="_blank" rel="noopener noreferrer"
              className="btn btn-s btn-sm">
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
export default function TerIntConocimiento() {
  const { authFetch } = useAuth()
  const [articulos, setArticulos]     = useState([])
  const [loading, setLoading]         = useState(true)
  const [busqueda, setBusqueda]       = useState('')
  const [cat, setCat]                 = useState('Todas')
  const [expandido, setExpandido]     = useState(null)
  const [modal, setModal]             = useState(false)
  const [verContenido, setVerContenido] = useState(null)  // recurso cuyo texto se muestra
  const [toast, setToast]             = useState({ msg: '', ok: true })
  const [validando, setValidando]     = useState(null)   // id del recurso que se está validando

  function showToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 2800)
  }

  // ── Carga inicial ────────────────────────────────────────────────────
  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/recursos/?solo_validados=false')
        if (res.ok) {
          const data = await res.json()
          setArticulos(Array.isArray(data) ? data.map(normalizeRecurso) : [])
        } else {
          setArticulos([])
        }
      } catch {
        setArticulos(MOCK)
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [authFetch])

  // ── Crear nuevo recurso ──────────────────────────────────────────────
  async function handleSave(formData) {
    try {
      const res = await authFetch('/recursos/', {
        method: 'POST',
        body: JSON.stringify(formData),
      })
      if (res.ok) {
        const data = await res.json()
        const nuevo = normalizeRecurso(data)
        setArticulos(prev => [nuevo, ...prev])
        setModal(false)
        showToast('Recurso agregado. Pendiente de validación.')
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err?.detail ?? 'Error al guardar el recurso.', false)
        setModal(false)
      }
    } catch {
      // Fallback local si no hay conexión
      const local = {
        id:        Date.now(),
        titulo:    formData.titulo,
        categoria: TIPO_LABEL[formData.tipo] ?? 'Recurso',
        resumen:   formData.descripcion ?? '',
        tags:      [],
        fecha:     new Date().toLocaleDateString('es-AR', { year: 'numeric', month: '2-digit' }).split('/').reverse().join('-'),
        destacado: false,
        validado:  false,
        url:       formData.url_storage ?? null,
      }
      setArticulos(prev => [local, ...prev])
      setModal(false)
      showToast('Sin conexión. Guardado localmente.', false)
    }
  }

  // ── Validar recurso ──────────────────────────────────────────────────
  async function handleValidar(id, e) {
    e.stopPropagation()
    setValidando(id)
    const recurso = articulos.find(a => a.id === id)
    const tieneContenido = !!(recurso?.contenido_texto)
    try {
      const res = await authFetch(`/recursos/${id}/validar`, { method: 'POST' })
      if (res.ok) {
        setArticulos(prev => prev.map(a =>
          a.id === id ? { ...a, validado: true, destacado: true } : a
        ))
        // Si el recurso tenía texto, el embedding se genera en background (~30 s)
        showToast(
          tieneContenido
            ? 'Recurso validado. El embedding para el Asistente IA se está generando en segundo plano.'
            : 'Recurso validado y disponible para el equipo.'
        )
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err?.detail ?? 'Error al validar el recurso.', false)
      }
    } catch {
      showToast('Error de conexión al intentar validar.', false)
    } finally {
      setValidando(null)
    }
  }

  const categorias = ['Todas', ...new Set(articulos.map(a => a.categoria))]
  const pendientes = articulos.filter(a => !a.validado).length

  const filtrados = articulos.filter(a => {
    const q = busqueda.toLowerCase()
    const matchQ = !q || a.titulo.toLowerCase().includes(q) || a.resumen.toLowerCase().includes(q)
    const matchC = cat === 'Todas' || a.categoria === cat
    return matchQ && matchC
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
                {articulos.length} recursos
                {pendientes > 0 && (
                  <span style={{ color: 'var(--amber)', marginLeft: 6 }}>
                    · {pendientes} pendiente{pendientes > 1 ? 's' : ''} de validación
                  </span>
                )}
              </>
            )}
          </div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => setModal(true)}>
          + Nuevo recurso
        </button>
      </div>

      {/* Buscador */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }}>
          <IcoSearch />
        </span>
        <input className="fi" value={busqueda} onChange={e => setBusqueda(e.target.value)}
          placeholder="Buscar por título o descripción…" style={{ paddingLeft: 34 }} />
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      ) : (
        <>
          {/* Filtros por tipo */}
          <div className="flex ic g8 mb20" style={{ flexWrap: 'wrap' }}>
            {categorias.map(c => (
              <button key={c} className={`btn btn-sm ${cat === c ? 'btn-p' : 'btn-s'}`} onClick={() => setCat(c)}>
                {c}
              </button>
            ))}
          </div>

          {/* Destacados (validados) */}
          {cat === 'Todas' && !busqueda && articulos.some(a => a.destacado) && (
            <div className="mb20">
              <div className="ts f6 mb12 flex ic g6" style={{ color: 'var(--amber)' }}>
                <IcoStar /> Recursos validados
              </div>
              <div className="g2">
                {articulos.filter(a => a.destacado).map(a => (
                  <div key={a.id} className="card"
                    style={{ background: 'var(--amber2)', border: '1px solid #f0cb8a', cursor: 'pointer' }}
                    onClick={() => setExpandido(expandido === a.id ? null : a.id)}>
                    <div className="flex ic jb mb8">
                      <span className={`chip ${CAT_COLORS[a.categoria] ?? 'ch-gray'}`}>{a.categoria}</span>
                      <span className="txs tm">{a.fecha}</span>
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>{a.titulo}</div>
                    {expandido === a.id && (
                      <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55, marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(0,0,0,0.08)' }}>
                        {a.resumen || <span style={{ color: 'var(--text3)', fontStyle: 'italic' }}>Sin descripción.</span>}
                        {a.url && (
                          <a href={a.url} target="_blank" rel="noopener noreferrer"
                            className="btn btn-s btn-sm" style={{ display: 'inline-block', marginTop: 10 }}
                            onClick={e => e.stopPropagation()}>
                            Ver recurso →
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lista completa */}
          {filtrados.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
              <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin resultados</div>
              <div className="ts tm" style={{ marginTop: 4 }}>Probá con otros términos de búsqueda.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {filtrados.map(a => (
                <div key={a.id} className="card" style={{ transition: 'box-shadow 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.boxShadow = ''}>

                  <div className="flex ic jb">
                    <div className="flex ic g10" style={{ flex: 1, minWidth: 0 }}>
                      {/* Ícono libro — abre el contenido_texto */}
                      <button
                        onClick={() => setVerContenido(a)}
                        title={a.contenido_texto ? 'Ver contenido del recurso' : 'Sin contenido de texto cargado'}
                        style={{
                          width: 34, height: 34, borderRadius: 8, border: 'none', cursor: 'pointer',
                          background: a.validado ? 'var(--purple2)' : 'var(--bg2)',
                          color: a.validado ? 'var(--purple)' : 'var(--text3)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                          transition: 'opacity 0.15s',
                        }}
                        onMouseEnter={e => e.currentTarget.style.opacity = '0.75'}
                        onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                      >
                        <IcoBook />
                      </button>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{a.titulo}</div>
                        <div className="flex ic g6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                          <span className={`chip ${CAT_COLORS[a.categoria] ?? 'ch-gray'}`}>{a.categoria}</span>
                          {a.validado
                            ? <span className="chip ch-teal">Validado</span>
                            : <span className="chip ch-am">Pendiente validación</span>
                          }
                        </div>
                      </div>
                    </div>
                    <div className="flex ic g8" style={{ flexShrink: 0, marginLeft: 8 }}>
                      {!a.validado && (
                        <button
                          className="btn btn-s btn-sm"
                          disabled={validando === a.id}
                          onClick={e => handleValidar(a.id, e)}
                          title="Marcar como validado para que el Asistente IA lo use">
                          {validando === a.id ? 'Validando…' : 'Validar'}
                        </button>
                      )}
                      {/* Botón + — expande la descripción */}
                      <button
                        style={{ background: 'none', border: 'none', cursor: 'pointer',
                          color: 'var(--text3)', fontSize: 20, lineHeight: 1, padding: '0 2px' }}
                        onClick={() => setExpandido(expandido === a.id ? null : a.id)}
                        title={expandido === a.id ? 'Ocultar descripción' : 'Ver descripción'}
                      >
                        {expandido === a.id ? '−' : '+'}
                      </button>
                    </div>
                  </div>

                  {expandido === a.id && (
                    <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55, marginTop: 12,
                      paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                      {a.resumen || <span style={{ color: 'var(--text3)', fontStyle: 'italic' }}>Sin descripción.</span>}
                      {a.url && (
                        <a href={a.url} target="_blank" rel="noopener noreferrer"
                          className="btn btn-s btn-sm" style={{ display: 'inline-block', marginTop: 10 }}>
                          Ver recurso →
                        </a>
                      )}
                      <div className="txs tm" style={{ marginTop: 8 }}>Subido: {a.fecha}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {modal && <ModalNuevoRecurso onClose={() => setModal(false)} onSave={handleSave} />}
      {verContenido && <ModalContenido recurso={verContenido} onClose={() => setVerContenido(null)} />}
    </div>
  )
}
