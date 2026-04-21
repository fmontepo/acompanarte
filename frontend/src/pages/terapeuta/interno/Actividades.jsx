import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

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

function ModalNueva({ onClose, onSave, pacientes }) {
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
                {pacientes.map(p => <option key={p.id ?? p} value={p.nombre ?? p}>{p.nombre ?? p}</option>)}
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
  const [pacientes, setPacientes]     = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal]     = useState(false)
  const [filtroPac, setFiltroPac] = useState('todos')
  const [toast, setToast]     = useState('')

  useEffect(() => {
    // Backend devuelve: {id, terapeuta_id, paciente_id, titulo, descripcion, frecuencia, activa, …}
    // Frontend espera: {id, titulo, paciente, categoria, frecuencia, completadas, total, activa}
    function normalizeActividad(a, pacsMap) {
      const pac = pacsMap?.[a.paciente_id]
      return {
        id:          a.id,
        titulo:      a.titulo,
        paciente:    pac?.nombre || a.paciente || 'Paciente',
        categoria:   a.categoria || 'Bienestar',
        frecuencia:  a.frecuencia ? (a.frecuencia.charAt(0).toUpperCase() + a.frecuencia.slice(1)) : 'Diaria',
        completadas: a.completadas ?? 0,
        total:       a.total ?? 7,
        activa:      a.activa ?? true,
      }
    }

    async function cargar() {
      setLoading(true)
      try {
        const [resPacs, resActs] = await Promise.allSettled([
          authFetch('/api/v1/pacientes/'),
          authFetch('/api/v1/actividades/'),
        ])
        let pacsMap = {}
        if (resPacs.status === 'fulfilled' && resPacs.value.ok) {
          const pacs = await resPacs.value.json()
          if (Array.isArray(pacs) && pacs.length > 0) {
            setPacientes(pacs.map(p => ({ id: p.id, nombre: p.nombre_enc || 'Paciente' })))
            pacs.forEach(p => { pacsMap[p.id] = p })
          }
        }
        if (resActs.status === 'fulfilled' && resActs.value.ok) {
          const data = await resActs.value.json()
          const norm = Array.isArray(data) ? data.map(a => normalizeActividad(a, pacsMap)) : []
          setActividades(norm)
        } else { setActividades([]) }
      } catch { setActividades(MOCK) }  // error de red → mock
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  const FREQ_MAP = { 'Diaria': 'diaria', 'Semanal': 'semanal', 'Quincenal': 'quincenal', 'Mensual': 'libre' }

  async function handleSave(form) {
    // El form usa nombre de paciente; buscamos el id desde el estado
    const pac = pacientes.find(p => (p.nombre ?? p) === form.paciente)

    try {
      const res = await authFetch('/api/v1/actividades/', {
        method: 'POST',
        body: JSON.stringify({
          paciente_id: pac?.id ?? null,
          titulo:      form.titulo,
          descripcion: form.descripcion || null,
          frecuencia:  FREQ_MAP[form.frecuencia] ?? 'diaria',
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setActividades(prev => [{
          id:          data.id,
          titulo:      data.titulo,
          paciente:    form.paciente,
          categoria:   form.categoria,
          frecuencia:  form.frecuencia,
          completadas: 0,
          total:       7,
          activa:      true,
        }, ...prev])
        setToast('Actividad creada correctamente.')
      } else {
        setToast('Error al crear la actividad.')
      }
    } catch {
      // Fallback local
      setActividades(prev => [{ id: Date.now(), ...form, completadas: 0, total: 7, activa: true }, ...prev])
      setToast('Guardada localmente (sin conexión).')
    }
    setModal(false)
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
        {pacientes.map(p => (
          <button key={p.id ?? p} className={`btn btn-sm ${filtroPac === (p.nombre ?? p) ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltroPac(p.nombre ?? p)}>
            {(p.nombre ?? p).split(' ')[0]}
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

      {modal && <ModalNueva pacientes={pacientes} onClose={() => setModal(false)} onSave={handleSave} />}
    </div>
  )
}
