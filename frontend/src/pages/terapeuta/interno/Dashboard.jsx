import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../context/AuthContext'


function BioBarra({ pct }) {
  if (pct == null) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
        <div className="pbar" style={{ flex: 1, height: 5 }}>
          <div className="pf" style={{ width: '0%' }} />
        </div>
        <span className="txs" style={{ color: 'var(--text3)', width: 50, fontSize: 10 }}>sin datos</span>
      </div>
    )
  }
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
  const [kpis, setKpis]           = useState({ sesiones: 0, alertas: 0, actividades: 0 })
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/terapeuta/dashboard')
        if (res.ok) {
          const data = await res.json()
          setPacientes(data.pacientes ?? [])
          setAlertas(data.alertas ?? [])
          setKpis(data.kpis ?? { sesiones: 0, alertas: 0, actividades: 0 })
        } else { setPacientes([]); setAlertas([]); setKpis({ sesiones: 0, alertas: 0, actividades: 0 }) }
      } catch { setPacientes([]); setAlertas([]); setKpis({ sesiones: 0, alertas: 0, actividades: 0 }) }
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
      </div>

      {/* KPIs */}
      <div className="g4 mb20">
        {[
          { label: 'Pacientes activos',      value: pacientes.length,                                          color: 'var(--teal)' },
          { label: 'Sesiones esta semana',   value: kpis.sesiones,                                             color: 'var(--purple)' },
          { label: 'Alertas pendientes',     value: alertas.length,                                             color: alertas.length > 0 ? 'var(--amber)' : 'var(--teal)' },
          { label: 'Actividades asignadas',  value: kpis.actividades,                                          color: 'var(--blue)' },
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
                        <div className="txs tm">{p.edad != null ? `${p.edad} años · ` : ''}{p.diagnostico}</div>
                        <BioBarra pct={p.bienestar} />
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div className="txs tm">Última sesión</div>
                      <div className="ts f5">{p.ultima_sesion ?? 'Sin registros'}</div>
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
