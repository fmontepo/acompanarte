import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

// ─── Iconos ──────────────────────────────────────────────────────────────
const IcoHeart = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
  </svg>
)
const IcoBot = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <path strokeLinecap="round" d="M12 11V7m-4 4V9a4 4 0 018 0v2"/>
    <circle cx="9" cy="16" r="1" fill="currentColor"/>
    <circle cx="15" cy="16" r="1" fill="currentColor"/>
  </svg>
)
const IcoBell = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
  </svg>
)
const IcoClipboard = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
  </svg>
)
const IcoCheck = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
  </svg>
)
const IcoArrow = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
  </svg>
)
const IcoStar = () => (
  <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
)

// ─── Mock data ───────────────────────────────────────────────────────────
const MOCK_PACIENTE = {
  nombre: 'Roberto',
  apellido: 'Méndez',
  edad: 68,
  diagnostico: 'Deterioro cognitivo leve',
  equipo: [
    { nombre: 'Dr. Luis Herrera', rol: 'Terapeuta principal', av: 'LH', avClass: 'av-pp' },
    { nombre: 'Lic. Patricia Ruiz', rol: 'Terapeuta cognitiva', av: 'PR', avClass: 'av-tl' },
  ],
  bienestar: 72, // porcentaje
  bienestar_label: 'Estable',
  ultimo_registro: 'Hoy, 09:15',
}

const MOCK_ACTIVIDADES = [
  { id: 1, titulo: 'Ejercicio de respiración',       completada: true,  hora: '08:30', color: 'var(--teal)' },
  { id: 2, titulo: 'Lectura guiada — 15 minutos',    completada: true,  hora: '10:00', color: 'var(--blue)' },
  { id: 3, titulo: 'Caminata matutina',               completada: false, hora: '11:30', color: 'var(--purple)' },
  { id: 4, titulo: 'Ejercicio de memoria visual',    completada: false, hora: '16:00', color: 'var(--amber)' },
]

const MOCK_SEGUIMIENTOS = [
  { id: 1, fecha: 'Hoy, 09:15',        autor: 'Dr. Herrera',  texto: 'Buena respuesta a los ejercicios matutinos. Estado de ánimo positivo.', tipo: 'positivo' },
  { id: 2, fecha: 'Ayer, 18:00',       autor: 'Lic. Ruiz',    texto: 'Sesión de terapia cognitiva completada. Se notan mejoras en reconocimiento de caras.', tipo: 'positivo' },
  { id: 3, fecha: 'Lun, 10:30',        autor: 'Dr. Herrera',  texto: 'Episodio de desorientación breve durante la mañana. Recomendamos mantener rutina.', tipo: 'neutral' },
]

const MOCK_ALERTAS = [
  { id: 1, texto: 'Recordá renovar el consentimiento de seguimiento (vence en 5 días).', tipo: 'am' },
  { id: 2, texto: 'Nueva actividad asignada por el equipo terapéutico para esta semana.', tipo: 'tl' },
]

// ─── Sub-componentes ─────────────────────────────────────────────────────
function BienestarMeter({ pct, label }) {
  const color = pct >= 70 ? 'var(--teal)' : pct >= 40 ? 'var(--amber)' : 'var(--red)'
  return (
    <div>
      <div className="flex ic jb" style={{ marginBottom: 6 }}>
        <span className="ts tm">Índice de bienestar</span>
        <span style={{ fontSize: 18, fontWeight: 700, color }}>{pct}%</span>
      </div>
      <div className="pbar" style={{ height: 8 }}>
        <div className="pf" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="txs" style={{ marginTop: 5, color }}>● {label}</div>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────
export default function FamiliarDashboard() {
  const { user, authFetch } = useAuth()
  const navigate = useNavigate()

  const [paciente, setPaciente]       = useState(null)
  const [actividades, setActividades] = useState([])
  const [seguimientos, setSeguimientos] = useState([])
  const [alertas, setAlertas]         = useState([])
  const [loading, setLoading]         = useState(true)

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/familiar/dashboard')
        if (res.ok) {
          const data = await res.json()

          // Paciente vinculado (null si no hay vínculo activo)
          setPaciente(data.paciente ?? null)

          // Backend devuelve "actividades_hoy", no "actividades"
          setActividades(data.actividades_hoy ?? data.actividades ?? [])

          setSeguimientos(data.seguimientos ?? [])

          // Normalizar alertas: tipo "urgente"/"aviso"/"positivo" → "am"/"tl"
          setAlertas((data.alertas ?? []).map(a => ({
            id:    a.id,
            texto: a.texto || a.descripcion || '',
            tipo:  a.tipo === 'urgente' ? 'am' : 'tl',
          })))
        } else {
          // Solo usamos mock si el backend falló (no si devolvió vacío)
          setPaciente(null); setActividades([]); setSeguimientos([]); setAlertas([])
        }
      } catch {
        // Error de red: mostrar mock para que la UI no quede en blanco
        setPaciente(MOCK_PACIENTE); setActividades(MOCK_ACTIVIDADES)
        setSeguimientos(MOCK_SEGUIMIENTOS); setAlertas(MOCK_ALERTAS)
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [authFetch])

  if (loading) {
    return (
      <div>
        <div className="g2 mb16">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="card" style={{ height: 180 }}>
              <div style={{ width: '60%', height: 20, borderRadius: 6, background: 'var(--bg)', marginBottom: 12 }} />
              <div style={{ width: '90%', height: 14, borderRadius: 6, background: 'var(--bg)' }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const hora   = new Date().getHours()
  const saludo = hora < 13 ? 'Buenos días' : hora < 20 ? 'Buenas tardes' : 'Buenas noches'
  const actCompletas = actividades.filter(a => a.completada).length

  // Sin paciente vinculado aún
  if (!paciente) {
    return (
      <div>
        <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{saludo}, {user?.nombre ?? 'familiar'} 👋</div>
        <div className="ts tm" style={{ marginBottom: 24 }}>
          {new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>👤</div>
          <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 6 }}>Sin paciente vinculado</div>
          <div className="ts tm">Tu cuenta todavía no tiene un ser querido asociado. El equipo terapéutico configurará el vínculo.</div>
        </div>
      </div>
    )
  }

  return (
    <div>

      {/* ── Saludo ──────────────────────────────────────────────── */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{saludo}, {user?.nombre ?? nombre} 👋</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => navigate('/familiar/asistente')}>
          <IcoBot /> Hablar con el asistente
        </button>
      </div>

      {/* ── Alertas importantes ─────────────────────────────────── */}
      {alertas.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
          {alertas.map(a => (
            <div key={a.id} className={`disc disc-${a.tipo === 'am' ? '' : 'tl'}`}
              style={a.tipo === 'am' ? {} : { background: 'var(--teal2)', borderColor: '#a5ddc8', color: 'var(--teal3)' }}>
              <IcoBell />
              <span>{a.texto}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Fila principal ──────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>

        {/* Tarjeta del ser querido */}
        <div className="card">
          <div className="flex ic g10 mb16">
            <div className="av av-tl" style={{ width: 48, height: 48, fontSize: 18 }}>
              {(paciente.nombre?.[0] ?? '?')}{(paciente.apellido?.[0] ?? '')}
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700 }}>
                {paciente.nombre} {paciente.apellido}
              </div>
              <div className="ts tm">{paciente.edad != null ? `${paciente.edad} años · ` : ''}{paciente.diagnostico}</div>
            </div>
          </div>

          <BienestarMeter pct={paciente.bienestar} label={paciente.bienestar_label} />

          <div className="divider" />

          <div className="ts tm mb8">Equipo terapéutico</div>
          {paciente.equipo.map((t, i) => (
            <div key={i} className="flex ic g10" style={{ marginBottom: 8 }}>
              <div className={`av ${t.avClass}`} style={{ width: 28, height: 28, fontSize: 10 }}>{t.av}</div>
              <div>
                <div className="ts f5">{t.nombre}</div>
                <div className="txs tm">{t.rol}</div>
              </div>
            </div>
          ))}

          <div className="divider" />
          <div className="txs tm">Último registro: <span className="f5" style={{ color: 'var(--text)' }}>{paciente.ultimo_registro}</span></div>
        </div>

        {/* Actividades del día */}
        <div className="card">
          <div className="flex ic jb mb16">
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Actividades de hoy</div>
              <div className="txs tm" style={{ marginTop: 2 }}>
                {actCompletas} de {actividades.length} completadas
              </div>
            </div>
            <button className="btn btn-g btn-sm" onClick={() => navigate('/familiar/actividades')}>
              Ver todas <IcoArrow />
            </button>
          </div>

          {/* Barra de progreso global */}
          <div className="pbar mb16" style={{ height: 6 }}>
            <div className="pf" style={{ width: `${actividades.length > 0 ? (actCompletas / actividades.length) * 100 : 0}%` }} />
          </div>

          {actividades.map(act => (
            <div key={act.id} className="flex ic g10" style={{
              padding: '9px 12px', marginBottom: 6, borderRadius: 8,
              background: act.completada ? 'var(--teal2)' : 'var(--bg)',
              border: `1px solid ${act.completada ? '#a5ddc8' : 'var(--border)'}`,
            }}>
              <div style={{
                width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                background: act.completada ? 'var(--teal)' : 'var(--bg2)',
                border: `2px solid ${act.completada ? 'var(--teal)' : 'var(--border2)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff',
              }}>
                {act.completada && <IcoCheck />}
              </div>
              <div style={{ flex: 1 }}>
                <div className="ts" style={{
                  fontWeight: 500,
                  textDecoration: act.completada ? 'line-through' : 'none',
                  color: act.completada ? 'var(--text3)' : 'var(--text)',
                }}>
                  {act.titulo}
                </div>
              </div>
              <div className="txs tm">{act.hora}</div>
            </div>
          ))}
        </div>

      </div>

      {/* ── Seguimientos recientes ───────────────────────────────── */}
      <div className="card mb16">
        <div className="flex ic jb mb16">
          <div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>Últimos seguimientos</div>
            <div className="txs tm" style={{ marginTop: 2 }}>Notas del equipo terapéutico</div>
          </div>
          <button className="btn btn-g btn-sm" onClick={() => navigate('/familiar/seguimientos')}>
            Ver todos <IcoArrow />
          </button>
        </div>
        {seguimientos.map(s => (
          <div key={s.id} style={{
            padding: '12px 14px', marginBottom: 10, borderRadius: 8,
            background: s.tipo === 'positivo' ? 'var(--teal2)' : 'var(--bg)',
            border: `1px solid ${s.tipo === 'positivo' ? '#a5ddc8' : 'var(--border)'}`,
          }}>
            <div className="flex ic jb mb8">
              <div className="flex ic g6">
                {s.tipo === 'positivo' && <span style={{ color: 'var(--teal)' }}><IcoStar /></span>}
                <span className="ts f5">{s.autor}</span>
              </div>
              <span className="txs tm">{s.fecha}</span>
            </div>
            <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.5 }}>{s.texto}</div>
          </div>
        ))}
      </div>

      {/* ── Accesos rápidos ──────────────────────────────────────── */}
      <div className="g4">
        {[
          { label: 'Seguimientos',  icon: <IcoClipboard />, path: '/familiar/seguimientos', color: 'var(--teal)',   bg: 'var(--teal2)' },
          { label: 'Actividades',   icon: <IcoCheck />,     path: '/familiar/actividades',  color: 'var(--purple)', bg: 'var(--purple2)' },
          { label: 'Alertas',       icon: <IcoBell />,      path: '/familiar/alertas',      color: 'var(--amber)',  bg: 'var(--amber2)' },
          { label: 'Asistente IA',  icon: <IcoBot />,       path: '/familiar/asistente',    color: 'var(--blue)',   bg: 'var(--blue2)' },
        ].map(item => (
          <div key={item.label}
            className="card"
            style={{ cursor: 'pointer', textAlign: 'center', transition: 'box-shadow 0.15s' }}
            onClick={() => navigate(item.path)}
            onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.10)'}
            onMouseLeave={e => e.currentTarget.style.boxShadow = ''}>
            <div style={{
              width: 42, height: 42, borderRadius: 10, margin: '0 auto 10px',
              background: item.bg, color: item.color,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {item.icon}
            </div>
            <div className="ts f5">{item.label}</div>
          </div>
        ))}
      </div>

    </div>
  )
}
