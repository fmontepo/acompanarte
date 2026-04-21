import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

const MOCK = [
  { id: 1, titulo: 'Ejercicio de respiración',     descripcion: 'Técnica de respiración diafragmática 4-7-8. Duración: 10 minutos.', completada: true,  hora: '08:30', categoria: 'Bienestar',   color: 'var(--teal)',   bg: 'var(--teal2)',   progreso: 100 },
  { id: 2, titulo: 'Lectura guiada',               descripcion: 'Lectura de 2 páginas del libro seleccionado con voz en voz alta.', completada: true,  hora: '10:00', categoria: 'Cognitiva',   color: 'var(--blue)',   bg: 'var(--blue2)',   progreso: 100 },
  { id: 3, titulo: 'Caminata matutina',             descripcion: 'Caminata de 20 minutos a paso moderado en el patio o parque.', completada: false, hora: '11:30', categoria: 'Física',      color: 'var(--purple)', bg: 'var(--purple2)', progreso: 0 },
  { id: 4, titulo: 'Ejercicio de memoria visual',  descripcion: 'Identificar 5 fotografías familiares y nombrar a las personas.', completada: false, hora: '16:00', categoria: 'Cognitiva',   color: 'var(--amber)',  bg: 'var(--amber2)',  progreso: 0 },
  { id: 5, titulo: 'Música y relajación',          descripcion: 'Escuchar playlist seleccionada por el terapeuta. 30 minutos.', completada: false, hora: '20:00', categoria: 'Bienestar',   color: 'var(--pink)',   bg: 'var(--pink2)',   progreso: 0 },
]

const IcoCheck = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
  </svg>
)

export default function FamiliarActividades() {
  const { authFetch } = useAuth()
  const [actividades, setActividades] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState('')

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/familiar/actividades')
        if (res.ok) {
          const data = await res.json()
          setActividades(Array.isArray(data) ? data : [])
        } else { setActividades([]) }
      } catch { setActividades(MOCK) }  // error de red → mock
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  async function toggleCompletada(id) {
    const act = actividades.find(a => a.id === id)
    if (!act) return

    // Actualización optimista
    setActividades(prev => prev.map(a => a.id === id
      ? { ...a, completada: !a.completada, progreso: a.completada ? 0 : 100 }
      : a
    ))

    if (!act.completada) {
      // Marcar como completada → registrar progreso en el backend
      try {
        await authFetch('/api/v1/progreso/', {
          method: 'POST',
          body: JSON.stringify({ actividad_id: id }),
        })
        setToast('¡Actividad completada!')
      } catch {
        // Si falla, revertir el cambio optimista
        setActividades(prev => prev.map(a => a.id === id ? { ...a, completada: false, progreso: 0 } : a))
        setToast('Error al guardar. Intentá de nuevo.')
      }
    } else {
      // Desmarcar — no hay endpoint de borrado, queda en estado local
      setToast('Actividad marcada como pendiente.')
    }
    setTimeout(() => setToast(''), 2500)
  }

  const completadas = actividades.filter(a => a.completada).length
  const pct = actividades.length > 0 ? Math.round((completadas / actividades.length) * 100) : 0

  return (
    <div>
      <div className={`toast ${toast ? 'visible' : ''}`}>{toast}</div>

      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Actividades</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {completadas} de {actividades.length} completadas hoy · {pct}%
          </div>
        </div>
      </div>

      {/* Progreso global */}
      <div className="card mb20">
        <div className="flex ic jb mb8">
          <span className="ts f5">Progreso del día</span>
          <span style={{ fontSize: 22, fontWeight: 700, color: pct >= 70 ? 'var(--teal)' : pct >= 40 ? 'var(--amber)' : 'var(--text3)' }}>
            {pct}%
          </span>
        </div>
        <div className="pbar" style={{ height: 10 }}>
          <div className="pf" style={{
            width: `${pct}%`,
            background: pct >= 70 ? 'var(--teal)' : pct >= 40 ? 'var(--amber)' : 'var(--text3)',
          }} />
        </div>
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {actividades.map(act => (
            <div key={act.id} className="card" style={{
              borderLeft: `4px solid ${act.completada ? 'var(--teal)' : act.color}`,
              borderRadius: '0 var(--radius) var(--radius) 0',
              opacity: act.completada ? 0.75 : 1,
              transition: 'opacity 0.2s',
            }}>
              <div className="flex ic g12">
                {/* Checkbox */}
                <button
                  onClick={() => toggleCompletada(act.id)}
                  style={{
                    width: 26, height: 26, borderRadius: '50%', border: 'none',
                    background: act.completada ? 'var(--teal)' : 'var(--bg)',
                    border: `2px solid ${act.completada ? 'var(--teal)' : 'var(--border2)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: 'pointer', color: '#fff', flexShrink: 0, transition: 'all 0.15s',
                  }}>
                  {act.completada && <IcoCheck />}
                </button>

                {/* Info */}
                <div style={{ flex: 1 }}>
                  <div className="flex ic jb">
                    <div style={{
                      fontSize: 14, fontWeight: 600,
                      textDecoration: act.completada ? 'line-through' : 'none',
                      color: act.completada ? 'var(--text3)' : 'var(--text)',
                    }}>
                      {act.titulo}
                    </div>
                    <div className="flex ic g8">
                      <span className="chip ch-gray txs">{act.hora}</span>
                      <span className="chip" style={{ background: act.bg, color: act.color, fontSize: 11 }}>
                        {act.categoria}
                      </span>
                    </div>
                  </div>
                  <div className="ts tm" style={{ marginTop: 4 }}>{act.descripcion}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
