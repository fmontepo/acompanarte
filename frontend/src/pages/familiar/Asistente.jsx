import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

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

const RESPUESTAS_IA = {
  default: [
    'Entiendo tu consulta. Basándome en los registros de seguimiento recientes, Roberto ha mostrado una evolución positiva en las últimas semanas. ¿Hay algún aspecto específico que te preocupe?',
    'Esa es una pregunta muy importante. El equipo terapéutico ha estado trabajando en ese aspecto. Te recomiendo también revisar los últimos seguimientos para más contexto.',
    'Según la información disponible en el historial de Roberto, este tipo de situaciones es frecuente en su condición. Lo más importante es mantener la calma y aplicar las técnicas recomendadas por el equipo.',
    'Puedo ayudarte con eso. Basándome en el plan terapéutico actual, la recomendación es mantener la rutina diaria y consultar con el Dr. Herrera si el episodio se repite.',
  ],
  bienestar: 'El índice de bienestar de Roberto esta semana es del 72%, lo que se considera estable. Ha completado el 80% de sus actividades y no hubo episodios significativos en los últimos 3 días.',
  actividades: 'Hoy Roberto tiene 5 actividades programadas. Completó 2 hasta ahora: ejercicio de respiración y lectura guiada. Le quedan la caminata, el ejercicio de memoria y música/relajación.',
  equipo: 'El equipo terapéutico de Roberto está integrado por el Dr. Luis Herrera como terapeuta principal y la Lic. Patricia Ruiz en terapia cognitiva. Ambos están disponibles para consultas a través del sistema.',
}

const SUGERENCIAS = [
  '¿Cómo está Roberto esta semana?',
  '¿Qué actividades tiene hoy?',
  '¿Quiénes son sus terapeutas?',
  '¿Qué hago si se desorienta?',
]

function getIA(texto) {
  const t = texto.toLowerCase()
  if (t.includes('bienestar') || t.includes('cómo está') || t.includes('estado')) return RESPUESTAS_IA.bienestar
  if (t.includes('actividad') || t.includes('ejercicio') || t.includes('tarea')) return RESPUESTAS_IA.actividades
  if (t.includes('terapeuta') || t.includes('equipo') || t.includes('médico') || t.includes('doctor')) return RESPUESTAS_IA.equipo
  const idx = Math.floor(Math.random() * RESPUESTAS_IA.default.length)
  return RESPUESTAS_IA.default[idx]
}

const INTRO = {
  id: 0,
  rol: 'ia',
  texto: '¡Hola! Soy el asistente de **Acompañarte**. Estoy aquí para ayudarte con información sobre el estado de Roberto, sus actividades, el equipo terapéutico y cualquier duda que tengas sobre su cuidado.\n\n¿En qué te puedo ayudar hoy?',
  hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
}

export default function FamiliarAsistente() {
  const { user, authFetch } = useAuth()
  const [mensajes, setMensajes] = useState([INTRO])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef               = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes])

  async function enviar(texto) {
    if (!texto.trim() || loading) return
    const msgUsuario = {
      id: Date.now(),
      rol: 'usuario',
      texto: texto.trim(),
      hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
    }
    setMensajes(prev => [...prev, msgUsuario])
    setInput('')
    setLoading(true)

    try {
      // Intentar con el backend RAG real
      const res = await authFetch('/api/v1/ia/chat', {
        method: 'POST',
        body: JSON.stringify({ mensaje: texto.trim(), contexto: 'familiar' }),
      })
      if (res.ok) {
        const data = await res.json()
        setMensajes(prev => [...prev, {
          id: Date.now() + 1,
          rol: 'ia',
          texto: data.respuesta ?? getIA(texto),
          hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
        }])
      } else {
        throw new Error('fallback')
      }
    } catch {
      // Simular delay y usar respuesta mock
      await new Promise(r => setTimeout(r, 900 + Math.random() * 600))
      setMensajes(prev => [...prev, {
        id: Date.now() + 1,
        rol: 'ia',
        texto: getIA(texto),
        hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(input) }
  }

  // Renderizar texto con **negrita** simple
  function renderTexto(texto) {
    const parts = texto.split(/\*\*(.*?)\*\*/g)
    return parts.map((p, i) => i % 2 === 1 ? <strong key={i}>{p}</strong> : p)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px - 48px)', maxHeight: 680 }}>

      {/* Header */}
      <div className="card mb16" style={{ flexShrink: 0, padding: '14px 18px' }}>
        <div className="flex ic g10">
          <div style={{ width: 38, height: 38, borderRadius: 10, background: 'var(--purple2)',
            color: 'var(--purple)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <IcoBot />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>Asistente Acompañarte</div>
            <div className="txs" style={{ color: 'var(--teal)', fontWeight: 500 }}>● En línea</div>
          </div>
        </div>
      </div>

      {/* Historial de mensajes */}
      <div style={{ flex: 1, overflowY: 'auto', marginBottom: 12, paddingRight: 4 }}>

        {mensajes.map(msg => (
          <div key={msg.id} style={{
            display: 'flex',
            justifyContent: msg.rol === 'usuario' ? 'flex-end' : 'flex-start',
            marginBottom: 14,
            gap: 8,
          }}>
            {/* Avatar IA */}
            {msg.rol === 'ia' && (
              <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--purple2)',
                color: 'var(--purple)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, alignSelf: 'flex-end' }}>
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
              fontSize: 13.5,
              lineHeight: 1.55,
            }}>
              {renderTexto(msg.texto)}
              <div style={{
                fontSize: 10,
                marginTop: 5,
                color: msg.rol === 'usuario' ? 'rgba(255,255,255,0.65)' : 'var(--text3)',
                textAlign: 'right',
              }}>
                {msg.hora}
              </div>
            </div>

            {/* Avatar usuario */}
            {msg.rol === 'usuario' && (
              <div className={`av ${user?.avatar_class ?? 'av-tl'}`} style={{
                width: 30, height: 30, fontSize: 10, flexShrink: 0, alignSelf: 'flex-end',
              }}>
                {user?.avatar_initials ?? '?'}
              </div>
            )}
          </div>
        ))}

        {/* Indicador de escritura */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--purple2)',
              color: 'var(--purple)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <IcoBot />
            </div>
            <div style={{ padding: '10px 14px', background: 'var(--bg2)', border: '1px solid var(--border)',
              borderRadius: '14px 14px 14px 2px', display: 'flex', gap: 4, alignItems: 'center' }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 6, height: 6, borderRadius: '50%', background: 'var(--text3)',
                  animation: `bounce 1.2s ${i * 0.2}s infinite`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Sugerencias */}
      {mensajes.length <= 1 && (
        <div className="flex ic g6 mb12" style={{ flexWrap: 'wrap' }}>
          {SUGERENCIAS.map(s => (
            <button key={s} className="btn btn-s btn-sm" onClick={() => enviar(s)}
              style={{ fontSize: 12 }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
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

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>

    </div>
  )
}
