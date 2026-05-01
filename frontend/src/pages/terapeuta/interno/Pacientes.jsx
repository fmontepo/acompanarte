// frontend/src/pages/terapeuta/interno/Pacientes.jsx
// Gestión de pacientes del terapeuta interno
// — listado, alta, edición, vinculación de familiares

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../../context/AuthContext'

// ─── Iconos ──────────────────────────────────────────────────────────────────

const IcoPlus = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M12 4v16m8-8H4"/>
  </svg>
)
const IcoClose = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12"/>
  </svg>
)
const IcoChevron = ({ dir = 'down' }) => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"
    style={{ transform: dir === 'up' ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
    <path strokeLinecap="round" d="M19 9l-7 7-7-7"/>
  </svg>
)
const IcoSearch = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="M21 21l-4.35-4.35"/>
  </svg>
)
const IcoLink = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
  </svg>
)
const IcoUnlink = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"/>
  </svg>
)
const IcoEdit = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
  </svg>
)

// ─── Helpers ─────────────────────────────────────────────────────────────────

function initiales(nombre, apellido) {
  const n = (nombre || '').trim()[0] || ''
  const a = (apellido || '').trim()[0] || ''
  return (n + a).toUpperCase() || '?'
}

function sexoLabel(s) {
  return s === 'M' ? 'Masculino' : s === 'F' ? 'Femenino' : s === 'X' ? 'No binario' : '—'
}

// ─── Modal: Crear / Editar paciente ──────────────────────────────────────────

function ModalPaciente({ paciente, onClose, onSaved, authFetch }) {
  const esEdicion = !!paciente
  const [form, setForm] = useState({
    nombre:          paciente?.nombre           || '',
    apellido:        paciente?.apellido         || '',
    fecha_nacimiento: paciente?.fecha_nacimiento || '',
    sexo:            paciente?.sexo             || '',
    activo:          paciente?.activo           ?? true,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.nombre.trim()) { setError('El nombre es obligatorio.'); return }
    setSaving(true); setError('')
    try {
      const payload = {
        nombre:           form.nombre.trim(),
        apellido:         form.apellido.trim() || null,
        fecha_nacimiento: form.fecha_nacimiento || null,
        sexo:             form.sexo || null,
      }
      if (esEdicion) payload.activo = form.activo

      const method  = esEdicion ? 'PATCH' : 'POST'
      const url     = esEdicion ? `/pacientes/${paciente.id}` : '/pacientes/'
      const res     = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || 'Error al guardar')
      }
      const saved = await res.json()
      onSaved(saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">{esEdicion ? 'Editar paciente' : 'Nuevo paciente'}</div>
          <button className="btn btn-g btn-sm" onClick={onClose}><IcoClose /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb">
            {error && (
              <div style={{ background: 'rgba(229,62,62,0.08)', border: '1px solid rgba(229,62,62,0.3)',
                borderRadius: 8, padding: '10px 14px', marginBottom: 14,
                color: 'var(--danger)', fontSize: 13 }}>{error}</div>
            )}
            <div className="fg">
              <label className="fl">Nombre *</label>
              <input className="fi" value={form.nombre}
                onChange={e => set('nombre', e.target.value)} placeholder="Ej: Lucía" />
            </div>
            <div className="fg">
              <label className="fl">Apellido</label>
              <input className="fi" value={form.apellido}
                onChange={e => set('apellido', e.target.value)} placeholder="Ej: Gómez" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="fg">
                <label className="fl">Fecha de nacimiento</label>
                <input type="date" className="fi" value={form.fecha_nacimiento}
                  onChange={e => set('fecha_nacimiento', e.target.value)} />
              </div>
              <div className="fg">
                <label className="fl">Sexo</label>
                <select className="fs" value={form.sexo} onChange={e => set('sexo', e.target.value)}>
                  <option value="">Sin especificar</option>
                  <option value="M">Masculino</option>
                  <option value="F">Femenino</option>
                  <option value="X">No binario</option>
                </select>
              </div>
            </div>
            {esEdicion && (
              <div className="fg">
                <label className="fl">Estado</label>
                <select className="fs" value={form.activo ? '1' : '0'}
                  onChange={e => set('activo', e.target.value === '1')}>
                  <option value="1">Activo</option>
                  <option value="0">Inactivo</option>
                </select>
              </div>
            )}
          </div>
          <div className="mf">
            <button type="button" className="btn btn-g" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving}>
              {saving ? 'Guardando…' : esEdicion ? 'Guardar cambios' : 'Crear paciente'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Modal: Vincular familiar ─────────────────────────────────────────────────

function ModalVincularFamiliar({ paciente, onClose, onSaved, authFetch }) {
  const [familiares,   setFamiliares]   = useState([])
  const [parentescos,  setParentescos]  = useState([])
  const [loadingData,  setLoadingData]  = useState(true)
  const [form, setForm] = useState({
    familiar_id:       '',
    id_parentesco:     '',
    es_tutor_legal:    false,
    autorizado_medico: false,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [resFam, resPar] = await Promise.all([
          authFetch('/pacientes/familiares-disponibles'),
          authFetch('/pacientes/parentescos'),
        ])
        const dataFam = resFam.ok ? await resFam.json() : []
        const dataPar = resPar.ok ? await resPar.json() : []

        // Excluir familiares ya vinculados y activos
        const yaVinculados = new Set((paciente.vinculos || []).filter(v => v.activo).map(v => v.familiar_id))
        setFamiliares(dataFam.filter(f => !yaVinculados.has(f.familiar_id)))
        setParentescos(dataPar)
      } finally {
        setLoadingData(false)
      }
    }
    load()
  }, [authFetch, paciente])

  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.familiar_id)   { setError('Seleccioná un familiar.'); return }
    if (!form.id_parentesco) { setError('Seleccioná el parentesco.'); return }
    setSaving(true); setError('')
    try {
      const res = await authFetch(`/pacientes/${paciente.id}/vincular-familiar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || 'Error al vincular')
      }
      const saved = await res.json()
      onSaved(saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="ov open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mo">
        <div className="mh">
          <div className="mt">
            Vincular familiar
            <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
              — {paciente.nombre} {paciente.apellido || ''}
            </span>
          </div>
          <button className="btn btn-g btn-sm" onClick={onClose}><IcoClose /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb">
            {error && (
              <div style={{ background: 'rgba(229,62,62,0.08)', border: '1px solid rgba(229,62,62,0.3)',
                borderRadius: 8, padding: '10px 14px', marginBottom: 14,
                color: 'var(--danger)', fontSize: 13 }}>{error}</div>
            )}
            {loadingData ? (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: 14 }}>
                Cargando datos…
              </div>
            ) : (
              <>
                <div className="fg">
                  <label className="fl">Familiar *</label>
                  {familiares.length === 0 ? (
                    <div style={{ fontSize: 13, color: 'var(--text-muted)', padding: '8px 0' }}>
                      No hay familiares disponibles para vincular. Asegurate de que existan usuarios con rol Familia.
                    </div>
                  ) : (
                    <select className="fs" value={form.familiar_id}
                      onChange={e => set('familiar_id', e.target.value)}>
                      <option value="">Seleccioná un familiar…</option>
                      {familiares.map(f => (
                        <option key={f.familiar_id} value={f.familiar_id}>
                          {f.nombre_completo} — {f.email}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
                <div className="fg">
                  <label className="fl">Parentesco *</label>
                  <select className="fs" value={form.id_parentesco}
                    onChange={e => set('id_parentesco', e.target.value)}>
                    <option value="">Seleccioná el parentesco…</option>
                    {parentescos.map(p => (
                      <option key={p.id} value={p.id}>{p.nombre}</option>
                    ))}
                  </select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 4 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 14 }}>
                    <input type="checkbox" checked={form.es_tutor_legal}
                      onChange={e => set('es_tutor_legal', e.target.checked)}
                      style={{ width: 16, height: 16, cursor: 'pointer' }} />
                    <span>Es tutor/a legal</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 14 }}>
                    <input type="checkbox" checked={form.autorizado_medico}
                      onChange={e => set('autorizado_medico', e.target.checked)}
                      style={{ width: 16, height: 16, cursor: 'pointer' }} />
                    <span>Autorizado para decisiones médicas</span>
                  </label>
                </div>
              </>
            )}
          </div>
          <div className="mf">
            <button type="button" className="btn btn-g" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-p" disabled={saving || loadingData || familiares.length === 0}>
              {saving ? 'Vinculando…' : 'Vincular'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Fila de paciente expandible ─────────────────────────────────────────────

function FilaPaciente({ paciente, onEdit, onVincular, onDesvincular }) {
  const [expandido, setExpandido] = useState(false)

  const vinculosActivos = (paciente.vinculos || []).filter(v => v.activo)
  const ini = initiales(paciente.nombre, paciente.apellido)

  return (
    <>
      <tr style={{ cursor: 'pointer' }} onClick={() => setExpandido(x => !x)}>
        <td>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="av av-tl" style={{ width: 32, height: 32, fontSize: 13, borderRadius: 8, flexShrink: 0 }}>
              {ini}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                {paciente.nombre} {paciente.apellido || ''}
              </div>
              {!paciente.activo && (
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Inactivo</span>
              )}
            </div>
          </div>
        </td>
        <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {paciente.edad != null ? `${paciente.edad} años` : '—'}
        </td>
        <td style={{ fontSize: 13 }}>{sexoLabel(paciente.sexo)}</td>
        <td>
          {vinculosActivos.length === 0 ? (
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Sin familiar</span>
          ) : (
            <span className="ch ch-teal" style={{ fontSize: 12 }}>
              {vinculosActivos.length === 1
                ? vinculosActivos[0].nombre_familiar
                : `${vinculosActivos.length} familiares`}
            </span>
          )}
        </td>
        <td>
          <span className={`ch ${paciente.activo ? 'ch-teal' : 'ch-gray'}`} style={{ fontSize: 11 }}>
            {paciente.activo ? 'Activo' : 'Inactivo'}
          </span>
        </td>
        <td>
          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}
               onClick={e => e.stopPropagation()}>
            <button className="btn btn-g btn-sm" title="Editar" onClick={() => onEdit(paciente)}
              style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12 }}>
              <IcoEdit /> Editar
            </button>
            <button className="btn btn-sm" title="Vincular familiar"
              onClick={() => onVincular(paciente)}
              style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12,
                background: 'var(--teal)', color: '#fff', border: 'none' }}>
              <IcoLink /> Vincular
            </button>
          </div>
        </td>
        <td style={{ width: 28, textAlign: 'center', color: 'var(--text-muted)' }}>
          <IcoChevron dir={expandido ? 'up' : 'down'} />
        </td>
      </tr>

      {expandido && (
        <tr>
          <td colSpan={7} style={{ padding: 0 }}>
            <div style={{
              background: 'var(--surface-2, rgba(0,0,0,0.03))',
              borderTop: '1px solid var(--border)',
              padding: '14px 20px',
            }}>
              {/* Datos clínicos */}
              <div style={{ display: 'flex', gap: 24, marginBottom: 14, fontSize: 13, color: 'var(--text-muted)' }}>
                {paciente.nivel_soporte && (
                  <span>Nivel TEA: <strong style={{ color: 'var(--text)' }}>{paciente.nivel_soporte}</strong></span>
                )}
                {paciente.fecha_nacimiento && (
                  <span>Nacimiento: <strong style={{ color: 'var(--text)' }}>
                    {new Date(paciente.fecha_nacimiento + 'T12:00:00').toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                  </strong></span>
                )}
                <span>Dado de alta: <strong style={{ color: 'var(--text)' }}>
                  {paciente.creado_en
                    ? new Date(paciente.creado_en).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
                    : '—'}
                </strong></span>
              </div>

              {/* Vínculos familiares */}
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                Familiares vinculados
              </div>
              {vinculosActivos.length === 0 ? (
                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  Este paciente no tiene familiares vinculados aún.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {vinculosActivos.map(v => (
                    <div key={v.vinculo_id} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      background: 'var(--surface)', border: '1px solid var(--border)',
                      borderRadius: 8, padding: '8px 14px',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div className="av av-tl" style={{ width: 28, height: 28, fontSize: 11, borderRadius: 6 }}>
                          {(v.nombre_familiar || '—').slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600 }}>{v.nombre_familiar}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{v.email || ''}</div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className="ch ch-pp" style={{ fontSize: 11 }}>{v.parentesco_nombre}</span>
                        {v.es_tutor_legal    && <span className="ch ch-am"   style={{ fontSize: 11 }}>Tutor legal</span>}
                        {v.autorizado_medico && <span className="ch ch-teal" style={{ fontSize: 11 }}>Aut. médico</span>}
                        <button
                          className="btn btn-g btn-sm"
                          title="Desvincular"
                          onClick={() => onDesvincular(paciente.id, v.vinculo_id, v.nombre_familiar)}
                          style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--danger)' }}>
                          <IcoUnlink /> Desvincular
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────────

export default function TerIntPacientes() {
  const { authFetch } = useAuth()

  const [pacientes,   setPacientes]   = useState([])
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState('')
  const [busqueda,    setBusqueda]    = useState('')
  const [soloActivos, setSoloActivos] = useState(true)
  const [modal,       setModal]       = useState(null)  // null | 'crear' | 'editar' | 'vincular'
  const [seleccionado, setSeleccionado] = useState(null)
  const [toast,       setToast]       = useState({ msg: '', ok: true })

  // ── Carga de datos ──────────────────────────────────────────────────────────
  const cargar = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const res = await authFetch(`/pacientes/?activos_solo=${soloActivos}`)
      if (!res.ok) throw new Error('Error al cargar pacientes')
      setPacientes(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [authFetch, soloActivos])

  useEffect(() => { cargar() }, [cargar])

  // ── Toast ───────────────────────────────────────────────────────────────────
  function mostrarToast(msg, ok = true) {
    setToast({ msg, ok })
    setTimeout(() => setToast({ msg: '', ok: true }), 3000)
  }

  // ── Filtrado ────────────────────────────────────────────────────────────────
  const q = busqueda.trim().toLowerCase()
  const filtrados = pacientes.filter(p => {
    if (!q) return true
    const fullName = `${p.nombre} ${p.apellido || ''}`.toLowerCase()
    return fullName.includes(q)
  })

  // ── Handlers ────────────────────────────────────────────────────────────────
  function onCreado(nuevo) {
    setPacientes(ps => [nuevo, ...ps])
    setModal(null)
    mostrarToast('Paciente creado correctamente.')
  }

  function onEditado(actualizado) {
    setPacientes(ps => ps.map(p => p.id === actualizado.id ? actualizado : p))
    setModal(null)
    mostrarToast('Datos del paciente actualizados.')
  }

  function onVinculado(actualizado) {
    setPacientes(ps => ps.map(p => p.id === actualizado.id ? actualizado : p))
    setModal(null)
    mostrarToast('Familiar vinculado correctamente.')
  }

  async function onDesvincular(pacienteId, vinculoId, nombreFamiliar) {
    if (!window.confirm(`¿Desvincular a ${nombreFamiliar} de este paciente?`)) return
    try {
      const res = await authFetch(`/pacientes/${pacienteId}/vinculos/${vinculoId}`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) throw new Error('Error al desvincular')
      // Recargar el paciente afectado
      const res2 = await authFetch(`/pacientes/${pacienteId}`)
      if (res2.ok) {
        const actualizado = await res2.json()
        setPacientes(ps => ps.map(p => p.id === actualizado.id ? actualizado : p))
      }
      mostrarToast('Familiar desvinculado.')
    } catch (err) {
      mostrarToast(`Error: ${err.message}`, false)
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '24px 28px', maxWidth: 1100, margin: '0 auto' }}>

      {/* Toast */}
      <div className={`toast ${toast.msg ? 'visible' : ''} ${!toast.ok ? 'error' : ''}`}>{toast.msg}</div>

      {/* Modales */}
      {modal === 'crear' && (
        <ModalPaciente
          onClose={() => setModal(null)}
          onSaved={onCreado}
          authFetch={authFetch}
        />
      )}
      {modal === 'editar' && seleccionado && (
        <ModalPaciente
          paciente={seleccionado}
          onClose={() => { setModal(null); setSeleccionado(null) }}
          onSaved={onEditado}
          authFetch={authFetch}
        />
      )}
      {modal === 'vincular' && seleccionado && (
        <ModalVincularFamiliar
          paciente={seleccionado}
          onClose={() => { setModal(null); setSeleccionado(null) }}
          onSaved={onVinculado}
          authFetch={authFetch}
        />
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Pacientes</h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
            Gestión de pacientes y sus familiares vinculados
          </p>
        </div>
        <button
          className="btn btn-p"
          onClick={() => setModal('crear')}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <IcoPlus /> Nuevo paciente
        </button>
      </div>

      {/* Barra de filtros */}
      <div style={{
        display: 'flex', gap: 12, alignItems: 'center',
        marginBottom: 20, flexWrap: 'wrap',
      }}>
        <div style={{ position: 'relative', flex: '1', minWidth: 200, maxWidth: 360 }}>
          <span style={{
            position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-muted)', pointerEvents: 'none',
          }}>
            <IcoSearch />
          </span>
          <input
            className="fi"
            style={{ paddingLeft: 32 }}
            placeholder="Buscar por nombre o apellido…"
            value={busqueda}
            onChange={e => setBusqueda(e.target.value)}
          />
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={soloActivos}
            onChange={e => setSoloActivos(e.target.checked)}
            style={{ width: 15, height: 15 }}
          />
          Solo activos
        </label>
        <button className="btn btn-g btn-sm" onClick={cargar} style={{ fontSize: 13 }}>
          Actualizar
        </button>
      </div>

      {/* Tabla */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: 15, marginBottom: 8 }}>Cargando pacientes…</div>
        </div>
      ) : error ? (
        <div style={{
          background: 'rgba(229,62,62,0.08)', border: '1px solid rgba(229,62,62,0.25)',
          borderRadius: 10, padding: 20, color: 'var(--danger)', fontSize: 14, textAlign: 'center',
        }}>
          {error} — <button className="btn btn-g btn-sm" onClick={cargar}>Reintentar</button>
        </div>
      ) : filtrados.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px 0',
          color: 'var(--text-muted)', fontSize: 14,
        }}>
          {pacientes.length === 0
            ? 'No hay pacientes registrados. Creá el primero con el botón de arriba.'
            : 'No se encontraron pacientes con ese criterio.'}
        </div>
      ) : (
        <div style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 12, overflow: 'hidden',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface-2, rgba(0,0,0,0.02))' }}>
                {['Paciente', 'Edad', 'Sexo', 'Familiar', 'Estado', 'Acciones', ''].map((h, i) => (
                  <th key={i} style={{
                    padding: '10px 14px', textAlign: i >= 5 ? 'right' : 'left',
                    fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((p, idx) => (
                <FilaPaciente
                  key={p.id}
                  paciente={p}
                  onEdit={pac => { setSeleccionado(pac); setModal('editar') }}
                  onVincular={pac => { setSeleccionado(pac); setModal('vincular') }}
                  onDesvincular={onDesvincular}
                  style={idx % 2 === 0 ? {} : { background: 'var(--surface-2)' }}
                />
              ))}
            </tbody>
          </table>
          <div style={{
            padding: '10px 14px', borderTop: '1px solid var(--border)',
            fontSize: 12, color: 'var(--text-muted)',
          }}>
            {filtrados.length} paciente{filtrados.length !== 1 ? 's' : ''} mostrado{filtrados.length !== 1 ? 's' : ''}
            {filtrados.length !== pacientes.length && ` de ${pacientes.length} en total`}
          </div>
        </div>
      )}
    </div>
  )
}
