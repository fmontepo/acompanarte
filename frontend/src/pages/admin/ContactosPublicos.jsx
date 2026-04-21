// admin/ContactosPublicos.jsx
// Vista de administrador: contactos generados desde el Asistente TEA público
// Permite ver datos de contacto, el intercambio que disparó la alerta,
// y derivar o re-derivar a un terapeuta interno con nota opcional.

import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Íconos ───────────────────────────────────────────────────────────────
const IcoRefresh = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
  </svg>
)
const IcoChevron = ({ down }) => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" d={down ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"}/>
  </svg>
)
const IcoUser = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IcoPhone = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
  </svg>
)
const IcoMail = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
  </svg>
)
const IcoSend = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
  </svg>
)
const IcoX = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12"/>
  </svg>
)

// ─── Helpers ──────────────────────────────────────────────────────────────
function formatFecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

// ─── Modal de derivación ──────────────────────────────────────────────────
function ModalDerivar({ contacto, terapeutas, onDerivado, onClose }) {
  const { authFetch }   = useAuth()
  const [terapeutaId, setTerapeutaId] = useState(contacto.terapeuta?.id ?? '')
  const [nota,        setNota]        = useState(contacto.nota_derivacion ?? '')
  const [guardando,   setGuardando]   = useState(false)
  const [error,       setError]       = useState('')

  async function guardar() {
    if (!terapeutaId) { setError('Seleccioná un terapeuta.'); return }
    setError('')
    setGuardando(true)
    try {
      const res = await authFetch(`/admin/contactos/${contacto.id}/derivar`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ terapeuta_id: terapeutaId, nota: nota || null }),
      })
      if (res.ok) {
        const updated = await res.json()
        onDerivado(updated)
      } else {
        const d = await res.json().catch(() => ({}))
        setError(d.detail || 'Error al guardar.')
      }
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 16,
    }}>
      <div className="card" style={{ width: '100%', maxWidth: 480, padding: '24px 28px' }}>

        <div className="flex ic jb mb16">
          <div style={{ fontSize: 15, fontWeight: 700 }}>
            {contacto.estado === 'derivado' ? 'Reasignar contacto' : 'Derivar a terapeuta'}
          </div>
          <button className="btn btn-g btn-xs" onClick={onClose}><IcoX /></button>
        </div>

        {/* Resumen del contacto */}
        <div style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 8, padding: '10px 14px', marginBottom: 16,
          fontSize: 13,
        }}>
          <div style={{ fontWeight: 600 }}>{contacto.nombre}</div>
          {contacto.celular && (
            <div className="flex ic g6 tm" style={{ color: 'var(--text2)' }}>
              <IcoPhone /> {contacto.celular}
            </div>
          )}
          {contacto.mail && (
            <div className="flex ic g6 tm" style={{ color: 'var(--text2)' }}>
              <IcoMail /> {contacto.mail}
            </div>
          )}
        </div>

        {/* Selector de terapeuta */}
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 12, color: 'var(--text2)', display: 'block', marginBottom: 4 }}>
            Terapeuta interno <span style={{ color: 'var(--red)' }}>*</span>
          </label>
          {terapeutas.length === 0 ? (
            <div style={{ fontSize: 13, color: 'var(--text3)', padding: '8px 0' }}>
              No hay terapeutas internos activos cargados en el sistema.
            </div>
          ) : (
            <select
              className="fs"
              value={terapeutaId}
              onChange={e => setTerapeutaId(e.target.value)}
              style={{ fontSize: 13, width: '100%' }}
            >
              <option value="">— Seleccioná un terapeuta —</option>
              {terapeutas.map(t => (
                <option key={t.id} value={t.id}>
                  {t.nombre_completo} · {t.profesion}{t.especialidad ? ` (${t.especialidad})` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Nota */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 12, color: 'var(--text2)', display: 'block', marginBottom: 4 }}>
            Nota para el terapeuta <span style={{ color: 'var(--text3)' }}>(opcional)</span>
          </label>
          <textarea
            className="fi"
            value={nota}
            onChange={e => setNota(e.target.value)}
            placeholder="Contexto, urgencia, instrucciones…"
            rows={3}
            style={{ fontSize: 13, resize: 'none', width: '100%' }}
          />
        </div>

        {error && (
          <div style={{ fontSize: 12, color: 'var(--red)', marginBottom: 10 }}>{error}</div>
        )}

        <div className="flex ic g8">
          <button
            className="btn btn-p btn-sm"
            onClick={guardar}
            disabled={guardando || terapeutas.length === 0}
          >
            {guardando ? 'Guardando…' : contacto.estado === 'derivado' ? 'Reasignar' : 'Derivar'}
          </button>
          <button className="btn btn-g btn-sm" onClick={onClose}>Cancelar</button>
        </div>
      </div>
    </div>
  )
}

// ─── Fila expandible ──────────────────────────────────────────────────────
function FilaContacto({ contacto: initial, terapeutas, onActualizado }) {
  const [abierto,   setAbierto]   = useState(false)
  const [modal,     setModal]     = useState(false)
  const [contacto,  setContacto]  = useState(initial)

  useEffect(() => { setContacto(initial) }, [initial])

  function handleDerivado(updated) {
    setContacto(updated)
    setModal(false)
    onActualizado(updated)
  }

  const pendiente = contacto.estado === 'pendiente'

  return (
    <>
      {/* Fila principal */}
      <tr
        onClick={() => setAbierto(v => !v)}
        style={{
          borderBottom: abierto ? 'none' : '1px solid var(--border)',
          cursor: 'pointer',
          background: abierto ? 'var(--bg)' : undefined,
          transition: 'background 0.15s',
        }}
      >
        <td style={{ padding: '12px 14px', width: 28 }}>
          <span style={{ color: 'var(--text3)' }}>
            <IcoChevron down={!abierto} />
          </span>
        </td>
        <td style={{ padding: '12px 14px' }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{contacto.nombre}</div>
          <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>
            {formatFecha(contacto.creado_en)}
          </div>
        </td>
        <td style={{ padding: '12px 14px' }}>
          <div className="flex ic g6" style={{ fontSize: 12, color: 'var(--text2)', flexWrap: 'wrap', gap: '4px 10px' }}>
            {contacto.celular && (
              <span className="flex ic g4"><IcoPhone /> {contacto.celular}</span>
            )}
            {contacto.mail && (
              <span className="flex ic g4"><IcoMail /> {contacto.mail}</span>
            )}
            {!contacto.celular && !contacto.mail && <span style={{ color: 'var(--text3)' }}>—</span>}
          </div>
        </td>
        <td style={{ padding: '12px 14px' }}>
          <span className={`chip ${pendiente ? 'ch-am' : 'ch-teal'}`}>
            {pendiente ? 'Pendiente' : 'Derivado'}
          </span>
        </td>
        <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--text2)' }}>
          {contacto.terapeuta
            ? <span className="flex ic g6"><IcoUser /> {contacto.terapeuta.nombre_completo}</span>
            : <span style={{ color: 'var(--text3)' }}>—</span>
          }
        </td>
        <td style={{ padding: '12px 14px' }}>
          <button
            className={`btn btn-sm ${pendiente ? 'btn-p' : 'btn-s'}`}
            style={{ fontSize: 12 }}
            onClick={e => { e.stopPropagation(); setModal(true) }}
          >
            {pendiente ? 'Derivar →' : 'Reasignar'}
          </button>
        </td>
      </tr>

      {/* Detalle expandido */}
      {abierto && (
        <tr style={{ borderBottom: '1px solid var(--border)' }}>
          <td colSpan={6} style={{ padding: '0 14px 16px 42px', background: 'var(--bg)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 6 }}>

              <div style={{
                background: 'var(--bg2)', border: '1px solid var(--border)',
                borderRadius: 8, padding: '12px 14px',
              }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text3)',
                  textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                  Mensaje que activó la alerta
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.55 }}>
                  {contacto.mensaje_alerta}
                </div>
              </div>

              <div style={{
                background: 'var(--purple2)', border: '1px solid var(--border)',
                borderRadius: 8, padding: '12px 14px',
              }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--purple)',
                  textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                  Respuesta de la IA
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.55 }}>
                  {contacto.respuesta_ia}
                </div>
              </div>

              {contacto.comentario && (
                <div style={{
                  background: 'var(--bg2)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '12px 14px', gridColumn: '1 / -1',
                }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text3)',
                    textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                    Comentario del usuario
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.55 }}>
                    {contacto.comentario}
                  </div>
                </div>
              )}

              {contacto.nota_derivacion && (
                <div style={{
                  background: 'rgba(56,161,105,0.07)', border: '1px solid rgba(56,161,105,0.25)',
                  borderRadius: 8, padding: '12px 14px', gridColumn: '1 / -1',
                }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--teal)',
                    textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                    Nota de derivación · {formatFecha(contacto.derivado_en)}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.55 }}>
                    {contacto.nota_derivacion}
                  </div>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}

      {modal && (
        <ModalDerivar
          contacto={contacto}
          terapeutas={terapeutas}
          onDerivado={handleDerivado}
          onClose={() => setModal(false)}
        />
      )}
    </>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
export default function AdminContactosPublicos() {
  const { authFetch } = useAuth()

  const [contactos,   setContactos]   = useState([])
  const [terapeutas,  setTerapeutas]  = useState([])
  const [loading,     setLoading]     = useState(true)
  const [filtroEstado, setFiltroEstado] = useState('todos')

  async function cargar() {
    setLoading(true)
    try {
      const [resC, resT] = await Promise.all([
        authFetch('/admin/contactos'),
        authFetch('/admin/terapeutas-internos'),
      ])
      if (resC.ok) setContactos(await resC.json())
      if (resT.ok) setTerapeutas(await resT.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  function handleActualizado(updated) {
    setContactos(prev => prev.map(c => c.id === updated.id ? updated : c))
  }

  const filtrados = useMemo(() => {
    if (filtroEstado === 'todos') return contactos
    return contactos.filter(c => c.estado === filtroEstado)
  }, [contactos, filtroEstado])

  const stats = useMemo(() => ({
    total:    contactos.length,
    pendiente: contactos.filter(c => c.estado === 'pendiente').length,
    derivado:  contactos.filter(c => c.estado === 'derivado').length,
  }), [contactos])

  return (
    <div>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Contactos — Asistente TEA</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            Solicitudes de familias desde el chat público · {contactos.length} registros
          </div>
        </div>
        <button className="btn btn-s btn-sm" onClick={cargar}>
          <IcoRefresh /> Actualizar
        </button>
      </div>

      {/* ── KPIs ────────────────────────────────────────────────── */}
      <div className="g4 mb20" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        {[
          { label: 'Total recibidos',  value: stats.total,     color: 'var(--teal)',   bg: 'var(--teal2)' },
          { label: 'Pendientes',       value: stats.pendiente, color: 'var(--amber)',  bg: 'var(--amber2)' },
          { label: 'Derivados',        value: stats.derivado,  color: 'var(--purple)', bg: 'var(--purple2)' },
        ].map(s => (
          <div key={s.label} className="stat">
            <div className="sn" style={{ color: s.color }}>{s.value}</div>
            <div className="sl">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Filtros ─────────────────────────────────────────────── */}
      <div className="card mb16" style={{ padding: '10px 16px' }}>
        <div className="flex ic g8">
          <span style={{ fontSize: 13, color: 'var(--text2)' }}>Filtrar por estado:</span>
          {[
            { value: 'todos',     label: 'Todos' },
            { value: 'pendiente', label: 'Pendientes' },
            { value: 'derivado',  label: 'Derivados' },
          ].map(f => (
            <button
              key={f.value}
              className={`btn btn-sm ${filtroEstado === f.value ? 'btn-p' : 'btn-s'}`}
              style={{ fontSize: 12 }}
              onClick={() => setFiltroEstado(f.value)}
            >
              {f.label}
              {f.value !== 'todos' && (
                <span style={{
                  marginLeft: 5,
                  background: filtroEstado === f.value ? 'rgba(255,255,255,0.25)' : 'var(--bg3)',
                  borderRadius: 20, padding: '0 5px', fontSize: 10, fontWeight: 700,
                }}>
                  {f.value === 'pendiente' ? stats.pendiente : stats.derivado}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tabla ───────────────────────────────────────────────── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
            Cargando contactos…
          </div>
        ) : filtrados.length === 0 ? (
          <div style={{ padding: 56, textAlign: 'center', color: 'var(--text3)' }}>
            <div style={{ fontSize: 30, marginBottom: 10 }}>📬</div>
            <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
              {contactos.length === 0 ? 'Todavía no hay contactos' : 'Sin resultados para este filtro'}
            </div>
            <div className="ts">
              {contactos.length === 0
                ? 'Cuando una familia solicite ser contactada desde el asistente público, aparecerá aquí.'
                : 'Probá cambiando el filtro de estado.'
              }
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['', 'Contacto', 'Teléfono / Mail', 'Estado', 'Terapeuta asignado', 'Acción'].map(h => (
                    <th key={h} style={{
                      padding: '10px 14px', textAlign: 'left', fontSize: 11,
                      fontWeight: 600, color: 'var(--text3)',
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      background: 'var(--bg)', whiteSpace: 'nowrap',
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtrados.map(c => (
                  <FilaContacto
                    key={c.id}
                    contacto={c}
                    terapeutas={terapeutas}
                    onActualizado={handleActualizado}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && filtrados.length > 0 && (
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)',
            background: 'var(--bg)', fontSize: 12, color: 'var(--text3)' }}>
            {filtrados.length} contacto{filtrados.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

    </div>
  )
}
