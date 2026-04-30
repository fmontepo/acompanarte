// admin/ReglasIA.jsx
// Gestión de reglas de comportamiento del Asistente IA
// Reglas positivas → qué puede responder
// Reglas negativas → qué NO puede responder
// Contexto: familiar | terapeuta | global (aplican a todos)

import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Íconos ───────────────────────────────────────────────────────────────
const IcoPlus = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" d="M12 4v16m8-8H4"/>
  </svg>
)
const IcoEdit = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
  </svg>
)
const IcoTrash = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
  </svg>
)
const IcoCheck = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" d="M5 13l4 4L19 7"/>
  </svg>
)
const IcoX = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
    <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12"/>
  </svg>
)
const IcoRefresh = () => (
  <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
  </svg>
)

// ─── Metadatos por tipo ───────────────────────────────────────────────────
const TIPO_META = {
  positiva: {
    label:       'Reglas positivas',
    sublabel:    'Lo que el asistente PUEDE y DEBE responder',
    accentColor: 'var(--teal)',
    bgColor:     'rgba(56,161,105,0.06)',
    borderColor: 'rgba(56,161,105,0.25)',
    icon:        '✓',
  },
  negativa: {
    label:       'Reglas negativas',
    sublabel:    'Lo que el asistente NO DEBE responder ni hacer',
    accentColor: 'var(--red)',
    bgColor:     'rgba(163,45,45,0.05)',
    borderColor: 'rgba(163,45,45,0.2)',
    icon:        '✗',
  },
}

// ─── Metadatos por contexto ───────────────────────────────────────────────
const CONTEXTO_META = {
  familiar:   { label: 'Familiar',   color: '#3b82f6', bg: 'rgba(59,130,246,0.1)'  },
  terapeuta:  { label: 'Terapeuta',  color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)'  },
  global:     { label: 'Global',     color: '#64748b', bg: 'rgba(100,116,139,0.1)' },
}

function ChipContexto({ contexto }) {
  const m = CONTEXTO_META[contexto] || CONTEXTO_META.global
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 20,
      background: m.bg, color: m.color, letterSpacing: '0.02em',
      flexShrink: 0,
    }}>
      {m.label}
    </span>
  )
}

// ─── Formulario de nueva regla ────────────────────────────────────────────
function FormNuevaRegla({ tipo, contextoFiltro, onCreada, onCancelar }) {
  const { authFetch }   = useAuth()
  const meta            = TIPO_META[tipo]
  const [texto,       setTexto]       = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [contexto,    setContexto]    = useState(contextoFiltro !== 'todos' ? contextoFiltro : 'global')
  const [guardando,   setGuardando]   = useState(false)
  const [error,       setError]       = useState('')

  async function guardar() {
    if (!texto.trim()) { setError('El texto de la regla es obligatorio.'); return }
    setError('')
    setGuardando(true)
    try {
      const res = await authFetch('/admin/reglas-ia', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          tipo,
          contexto,
          texto:      texto.trim(),
          descripcion: descripcion.trim() || null,
        }),
      })
      if (res.ok) {
        const nueva = await res.json()
        onCreada(nueva)
        setTexto('')
        setDescripcion('')
      } else {
        const d = await res.json().catch(() => ({}))
        setError(d.detail || 'Error al guardar.')
      }
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div style={{
      background: meta.bgColor, border: `1px dashed ${meta.accentColor}`,
      borderRadius: 8, padding: '12px 14px', marginTop: 8,
    }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: meta.accentColor, marginBottom: 8 }}>
        Nueva regla {tipo}
      </div>

      {/* Selector de contexto */}
      <div style={{ marginBottom: 8 }}>
        <label style={{ fontSize: 11, color: 'var(--text3)', display: 'block', marginBottom: 4 }}>
          Módulo donde aplica
        </label>
        <div className="flex ic g6">
          {Object.entries(CONTEXTO_META).map(([key, m]) => (
            <button
              key={key}
              onClick={() => setContexto(key)}
              style={{
                fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
                border: `1.5px solid ${contexto === key ? m.color : 'var(--border)'}`,
                background: contexto === key ? m.bg : 'transparent',
                color: contexto === key ? m.color : 'var(--text3)',
                cursor: 'pointer',
              }}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <textarea
        className="fi"
        value={texto}
        onChange={e => setTexto(e.target.value)}
        placeholder={tipo === 'positiva'
          ? 'Ej: Orientar sobre señales tempranas del TEA en niños menores de 3 años'
          : 'Ej: Emitir diagnósticos ni afirmar que un niño tiene o no tiene TEA'
        }
        rows={2}
        autoFocus
        style={{ fontSize: 13, resize: 'none', width: '100%', marginBottom: 6 }}
      />
      <input
        className="fi"
        type="text"
        value={descripcion}
        onChange={e => setDescripcion(e.target.value)}
        placeholder="Nota interna (opcional — no se envía al modelo)"
        style={{ fontSize: 12, marginBottom: 8, width: '100%' }}
      />
      {error && <div style={{ fontSize: 12, color: 'var(--red)', marginBottom: 6 }}>{error}</div>}
      <div className="flex ic g6">
        <button className="btn btn-p btn-xs" onClick={guardar} disabled={guardando}>
          <IcoCheck /> {guardando ? 'Guardando…' : 'Guardar'}
        </button>
        <button className="btn btn-g btn-xs" onClick={onCancelar}><IcoX /> Cancelar</button>
      </div>
    </div>
  )
}

// ─── Ítem de regla ────────────────────────────────────────────────────────
function ItemRegla({ regla, onActualizada, onEliminada }) {
  const { authFetch } = useAuth()
  const meta = TIPO_META[regla.tipo]

  const [editando,    setEditando]    = useState(false)
  const [textoEdit,   setTextoEdit]   = useState(regla.texto)
  const [descEdit,    setDescEdit]    = useState(regla.descripcion ?? '')
  const [ctxEdit,     setCtxEdit]     = useState(regla.contexto || 'global')
  const [guardando,   setGuardando]   = useState(false)
  const [confirmDel,  setConfirmDel]  = useState(false)

  async function guardarEdicion() {
    if (!textoEdit.trim()) return
    setGuardando(true)
    try {
      const res = await authFetch(`/admin/reglas-ia/${regla.id}`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          texto:      textoEdit.trim(),
          descripcion: descEdit.trim() || null,
          contexto:   ctxEdit,
        }),
      })
      if (res.ok) { onActualizada(await res.json()); setEditando(false) }
    } finally {
      setGuardando(false)
    }
  }

  async function toggleActiva() {
    const res = await authFetch(`/admin/reglas-ia/${regla.id}`, {
      method:  'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ activa: !regla.activa }),
    })
    if (res.ok) onActualizada(await res.json())
  }

  async function eliminar() {
    const res = await authFetch(`/admin/reglas-ia/${regla.id}`, { method: 'DELETE' })
    if (res.ok || res.status === 204) onEliminada(regla.id)
  }

  return (
    <div style={{
      border: `1px solid ${regla.activa ? meta.borderColor : 'var(--border)'}`,
      borderRadius: 8,
      background: regla.activa ? meta.bgColor : 'var(--bg)',
      padding: '10px 12px',
      opacity: regla.activa ? 1 : 0.55,
      transition: 'all 0.2s',
    }}>
      {editando ? (
        <div>
          {/* Selector de contexto en edición */}
          <div style={{ marginBottom: 8 }}>
            <label style={{ fontSize: 11, color: 'var(--text3)', display: 'block', marginBottom: 4 }}>
              Módulo donde aplica
            </label>
            <div className="flex ic g6">
              {Object.entries(CONTEXTO_META).map(([key, m]) => (
                <button
                  key={key}
                  onClick={() => setCtxEdit(key)}
                  style={{
                    fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
                    border: `1.5px solid ${ctxEdit === key ? m.color : 'var(--border)'}`,
                    background: ctxEdit === key ? m.bg : 'transparent',
                    color: ctxEdit === key ? m.color : 'var(--text3)',
                    cursor: 'pointer',
                  }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
          <textarea
            className="fi"
            value={textoEdit}
            onChange={e => setTextoEdit(e.target.value)}
            rows={2}
            autoFocus
            style={{ fontSize: 13, resize: 'none', width: '100%', marginBottom: 6 }}
          />
          <input
            className="fi"
            type="text"
            value={descEdit}
            onChange={e => setDescEdit(e.target.value)}
            placeholder="Nota interna (opcional)"
            style={{ fontSize: 12, marginBottom: 8, width: '100%' }}
          />
          <div className="flex ic g6">
            <button className="btn btn-p btn-xs" onClick={guardarEdicion} disabled={guardando}>
              <IcoCheck /> {guardando ? 'Guardando…' : 'Guardar'}
            </button>
            <button className="btn btn-g btn-xs" onClick={() => {
              setEditando(false)
              setTextoEdit(regla.texto)
              setDescEdit(regla.descripcion ?? '')
              setCtxEdit(regla.contexto || 'global')
            }}>
              <IcoX /> Cancelar
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div className="flex" style={{ gap: 8, alignItems: 'flex-start' }}>
            {/* Símbolo ✓ / ✗ */}
            <span style={{
              fontSize: 13, fontWeight: 800,
              color: meta.accentColor, flexShrink: 0, marginTop: 1,
            }}>
              {meta.icon}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <ChipContexto contexto={regla.contexto || 'global'} />
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.5, color: 'var(--text)' }}>
                {regla.texto}
              </div>
              {regla.descripcion && (
                <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 3, fontStyle: 'italic' }}>
                  {regla.descripcion}
                </div>
              )}
            </div>
            {/* Acciones */}
            <div className="flex ic g4" style={{ flexShrink: 0 }}>
              <button
                title={regla.activa ? 'Desactivar' : 'Activar'}
                className={`btn btn-xs ${regla.activa ? 'btn-s' : 'btn-g'}`}
                style={{ fontSize: 11, padding: '2px 7px' }}
                onClick={toggleActiva}
              >
                {regla.activa ? 'Activa' : 'Inactiva'}
              </button>
              <button title="Editar" className="btn btn-s btn-xs" onClick={() => setEditando(true)}>
                <IcoEdit />
              </button>
              {confirmDel ? (
                <>
                  <button
                    className="btn btn-xs"
                    style={{ background: 'var(--red)', color: '#fff', fontSize: 11 }}
                    onClick={eliminar}
                  >
                    Confirmar
                  </button>
                  <button className="btn btn-g btn-xs" onClick={() => setConfirmDel(false)}>
                    <IcoX />
                  </button>
                </>
              ) : (
                <button title="Eliminar" className="btn btn-s btn-xs" onClick={() => setConfirmDel(true)}>
                  <IcoTrash />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Panel por tipo ───────────────────────────────────────────────────────
function PanelTipo({ tipo, reglas, contextoFiltro, onCreada, onActualizada, onEliminada }) {
  const meta            = TIPO_META[tipo]
  const [agregando, setAgregando] = useState(false)
  const activas = reglas.filter(r => r.activa).length

  return (
    <div className="card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>

      {/* Header del panel */}
      <div className="flex ic jb" style={{ marginBottom: 4 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: meta.accentColor }}>
            {meta.label}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 2 }}>
            {meta.sublabel}
          </div>
        </div>
        <div className="flex ic g8">
          <span style={{
            fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 20,
            background: meta.bgColor, color: meta.accentColor,
            border: `1px solid ${meta.borderColor}`,
          }}>
            {activas} activa{activas !== 1 ? 's' : ''} / {reglas.length}
          </span>
          <button
            className="btn btn-sm"
            style={{ fontSize: 12, background: meta.accentColor, color: '#fff', border: 'none' }}
            onClick={() => setAgregando(true)}
          >
            <IcoPlus /> Agregar
          </button>
        </div>
      </div>

      {/* Lista de reglas */}
      {reglas.length === 0 && !agregando && (
        <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text3)', fontSize: 13 }}>
          No hay reglas {tipo === 'positiva' ? 'positivas' : 'negativas'} para este módulo.
          <br />
          <span style={{ fontSize: 12 }}>
            Agregá la primera para guiar al asistente.
          </span>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {reglas.map(r => (
          <ItemRegla
            key={r.id}
            regla={r}
            onActualizada={onActualizada}
            onEliminada={onEliminada}
          />
        ))}

        {agregando && (
          <FormNuevaRegla
            tipo={tipo}
            contextoFiltro={contextoFiltro}
            onCreada={r => { onCreada(r); setAgregando(false) }}
            onCancelar={() => setAgregando(false)}
          />
        )}
      </div>

    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
const TABS = [
  { key: 'todos',    label: 'Todos los módulos' },
  { key: 'familiar', label: 'Módulo Familiar' },
  { key: 'terapeuta',label: 'Módulo Terapeuta' },
  { key: 'global',   label: 'Global (ambos)' },
]

export default function AdminReglasIA() {
  const { authFetch } = useAuth()
  const [reglas,      setReglas]      = useState([])
  const [loading,     setLoading]     = useState(true)
  const [tabActiva,   setTabActiva]   = useState('todos')

  async function cargar() {
    setLoading(true)
    try {
      const res = await authFetch('/admin/reglas-ia')
      if (res.ok) setReglas(await res.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  function handleCreada(nueva) {
    setReglas(prev => [...prev, nueva])
  }
  function handleActualizada(updated) {
    setReglas(prev => prev.map(r => r.id === updated.id ? updated : r))
  }
  function handleEliminada(id) {
    setReglas(prev => prev.filter(r => r.id !== id))
  }

  // Normaliza null/undefined → 'global' para comparaciones
  const ctxOf = r => r.contexto || 'global'

  // Filtrar por tab
  const reglasFiltradas = tabActiva === 'todos'
    ? reglas
    : reglas.filter(r => ctxOf(r) === tabActiva)

  const positivas = reglasFiltradas.filter(r => r.tipo === 'positiva').sort((a, b) => a.orden - b.orden)
  const negativas = reglasFiltradas.filter(r => r.tipo === 'negativa').sort((a, b) => a.orden - b.orden)
  const totalActivas = reglas.filter(r => r.activa).length

  return (
    <div>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Reglas del Asistente IA</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            Las reglas activas se inyectan en cada prompt según el módulo ·{' '}
            <strong>{totalActivas}</strong> regla{totalActivas !== 1 ? 's' : ''} activa{totalActivas !== 1 ? 's' : ''}
          </div>
        </div>
        <button className="btn btn-s btn-sm" onClick={cargar}>
          <IcoRefresh /> Actualizar
        </button>
      </div>

      {/* ── Info ────────────────────────────────────────────────── */}
      <div style={{
        background: 'var(--blue2)', border: '1px solid var(--blue)',
        borderRadius: 10, padding: '12px 16px', marginBottom: 20,
        fontSize: 13, color: 'var(--text)', lineHeight: 1.6,
      }}>
        <strong>¿Cómo funciona?</strong> Las reglas se aplican por módulo: las del módulo{' '}
        <span style={{ color: '#3b82f6', fontWeight: 600 }}>Familiar</span> guían al asistente
        para familias, las del módulo{' '}
        <span style={{ color: '#8b5cf6', fontWeight: 600 }}>Terapeuta</span> al asistente
        clínico, y las{' '}
        <span style={{ color: '#64748b', fontWeight: 600 }}>Globales</span> aplican a ambos.
        Las <span style={{ color: 'var(--teal)', fontWeight: 600 }}>reglas positivas</span> definen
        sobre qué puede orientar. Las{' '}
        <span style={{ color: 'var(--red)', fontWeight: 600 }}>negativas</span> establecen restricciones.
      </div>

      {/* ── Tabs por contexto ───────────────────────────────────── */}
      <div className="flex ic g8" style={{ marginBottom: 20 }}>
        {TABS.map(tab => {
          const count = tab.key === 'todos'
            ? reglas.length
            : reglas.filter(r => ctxOf(r) === tab.key).length
          const activo = tabActiva === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setTabActiva(tab.key)}
              style={{
                fontSize: 12, fontWeight: activo ? 700 : 500,
                padding: '5px 14px', borderRadius: 20,
                border: `1.5px solid ${activo ? 'var(--teal)' : 'var(--border)'}`,
                background: activo ? 'rgba(56,161,105,0.08)' : 'transparent',
                color: activo ? 'var(--teal)' : 'var(--text3)',
                cursor: 'pointer',
              }}
            >
              {tab.label}
              <span style={{
                marginLeft: 6, fontSize: 10, fontWeight: 700,
                background: activo ? 'var(--teal)' : 'var(--border)',
                color: activo ? '#fff' : 'var(--text3)',
                borderRadius: 20, padding: '1px 6px',
              }}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {loading ? (
        <div style={{ padding: 60, textAlign: 'center', color: 'var(--text3)' }}>
          Cargando reglas…
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
          <PanelTipo
            tipo="positiva"
            reglas={positivas}
            contextoFiltro={tabActiva}
            onCreada={handleCreada}
            onActualizada={handleActualizada}
            onEliminada={handleEliminada}
          />
          <PanelTipo
            tipo="negativa"
            reglas={negativas}
            contextoFiltro={tabActiva}
            onCreada={handleCreada}
            onActualizada={handleActualizada}
            onEliminada={handleEliminada}
          />
        </div>
      )}

    </div>
  )
}
