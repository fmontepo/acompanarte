import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../../context/AuthContext'

// ── Íconos ────────────────────────────────────────────────────────────────────
const IcoSend = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
  </svg>
)
const IcoBot = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <path strokeLinecap="round" d="M12 11V7m-4 4V9a4 4 0 018 0v2"/>
    <circle cx="9" cy="16" r="1" fill="currentColor"/>
    <circle cx="15" cy="16" r="1" fill="currentColor"/>
  </svg>
)
const IcoRefresh = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
  </svg>
)

// ── Colores para tipos de registro ────────────────────────────────────────────
const TIPO_COLORS = {
  logro:       { color: 'var(--teal)',   bg: 'var(--teal2)' },
  objetivo:    { color: 'var(--blue)',   bg: 'var(--blue2)' },
  evolucion:   { color: 'var(--purple)', bg: 'var(--purple2)' },
  observacion: { color: 'var(--amber)',  bg: 'var(--amber2)' },
  incidente:   { color: 'var(--red)',    bg: 'var(--red2, #fde8e8)' },
}

// ── Sugerencias de consulta ────────────────────────────────────────────────────
const SUGERENCIAS = [
  '¿Cuál es la actividad con mayor tasa de cumplimiento?',
  '¿Qué paciente mostró más mejoras en las últimas semanas?',
  '¿Qué tipo de registro prevalece en el grupo?',
  '¿Hay algún patrón preocupante en el historial reciente?',
  '¿Qué estrategias recomienda la bibliografía para el diagnóstico más frecuente?',
]

// ── Componente: barra de progreso horizontal ──────────────────────────────────
function BarraHorizontal({ label, value, total, color = 'var(--blue)', max }) {
  const pct = max ? Math.round((value / max) * 100) : Math.round((value / (total || 1)) * 100)
  return (
    <div style={{ marginBottom: 10 }}>
      <div className="flex ic jb" style={{ marginBottom: 4 }}>
        <span className="txs" style={{ color: 'var(--text2)' }}>{label}</span>
        <span className="txs" style={{ fontWeight: 600, color }}>{value}{total ? ` (${Math.round(value/total*100)}%)` : '%'}</span>
      </div>
      <div className="pbar" style={{ height: 7 }}>
        <div className="pf" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

// ── Componente: gráfico semanal de bienestar ──────────────────────────────────
function GraficoSemanal({ datos }) {
  if (!datos || datos.length === 0) return null
  const max = 100
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 80, marginTop: 8 }}>
      {datos.map((d, i) => {
        const h = d.bienestar != null ? Math.round((d.bienestar / max) * 72) : 0
        const color = d.bienestar == null ? 'var(--border2)'
          : d.bienestar >= 70 ? 'var(--teal)' : d.bienestar >= 50 ? 'var(--amber)' : 'var(--red)'
        return (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <span className="txs" style={{ color: 'var(--text3)', fontSize: 9 }}>
              {d.bienestar != null ? `${d.bienestar}%` : '—'}
            </span>
            <div style={{
              width: '100%', height: h || 4, borderRadius: 3,
              background: color, transition: 'height 0.3s',
            }} />
            <span className="txs" style={{ color: 'var(--text3)', fontSize: 9 }}>{d.semana}</span>
          </div>
        )
      })}
    </div>
  )
}

// ── Componente: burbuja de chat ───────────────────────────────────────────────
function Burbuja({ msg }) {
  const esIA = msg.rol === 'ia'
  return (
    <div style={{
      display: 'flex', gap: 10, justifyContent: esIA ? 'flex-start' : 'flex-end',
      marginBottom: 12,
    }}>
      {esIA && (
        <div style={{
          width: 30, height: 30, borderRadius: '50%', background: 'var(--purple2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--purple)', flexShrink: 0, marginTop: 2,
        }}>
          <IcoBot />
        </div>
      )}
      <div style={{
        maxWidth: '75%',
        background: esIA ? 'var(--bg2)' : 'var(--purple)',
        color: esIA ? 'var(--text)' : '#fff',
        borderRadius: esIA ? '4px 14px 14px 14px' : '14px 4px 14px 14px',
        padding: '10px 14px',
        fontSize: 13,
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        {msg.texto}
        <div style={{ fontSize: 10, marginTop: 4, opacity: 0.6, textAlign: 'right' }}>{msg.hora}</div>
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function TerIntAsistente() {
  const { authFetch } = useAuth()

  // Stats
  const [stats, setStats]       = useState(null)
  const [loadStats, setLoadStats] = useState(true)
  const [errorStats, setErrorStats] = useState(false)

  // Chat
  const [mensajes, setMensajes] = useState([{
    id: 0, rol: 'ia',
    texto: '¡Hola! Soy tu asistente clínico. Podés consultarme sobre el historial de tus pacientes, tendencias de bienestar, efectividad de actividades o estrategias terapéuticas basadas en bibliografía validada.\n\n¿En qué te puedo ayudar hoy?',
    hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
  }])
  const [input, setInput]       = useState('')
  const [sending, setSending]   = useState(false)
  const bottomRef               = useRef(null)
  const inputRef                = useRef(null)

  // ── Cargar stats ─────────────────────────────────────────────────────────
  async function cargarStats() {
    setLoadStats(true)
    setErrorStats(false)
    try {
      const res = await authFetch('/ia/terapeuta/stats')
      if (res.ok) {
        setStats(await res.json())
      } else {
        setErrorStats(true)
      }
    } catch {
      setErrorStats(true)
    } finally {
      setLoadStats(false)
    }
  }

  useEffect(() => { cargarStats() }, [])

  // ── Auto-scroll al último mensaje ────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes])

  // ── Enviar mensaje ────────────────────────────────────────────────────────
  async function enviar(texto) {
    const msg = texto || input.trim()
    if (!msg || sending) return
    setInput('')
    setSending(true)

    const hora = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    const idUser = Date.now()
    setMensajes(prev => [...prev, { id: idUser, rol: 'user', texto: msg, hora }])

    try {
      const res = await authFetch('/ia/terapeuta/chat', {
        method: 'POST',
        body: JSON.stringify({ mensaje: msg }),
      })
      const data = res.ok ? await res.json() : null
      const respuesta = data?.respuesta || 'No pude procesar tu consulta. Verificá que Ollama esté activo.'
      const horaIA = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
      setMensajes(prev => [...prev, { id: Date.now(), rol: 'ia', texto: respuesta, hora: horaIA }])
    } catch {
      const horaIA = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
      setMensajes(prev => [...prev, {
        id: Date.now(), rol: 'ia',
        texto: 'El asistente no está disponible en este momento. Verificá que el servicio de IA esté activo.',
        hora: horaIA,
      }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  const bienestarColor = stats?.bienestar_promedio == null ? 'var(--text3)'
    : stats.bienestar_promedio >= 70 ? 'var(--teal)'
    : stats.bienestar_promedio >= 50 ? 'var(--amber)' : 'var(--red)'

  return (
    <div>
      {/* Título */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Asistente IA Clínico</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            Análisis de pacientes y consultas en lenguaje natural
          </div>
        </div>
        <button className="btn btn-s btn-sm" onClick={cargarStats} title="Actualizar métricas">
          <IcoRefresh />
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>

        {/* ── Panel izquierdo: Analytics ──────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* KPIs rápidos */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div className="stat">
              <div className="sn" style={{ color: 'var(--teal)' }}>
                {loadStats ? '—' : stats?.total_pacientes ?? 0}
              </div>
              <div className="sl">Pacientes activos</div>
            </div>
            <div className="stat">
              <div className="sn" style={{ color: bienestarColor }}>
                {loadStats ? '—' : stats?.bienestar_promedio != null ? `${stats.bienestar_promedio}%` : '—'}
              </div>
              <div className="sl">Bienestar promedio</div>
            </div>
          </div>

          {/* Distribución de diagnósticos */}
          <div className="card">
            <div className="ts f6 mb12">Distribución de diagnósticos</div>
            {loadStats ? (
              <div className="txs tm">Cargando…</div>
            ) : errorStats ? (
              <div className="txs" style={{ color: 'var(--red)' }}>Error al cargar</div>
            ) : !stats?.diagnosticos?.length ? (
              <div className="txs tm">Sin datos</div>
            ) : (
              stats.diagnosticos.map((d, i) => (
                <BarraHorizontal
                  key={i}
                  label={d.nombre}
                  value={d.cantidad}
                  total={stats.total_pacientes}
                  color={['var(--teal)', 'var(--blue)', 'var(--purple)', 'var(--amber)', 'var(--red)'][i % 5]}
                />
              ))
            )}
          </div>

          {/* Tipos de registros */}
          <div className="card">
            <div className="ts f6 mb12">Tipos de registros</div>
            {loadStats ? (
              <div className="txs tm">Cargando…</div>
            ) : !stats?.registros_tipos?.length ? (
              <div className="txs tm">Sin registros aún</div>
            ) : (
              stats.registros_tipos.map((t, i) => {
                const c = TIPO_COLORS[t.tipo] || { color: 'var(--text2)', bg: 'var(--bg2)' }
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 7 }}>
                    <span className="chip txs" style={{ background: c.bg, color: c.color, minWidth: 90 }}>
                      {t.label}
                    </span>
                    <div className="pbar" style={{ flex: 1, height: 6 }}>
                      <div className="pf" style={{ width: `${t.porcentaje}%`, background: c.color }} />
                    </div>
                    <span className="txs" style={{ color: c.color, fontWeight: 600, width: 32, textAlign: 'right' }}>
                      {t.cantidad}
                    </span>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* ── Panel derecho: Efectividad y Evolución ───────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Evolución de bienestar */}
          <div className="card">
            <div className="ts f6 mb4">Evolución del bienestar (8 semanas)</div>
            <div className="txs tm mb8">Promedio del grupo</div>
            {loadStats ? (
              <div className="txs tm">Cargando…</div>
            ) : (
              <GraficoSemanal datos={stats?.evolucion_bienestar ?? []} />
            )}
          </div>

          {/* Actividades más efectivas */}
          <div className="card" style={{ flex: 1 }}>
            <div className="ts f6 mb12">Actividades — tasa de cumplimiento</div>
            {loadStats ? (
              <div className="txs tm">Cargando…</div>
            ) : !stats?.actividades_efectividad?.length ? (
              <div className="txs tm">Sin actividades asignadas</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {stats.actividades_efectividad.slice(0, 6).map((a, i) => {
                  const color = a.tasa_cumplimiento >= 70 ? 'var(--teal)'
                    : a.tasa_cumplimiento >= 40 ? 'var(--amber)' : 'var(--red)'
                  return (
                    <div key={a.id}>
                      <div className="flex ic jb" style={{ marginBottom: 3 }}>
                        <span className="txs" style={{ color: 'var(--text2)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {a.titulo}
                        </span>
                        <span className="txs" style={{ fontWeight: 700, color }}>{a.tasa_cumplimiento}%</span>
                      </div>
                      <div className="pbar" style={{ height: 5 }}>
                        <div className="pf" style={{ width: `${a.tasa_cumplimiento}%`, background: color }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Chat clínico ──────────────────────────────────────────────────── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Header chat */}
        <div style={{
          padding: '14px 18px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--purple2)',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%', background: 'var(--purple)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
          }}>
            <IcoBot />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--purple)' }}>Asistente Clínico</div>
            <div className="txs" style={{ color: 'var(--purple)', opacity: 0.7 }}>
              Consultas sobre tus pacientes · Bibliografía validada
            </div>
          </div>
        </div>

        {/* Mensajes */}
        <div style={{
          height: 280, overflowY: 'auto', padding: '16px 18px',
          display: 'flex', flexDirection: 'column',
        }}>
          {mensajes.map(m => <Burbuja key={m.id} msg={m} />)}
          {sending && (
            <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
              <div style={{
                width: 30, height: 30, borderRadius: '50%', background: 'var(--purple2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--purple)',
              }}><IcoBot /></div>
              <div style={{
                background: 'var(--bg2)', borderRadius: '4px 14px 14px 14px',
                padding: '10px 16px', display: 'flex', gap: 5, alignItems: 'center',
              }}>
                {[0,1,2].map(i => (
                  <div key={i} style={{
                    width: 7, height: 7, borderRadius: '50%', background: 'var(--purple)',
                    animation: 'pulse 1.2s ease-in-out infinite',
                    animationDelay: `${i * 0.2}s`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Sugerencias */}
        {mensajes.length <= 1 && (
          <div style={{ padding: '0 18px 10px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {SUGERENCIAS.map((s, i) => (
              <button key={i} onClick={() => enviar(s)} className="chip ch-gray txs"
                style={{ cursor: 'pointer', border: '1px solid var(--border2)', background: 'var(--bg)' }}>
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10 }}>
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), enviar())}
            placeholder="Consultame sobre tus pacientes, actividades o estrategias…"
            disabled={sending}
            style={{
              flex: 1, border: '1px solid var(--border2)', borderRadius: 8,
              padding: '9px 13px', fontSize: 13, outline: 'none',
              background: sending ? 'var(--bg2)' : 'var(--bg)',
              color: 'var(--text)',
            }}
          />
          <button
            onClick={() => enviar()}
            disabled={!input.trim() || sending}
            className="btn btn-p btn-sm"
            style={{ borderRadius: 8, padding: '9px 14px' }}
          >
            <IcoSend />
          </button>
        </div>
      </div>
    </div>
  )
}
