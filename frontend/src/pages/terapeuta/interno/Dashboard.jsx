import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../context/AuthContext'

const MOCK_PACIENTES = [
  { id: 1, nombre: 'Roberto Méndez',    edad: 68, diagnostico: 'Deterioro cognitivo leve',    bienestar: 72, ultima_sesion: 'Hoy',       proxima: 'Mañana 10:00',  av: 'RM', avClass: 'av-tl' },
  { id: 2, nombre: 'Carmen Villalba',   edad: 74, diagnostico: 'Alzheimer estadio temprano',  bienestar: 55, ultima_sesion: 'Ayer',      proxima: 'Vie 11:30',     av: 'CV', avClass: 'av-pp' },
  { id: 3, nombre: 'Héctor Rodríguez',  edad: 71, diagnostico: 'Parkinson + deterioro leve',  bienestar: 81, ultima_sesion: 'Lun',       proxima: 'Jue 09:00',     av: 'HR', avClass: 'av-am' },
  { id: 4, nombre: 'Sofía Blanco',      edad: 66, diagnostico: 'Depresión + ansiedad',        bienestar: 63, ultima_sesion: 'hace 3 d.', proxima: 'Vie 15:00',     av: 'SB', avClass: 'av-bu' },
]
const MOCK_ALERTAS = [
  { id: 1, paciente: 'Carmen Villalba',  texto: 'Sin actividades completadas en 3 días.',          tipo: 'rd' },
  { id: 2, paciente: 'Sofía Blanco',     texto: 'Familiar reportó episodio de agitación vespertina.', tipo: 'am' },
  { id: 3, paciente: 'Roberto Méndez',   texto: 'Consentimiento de seguimiento próximo a vencer.',  tipo: 'am' },
]

function BioBarra({ pct }) {
  const color = pct >= 70 ? 'var(--teal)' : pct >= 50 ? 'var(--amber)' : 'var(--red)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
      <div className="pbar" style={{ flex: 1, height: 5 }}>
        <div className="pf" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="txs" style={{ color, fontWeight: 600, width: 28 }}>{pct}%</span>
    </div>
  )
}

export default function TerIntDashboard() {
  const { user, authFetch } = useAuth()
  const navigate = useNavigate()
  const [pacientes, setPacientes] = useState([])
  const [alertas, setAlertas]     = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/terapeuta/dashboard')
        if (res.ok) {
          const data = await res.json()
          setPacientes(data.pacientes ?? MOCK_PACIENTES)
          setAlertas(data.alertas ?? MOCK_ALERTAS)
        } else { setPacientes(MOCK_PACIENTES); setAlertas(MOCK_ALERTAS) }
      } catch { setPacientes(MOCK_PACIENTES); setAlertas(MOCK_ALERTAS) }
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  const hora   = new Date().getHours()
  const saludo = hora < 13 ? 'Buenos días' : hora < 20 ? 'Buenas tardes' : 'Buenas noches'

  return (
    <div>
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{saludo}, {user?.nombre ?? 'Terapeuta'} 👋</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {pacientes.length} pacientes a cargo · {new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => navigate('/terapeuta/interno/registros')}>
          + Nuevo registro
        </button>
      </div>

      {/* KPIs */}
      <div className="g4 mb20">
        {[
          { label: 'Pacientes activos',      value: pacientes.length,                                          color: 'var(--teal)' },
          { label: 'Sesiones esta semana',   value: 8,                                                          color: 'var(--purple)' },
          { label: 'Alertas pendientes',     value: alertas.length,                                             color: alertas.length > 0 ? 'var(--amber)' : 'var(--teal)' },
          { label: 'Actividades asignadas',  value: 17,                                                         color: 'var(--blue)' },
        ].map(k => (
          <div key={k.label} className="stat">
            <div className="sn" style={{ color: k.color }}>{k.value}</div>
            <div className="sl">{k.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16 }}>
        {/* Pacientes */}
        <div>
          <div className="ts f6 mb12">Mis pacientes</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {loading ? <div style={{ padding: 32, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div> :
              pacientes.map(p => (
                <div key={p.id} className="card" style={{ cursor: 'pointer' }}
                  onClick={() => navigate('/terapeuta/interno/registros')}>
                  <div className="flex ic jb">
                    <div className="flex ic g10">
                      <div className={`av ${p.avClass}`} style={{ width: 38, height: 38, fontSize: 13 }}>{p.av}</div>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{p.nombre}</div>
                        <div className="txs tm">{p.edad} años · {p.diagnostico}</div>
                        <BioBarra pct={p.bienestar} />
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div className="txs tm">Última sesión</div>
                      <div className="ts f5">{p.ultima_sesion}</div>
                      <div className="txs tm" style={{ marginTop: 4 }}>Próxima</div>
                      <div className="txs" style={{ color: 'var(--teal)', fontWeight: 500 }}>{p.proxima}</div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Alertas panel */}
        <div>
          <div className="ts f6 mb12">Alertas activas</div>
          {alertas.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 24, color: 'var(--text3)' }}>
              <div style={{ fontSize: 24, marginBottom: 6 }}>✅</div>
              <div className="ts">Sin alertas pendientes</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {alertas.map(a => (
                <div key={a.id} className={`disc disc-${a.tipo === 'rd' ? 'rd' : ''}`}
                  style={a.tipo === 'am' ? { background: 'var(--amber2)', borderColor: '#f0cb8a', color: 'var(--amber)' } : {}}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 12 }}>{a.paciente}</div>
                    <div style={{ marginTop: 2 }}>{a.texto}</div>
                  </div>
                </div>
              ))}
              <button className="btn btn-s btn-sm w100" onClick={() => navigate('/terapeuta/interno/alertas')}>
                Ver todas las alertas
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
