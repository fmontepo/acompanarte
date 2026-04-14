import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

const PACIENTES = ['Roberto Méndez', 'Carmen Villalba', 'Héctor Rodríguez', 'Sofía Blanco']
const CATEGORIAS = ['Cognitiva', 'Física', 'Bienestar', 'Social', 'Comunicación']

const MOCK = [
  { id: 1, titulo: 'Ejercicio de respiración',    paciente: 'Roberto Méndez',   categoria: 'Bienestar',  frecuencia: 'Diaria',   completadas: 6, total: 7, activa: true },
  { id: 2, titulo: 'Reconocimiento fotográfico',  paciente: 'Carmen Villalba',  categoria: 'Cognitiva',  frecuencia: 'Diaria',   completadas: 2, total: 7, activa: true },
  { id: 3, titulo: 'Caminata matutina',            paciente: 'Héctor Rodríguez', categoria: 'Física',     frecuencia: 'Diaria',   completadas: 5, total: 7, activa: true },
  { id: 4, titulo: 'Lectura guiada',               paciente: 'Roberto Méndez',   categoria: 'Cognitiva',  frecuencia: 'Diaria',   completadas: 7, total: 7, activa: true },
  { id: 5, titulo: 'Terapia de reminiscencia',    paciente: 'Carmen Villalba',  categoria: 'Social',     frecuencia: 'Semanal',  completadas: 1, total: 2, activa: true },
  { id: 6, titulo: 'Ejercicios de equilibrio',    paciente: 'Héctor Rodríguez', categoria: 'Física',     frecuencia: 'Semanal',  completadas: 2, total: 2, activa: false },
  { id: 7, titulo: 'Música y relajación',          paciente: 'Sofía Blanco',     categoria: 'Bienestar',  frecuencia: 'Diaria',   completadas: 4, total: 7, activa: true },
]

const CAT_COLORS = {
  Cognitiva: { color: 'var(--purple)', bg: 'var(--purple2)' },
  Física:    { color: 'var(--blue)',   bg: 'var(--blue2)' },
  Bienestar: { color: 'var(--teal)',   bg: 'var(--teal2)' },
  Social:    { color: 'var(--amber)',  bg: 'var(--amber2)' },
  Comunicación: { color: 'var(--pink)', bg: 'var(--pink2)' },
}

function ModalNueva({ onClose, onSave }) {
  const [form, setForm] = useState({ titulo: '', paciente: '', categoria: 'Cognitiva', frecuencia: 'Diaria', descripcion: '' })
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.titulo.trim() || !form.paciente) return
    setSaving(true)
    await new Promise(r => setTimeout(r, 500))
    setSaving(false)
    onSave(form)
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">Nueva actividad</div>
          <button className="btn btn-g btn-sm" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb">
            <div className="fg">
              <label className="fl">Título *</label>
              <input className="fi" value={form.titulo} onChange={e => setForm(f => ({ ...f, titulo: e.target.value }))} placeholder="Ej: Ejercicio de memoria visual" />
            </div>
            <div className="fg">
              <label className="fl">Paciente *</label>
              <select className="fs" value={form.paciente} onChange={e => setForm(f => ({ ...f, paciente: e.target.value }))}>
                <option value="">Seleccioná…</option>
                {PACIENTES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="fr2">
              <div className="fg">
                <label className="fl">Categoría</label>
                <select className="fs" value={form.categoria} onChange={e => setForm(f => ({ ...f, categoria: e.target.value }))}>
                  {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="fg">
                <label className="fl">Frecuencia</label>
                <select className="fs" value={form.frecuencia} onChange={e => setForm(f => ({ ...f, frecuencia: e.target.value }))}>
                  {['Diaria', 'Semanal', 'Quincenal', 'Mensual'].map(fr => <option key={fr} value={fr}>{fr}</option>)}
                </select>
              </div>
            </div>
            <div className="fg">
              <label className="fl">Descripción</label>
              <textarea className="fi fta" value={form.descripcion} rows={3}
                onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                placeholder="Instrucciones para el familiar o cuidador…" />
            </div>
          </div>
          <div className="mf">
            <button type="button" className="btn btn-s" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving || !form.titulo || !form.paciente}>
              {saving ? 'Guardando…' : 'Crear actividad'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function TerIntActividades() {
  const { authFetch } = useAuth()
  const [actividades, setActividades] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal]     = useState(false)
  const [filtroPac, setFiltroPac] = useState('todos')
  const [toast, setToast]     = useState('')

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/actividades/')
        if (res.ok) {
          const data = await res.json()
          setActividades(Array.isArray(data) && data.length > 0 ? data : MOCK)
        } else { setActividades(MOCK) }
      } catch { setActividades(MOCK) }
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  function handleSave(form) {
    setActividades(prev => [{ id: Date.now(), ...form, completadas: 0, total: 7, activa: true }, ...prev])
    setModal(false)
    setToast('Actividad creada correctamente.')
    setTimeout(() => setToast(''), 2500)
  }

  const filtradas = filtroPac === 'todos' ? actividades : actividades.filter(a => a.paciente === filtroPac)

  return (
    <div>
      <div className={`toast ${toast ? 'visible' : ''}`}>{toast}</div>
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Actividades</div>
          <div className="ts tm" style={{ marginTop: 3 }}>{actividades.length} actividades asignadas</div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => setModal(true)}>+ Nueva actividad</button>
      </div>

      <div className="flex ic g8 mb16" style={{ flexWrap: 'wrap' }}>
        <button className={`btn btn-sm ${filtroPac === 'todos' ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltroPac('todos')}>
          Todos los pacientes
        </button>
        {PACIENTES.map(p => (
          <button key={p} className={`btn btn-sm ${filtroPac === p ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltroPac(p)}>
            {p.split(' ')[0]}
          </button>
        ))}
      </div>

      {loading ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div> : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {filtradas.map(a => {
            const cat = CAT_COLORS[a.categoria] ?? CAT_COLORS.Bienestar
            const pct = a.total > 0 ? Math.round((a.completadas / a.total) * 100) : 0
            return (
              <div key={a.id} className="card" style={{ opacity: a.activa ? 1 : 0.6 }}>
                <div className="flex ic jb mb10">
                  <span className="chip" style={{ background: cat.bg, color: cat.color, fontSize: 11 }}>{a.categoria}</span>
                  <span className={`chip ${a.activa ? 'ch-teal' : 'ch-gray'}`}>{a.activa ? 'Activa' : 'Inactiva'}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{a.titulo}</div>
                <div className="txs tm mb10">{a.paciente} · {a.frecuencia}</div>
                <div className="flex ic jb" style={{ marginBottom: 4 }}>
                  <span className="txs tm">Adherencia ({a.frecuencia.toLowerCase()})</span>
                  <span className="txs f5" style={{ color: pct >= 70 ? 'var(--teal)' : pct >= 40 ? 'var(--amber)' : 'var(--red)' }}>
                    {a.completadas}/{a.total} · {pct}%
                  </span>
                </div>
                <div className="pbar">
                  <div className="pf" style={{
                    width: `${pct}%`,
                    background: pct >= 70 ? 'var(--teal)' : pct >= 40 ? 'var(--amber)' : 'var(--red)',
                  }} />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modal && <ModalNueva onClose={() => setModal(false)} onSave={handleSave} />}
    </div>
  )
}
