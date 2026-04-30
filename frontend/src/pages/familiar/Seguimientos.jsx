import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

const MOCK = [
  { id: 1, fecha: '2026-04-14T09:15:00', autor: 'Dr. Luis Herrera',   rol: 'Terapeuta Interno', av: 'LH', avClass: 'av-pp', texto: 'Buena respuesta a los ejercicios matutinos. Estado de ánimo positivo y colaborativo durante toda la sesión. Se recomienda mantener la rutina actual.', tipo: 'positivo' },
  { id: 2, fecha: '2026-04-13T18:00:00', autor: 'Lic. Patricia Ruiz', rol: 'Terapeuta Cognitiva', av: 'PR', avClass: 'av-tl', texto: 'Sesión de terapia cognitiva completada satisfactoriamente. Se notan mejoras en reconocimiento de caras familiares y ubicación temporal.', tipo: 'positivo' },
  { id: 3, fecha: '2026-04-11T10:30:00', autor: 'Dr. Luis Herrera',   rol: 'Terapeuta Interno', av: 'LH', avClass: 'av-pp', texto: 'Episodio de desorientación breve durante la mañana. Duró aproximadamente 10 minutos. Se calmó con música y compañía familiar. Recomendamos mantener la rutina de horarios fijos.', tipo: 'neutral' },
  { id: 4, fecha: '2026-04-09T16:45:00', autor: 'Lic. Patricia Ruiz', rol: 'Terapeuta Cognitiva', av: 'PR', avClass: 'av-tl', texto: 'Ejercicios de memoria con fotografías familiares. Recordó correctamente 8 de 10 personas. Excelente progreso respecto a la semana anterior.', tipo: 'positivo' },
  { id: 5, fecha: '2026-04-07T11:00:00', autor: 'Dr. Luis Herrera',   rol: 'Terapeuta Interno', av: 'LH', avClass: 'av-pp', texto: 'Jornada con algo de agitación vespertina. Se aplicó técnica de redirección con éxito. Familiar presente durante todo el episodio. Recomendamos reducir estímulos en horario 17-19 hs.', tipo: 'alerta' },
]

function formatFecha(iso) {
  const d = new Date(iso)
  const hoy = new Date()
  const ayer = new Date(hoy); ayer.setDate(hoy.getDate() - 1)
  const hora = d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  if (d.toDateString() === hoy.toDateString())  return `Hoy, ${hora}`
  if (d.toDateString() === ayer.toDateString()) return `Ayer, ${hora}`
  return d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' }) + ', ' + hora
}

const TIPO_META = {
  positivo: { label: 'Positivo', chipClass: 'ch-teal',  barColor: 'var(--teal)' },
  neutral:  { label: 'Neutro',   chipClass: 'ch-gray',  barColor: 'var(--text3)' },
  alerta:   { label: 'Atención', chipClass: 'ch-am',    barColor: 'var(--amber)' },
}

export default function FamiliarSeguimientos() {
  const { authFetch } = useAuth()
  const [registros, setRegistros]         = useState([])
  const [pacienteNombre, setPacienteNombre] = useState('')
  const [loading, setLoading]             = useState(true)
  const [filtro, setFiltro]               = useState('todos')

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const [resDash, resSeg] = await Promise.allSettled([
          authFetch('/familiar/dashboard'),
          authFetch('/familiar/seguimientos'),
        ])
        if (resDash.status === 'fulfilled' && resDash.value.ok) {
          const dash = await resDash.value.json()
          setPacienteNombre(dash?.paciente?.nombre || '')
        }
        if (resSeg.status === 'fulfilled' && resSeg.value.ok) {
          const data = await resSeg.value.json()
          setRegistros(Array.isArray(data) ? data : [])
        } else { setRegistros([]) }
      } catch { setRegistros(MOCK) }  // error de red → mock
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  const filtrados = filtro === 'todos' ? registros : registros.filter(r => r.tipo === filtro)

  return (
    <div>
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Seguimientos</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {pacienteNombre ? `Notas del equipo terapéutico sobre ${pacienteNombre}` : 'Notas del equipo terapéutico'}
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex ic g8 mb20">
        {['todos', 'positivo', 'neutral', 'alerta'].map(f => (
          <button key={f} className={`btn btn-sm ${filtro === f ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltro(f)}>
            {f === 'todos' ? `Todos (${registros.length})` : `${TIPO_META[f]?.label} (${registros.filter(r => r.tipo === f).length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      ) : filtrados.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>📋</div>
          <div style={{ fontWeight: 600 }}>Sin seguimientos</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {filtrados.map(r => {
            const meta = TIPO_META[r.tipo] ?? TIPO_META.neutral
            return (
              <div key={r.id} className="card" style={{
                borderLeft: `4px solid ${meta.barColor}`,
                borderRadius: '0 var(--radius) var(--radius) 0',
              }}>
                <div className="flex ic jb mb12">
                  <div className="flex ic g10">
                    <div className={`av ${r.avClass}`} style={{ width: 32, height: 32, fontSize: 11 }}>{r.av}</div>
                    <div>
                      <div className="ts f5">{r.autor}</div>
                      <div className="txs tm">{r.rol}</div>
                    </div>
                  </div>
                  <div className="flex ic g8">
                    <span className={`chip ${meta.chipClass}`}>{meta.label}</span>
                    <span className="txs tm">{formatFecha(r.fecha)}</span>
                  </div>
                </div>
                <div style={{ fontSize: 13.5, color: 'var(--text2)', lineHeight: 1.6 }}>{r.texto}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
