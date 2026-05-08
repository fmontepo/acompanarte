// terapeuta/interno/ContactosDerivados.jsx
// Vista del terapeuta interno: contactos TEA derivados a él/ella por el admin.
// Permite "Atender" (crea usuario familiar inactivo) o "No Atender" cada contacto.

import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

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
const IcoCheck = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M5 13l4 4L19 7"/>
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

const ESTADO_CONFIG = {
  derivado:    { label: 'Pendiente',    bg: 'rgba(245,158,11,0.12)', color: '#b45309' },
  atendido:    { label: 'Atendido',     bg: 'rgba(16,185,129,0.12)', color: '#047857' },
  no_atendido: { label: 'No atendido',  bg: 'rgba(239,68,68,0.12)',  color: '#b91c1c' },
}

function EstadoBadge({ estado }) {
  const cfg = ESTADO_CONFIG[estado] ?? { label: estado, bg: 'var(--bg2)', color: 'var(--text)' }
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, padding: '2px 8px',
      borderRadius: 20, background: cfg.bg, color: cfg.color,
      display: 'inline-block',
    }}>{cfg.label}</span>
  )
}

// ─── Modal Atender ────────────────────────────────────────────────────────
function ModalAtender({ contacto, onAtendido, onClose }) {
  const { authFetch } = useAuth()
  // Pre-rellenar con los datos del contacto
  const [nombre,   setNombre]   = useState(contacto.nombre ?? '')
  const [apellido, setApellido] = useState('')
  const [email,    setEmail]    = useState(contacto.mail ?? '')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  async function confirmar() {
    if (!nombre.trim()) { setError('El nombre es obligatorio'); return }
    if (!email.trim())  { setError('El email es obligatorio'); return }
    setLoading(true); setError('')
    try {
      const res = await authFetch(`/ter-int/contactos/${contacto.id}/atender`, {
        method: 'POST',
        body: JSON.stringify({ nombre: nombre.trim(), apellido: apellido.trim() || null, email: email.trim().toLowerCase() }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Error al atender el contacto')
      onAtendido(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 16,
    }}>
      <div className="card" style={{ width: '100%', maxWidth: 440, padding: '24px 28px' }}>
        {/* Header */}
        <div className="flex ic g10 mb20" style={{ justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>Atender contacto</div>
            <div className="txs" style={{ color: 'var(--text2)', marginTop: 2 }}>
              Creá el usuario familiar con los datos del contacto
            </div>
          </div>
          <button className="btn btn-g btn-sm" onClick={onClose} style={{ flexShrink: 0 }}>
            <IcoX />
          </button>
        </div>

        {/* Contexto del contacto */}
        <div style={{
          background: 'var(--bg2)', border: '1px solid var(--border)',
          borderRadius: 8, padding: '10px 14px', marginBottom: 18,
        }}>
          <div className="txs" style={{ color: 'var(--text2)', marginBottom: 4 }}>Contacto TEA derivado</div>
          {contacto.celular && (
            <div className="flex ic g6 txs" style={{ color: 'var(--text)', marginBottom: 2 }}>
              <IcoPhone /> {contacto.celular}
            </div>
          )}
          {contacto.mail && (
            <div className="flex ic g6 txs" style={{ color: 'var(--text)', marginBottom: 2 }}>
              <IcoMail /> {contacto.mail}
            </div>
          )}
          {contacto.comentario && (
            <div className="txs" style={{ color: 'var(--text2)', marginTop: 4, fontStyle: 'italic' }}>
              "{contacto.comentario}"
            </div>
          )}
        </div>

        {/* Formulario */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label className="label">Nombre *</label>
            <input className="fi" value={nombre} onChange={e => setNombre(e.target.value)}
              placeholder="Nombre del familiar" />
          </div>
          <div>
            <label className="label">Apellido</label>
            <input className="fi" value={apellido} onChange={e => setApellido(e.target.value)}
              placeholder="Apellido (opcional)" />
          </div>
          <div>
            <label className="label">Email *</label>
            <input className="fi" type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="correo@ejemplo.com" />
          </div>
        </div>

        {error && (
          <div style={{ marginTop: 12, padding: '8px 12px', borderRadius: 8,
            background: 'rgba(239,68,68,0.08)', color: 'var(--danger)', fontSize: 13 }}>
            {error}
          </div>
        )}

        <div className="flex g8 mt20" style={{ justifyContent: 'flex-end' }}>
          <button className="btn btn-g btn-sm" onClick={onClose} disabled={loading}>Cancelar</button>
          <button className="btn btn-p btn-sm" onClick={confirmar} disabled={loading}>
            {loading ? 'Creando...' : 'Crear usuario familiar'}
          </button>
        </div>

        <div className="txs mt12" style={{ color: 'var(--text3)', textAlign: 'center' }}>
          El usuario se creará como <strong>inactivo</strong>. El administrador deberá activarlo.
        </div>
      </div>
    </div>
  )
}

// ─── Tarjeta de contacto ──────────────────────────────────────────────────
function ContactoCard({ contacto, onUpdate }) {
  const { authFetch }     = useAuth()
  const [expanded,  setExpanded]  = useState(false)
  const [modal,     setModal]     = useState(false)
  const [loadingNo, setLoadingNo] = useState(false)
  const [toast,     setToast]     = useState('')

  async function noAtender() {
    if (!window.confirm('¿Marcás este contacto como No Atendido?')) return
    setLoadingNo(true)
    try {
      const res = await authFetch(`/ter-int/contactos/${contacto.id}/no-atender`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Error')
      onUpdate(data)
    } catch (e) {
      setToast(e.message)
      setTimeout(() => setToast(''), 3500)
    } finally {
      setLoadingNo(false)
    }
  }

  const esPendiente = contacto.estado === 'derivado'

  return (
    <>
      {modal && (
        <ModalAtender
          contacto={contacto}
          onAtendido={data => { setModal(false); onUpdate(data) }}
          onClose={() => setModal(false)}
        />
      )}

      <div className="card mb12" style={{ padding: '16px 18px' }}>
        {/* Cabecera */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
          {/* Avatar */}
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: 'var(--purple2)', color: 'var(--purple)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <IcoUser />
          </div>

          {/* Info principal */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, fontSize: 14 }}>{contacto.nombre}</span>
              <EstadoBadge estado={contacto.estado} />
            </div>

            <div className="flex g12 mt4" style={{ flexWrap: 'wrap' }}>
              {contacto.celular && (
                <span className="flex ic g4 txs" style={{ color: 'var(--text2)' }}>
                  <IcoPhone /> {contacto.celular}
                </span>
              )}
              {contacto.mail && (
                <span className="flex ic g4 txs" style={{ color: 'var(--text2)' }}>
                  <IcoMail /> {contacto.mail}
                </span>
              )}
            </div>

            <div className="txs mt4" style={{ color: 'var(--text3)' }}>
              Derivado: {formatFecha(contacto.derivado_en)}
            </div>
          </div>

          {/* Botón expandir */}
          <button
            className="btn btn-g btn-sm"
            onClick={() => setExpanded(e => !e)}
            style={{ flexShrink: 0 }}
            title={expanded ? 'Contraer' : 'Ver detalle'}
          >
            <IcoChevron down={!expanded} />
          </button>
        </div>

        {/* Detalle expandido */}
        {expanded && (
          <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
            {contacto.comentario && (
              <div className="mb12">
                <div className="txs" style={{ color: 'var(--text3)', fontWeight: 600, marginBottom: 4 }}>
                  Comentario del contacto
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', background: 'var(--bg2)',
                  padding: '8px 12px', borderRadius: 8, borderLeft: '3px solid var(--purple)' }}>
                  {contacto.comentario}
                </div>
              </div>
            )}

            <div className="mb12">
              <div className="txs" style={{ color: 'var(--text3)', fontWeight: 600, marginBottom: 4 }}>
                Mensaje que activó la alerta
              </div>
              <div style={{ fontSize: 13, color: 'var(--text)', background: 'rgba(245,158,11,0.06)',
                padding: '8px 12px', borderRadius: 8, borderLeft: '3px solid #f59e0b',
                fontStyle: 'italic', lineHeight: 1.55 }}>
                "{contacto.mensaje_alerta}"
              </div>
            </div>

            <div>
              <div className="txs" style={{ color: 'var(--text3)', fontWeight: 600, marginBottom: 4 }}>
                Respuesta del asistente IA
              </div>
              <div style={{ fontSize: 13, color: 'var(--text)', background: 'var(--bg2)',
                padding: '8px 12px', borderRadius: 8, lineHeight: 1.55 }}>
                {contacto.respuesta_ia}
              </div>
            </div>

            {contacto.nota_derivacion && (
              <div className="mt12">
                <div className="txs" style={{ color: 'var(--text3)', fontWeight: 600, marginBottom: 4 }}>
                  Nota del administrador
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', fontStyle: 'italic' }}>
                  {contacto.nota_derivacion}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Acciones — solo si está pendiente */}
        {esPendiente && (
          <div className="flex g8 mt14" style={{ justifyContent: 'flex-end' }}>
            <button
              className="btn btn-g btn-sm"
              onClick={noAtender}
              disabled={loadingNo}
              style={{ color: 'var(--danger)', borderColor: 'var(--danger)' }}
            >
              <IcoX /> {loadingNo ? 'Procesando...' : 'No atender'}
            </button>
            <button
              className="btn btn-p btn-sm"
              onClick={() => setModal(true)}
            >
              <IcoCheck /> Atender
            </button>
          </div>
        )}

        {/* Toast local de error */}
        {toast && (
          <div style={{ marginTop: 8, padding: '6px 12px', borderRadius: 8,
            background: 'rgba(239,68,68,0.08)', color: 'var(--danger)', fontSize: 12 }}>
            {toast}
          </div>
        )}
      </div>
    </>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
export default function ContactosDerivados() {
  const { authFetch } = useAuth()
  const [contactos, setContactos] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [filtro,    setFiltro]    = useState('todos')   // todos | derivado | atendido | no_atendido
  const [toast,     setToast]     = useState({ msg: '', tipo: '' })

  async function cargar(f = filtro) {
    setLoading(true)
    try {
      const params = f !== 'todos' ? `?estado=${f}` : ''
      const res = await authFetch(`/ter-int/contactos${params}`)
      if (!res.ok) throw new Error('Error al cargar contactos')
      setContactos(await res.json())
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [filtro])

  function showToast(msg, tipo = 'ok') {
    setToast({ msg, tipo })
    setTimeout(() => setToast({ msg: '', tipo: '' }), 3500)
  }

  function onUpdate(updated) {
    setContactos(prev => prev.map(c => c.id === updated.id ? updated : c))
    showToast(
      updated.estado === 'atendido'    ? '✓ Contacto atendido. Usuario familiar creado.' :
      updated.estado === 'no_atendido' ? 'Contacto marcado como No Atendido.'           :
      'Contacto actualizado.',
      'ok'
    )
  }

  const counts = contactos.reduce((acc, c) => {
    acc[c.estado] = (acc[c.estado] || 0) + 1
    return acc
  }, {})

  const FILTROS = [
    { key: 'todos',       label: 'Todos' },
    { key: 'derivado',    label: 'Pendientes' },
    { key: 'atendido',    label: 'Atendidos' },
    { key: 'no_atendido', label: 'No atendidos' },
  ]

  return (
    <div>
      {/* Encabezado */}
      <div className="flex ic g12 mb20" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Contactos TEA derivados</h2>
          <div className="txs" style={{ color: 'var(--text2)', marginTop: 3 }}>
            Personas que solicitaron contacto a través del asistente público y te fueron asignadas
          </div>
        </div>
        <button className="btn btn-g btn-sm flex ic g6" onClick={() => cargar()}>
          <IcoRefresh /> Actualizar
        </button>
      </div>

      {/* Resumen */}
      {!loading && contactos.length > 0 && (
        <div className="flex g10 mb16" style={{ flexWrap: 'wrap' }}>
          {[
            { label: 'Pendientes',    val: counts.derivado ?? 0,    color: '#b45309' },
            { label: 'Atendidos',     val: counts.atendido ?? 0,    color: '#047857' },
            { label: 'No atendidos',  val: counts.no_atendido ?? 0, color: '#b91c1c' },
          ].map(s => (
            <div key={s.label} className="card" style={{ padding: '10px 16px', textAlign: 'center', minWidth: 90 }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.val}</div>
              <div className="txs" style={{ color: 'var(--text2)' }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filtros */}
      <div className="flex ic g8 mb16" style={{ flexWrap: 'wrap' }}>
        {FILTROS.map(f => (
          <button
            key={f.key}
            className={`btn btn-sm ${filtro === f.key ? 'btn-p' : 'btn-s'}`}
            style={{ fontSize: 12 }}
            onClick={() => setFiltro(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Toast global */}
      {toast.msg && (
        <div style={{
          marginBottom: 14, padding: '10px 16px', borderRadius: 8,
          background: toast.tipo === 'error' ? 'rgba(239,68,68,0.08)' : 'rgba(16,185,129,0.08)',
          color: toast.tipo === 'error' ? 'var(--danger)' : '#047857',
          fontSize: 13, fontWeight: 500,
        }}>
          {toast.msg}
        </div>
      )}

      {/* Lista */}
      {loading ? (
        <div className="card" style={{ padding: 32, textAlign: 'center', color: 'var(--text3)' }}>
          Cargando contactos…
        </div>
      ) : contactos.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Sin contactos derivados</div>
          <div className="txs" style={{ color: 'var(--text2)' }}>
            {filtro === 'todos'
              ? 'El administrador aún no te derivó ningún contacto.'
              : `No hay contactos con estado "${FILTROS.find(f => f.key === filtro)?.label}".`}
          </div>
        </div>
      ) : (
        contactos.map(c => (
          <ContactoCard key={c.id} contacto={c} onUpdate={onUpdate} />
        ))
      )}
    </div>
  )
}
