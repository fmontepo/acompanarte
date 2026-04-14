import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

const PACIENTES = ['Roberto Méndez', 'Elena Fernández']
const TIPOS = ['Seguimiento', 'Evaluación', 'Observación', 'Nota de evolución']

const MOCK = [
  { id: 1, paciente: 'Roberto Méndez',  av: 'RM', avClass: 'av-tl', tipo: 'Seguimiento',      fecha: '2026-04-09T10:15:00', nota: 'Visita domiciliaria. Paciente orientado en tiempo y lugar. Interactuó bien con la familia presente. Recomienda continuar con rutinas establecidas.', estado: 'completado' },
  { id: 2, paciente: 'Elena Fernández', av: 'EF', avClass: 'av-pp', tipo: 'Evaluación',        fecha: '2026-04-06T14:30:00', nota: 'Evaluación cognitiva de seguimiento. MMSE: 22/30 (estable respecto al mes anterior). Lenguaje conservado, memoria episódica con leve deterioro.', estado: 'completado' },
  { id: 3, paciente: 'Roberto Méndez',  av: 'RM', avClass: 'av-tl', tipo: 'Nota de evolución', fecha: '2026-03-28T11:00:00', nota: 'Progreso alentador en actividades físicas. Completa la caminata matutina con regularidad según reporte familiar. Se ajusta plan para próximo mes.', estado: 'completado' },
]

const ESTADO_META = {
  completado: { label: 'Completado', chipClass: 'ch-teal' },
  pendiente:  { label: 'Pendiente',  chipClass: 'ch-gray' },
}

function formatFecha(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

function ModalNuevo({ onClose, onSave }) {
  const [form, setForm] = useState({ paciente: '', tipo: 'Seguimiento', nota: '' })
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.paciente || !form.nota.trim()) return
    setSaving(true)
    await new Promise(r => setTimeout(r, 500))
    setSaving(false)
    onSave(form)
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">Nuevo registro</div>
          <button className="btn btn-g btn-sm" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb">
            <div className="fg">
              <label className="fl">Paciente *</label>
              <select className="fs" value={form.paciente} onChange={e => setForm(f => ({ ...f, paciente: e.target.value }))}>
                <option value="">Seleccioná…</option>
                {PACIENTES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="fg">
              <label className="fl">Tipo de registro</label>
              <select className="fs" value={form.tipo} onChange={e => setForm(f => ({ ...f, tipo: e.target.value }))}>
                {TIPOS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="fg">
              <label className="fl">Nota *</label>
              <textarea className="fi fta" value={form.nota} rows={5}
                onChange={e => setForm(f => ({ ...f, nota: e.target.value }))}
                placeholder="Describí las observaciones de la visita o evaluación…" />
            </div>
            <div className="disc disc-tl txs">
              Recordá incluir solo información clínica relevante. Estos registros son visibles para el equipo terapéutico interno.
            </div>
          </div>
          <div className="mf">
            <button type="button" className="btn btn-s" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving || !form.paciente || !form.nota.trim()}>
              {saving ? 'Guardando…' : 'Guardar registro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function TerExtRegistros() {
  const { authFetch } = useAuth()
  const [registros, setRegistros] = useState([])
  const [loading, setLoading]     = useState(true)
  const [modal, setModal]         = useState(false)
  const [toast, setToast]         = useState('')

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        const res = await authFetch('/api/v1/registros/mis-registros')
        if (res.ok) {
          const data = await res.json()
          setRegistros(Array.isArray(data) && data.length > 0 ? data : MOCK)
        } else { setRegistros(MOCK) }
      } catch { setRegistros(MOCK) }
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  function handleSave(form) {
    const pac = PACIENTES.find(p => p === form.paciente)
    const initials = pac ? pac.split(' ').map(w => w[0]).join('') : '?'
    const avClass  = initials === 'RM' ? 'av-tl' : 'av-pp'
    setRegistros(prev => [{
      id: Date.now(), paciente: form.paciente, av: initials, avClass,
      tipo: form.tipo, fecha: new Date().toISOString(), nota: form.nota, estado: 'completado',
    }, ...prev])
    setModal(false)
    setToast('Registro guardado correctamente.')
    setTimeout(() => setToast(''), 2500)
  }

  return (
    <div>
      <div className={`toast ${toast ? 'visible' : ''}`}>{toast}</div>
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Mis registros</div>
          <div className="ts tm" style={{ marginTop: 3 }}>{registros.length} registros propios</div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => setModal(true)}>+ Nuevo registro</button>
      </div>

      {loading ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div>
      : registros.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text3)' }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>📝</div>
          <div style={{ fontWeight: 600, color: 'var(--text)' }}>Sin registros aún</div>
          <button className="btn btn-p btn-sm" style={{ marginTop: 12 }} onClick={() => setModal(true)}>
            Crear primer registro
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {registros.map(r => {
            const em = ESTADO_META[r.estado] ?? ESTADO_META.completado
            return (
              <div key={r.id} className="card">
                <div className="flex ic jb mb10">
                  <div className="flex ic g10">
                    <div className={`av ${r.avClass}`} style={{ width: 32, height: 32, fontSize: 11 }}>{r.av}</div>
                    <div>
                      <div className="ts f5">{r.paciente}</div>
                      <div className="txs tm">{r.tipo} · {formatFecha(r.fecha)}</div>
                    </div>
                  </div>
                  <span className={`chip ${em.chipClass}`}>{em.label}</span>
                </div>
                <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55,
                  padding: '10px 12px', background: 'var(--bg)', borderRadius: 7 }}>
                  {r.nota}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modal && <ModalNuevo onClose={() => setModal(false)} onSave={handleSave} />}
    </div>
  )
}
