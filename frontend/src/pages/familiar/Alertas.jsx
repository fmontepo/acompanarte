import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

const MOCK = [
  { id: 1, tipo: 'urgente',   titulo: 'Episodio de desorientación',     texto: 'Se registró un episodio de desorientación el día lunes a las 17:30. El equipo lo monitoreó y fue resuelto. Se recomienda estar atento en ese horario.', fecha: 'hace 2 días', leida: false },
  { id: 2, tipo: 'aviso',     titulo: 'Consentimiento próximo a vencer', texto: 'El consentimiento de seguimiento vence en 5 días. Por favor, coordiná con el equipo para renovarlo a tiempo.', fecha: 'hace 1 día', leida: false },
  { id: 3, tipo: 'positivo',  titulo: 'Progreso destacado',              texto: 'Roberto completó el 100% de las actividades del día por tercera vez consecutiva. ¡Excelente trabajo del equipo y la familia!', fecha: 'hace 3 días', leida: true },
  { id: 4, tipo: 'aviso',     titulo: 'Nueva actividad asignada',        texto: 'El terapeuta asignó una nueva actividad de memoria visual para esta semana. Revisala en la sección Actividades.', fecha: 'hace 4 días', leida: true },
  { id: 5, tipo: 'positivo',  titulo: 'Mejora en sesión cognitiva',      texto: 'La Lic. Ruiz reporta mejoras significativas en el reconocimiento facial durante la última sesión.', fecha: 'hace 5 días', leida: true },
]

const TIPO_META = {
  urgente:  { label: 'Urgente', chipClass: 'ch-rd',   barColor: 'var(--red)',   bg: 'var(--red2)' },
  aviso:    { label: 'Aviso',   chipClass: 'ch-am',   barColor: 'var(--amber)', bg: 'var(--amber2)' },
  positivo: { label: 'Buenas noticias', chipClass: 'ch-teal', barColor: 'var(--teal)', bg: 'var(--teal2)' },
}

const IcoBell = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
  </svg>
)

export default function FamiliarAlertas() {
  const { authFetch } = useAuth()
  const [alertas, setAlertas]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [filtro, setFiltro]     = useState('todas')

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/familiar/alertas')
        if (res.ok) {
          const data = await res.json()
          setAlertas(Array.isArray(data) ? data : [])
        } else { setAlertas([]) }
      } catch { setAlertas(MOCK) }  // error de red → mock
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  function marcarLeida(id) {
    setAlertas(prev => prev.map(a => a.id === id ? { ...a, leida: true } : a))
  }

  const noLeidas = alertas.filter(a => !a.leida).length
  const filtradas = filtro === 'todas' ? alertas
    : filtro === 'noLeidas' ? alertas.filter(a => !a.leida)
    : alertas.filter(a => a.tipo === filtro)

  return (
    <div>
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Alertas</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {noLeidas > 0 ? `${noLeidas} sin leer` : 'Todo al día'} · {alertas.length} alertas en total
          </div>
        </div>
        {noLeidas > 0 && (
          <button className="btn btn-s btn-sm" onClick={() => setAlertas(prev => prev.map(a => ({ ...a, leida: true })))}>
            Marcar todas como leídas
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="flex ic g8 mb20" style={{ flexWrap: 'wrap' }}>
        {[
          { val: 'todas',    label: `Todas (${alertas.length})` },
          { val: 'noLeidas', label: `Sin leer (${noLeidas})` },
          { val: 'urgente',  label: 'Urgentes' },
          { val: 'aviso',    label: 'Avisos' },
          { val: 'positivo', label: 'Noticias' },
        ].map(f => (
          <button key={f.val} className={`btn btn-sm ${filtro === f.val ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltro(f.val)}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      ) : filtradas.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🔔</div>
          <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin alertas</div>
          <div className="ts tm" style={{ marginTop: 4 }}>No hay alertas que coincidan con el filtro seleccionado.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtradas.map(a => {
            const meta = TIPO_META[a.tipo] ?? TIPO_META.aviso
            return (
              <div key={a.id} className="card" style={{
                borderLeft: `4px solid ${meta.barColor}`,
                borderRadius: '0 var(--radius) var(--radius) 0',
                opacity: a.leida ? 0.7 : 1,
                background: a.leida ? undefined : meta.bg,
              }}>
                <div className="flex ic jb mb8">
                  <div className="flex ic g8">
                    <span style={{ color: meta.barColor }}><IcoBell /></span>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>{a.titulo}</span>
                    {!a.leida && <span className="chip ch-rd" style={{ fontSize: 10 }}>Nuevo</span>}
                  </div>
                  <div className="flex ic g8">
                    <span className={`chip ${meta.chipClass}`}>{meta.label}</span>
                    <span className="txs tm">{a.fecha}</span>
                  </div>
                </div>
                <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.5, marginBottom: a.leida ? 0 : 10 }}>
                  {a.texto}
                </div>
                {!a.leida && (
                  <button className="btn btn-s btn-xs" onClick={() => marcarLeida(a.id)}>
                    Marcar como leída
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
