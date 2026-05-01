import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Íconos ───────────────────────────────────────────────────────────────
const IcoCheck = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
  </svg>
)
const IcoX = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
  </svg>
)
const IcoStar = ({ filled }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor" strokeWidth="1.5">
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.562.562 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"/>
  </svg>
)

// ─── Modal de registro de progreso ───────────────────────────────────────
function ModalProgreso({ actividad, onGuardar, onCerrar }) {
  const esMultietapa = actividad.total_etapas > 1
  const [tipo,         setTipo]         = useState('completa')
  const [etapas,       setEtapas]       = useState(1)
  const [observacion,  setObservacion]  = useState('')
  const [satisfaccion, setSatisfaccion] = useState(0)
  const [guardando,    setGuardando]    = useState(false)

  async function handleGuardar() {
    setGuardando(true)
    await onGuardar({
      es_completada:      tipo === 'completa',
      etapas_completadas: tipo === 'parcial' ? etapas : null,
      observacion:        observacion.trim() || null,
      nivel_satisfaccion: satisfaccion || null,
    })
    setGuardando(false)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 999, padding: 16,
    }}>
      <div className="card" style={{
        width: '100%', maxWidth: 400, padding: '20px 22px',
        borderTop: '4px solid var(--teal)',
      }}>
        {/* Header */}
        <div className="flex ic jb mb20">
          <div style={{ fontSize: 15, fontWeight: 700 }}>Registrar actividad</div>
          <button className="btn btn-s btn-xs" onClick={onCerrar}><IcoX /></button>
        </div>

        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text3)', marginBottom: 14 }}>
          {actividad.titulo}
        </div>

        {/* Selector completa / parcial */}
        {esMultietapa ? (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 8 }}>
              ¿Cuántas etapas completaste?
            </div>
            <div className="flex ic g8" style={{ marginBottom: 10 }}>
              <button
                onClick={() => setTipo('completa')}
                style={{
                  flex: 1, padding: '8px 0', borderRadius: 8, fontSize: 13, fontWeight: 600,
                  border: `2px solid ${tipo === 'completa' ? 'var(--teal)' : 'var(--border)'}`,
                  background: tipo === 'completa' ? 'rgba(56,161,105,0.08)' : 'var(--bg)',
                  color: tipo === 'completa' ? 'var(--teal)' : 'var(--text3)', cursor: 'pointer',
                }}
              >
                ✅ Todas ({actividad.total_etapas})
              </button>
              <button
                onClick={() => setTipo('parcial')}
                style={{
                  flex: 1, padding: '8px 0', borderRadius: 8, fontSize: 13, fontWeight: 600,
                  border: `2px solid ${tipo === 'parcial' ? 'var(--amber)' : 'var(--border)'}`,
                  background: tipo === 'parcial' ? 'rgba(245,158,11,0.08)' : 'var(--bg)',
                  color: tipo === 'parcial' ? 'var(--amber)' : 'var(--text3)', cursor: 'pointer',
                }}
              >
                ⏳ Parcial
              </button>
            </div>

            {tipo === 'parcial' && (
              <div style={{ marginBottom: 4 }}>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 6 }}>
                  Etapas completadas (de {actividad.total_etapas})
                </div>
                <div className="flex ic g8" style={{ flexWrap: 'wrap' }}>
                  {Array.from({ length: actividad.total_etapas }, (_, i) => i + 1).map(n => (
                    <button
                      key={n}
                      onClick={() => setEtapas(n)}
                      style={{
                        width: 36, height: 36, borderRadius: 8, fontSize: 13, fontWeight: 700,
                        border: `2px solid ${etapas === n ? 'var(--amber)' : 'var(--border)'}`,
                        background: etapas === n ? 'rgba(245,158,11,0.12)' : 'var(--bg)',
                        color: etapas === n ? 'var(--amber)' : 'var(--text3)', cursor: 'pointer',
                      }}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{
            background: 'rgba(56,161,105,0.08)', border: '1px solid rgba(56,161,105,0.3)',
            borderRadius: 8, padding: '10px 12px', marginBottom: 16,
            fontSize: 13, color: 'var(--teal)', fontWeight: 600,
          }}>
            ✅ Actividad completada
          </div>
        )}

        {/* Satisfacción 1-5 */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 8 }}>
            ¿Cómo estuvo? <span style={{ opacity: 0.6 }}>(opcional)</span>
          </div>
          <div className="flex ic g4">
            {[1,2,3,4,5].map(n => (
              <button
                key={n}
                onClick={() => setSatisfaccion(satisfaccion === n ? 0 : n)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: 2,
                  color: n <= satisfaccion ? 'var(--amber)' : 'var(--border2)',
                }}
              >
                <IcoStar filled={n <= satisfaccion} />
              </button>
            ))}
            {satisfaccion > 0 && (
              <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 4 }}>
                {['','Muy difícil','Difícil','Normal','Bien','¡Excelente!'][satisfaccion]}
              </span>
            )}
          </div>
        </div>

        {/* Observación */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 6 }}>
            Observación <span style={{ opacity: 0.6 }}>(opcional)</span>
          </div>
          <textarea
            className="fi"
            value={observacion}
            onChange={e => setObservacion(e.target.value)}
            placeholder="¿Algo que quieras comentarle al terapeuta?"
            rows={2}
            style={{ fontSize: 13, resize: 'none', width: '100%' }}
          />
        </div>

        <div className="flex ic g8">
          <button
            className="btn btn-p"
            style={{ flex: 1 }}
            onClick={handleGuardar}
            disabled={guardando}
          >
            <IcoCheck /> {guardando ? 'Guardando…' : 'Guardar'}
          </button>
          <button className="btn btn-g" onClick={onCerrar}>Cancelar</button>
        </div>
      </div>
    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
export default function FamiliarActividades() {
  const { authFetch } = useAuth()
  const [actividades, setActividades] = useState([])
  const [loading,     setLoading]     = useState(true)
  const [toast,       setToast]       = useState({ msg: '', ok: true })
  const [modal,       setModal]       = useState(null)

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/familiar/actividades')
        if (res.ok) {
          const data = await res.json()
          setActividades(Array.isArray(data) ? data : [])
        } else { setActividades([]) }
      } catch { setActividades([]) }
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  function showToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 2800)
  }

  async function handleGuardarProgreso(opciones) {
    if (!modal) return
    try {
      const res = await authFetch('/progreso', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          actividad_id:       modal.id,
          es_completada:      opciones.es_completada,
          etapas_completadas: opciones.etapas_completadas,
          observacion:        opciones.observacion,
          nivel_satisfaccion: opciones.nivel_satisfaccion,
        }),
      })
      if (res.ok) {
        setActividades(prev => prev.map(a => a.id === modal.id
          ? { ...a, completada: opciones.es_completada, veces_realizadas: (a.veces_realizadas || 0) + 1 }
          : a
        ))
        showToast(
          opciones.es_completada
            ? '¡Actividad completada!'
            : `Progreso guardado (${opciones.etapas_completadas} etapa${opciones.etapas_completadas !== 1 ? 's' : ''})`
        )
      } else {
        showToast('Error al guardar. Intentá de nuevo.', false)
      }
    } catch {
      showToast('No se pudo conectar con el servidor.', false)
    }
    setModal(null)
  }

  const completadas = actividades.filter(a => a.completada).length
  const pct = actividades.length > 0 ? Math.round((completadas / actividades.length) * 100) : 0

  return (
    <div>
      <div className={`toast ${toast.msg ? 'visible' : ''} ${!toast.ok ? 'error' : ''}`}>{toast.msg}</div>

      {modal && (
        <ModalProgreso
          actividad={modal}
          onGuardar={handleGuardarProgreso}
          onCerrar={() => setModal(null)}
        />
      )}

      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Actividades</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            {completadas} de {actividades.length} completadas hoy · {pct}%
          </div>
        </div>
      </div>

      {/* Progreso del día */}
      <div className="card mb20">
        <div className="flex ic jb mb8">
          <span className="ts f5">Progreso del día</span>
          <span style={{
            fontSize: 22, fontWeight: 700,
            color: pct >= 70 ? 'var(--teal)' : pct >= 40 ? 'var(--amber)' : 'var(--text3)',
          }}>
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
      ) : actividades.length === 0 ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)', fontSize: 14 }}>
          No tenés actividades asignadas todavía.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {actividades.map(act => (
            <div
              key={act.id}
              className="card"
              onClick={() => !act.completada && setModal(act)}
              style={{
                borderLeft: `4px solid ${act.completada ? 'var(--teal)' : 'var(--blue)'}`,
                borderRadius: '0 var(--radius) var(--radius) 0',
                opacity: act.completada ? 0.75 : 1,
                transition: 'opacity 0.2s',
                cursor: act.completada ? 'default' : 'pointer',
              }}
            >
              <div className="flex ic g12">
                {/* Círculo indicador */}
                <div style={{
                  width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                  background: act.completada ? 'var(--teal)' : 'var(--bg)',
                  border: `2px solid ${act.completada ? 'var(--teal)' : 'var(--border2)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', transition: 'all 0.15s',
                }}>
                  {act.completada && <IcoCheck />}
                </div>

                {/* Info de la actividad */}
                <div style={{ flex: 1 }}>
                  <div className="flex ic jb">
                    <div style={{
                      fontSize: 14, fontWeight: 600,
                      textDecoration: act.completada ? 'line-through' : 'none',
                      color: act.completada ? 'var(--text3)' : 'var(--text)',
                    }}>
                      {act.titulo}
                    </div>
                    <div className="flex ic g6">
                      {act.total_etapas > 1 && (
                        <span className="chip txs" style={{
                          background: 'rgba(139,92,246,0.1)', color: '#8b5cf6',
                        }}>
                          {act.total_etapas} etapas
                        </span>
                      )}
                      {act.frecuencia && (
                        <span className="chip ch-gray txs">{act.frecuencia}</span>
                      )}
                    </div>
                  </div>

                  {act.descripcion && (
                    <div className="ts tm" style={{ marginTop: 4 }}>{act.descripcion}</div>
                  )}

                  <div className="flex ic g12" style={{ marginTop: 6 }}>
                    {act.veces_realizadas > 0 && (
                      <span className="txs" style={{ color: 'var(--teal)' }}>
                        {act.veces_realizadas} {act.veces_realizadas === 1 ? 'sesión' : 'sesiones'}
                      </span>
                    )}
                    {act.tasa_cumplimiento > 0 && (
                      <span className="txs" style={{
                        fontWeight: 600,
                        color: act.tasa_cumplimiento >= 80 ? 'var(--teal)'
                             : act.tasa_cumplimiento >= 50 ? 'var(--amber)' : 'var(--red)',
                      }}>
                        {act.tasa_cumplimiento}% cumplimiento
                      </span>
                    )}
                  </div>
                </div>

                {/* Botón registrar */}
                {!act.completada && (
                  <button
                    className="btn btn-p btn-sm"
                    style={{ flexShrink: 0, fontSize: 12 }}
                    onClick={e => { e.stopPropagation(); setModal(act) }}
                  >
                    Registrar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
