import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

const MOCK = [
  { id: 1, paciente: 'Carmen Villalba',  av: 'CV', avClass: 'av-pp', tipo: 'inactividad',  titulo: 'Sin actividades completadas',       texto: 'Carmen no ha completado ninguna actividad en los últimos 3 días. Se recomienda contactar al familiar para evaluar la situación.', fecha: 'hace 6 h',   resuelta: false },
  { id: 2, paciente: 'Sofía Blanco',     av: 'SB', avClass: 'av-bu', tipo: 'incidente',    titulo: 'Episodio de agitación reportado',   texto: 'El familiar reportó un episodio de agitación vespertina el día martes. Duración aproximada: 20 minutos. Se recomienda revisar el plan de actividades del horario 17-19 hs.', fecha: 'hace 1 día',  resuelta: false },
  { id: 3, paciente: 'Roberto Méndez',   av: 'RM', avClass: 'av-tl', tipo: 'consentimiento', titulo: 'Consentimiento próximo a vencer',  texto: 'El consentimiento de seguimiento de Roberto vence en 5 días. Es necesario coordinar la renovación con el familiar antes del vencimiento.', fecha: 'hace 2 días', resuelta: false },
  { id: 4, paciente: 'Héctor Rodríguez', av: 'HR', avClass: 'av-am', tipo: 'progreso',     titulo: 'Mejora destacada en motricidad',     texto: 'Héctor logró completar el circuito de equilibrio sin asistencia por primera vez. Se recomienda aumentar la dificultad de los ejercicios.', fecha: 'hace 3 días', resuelta: true },
  { id: 5, paciente: 'Carmen Villalba',  av: 'CV', avClass: 'av-pp', tipo: 'progreso',     titulo: 'Sesión cognitiva exitosa',           texto: 'La sesión de reconocimiento fotográfico de ayer tuvo excelentes resultados. Carmen recordó correctamente 9 de 10 imágenes familiares.', fecha: 'hace 4 días', resuelta: true },
]

const TIPO_META = {
  inactividad:   { label: 'Inactividad',   chipClass: 'ch-rd',   barColor: 'var(--red)',    bg: 'var(--red2)' },
  incidente:     { label: 'Incidente',     chipClass: 'ch-am',   barColor: 'var(--amber)',  bg: 'var(--amber2)' },
  consentimiento:{ label: 'Consentimiento',chipClass: 'ch-am',   barColor: 'var(--amber)',  bg: 'var(--amber2)' },
  progreso:      { label: 'Progreso',      chipClass: 'ch-teal', barColor: 'var(--teal)',   bg: 'var(--teal2)' },
}

export default function TerIntAlertas() {
  const { authFetch } = useAuth()
  const [alertas, setAlertas]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [filtro, setFiltro]     = useState('activas')
  const [toast, setToast]       = useState('')

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/alertas/')
        if (res.ok) {
          const data = await res.json()
          setAlertas(Array.isArray(data) && data.length > 0 ? data : MOCK)
        } else { setAlertas(MOCK) }
      } catch { setAlertas(MOCK) }
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  function resolver(id) {
    setAlertas(prev => prev.map(a => a.id === id ? { ...a, resuelta: true } : a))
    setToast('Alerta marcada como resuelta.')
    setTimeout(() => setToast(''), 2500)
  }

  const pendientes = alertas.filter(a => !a.resuelta)
  const resueltas  = alertas.filter(a => a.resuelta)
  const mostrar = filtro === 'activas' ? pendientes : filtro === 'resueltas' ? resueltas : alertas

  return (
    <div>
      <div className={`toast ${toast ? 'visible' : ''}`}>{toast}</div>

      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Alertas clínicas</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {pendientes.length} activas · {resueltas.length} resueltas
          </div>
        </div>
      </div>

      <div className="flex ic g8 mb20">
        {[
          { val: 'activas',   label: `Activas (${pendientes.length})` },
          { val: 'resueltas', label: `Resueltas (${resueltas.length})` },
          { val: 'todas',     label: `Todas (${alertas.length})` },
        ].map(f => (
          <button key={f.val} className={`btn btn-sm ${filtro === f.val ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltro(f.val)}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      : mostrar.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
          <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin alertas activas</div>
          <div className="ts tm" style={{ marginTop: 4 }}>Todos los pacientes están en seguimiento normal.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {mostrar.map(a => {
            const meta = TIPO_META[a.tipo] ?? TIPO_META.incidente
            return (
              <div key={a.id} className="card" style={{
                borderLeft: `4px solid ${meta.barColor}`,
                borderRadius: '0 var(--radius) var(--radius) 0',
                opacity: a.resuelta ? 0.65 : 1,
              }}>
                <div className="flex ic jb mb10">
                  <div className="flex ic g10">
                    <div className={`av ${a.avClass}`} style={{ width: 32, height: 32, fontSize: 11 }}>{a.av}</div>
                    <div>
                      <div className="ts f5">{a.paciente}</div>
                      <div className="txs tm">{a.fecha}</div>
                    </div>
                  </div>
                  <div className="flex ic g8">
                    <span className={`chip ${meta.chipClass}`}>{meta.label}</span>
                    {a.resuelta && <span className="chip ch-teal">Resuelta</span>}
                  </div>
                </div>
                <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 6 }}>{a.titulo}</div>
                <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55, marginBottom: a.resuelta ? 0 : 12 }}>
                  {a.texto}
                </div>
                {!a.resuelta && (
                  <button className="btn btn-s btn-sm" onClick={() => resolver(a.id)}>
                    Marcar como resuelta
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
