import { useState } from 'react'

const ARTICULOS = [
  { id: 1, titulo: 'Técnicas de redirección en demencia',         categoria: 'Demencia',      resumen: 'Estrategias basadas en evidencia para manejar episodios de agitación y desorientación en pacientes con deterioro cognitivo.', tags: ['agitación', 'redirección', 'demencia'], fecha: '2025-11', destacado: true },
  { id: 2, titulo: 'Comunicación efectiva con el familiar cuidador', categoria: 'Familia',    resumen: 'Guía para establecer comunicación clara y empática con los familiares, reduciendo la carga emocional y mejorando la adherencia al plan terapéutico.', tags: ['familia', 'comunicación', 'cuidador'], fecha: '2025-10', destacado: true },
  { id: 3, titulo: 'Ejercicios cognitivos adaptados por nivel',   categoria: 'Cognitiva',     resumen: 'Banco de actividades cognitivas clasificadas por nivel de deterioro (leve, moderado, severo), con instrucciones para familiares.', tags: ['memoria', 'ejercicios', 'cognitiva'], fecha: '2025-09', destacado: false },
  { id: 4, titulo: 'Evaluación de bienestar — escala CMAI',       categoria: 'Evaluación',    resumen: 'Protocolo de uso de la escala CMAI para evaluar agitación en adultos mayores con demencia. Incluye interpretación de resultados.', tags: ['evaluación', 'escala', 'bienestar'], fecha: '2025-08', destacado: false },
  { id: 5, titulo: 'Plan de cuidados personalizado — plantilla',  categoria: 'Herramientas', resumen: 'Plantilla estructurada para armar el plan de cuidados individualizado, con campos para objetivos, actividades, frecuencia y seguimiento.', tags: ['plan', 'plantilla', 'herramienta'], fecha: '2025-07', destacado: false },
  { id: 6, titulo: 'Parkinson y deterioro cognitivo — manejo',    categoria: 'Neurología',    resumen: 'Abordaje terapéutico integral del paciente con Parkinson y compromiso cognitivo asociado. Farmacología, fisioterapia y terapia ocupacional.', tags: ['parkinson', 'neurología', 'fisioterapia'], fecha: '2025-06', destacado: false },
]

const CATEGORIAS = ['Todas', ...new Set(ARTICULOS.map(a => a.categoria))]
const CAT_COLORS = { Demencia: 'ch-pp', Familia: 'ch-teal', Cognitiva: 'ch-blu', Evaluación: 'ch-am', Herramientas: 'ch-gray', Neurología: 'ch-rd' }

const IcoSearch = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="M21 21l-4.35-4.35"/>
  </svg>
)
const IcoBook = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
  </svg>
)
const IcoStar = () => (
  <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
)

export default function TerIntConocimiento() {
  const [busqueda, setBusqueda] = useState('')
  const [cat, setCat]           = useState('Todas')
  const [expandido, setExpandido] = useState(null)

  const filtrados = ARTICULOS.filter(a => {
    const q = busqueda.toLowerCase()
    const matchQ = !q || a.titulo.toLowerCase().includes(q) || a.resumen.toLowerCase().includes(q) || a.tags.some(t => t.includes(q))
    const matchC = cat === 'Todas' || a.categoria === cat
    return matchQ && matchC
  })

  return (
    <div>
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Base de conocimiento</div>
          <div className="ts tm" style={{ marginTop: 3 }}>{ARTICULOS.length} recursos disponibles</div>
        </div>
      </div>

      {/* Buscador */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }}>
          <IcoSearch />
        </span>
        <input className="fi" value={busqueda} onChange={e => setBusqueda(e.target.value)}
          placeholder="Buscar por título, tema o etiqueta…" style={{ paddingLeft: 34 }} />
      </div>

      {/* Categorías */}
      <div className="flex ic g8 mb20" style={{ flexWrap: 'wrap' }}>
        {CATEGORIAS.map(c => (
          <button key={c} className={`btn btn-sm ${cat === c ? 'btn-p' : 'btn-s'}`} onClick={() => setCat(c)}>
            {c}
          </button>
        ))}
      </div>

      {/* Destacados */}
      {cat === 'Todas' && !busqueda && (
        <div className="mb20">
          <div className="ts f6 mb12 flex ic g6" style={{ color: 'var(--amber)' }}>
            <IcoStar /> Recursos destacados
          </div>
          <div className="g2">
            {ARTICULOS.filter(a => a.destacado).map(a => (
              <div key={a.id} className="card" style={{ background: 'var(--amber2)', border: '1px solid #f0cb8a', cursor: 'pointer' }}
                onClick={() => setExpandido(expandido === a.id ? null : a.id)}>
                <div className="flex ic jb mb8">
                  <span className={`chip ${CAT_COLORS[a.categoria] ?? 'ch-gray'}`}>{a.categoria}</span>
                  <span className="txs tm">{a.fecha}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>{a.titulo}</div>
                {expandido === a.id && (
                  <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55, marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(0,0,0,0.08)' }}>
                    {a.resumen}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lista completa */}
      {filtrados.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
          <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin resultados</div>
          <div className="ts tm" style={{ marginTop: 4 }}>Probá con otros términos de búsqueda.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtrados.map(a => (
            <div key={a.id} className="card" style={{ cursor: 'pointer', transition: 'box-shadow 0.15s' }}
              onClick={() => setExpandido(expandido === a.id ? null : a.id)}
              onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.08)'}
              onMouseLeave={e => e.currentTarget.style.boxShadow = ''}>
              <div className="flex ic jb">
                <div className="flex ic g10" style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ width: 34, height: 34, borderRadius: 8, background: 'var(--purple2)',
                    color: 'var(--purple)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <IcoBook />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{a.titulo}</div>
                    <div className="flex ic g6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                      <span className={`chip ${CAT_COLORS[a.categoria] ?? 'ch-gray'}`}>{a.categoria}</span>
                      {a.tags.map(t => <span key={t} className="chip ch-gray" style={{ fontSize: 10 }}>{t}</span>)}
                    </div>
                  </div>
                </div>
                <span style={{ color: 'var(--text3)', fontSize: 18, flexShrink: 0, marginLeft: 8 }}>
                  {expandido === a.id ? '−' : '+'}
                </span>
              </div>
              {expandido === a.id && (
                <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55, marginTop: 12,
                  paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                  {a.resumen}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
