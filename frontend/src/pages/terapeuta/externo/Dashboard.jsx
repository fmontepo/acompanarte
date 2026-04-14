import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../context/AuthContext'

const MOCK_PACIENTES = [
  { id: 1, nombre: 'Roberto Méndez',   edad: 68, diagnostico: 'Deterioro cognitivo leve', ultima_visita: 'hace 5 días', proxima: 'Jue 10:00', av: 'RM', avClass: 'av-tl', registros: 12 },
  { id: 2, nombre: 'Elena Fernández',  edad: 72, diagnostico: 'Demencia vascular leve',    ultima_visita: 'hace 8 días', proxima: 'Vie 14:30', av: 'EF', avClass: 'av-pp', registros: 7  },
]

const MOCK_AGENDA = [
  { hora: '10:00', paciente: 'Roberto Méndez',  tipo: 'Evaluación',   av: 'RM', avClass: 'av-tl' },
  { hora: '14:30', paciente: 'Elena Fernández', tipo: 'Seguimiento',  av: 'EF', avClass: 'av-pp' },
]

export default function TerExtDashboard() {
  const { user, authFetch } = useAuth()
  const navigate = useNavigate()
  const [pacientes, setPacientes] = useState([])
  const [agenda, setAgenda]       = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/terapeuta/externo/dashboard')
        if (res.ok) {
          const data = await res.json()
          setPacientes(data.pacientes ?? MOCK_PACIENTES)
          setAgenda(data.agenda ?? MOCK_AGENDA)
        } else { setPacientes(MOCK_PACIENTES); setAgenda(MOCK_AGENDA) }
      } catch { setPacientes(MOCK_PACIENTES); setAgenda(MOCK_AGENDA) }
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
            {pacientes.length} pacientes asignados · {new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => navigate('/terapeuta/externo/registros')}>
          + Nuevo registro
        </button>
      </div>

      {/* Acceso limitado - info */}
      <div className="disc disc-tl mb20">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span>Como terapeuta externo, tenés acceso de solo lectura a los pacientes asignados y podés registrar tus propias observaciones.</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16 }}>
        {/* Pacientes */}
        <div>
          <div className="ts f6 mb12">Mis pacientes</div>
          {loading ? <div style={{ padding: 32, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
          : pacientes.map(p => (
            <div key={p.id} className="card mb10" style={{ cursor: 'pointer' }}
              onClick={() => navigate('/terapeuta/externo/registros')}>
              <div className="flex ic jb">
                <div className="flex ic g10">
                  <div className={`av ${p.avClass}`} style={{ width: 40, height: 40, fontSize: 14 }}>{p.av}</div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{p.nombre}</div>
                    <div className="txs tm">{p.edad} años · {p.diagnostico}</div>
                    <div className="txs tm" style={{ marginTop: 2 }}>
                      {p.registros} registros míos · Última visita: {p.ultima_visita}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div className="txs tm">Próxima visita</div>
                  <div className="ts f5" style={{ color: 'var(--teal)' }}>{p.proxima}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Agenda del día */}
        <div>
          <div className="ts f6 mb12">Agenda de hoy</div>
          <div className="card">
            {agenda.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 20, color: 'var(--text3)' }}>
                <div style={{ fontSize: 24, marginBottom: 6 }}>📅</div>
                <div className="ts">Sin visitas programadas</div>
              </div>
            ) : agenda.map((v, i) => (
              <div key={i} className="flex ic g10" style={{
                padding: '10px 0', borderBottom: i < agenda.length - 1 ? '1px solid var(--border)' : 'none',
              }}>
                <div style={{ width: 44, flexShrink: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--teal)' }}>{v.hora}</div>
                </div>
                <div className={`av ${v.avClass}`} style={{ width: 28, height: 28, fontSize: 10 }}>{v.av}</div>
                <div>
                  <div className="ts f5">{v.paciente}</div>
                  <div className="txs tm">{v.tipo}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
