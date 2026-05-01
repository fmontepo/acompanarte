// AsistentePublico.jsx
// Asistente TEA accesible sin autenticación — desde la pantalla de login
// No requiere cuenta. Usa el endpoint público /api/v1/ia/chat-publico
// Objetivo: orientar a familias con dudas sobre desarrollo infantil y TEA

import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

// ─── Íconos ───────────────────────────────────────────────────────────────
const IcoSend = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
  </svg>
)
const IcoBot = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <path strokeLinecap="round" d="M12 11V7m-4 4V9a4 4 0 018 0v2"/>
    <circle cx="9" cy="16" r="1" fill="currentColor"/>
    <circle cx="15" cy="16" r="1" fill="currentColor"/>
  </svg>
)
const IcoHeart = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth="2">
    <path strokeLinecap="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
  </svg>
)
const IcoBack = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
  </svg>
)

// ─── Contenido inicial ────────────────────────────────────────────────────
const INTRO_TEXTO = [
  '¡Hola! Soy el asistente de orientación TEA de **Acompañarte**.',
  'Estoy aquí para ayudarte con información sobre señales de desarrollo infantil, el espectro autista y cómo acceder a apoyo especializado.',
  '¿En qué te puedo ayudar hoy?',
].join('\n\n')

const SUGERENCIAS = [
  '¿Cuáles son las señales tempranas de TEA?',
  '¿Qué hago si mi hijo no hace contacto visual?',
  '¿Cómo puedo apoyar la comunicación de mi hijo?',
  '¿Cuándo debo consultar con un especialista?',
]

// ─── Mensaje de IA que pregunta si quiere contacto ────────────────────────
const MSG_CONTACTO = [
  'Noto que lo que describís puede requerir atención especializada.',
  '¿Querés que te ponga en contacto con un terapeuta de Acompañarte? Es completamente gratuito y sin compromiso.',
].join('\n\n')

const MSG_CONFIRMACION = [
  '¡Listo! Tu solicitud fue registrada.',
  'Un terapeuta de nuestro equipo se pondrá en contacto con vos a la brevedad.',
  'Mientras tanto, seguí consultándonos cualquier duda.',
].join('\n\n')

const MSG_SIN_CONTACTO = [
  'Entendido. Seguí consultándome lo que necesites.',
  'Recordá que siempre podés registrarte en Acompañarte para hacer un seguimiento continuo del desarrollo de tu familiar.',
].join('\n\n')

// ─── Tipos especiales de mensajes ────────────────────────────────────────
// rol: 'ia' | 'usuario' | 'opciones' | 'formulario'
// Para 'opciones': tiene .opciones: [{label, accion}]
// Para 'formulario': se renderea el form inline

// ─── Componente principal ─────────────────────────────────────────────────
export default function AsistentePublico() {
  const navigate  = useNavigate()
  const bottomRef = useRef(null)

  const [mensajes,     setMensajes]     = useState([{
    id: 0, rol: 'ia',
    texto: INTRO_TEXTO,
    hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
  }])
  const [input,        setInput]        = useState('')
  const [loading,      setLoading]      = useState(false)

  // Estado del flujo de contacto
  // null | 'preguntando' | 'formulario' | 'enviado'
  const [contactoFlujo, setContactoFlujo] = useState(null)

  // Último intercambio que disparó la alerta
  const alertaTriggerRef = useRef({ mensaje: '', respuesta: '' })

  // Estado del formulario de contacto
  const [formNombre,     setFormNombre]     = useState('')
  const [formCelular,    setFormCelular]    = useState('')
  const [formMail,       setFormMail]       = useState('')
  const [formComentario, setFormComentario] = useState('')
  const [formEnviando,   setFormEnviando]   = useState(false)
  const [formError,      setFormError]      = useState('')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes, contactoFlujo])

  function hora() {
    return new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  }

  function agregarMensajeIA(texto) {
    setMensajes(prev => [...prev, { id: Date.now(), rol: 'ia', texto, hora: hora() }])
  }

  async function enviar(texto) {
    if (!texto.trim() || loading) return

    setMensajes(prev => [...prev, {
      id:    Date.now(),
      rol:   'usuario',
      texto: texto.trim(),
      hora:  hora(),
    }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/ia/chat-publico`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ mensaje: texto.trim() }),
      })

      if (res.ok) {
        const data = await res.json()

        // Agregar respuesta de la IA al chat
        setMensajes(prev => [...prev, {
          id:    Date.now() + 1,
          rol:   'ia',
          texto: data.respuesta,
          hora:  hora(),
        }])

        // Si hay alerta y el flujo no está activo todavía, iniciar flujo conversacional
        if (data.alerta && !contactoFlujo) {
          alertaTriggerRef.current = {
            mensaje:   texto.trim(),
            respuesta: data.respuesta,
          }
          // Activar el banner de contacto sin agregar un segundo mensaje de IA
          setContactoFlujo('preguntando')
        }
      } else {
        throw new Error(`HTTP ${res.status}`)
      }
    } catch {
      await new Promise(r => setTimeout(r, 600))
      setMensajes(prev => [...prev, {
        id:    Date.now() + 1,
        rol:   'ia',
        texto: 'No pude conectarme al asistente en este momento. Por favor, intentá más tarde o consultá directamente con un especialista en TEA.',
        hora:  hora(),
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(input) }
  }

  function responderSi() {
    setMensajes(prev => [...prev, { id: Date.now(), rol: 'usuario', texto: 'Sí, me gustaría que me contacten.', hora: hora() }])
    setContactoFlujo('formulario')
  }

  function responderNo() {
    setMensajes(prev => [...prev, { id: Date.now(), rol: 'usuario', texto: 'No, gracias.', hora: hora() }])
    setContactoFlujo(null)
    setTimeout(() => agregarMensajeIA(MSG_SIN_CONTACTO), 400)
  }

  async function enviarFormulario(e) {
    e.preventDefault()
    if (!formNombre.trim()) { setFormError('El nombre es obligatorio.'); return }
    if (!formCelular.trim() && !formMail.trim()) {
      setFormError('Ingresá al menos un medio de contacto: celular o mail.')
      return
    }
    setFormError('')
    setFormEnviando(true)

    try {
      const res = await fetch(`${API_BASE}/ia/contacto-publico`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          nombre:         formNombre.trim(),
          celular:        formCelular.trim() || null,
          mail:           formMail.trim() || null,
          comentario:     formComentario.trim() || null,
          mensaje_alerta: alertaTriggerRef.current.mensaje,
          respuesta_ia:   alertaTriggerRef.current.respuesta,
        }),
      })

      if (res.ok) {
        setContactoFlujo('enviado')
        setFormNombre('')
        setFormCelular('')
        setFormMail('')
        setFormComentario('')
        setTimeout(() => agregarMensajeIA(MSG_CONFIRMACION), 300)
      } else {
        const data = await res.json().catch(() => ({}))
        setFormError(data.detail || 'Error al enviar. Intentá de nuevo.')
      }
    } catch {
      setFormError('No se pudo conectar con el servidor. Intentá de nuevo.')
    } finally {
      setFormEnviando(false)
    }
  }

  function renderTexto(texto) {
    const parts = texto.split(/\*\*(.*?)\*\*/g)
    return parts.map((p, i) =>
      i % 2 === 1 ? <strong key={i}>{p}</strong> : p
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '16px 12px 0',
    }}>

      {/* ── Top bar ─────────────────────────────────────────────────── */}
      <div style={{
        width: '100%', maxWidth: 680,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <button
          className="btn btn-g btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          onClick={() => navigate('/login')}
        >
          <IcoBack /> Volver al inicio
        </button>

        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8,
            background: 'var(--teal)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <IcoHeart />
          </div>
          <span style={{ fontWeight: 700, fontSize: 15 }}>acompañarte</span>
        </div>
      </div>

      {/* ── Área de chat ─────────────────────────────────────────────── */}
      <div style={{
        width: '100%', maxWidth: 680,
        flex: 1,
        display: 'flex', flexDirection: 'column',
        height: 'calc(100vh - 64px)',
      }}>

        {/* Header del asistente */}
        <div className="card mb12" style={{ padding: '14px 18px', flexShrink: 0 }}>
          <div className="flex ic jb">
            <div className="flex ic g10">
              <div style={{
                width: 38, height: 38, borderRadius: 10,
                background: 'var(--purple2)', color: 'var(--purple)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <IcoBot />
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>Asistente TEA · Acompañarte</div>
                <div className="txs" style={{ color: 'var(--teal)', fontWeight: 500 }}>
                  ● Orientación gratuita · Sin registro
                </div>
              </div>
            </div>
            <div className="chip ch-teal txs" style={{ flexShrink: 0 }}>Acceso libre</div>
          </div>
        </div>

        {/* Historial de mensajes */}
        <div style={{ flex: 1, overflowY: 'auto', marginBottom: 10, paddingRight: 4 }}>

          {mensajes.map(msg => (
            <div key={msg.id} style={{
              display: 'flex',
              justifyContent: msg.rol === 'usuario' ? 'flex-end' : 'flex-start',
              marginBottom: 14,
              gap: 8,
            }}>
              {/* Avatar IA */}
              {msg.rol === 'ia' && (
                <div style={{
                  width: 30, height: 30, borderRadius: 8,
                  background: 'var(--purple2)', color: 'var(--purple)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, alignSelf: 'flex-end',
                }}>
                  <IcoBot />
                </div>
              )}

              {/* Burbuja */}
              <div style={{
                maxWidth: '72%',
                padding: '10px 14px',
                borderRadius: msg.rol === 'usuario' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                background: msg.rol === 'usuario' ? 'var(--teal)' : 'var(--bg2)',
                color: msg.rol === 'usuario' ? '#fff' : 'var(--text)',
                border: msg.rol === 'ia' ? '1px solid var(--border)' : 'none',
                fontSize: 13.5, lineHeight: 1.55,
              }}>
                {renderTexto(msg.texto)}
                <div style={{
                  fontSize: 10, marginTop: 5,
                  color: msg.rol === 'usuario' ? 'rgba(255,255,255,0.65)' : 'var(--text3)',
                  textAlign: 'right',
                }}>
                  {msg.hora}
                </div>
              </div>

              {/* Avatar usuario */}
              {msg.rol === 'usuario' && (
                <div style={{
                  width: 30, height: 30, borderRadius: 8,
                  background: 'var(--bg3)', color: 'var(--text2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, alignSelf: 'flex-end', fontSize: 14,
                }}>
                  👤
                </div>
              )}
            </div>
          ))}

          {/* Indicador de carga */}
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{
                width: 30, height: 30, borderRadius: 8,
                background: 'var(--purple2)', color: 'var(--purple)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <IcoBot />
              </div>
              <div style={{
                padding: '10px 14px', background: 'var(--bg2)',
                border: '1px solid var(--border)', borderRadius: '14px 14px 14px 2px',
                display: 'flex', gap: 4, alignItems: 'center',
              }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: 6, height: 6, borderRadius: '50%', background: 'var(--text3)',
                    animation: `bounce 1.2s ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}

          {/* ── Banner de contacto (integrado, no como burbuja IA separada) ── */}
          {contactoFlujo === 'preguntando' && (
            <div style={{
              marginBottom: 14, paddingLeft: 38,
            }}>
              <div style={{
                background: 'rgba(56,161,105,0.08)',
                border: '1px solid rgba(56,161,105,0.3)',
                borderRadius: '12px 12px 12px 2px',
                padding: '12px 16px',
              }}>
                <div style={{ fontSize: 13, color: 'var(--text)', marginBottom: 10, lineHeight: 1.5 }}>
                  🤝 Lo que describís puede requerir atención especializada.
                  ¿Querés que te contacte un terapeuta de Acompañarte? Es <strong>gratuito</strong> y sin compromiso.
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-sm"
                    onClick={responderSi}
                    style={{ fontSize: 12, background: 'var(--teal)', color: '#fff', border: 'none' }}
                  >
                    Sí, quiero que me contacten
                  </button>
                  <button
                    className="btn btn-g btn-sm"
                    onClick={responderNo}
                    style={{ fontSize: 12 }}
                  >
                    No, gracias
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── Formulario de contacto inline ────────────────────────── */}
          {contactoFlujo === 'formulario' && (
            <div style={{
              marginBottom: 14, paddingLeft: 38,
            }}>
              <div style={{
                background: 'var(--bg2)',
                border: '1px solid var(--border)',
                borderRadius: '14px 14px 14px 2px',
                padding: '14px 16px',
                maxWidth: '80%',
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10, color: 'var(--text)' }}>
                  Completá tus datos y te contactamos
                </div>
                <form onSubmit={enviarFormulario} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div>
                    <label style={{ fontSize: 12, color: 'var(--text2)', display: 'block', marginBottom: 3 }}>
                      Nombre <span style={{ color: 'var(--red)' }}>*</span>
                    </label>
                    <input
                      className="fi"
                      type="text"
                      value={formNombre}
                      onChange={e => setFormNombre(e.target.value)}
                      placeholder="Tu nombre"
                      style={{ fontSize: 13, padding: '7px 10px', width: '100%' }}
                      autoFocus
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, color: 'var(--text2)', display: 'block', marginBottom: 3 }}>
                      Celular <span style={{ color: 'var(--text3)' }}>(al menos uno de los dos)</span>
                    </label>
                    <input
                      className="fi"
                      type="tel"
                      value={formCelular}
                      onChange={e => setFormCelular(e.target.value)}
                      placeholder="Ej: 11 1234-5678"
                      style={{ fontSize: 13, padding: '7px 10px', width: '100%' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, color: 'var(--text2)', display: 'block', marginBottom: 3 }}>
                      Mail <span style={{ color: 'var(--text3)' }}>(al menos uno de los dos)</span>
                    </label>
                    <input
                      className="fi"
                      type="email"
                      value={formMail}
                      onChange={e => setFormMail(e.target.value)}
                      placeholder="tu@mail.com"
                      style={{ fontSize: 13, padding: '7px 10px', width: '100%' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, color: 'var(--text2)', display: 'block', marginBottom: 3 }}>
                      Comentario <span style={{ color: 'var(--text3)' }}>(opcional)</span>
                    </label>
                    <textarea
                      className="fi"
                      value={formComentario}
                      onChange={e => setFormComentario(e.target.value)}
                      placeholder="¿Algún detalle que quieras agregar?"
                      rows={2}
                      style={{ fontSize: 13, padding: '7px 10px', width: '100%', resize: 'none' }}
                    />
                  </div>
                  {formError && (
                    <div style={{ fontSize: 12, color: 'var(--red)' }}>{formError}</div>
                  )}
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      type="submit"
                      className="btn btn-p btn-sm"
                      disabled={formEnviando}
                      style={{ fontSize: 12 }}
                    >
                      {formEnviando ? 'Enviando…' : 'Enviar solicitud'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-g btn-sm"
                      onClick={responderNo}
                      disabled={formEnviando}
                      style={{ fontSize: 12 }}
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Sugerencias iniciales ──────────────────────────────────── */}
        {mensajes.length <= 1 && (
          <div className="flex ic g6 mb10" style={{ flexWrap: 'wrap', flexShrink: 0 }}>
            {SUGERENCIAS.map(s => (
              <button
                key={s}
                className="btn btn-s btn-sm"
                onClick={() => enviar(s)}
                style={{ fontSize: 12 }}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* ── Input ─────────────────────────────────────────────────── */}
        <div className="flex ic g8" style={{ flexShrink: 0 }}>
          <textarea
            className="fi fta"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Escribí tu consulta… (Enter para enviar)"
            rows={1}
            disabled={loading}
            style={{ resize: 'none', minHeight: 42, maxHeight: 100, flex: 1, paddingTop: 10 }}
          />
          <button
            className="btn btn-p"
            onClick={() => enviar(input)}
            disabled={!input.trim() || loading}
            style={{ height: 42, padding: '0 14px', flexShrink: 0 }}
          >
            <IcoSend />
          </button>
        </div>

        {/* ── CTA registro ──────────────────────────────────────────── */}
        <div className="txs tm" style={{ textAlign: 'center', padding: '10px 0 14px' }}>
          ¿Querés hacer seguimiento continuo del desarrollo de tu familiar?{' '}
          <button
            onClick={() => navigate('/login')}
            style={{
              color: 'var(--teal)', fontWeight: 600,
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 12, textDecoration: 'underline',
            }}
          >
            Registrate gratis →
          </button>
        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>
    </div>
  )
}
