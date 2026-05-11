// frontend/src/pages/terapeuta/interno/Registros.jsx
// Registros de seguimiento clínico — conectado al backend real

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../../context/AuthContext'

// ─── Tipos válidos del backend ────────────────────────────────────────────────
const TIPOS_BACKEND = [
  { key: 'evolucion',   label: 'Evolución' },
  { key: 'observacion', label: 'Observación' },
  { key: 'incidente',   label: 'Incidente' },
  { key: 'objetivo',    label: 'Objetivo' },
  { key: 'logro',       label: 'Logro' },
]

const TIPO_LABEL = Object.fromEntries(TIPOS_BACKEND.map(t => [t.key, t.label]))
const TIPO_COLOR = {
  evolucion:   'ch-teal',
  observacion: 'ch-pp',
  incidente:   'ch-rd',
  objetivo:    'ch-am',
  logro:       'ch-bu',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatFecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const hoy  = new Date()
  const ayer = new Date(hoy); ayer.setDate(hoy.getDate() - 1)
  const hora = d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  if (d.toDateString() === hoy.toDateString())  return `Hoy ${hora}`
  if (d.toDateString() === ayer.toDateString()) return `Ayer ${hora}`
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }) + ' ' + hora
}

function iniciales(nombre) {
  return (nombre || '').trim().split(' ').filter(Boolean).slice(0, 2)
    .map(p => p[0]).join('').toUpperCase() || '?'
}

const AV_CLASSES = ['av-tl', 'av-pp', 'av-am', 'av-bu', 'av-gr']
function avClass(id) {
  // Asigna un color determinístico en base al UUID
  const sum = (id || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
  return AV_CLASSES[sum % AV_CLASSES.length]
}

// ─── Modal: Nuevo registro ────────────────────────────────────────────────────

function ModalNuevoRegistro({ onClose, onSave, pacientes }) {
  const [form, setForm] = useState({
    paciente_id: '',
    tipo:        'evolucion',
    contenido:   '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.paciente_id)      { setError('Seleccioná un paciente.'); return }
    if (!form.contenido.trim()) { setError('Escribí la nota clínica.'); return }
    setSaving(true); setError('')
    try {
      await onSave(form)
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
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
            {error && (
              <div style={{
                background: 'rgba(229,62,62,0.08)', border: '1px solid rgba(229,62,62,0.3)',
                borderRadius: 8, padding: '10px 14px', color: 'var(--danger)', fontSize: 13,
              }}>{error}</div>
            )}
            <div className="fg">
              <label className="fl">Paciente *</label>
              {pacientes.length === 0 ? (
                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No hay pacientes disponibles.
                </div>
              ) : (
                <select className="fs" value={form.paciente_id}
                  onChange={e => setForm(f => ({ ...f, paciente_id: e.target.value }))}>
                  <option value="">Seleccioná un paciente…</option>
                  {pacientes.map(p => (
                    <option key={p.id} value={p.id}>{p.nombre}</option>
                  ))}
                </select>
              )}
            </div>
            <div className="fg">
              <label className="fl">Tipo de registro</label>
              <select className="fs" value={form.tipo}
                onChange={e => setForm(f => ({ ...f, tipo: e.target.value }))}>
                {TIPOS_BACKEND.map(t => (
                  <option key={t.key} value={t.key}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="fg">
              <label className="fl">Nota clínica *</label>
              <textarea className="fi fta" rows={4} value={form.contenido}
                onChange={e => setForm(f => ({ ...f, contenido: e.target.value }))}
                placeholder="Describí la observación o el resultado de la sesión…" />
            </div>
          </div>
          <div className="mf">
            <button type="button" className="btn btn-g" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p"
              disabled={saving || pacientes.length === 0}>
              {saving ? 'Guardando…' : 'Guardar registro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────────

export default function TerIntRegistros() {
  const { authFetch } = useAuth()

  const [registros,  setRegistros]  = useState([])
  const [pacientes,  setPacientes]  = useState([])   // para el dropdown y el mapa
  const [pacsMap,    setPacsMap]    = useState({})   // { uuid: { nombre, avCls } }
  const [loading,    setLoading]    = useState(true)
  const [apiError,   setApiError]   = useState('')
  const [modal,      setModal]      = useState(false)
  const [filtroTipo, setFiltroTipo] = useState('todos')
  const [toast,      setToast]      = useState({ msg: '', ok: true })

  // ── Carga de datos ──────────────────────────────────────────────────────────
  const cargar = useCallback(async () => {
    setLoading(true); setApiError('')
    try {
      const [resPacs, resRegs] = await Promise.all([
        authFetch('/pacientes/?activos_solo=true'),
        authFetch('/registros/'),
      ])

      // Procesar pacientes
      let mapa = {}
      if (resPacs.ok) {
        const pacs = await resPacs.json()
        if (Array.isArray(pacs)) {
          const lista = pacs.map(p => ({
            id:     p.id,
            nombre: [p.nombre, p.apellido].filter(Boolean).join(' ') || 'Paciente',
          }))
          setPacientes(lista)
          lista.forEach(p => { mapa[p.id] = p })
        }
      }
      setPacsMap(mapa)

      // Procesar registros
      if (resRegs.ok) {
        const data = await resRegs.json()
        setRegistros(Array.isArray(data) ? data : [])
      } else {
        const err = await resRegs.json().catch(() => ({}))
        setApiError(err.detail || 'Error al cargar los registros.')
        setRegistros([])
      }
    } catch (err) {
      setApiError('Error de conexión. Verificá la red e intentá de nuevo.')
      setRegistros([])
    } finally {
      setLoading(false)
    }
  }, [authFetch])

  useEffect(() => { cargar() }, [cargar])

  // ── Toast ───────────────────────────────────────────────────────────────────
  function mostrarToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 3000)
  }

  // ── Guardar nuevo registro ──────────────────────────────────────────────────
  async function handleSave(form) {
    const res = await authFetch('/registros/', {
      method: 'POST',
      body: JSON.stringify({
        paciente_id:    form.paciente_id,
        contenido:      form.contenido.trim(),
        tipo:           form.tipo,
        visibilidad:    'equipo',
        fecha_registro: new Date().toISOString().slice(0, 10),
      }),
    })
    if (!res.ok) {
      const d = await res.json().catch(() => ({}))
      throw new Error(d.detail || 'Error al guardar el registro.')
    }
    const nuevo = await res.json()
    setRegistros(prev => [nuevo, ...prev])
    setModal(false)
    mostrarToast('Registro guardado correctamente.')
  }

  // ── Filtrado ────────────────────────────────────────────────────────────────
  const filtrados = filtroTipo === 'todos'
    ? registros
    : registros.filter(r => r.tipo === filtroTipo)

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '24px 28px', maxWidth: 900, margin: '0 auto' }}>

      {/* Toast */}
      <div className={`toast ${toast.msg ? 'visible' : ''} ${!toast.ok ? 'error' : ''}`}>
        {toast.msg}
      </div>

      {/* Modal */}
      {modal && (
        <ModalNuevoRegistro
          pacientes={pacientes}
          onClose={() => setModal(false)}
          onSave={handleSave}
        />
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Registros de seguimiento</h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
            {loading ? 'Cargando…' : `${registros.length} registro${registros.length !== 1 ? 's' : ''} en total`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-g btn-sm" onClick={cargar} style={{ fontSize: 13 }}>
            Actualizar
          </button>
          <button className="btn btn-p" onClick={() => setModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14 }}>
            + Nuevo registro
          </button>
        </div>
      </div>

      {/* Filtros por tipo */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
        <button
          className={`btn btn-sm ${filtroTipo === 'todos' ? 'btn-p' : 'btn-g'}`}
          onClick={() => setFiltroTipo('todos')}
        >
          Todos ({registros.length})
        </button>
        {TIPOS_BACKEND.map(t => {
          const cnt = registros.filter(r => r.tipo === t.key).length
          if (cnt === 0) return null
          return (
            <button
              key={t.key}
              className={`btn btn-sm ${filtroTipo === t.key ? 'btn-p' : 'btn-g'}`}
              onClick={() => setFiltroTipo(t.key)}
            >
              {t.label} ({cnt})
            </button>
          )
        })}
      </div>

      {/* Contenido */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)', fontSize: 15 }}>
          Cargando registros…
        </div>
      ) : apiError ? (
        <div style={{
          background: 'rgba(229,62,62,0.08)', border: '1px solid rgba(229,62,62,0.25)',
          borderRadius: 10, padding: 20, color: 'var(--danger)', fontSize: 14, textAlign: 'center',
        }}>
          {apiError} — <button className="btn btn-g btn-sm" onClick={cargar}>Reintentar</button>
        </div>
      ) : filtrados.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)', fontSize: 14 }}>
          {registros.length === 0
            ? 'No hay registros aún. Creá el primero con el botón de arriba.'
            : 'No hay registros del tipo seleccionado.'}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtrados.map(r => {
            const pac    = pacsMap[r.paciente_id]
            const nombre = pac?.nombre || 'Paciente'
            const ini    = iniciales(nombre)
            const avc    = avClass(r.paciente_id)
            const chipCls = TIPO_COLOR[r.tipo] || 'ch-gray'
            const tipoLbl = TIPO_LABEL[r.tipo]  || r.tipo

            return (
              <div key={r.id} style={{
                background: 'var(--bg2, #fff)',
                border: '1px solid var(--border)',
                borderRadius: 10,
                padding: '14px 16px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div className={`av ${avc}`} style={{ width: 32, height: 32, fontSize: 11, flexShrink: 0 }}>
                      {ini}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{nombre}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {formatFecha(r.fecha_registro || r.creado_en)}
                      </div>
                    </div>
                  </div>
                  <span className={`ch ${chipCls}`} style={{ fontSize: 11 }}>{tipoLbl}</span>
                </div>
                <div style={{
                  fontSize: 13, color: 'var(--text2)', lineHeight: 1.6,
                  padding: '10px 12px',
                  background: 'var(--bg, rgba(0,0,0,0.02))',
                  borderRadius: 7,
                }}>
                  {r.contenido_enc}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
