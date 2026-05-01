import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'

const PACIENTES = [
  { id: 1, nombre: 'Roberto Méndez',   av: 'RM', avClass: 'av-tl' },
  { id: 2, nombre: 'Carmen Villalba',  av: 'CV', avClass: 'av-pp' },
  { id: 3, nombre: 'Héctor Rodríguez', av: 'HR', avClass: 'av-am' },
  { id: 4, nombre: 'Sofía Blanco',     av: 'SB', avClass: 'av-bu' },
]
const TIPOS = ['Seguimiento', 'Evaluación', 'Incidente', 'Sesión terapéutica', 'Observación']
const MOCK = [
  { id: 1, paciente: 'Roberto Méndez',   av: 'RM', avClass: 'av-tl', tipo: 'Seguimiento',       fecha: '2026-04-14T09:15:00', nota: 'Buena respuesta a ejercicios matutinos. Estado de ánimo positivo. Completó todas las actividades del día.', estado: 'completado' },
  { id: 2, paciente: 'Carmen Villalba',  av: 'CV', avClass: 'av-pp', tipo: 'Sesión terapéutica', fecha: '2026-04-13T14:00:00', nota: 'Sesión de estimulación cognitiva. Trabajamos con fotografías familiares. Mejoría en reconocimiento de entorno inmediato.', estado: 'completado' },
  { id: 3, paciente: 'Héctor Rodríguez', av: 'HR', avClass: 'av-am', tipo: 'Evaluación',         fecha: '2026-04-11T10:30:00', nota: 'Evaluación mensual de progreso. Motricidad estable. Lenguaje con algunas dificultades de fluencia. Se ajusta plan.', estado: 'completado' },
  { id: 4, paciente: 'Sofía Blanco',     av: 'SB', avClass: 'av-bu', tipo: 'Incidente',          fecha: '2026-04-10T17:40:00', nota: 'Episodio de agitación vespertina. Duración: 15 min. Se aplicó técnica de redirección con música. Familiar notificada.', estado: 'alerta' },
  { id: 5, paciente: 'Roberto Méndez',   av: 'RM', avClass: 'av-tl', tipo: 'Observación',        fecha: '2026-04-09T11:00:00', nota: 'Sin novedades. Rutina cumplida. Buen apetito y descanso adecuado según reporte familiar.', estado: 'completado' },
]

const ESTADO_META = {
  completado: { label: 'Completado', chipClass: 'ch-teal' },
  alerta:     { label: 'Requiere atención', chipClass: 'ch-rd' },
  pendiente:  { label: 'Pendiente', chipClass: 'ch-gray' },
}

function formatFecha(iso) {
  const d = new Date(iso)
  const hoy  = new Date()
  const ayer = new Date(hoy); ayer.setDate(hoy.getDate() - 1)
  const hora = d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  if (d.toDateString() === hoy.toDateString())  return `Hoy ${hora}`
  if (d.toDateString() === ayer.toDateString()) return `Ayer ${hora}`
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' }) + ' ' + hora
}

function ModalNuevoRegistro({ onClose, onSave, pacientes }) {
  const [form, setForm] = useState({ paciente_id: '', tipo: 'Seguimiento', nota: '', estado: 'completado' })
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.paciente_id || !form.nota.trim()) { setError('Seleccioná un paciente y escribí la nota.'); return }
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
              <select className="fs" value={form.paciente_id}
                onChange={e => setForm(f => ({ ...f, paciente_id: e.target.value }))}>
                <option value="">Seleccioná un paciente…</option>
                {pacientes.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </div>
            <div className="fr2">
              <div className="fg">
                <label className="fl">Tipo</label>
                <select className="fs" value={form.tipo}
                  onChange={e => setForm(f => ({ ...f, tipo: e.target.value }))}>
                  {TIPOS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="fg">
                <label className="fl">Estado</label>
                <select className="fs" value={form.estado}
                  onChange={e => setForm(f => ({ ...f, estado: e.target.value }))}>
                  <option value="completado">Completado</option>
                  <option value="alerta">Requiere atención</option>
                  <option value="pendiente">Pendiente</option>
                </select>
              </div>
            </div>
            <div className="fg">
              <label className="fl">Nota clínica *</label>
              <textarea className="fi fta" value={form.nota} rows={4}
                onChange={e => setForm(f => ({ ...f, nota: e.target.value }))}
                placeholder="Describí la observación o el resultado de la sesión…" />
            </div>
            {error && <div className="disc disc-rd txs">{error}</div>}
          </div>
          <div className="mf">
            <button type="button" className="btn btn-s" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving}>
              {saving ? 'Guardando…' : 'Guardar registro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function TerIntRegistros() {
  const { authFetch } = useAuth()
  const [registros, setRegistros]   = useState([])
  const [pacientes, setPacientes]   = useState(PACIENTES)   // dropdown del modal
  const [loading, setLoading]       = useState(true)
  const [modal, setModal]           = useState(false)
  const [filtro, setFiltro]         = useState('todos')
  const [toast, setToast]           = useState({ msg: '', ok: true })

  // Normaliza el schema del backend al shape esperado por la tabla
  function normalizeRegistro(r, pacsMap) {
    const pac = pacsMap?.[r.paciente_id]
    return {
      id:       r.id,
      paciente: pac?.nombre || r.paciente || `Paciente`,
      av:       pac?.av || 'PT',
      avClass:  pac?.avClass || 'av-tl',
      tipo:     r.tipo ? (r.tipo.charAt(0).toUpperCase() + r.tipo.slice(1)) : 'Seguimiento',
      fecha:    r.fecha_registro || r.creado_en,
      nota:     r.contenido_enc || r.nota || '',
      estado:   r.estado || 'completado',
    }
  }

  useEffect(() => {
    async function cargar() {
      setLoading(true)
      try {
        // Cargar pacientes y registros en paralelo
        const [resPacs, resRegs] = await Promise.allSettled([
          authFetch('/pacientes/'),
          authFetch('/registros/'),
        ])
        // Mapa id→paciente para enriquecer registros
        let pacsMap = {}
        if (resPacs.status === 'fulfilled' && resPacs.value.ok) {
          const pacs = await resPacs.value.json()
          if (Array.isArray(pacs) && pacs.length > 0) {
            setPacientes(pacs.map(p => ({ id: p.id, nombre: p.nombre_enc || 'Paciente', av: (p.nombre_enc||'P').slice(0,2).toUpperCase(), avClass: 'av-tl' })))
            pacs.forEach(p => { pacsMap[p.id] = p })
          }
        }
        if (resRegs.status === 'fulfilled' && resRegs.value.ok) {
          const data = await resRegs.value.json()
          const norm = Array.isArray(data) ? data.map(r => normalizeRegistro(r, pacsMap)) : []
          setRegistros(norm)
        } else { setRegistros([]) }
      } catch { setRegistros(MOCK) }  // error de red → mock
      finally { setLoading(false) }
    }
    cargar()
  }, [authFetch])

  // Mapeo de tipos del frontend (español capitalizado) a claves del backend
  const TIPO_MAP = {
    'Seguimiento':        'evolucion',
    'Evaluación':         'observacion',
    'Incidente':          'incidente',
    'Sesión terapéutica': 'evolucion',
    'Observación':        'observacion',
  }

  async function handleSave(form) {
    const pac = pacientes.find(p => String(p.id) === String(form.paciente_id))

    try {
      const res = await authFetch('/registros/', {
        method: 'POST',
        body: JSON.stringify({
          paciente_id:     form.paciente_id,
          contenido:       form.nota,
          tipo:            TIPO_MAP[form.tipo] ?? 'evolucion',
          visibilidad:     'equipo',
          fecha_registro:  new Date().toISOString().slice(0, 10),
        }),
      })
      if (res.ok) {
        const data = await res.json()
        const nuevo = {
          id:       data.id,
          paciente: pac?.nombre ?? 'Paciente',
          av:       pac?.av ?? '?',
          avClass:  pac?.avClass ?? 'av-gr',
          tipo:     form.tipo,
          fecha:    data.creado_en ?? new Date().toISOString(),
          nota:     data.contenido_enc ?? form.nota,
          estado:   form.estado,
        }
        setRegistros(prev => [nuevo, ...prev])
        setToast({ msg: 'Registro guardado correctamente.', ok: true })
      } else {
        setToast({ msg: 'Error al guardar el registro.', ok: false })
      }
    } catch {
      // Fallback local si no hay conexión
      const nuevo = {
        id: Date.now(), paciente: pac?.nombre ?? 'Paciente',
        av: pac?.av ?? '?', avClass: pac?.avClass ?? 'av-gr',
        tipo: form.tipo, fecha: new Date().toISOString(),
        nota: form.nota, estado: form.estado,
      }
      setRegistros(prev => [nuevo, ...prev])
      setToast({ msg: 'Sin conexión. Guardado localmente.', ok: false })
    }
    setModal(false)
    setTimeout(() => setToast({ msg: '', ok: true }), 2500)
  }

  const filtrados = filtro === 'todos' ? registros : registros.filter(r => r.estado === filtro)

  return (
    <div>
      <div className={`toast ${toast.msg ? 'visible' : ''} ${!toast.ok ? 'error' : ''}`}>{toast.msg}</div>

      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Registros de seguimiento</div>
          <div className="ts tm" style={{ marginTop: 3 }}>{registros.length} registros totales</div>
        </div>
        <button className="btn btn-p btn-sm" onClick={() => setModal(true)}>+ Nuevo registro</button>
      </div>

      <div className="flex ic g8 mb16">
        {[
          { val: 'todos',      label: `Todos (${registros.length})` },
          { val: 'completado', label: `Completados (${registros.filter(r => r.estado === 'completado').length})` },
          { val: 'alerta',     label: `Con alerta (${registros.filter(r => r.estado === 'alerta').length})` },
        ].map(f => (
          <button key={f.val} className={`btn btn-sm ${filtro === f.val ? 'btn-p' : 'btn-s'}`} onClick={() => setFiltro(f.val)}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text3)' }}>Cargando…</div> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtrados.map(r => {
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
                <div className="ts" style={{ color: 'var(--text2)', lineHeight: 1.55, padding: '10px 12px',
                  background: 'var(--bg)', borderRadius: 7 }}>
                  {r.nota}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modal && <ModalNuevoRegistro pacientes={pacientes} onClose={() => setModal(false)} onSave={handleSave} />}
    </div>
  )
}
