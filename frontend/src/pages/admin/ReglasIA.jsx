// admin/ReglasIA.jsx
// Gestión de reglas de comportamiento del Asistente IA
// Reglas positivas → qué puede responder
// Reglas negativas → qué NO puede responder
// Las reglas activas se inyectan en el prompt de cada consulta al modelo.

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

// ─── Colores por tipo ─────────────────────────────────────────────────────
const TIPO_META = {
  positiva: {
    label:      'Reglas positivas',
    sublabel:   'Lo que el asistente PUEDE y DEBE responder',
    accentColor:'var(--teal)',
    bgColor:    'rgba(56,161,105,0.06)',
    borderColor:'rgba(56,161,105,0.25)',
    chipClass:  'ch-teal',
    dotColor:   'var(--teal)',
    icon:       '✓',
  },
  negativa: {
    label:      'Reglas negativas',
    sublabel:   'Lo que el asistente NO DEBE responder ni hacer',
    accentColor:'var(--red)',
    bgColor:    'rgba(163,45,45,0.05)',
    borderColor:'rgba(163,45,45,0.2)',
    chipClass:  'ch-rd',
    dotColor:   'var(--red)',
    icon:       '✗',
  },
}

// ─── Formulario de nueva regla ────────────────────────────────────────────
function FormNuevaRegla({ tipo, onCreada, onCancelar }) {
  const { authFetch }   = useAuth()
  const meta            = TIPO_META[tipo]
  const [texto,       setTexto]       = useState('')
  const [descripcion, setDescripcion] = useState('')
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
        body:    JSON.stringify({ tipo, texto: texto.trim(), descripcion: descripcion.trim() || null }),
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
  const [guardando,   setGuardando]   = useState(false)
  const [confirmDel,  setConfirmDel]  = useState(false)

  async function guardarEdicion() {
    if (!textoEdit.trim()) return
    setGuardando(true)
    try {
      const res = await authFetch(`/admin/reglas-ia/${regla.id}`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ texto: textoEdit.trim(), descripcion: descEdit.trim() || null }),
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
            <button className="btn btn-g btn-xs" onClick={() => { setEditando(false); setTextoEdit(regla.texto); setDescEdit(regla.descripcion ?? '') }}>
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
              {/* Toggle activa */}
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
                  <button className="btn btn-xs" style={{ background: 'var(--red)', color: '#fff', fontSize: 11 }} onClick={eliminar}>
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
function PanelTipo({ tipo, reglas, onCreada, onActualizada, onEliminada }) {
  const meta            = TIPO_META[tipo]
  const [agregando, setAgregando] = useState(false)
  const activas   = reglas.filter(r => r.activa).length

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
        <div style={{
          padding: '20px 0', textAlign: 'center', color: 'var(--text3)', fontSize: 13,
        }}>
          No hay reglas {tipo === 'positiva' ? 'positivas' : 'negativas'} aún.
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
            onCreada={r => { onCreada(r); setAgregando(false) }}
            onCancelar={() => setAgregando(false)}
          />
        )}
      </div>

    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
export default function AdminReglasIA() {
  const { authFetch } = useAuth()
  const [reglas,  setReglas]  = useState([])
  const [loading, setLoading] = useState(true)

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

  const positivas = reglas.filter(r => r.tipo === 'positiva').sort((a, b) => a.orden - b.orden)
  const negativas = reglas.filter(r => r.tipo === 'negativa').sort((a, b) => a.orden - b.orden)

  const totalActivas = reglas.filter(r => r.activa).length

  return (
    <div>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex ic jb mb20">
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Reglas del Asistente IA</div>
          <div className="ts tm" style={{ marginTop: 3 }}>
            Las reglas activas se inyectan en cada prompt enviado al modelo ·{' '}
            <strong>{totalActivas}</strong> regla{totalActivas !== 1 ? 's' : ''} activa{totalActivas !== 1 ? 's' : ''}
          </div>
        </div>
        <button className="btn btn-s btn-sm" onClick={cargar}>
          <IcoRefresh /> Actualizar
        </button>
      </div>

      {/* ── Cómo funciona ───────────────────────────────────────── */}
      <div style={{
        background: 'var(--blue2)', border: '1px solid var(--blue)',
        borderRadius: 10, padding: '12px 16px', marginBottom: 20,
        fontSize: 13, color: 'var(--text)', lineHeight: 1.6,
      }}>
        <strong>¿Cómo funciona?</strong> Cada vez que alguien hace una consulta al asistente,
        las reglas activas se incluyen en el prompt enviado al modelo de lenguaje.
        Las <span style={{ color: 'var(--teal)', fontWeight: 600 }}>reglas positivas</span> definen
        sobre qué temas puede orientar. Las{' '}
        <span style={{ color: 'var(--red)', fontWeight: 600 }}>reglas negativas</span> establecen
        restricciones y límites de seguridad. Podés activar, desactivar o editar reglas en cualquier
        momento sin reiniciar el sistema.
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
            onCreada={handleCreada}
            onActualizada={handleActualizada}
            onEliminada={handleEliminada}
          />
          <PanelTipo
            tipo="negativa"
            reglas={negativas}
            onCreada={handleCreada}
            onActualizada={handleActualizada}
            onEliminada={handleEliminada}
          />
        </div>
      )}

    </div>
  )
}
