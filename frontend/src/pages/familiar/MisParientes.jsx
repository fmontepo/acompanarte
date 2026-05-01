// frontend/src/pages/familiar/MisParientes.jsx
// Vista del familiar: lista de todos los pacientes a los que está vinculado,
// con parentesco, permisos y datos básicos de cada uno.

import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

// ─── Iconos ──────────────────────────────────────────────────────────────────

const IcoUser = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IcoShield = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
  </svg>
)
const IcoCalendar = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="4" width="18" height="18" rx="2"/><path strokeLinecap="round" d="M16 2v4M8 2v4M3 10h18"/>
  </svg>
)
const IcoHeart = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
  </svg>
)

// ─── Helpers ─────────────────────────────────────────────────────────────────

function initiales(nombre, apellido) {
  const n = (nombre || '').trim()[0] || ''
  const a = (apellido || '').trim()[0] || ''
  return (n + a).toUpperCase() || '?'
}

function sexoLabel(s) {
  return s === 'M' ? 'Masculino' : s === 'F' ? 'Femenino' : s === 'X' ? 'No binario' : null
}

function nivelLabel(n) {
  if (!n) return null
  const map = { 1: 'Nivel de soporte 1', 2: 'Nivel de soporte 2', 3: 'Nivel de soporte 3' }
  return map[n] ?? `Nivel ${n}`
}

function formatFecha(iso) {
  if (!iso) return '—'
  return new Date(iso + 'T12:00:00').toLocaleDateString('es-AR', {
    day: '2-digit', month: 'long', year: 'numeric',
  })
}

// ─── Tarjeta de pariente ─────────────────────────────────────────────────────

function TarjetaPariente({ vinculo }) {
  const ini = initiales(vinculo.nombre, vinculo.apellido)

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 14,
      padding: '20px 22px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
    }}>
      {/* Encabezado */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div className="av av-tl" style={{
          width: 52, height: 52, fontSize: 18, borderRadius: 14, flexShrink: 0,
        }}>
          {ini}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 16, lineHeight: 1.2 }}>
            {vinculo.nombre} {vinculo.apellido}
          </div>
          <div style={{ marginTop: 4, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <span className="ch ch-pp" style={{ fontSize: 11 }}>
              {vinculo.parentesco_nombre}
            </span>
            {vinculo.es_tutor_legal && (
              <span className="ch ch-am" style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 3 }}>
                <IcoShield /> Tutor/a legal
              </span>
            )}
            {vinculo.autorizado_medico && (
              <span className="ch ch-teal" style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 3 }}>
                <IcoShield /> Aut. médico
              </span>
            )}
            {!vinculo.activo && (
              <span className="ch ch-gray" style={{ fontSize: 11 }}>Inactivo</span>
            )}
          </div>
        </div>
      </div>

      {/* Datos */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
        gap: '8px 16px',
        paddingTop: 12,
        borderTop: '1px solid var(--border)',
      }}>
        {vinculo.edad != null && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
            <span style={{ color: 'var(--text-muted)' }}><IcoCalendar /></span>
            <span>{vinculo.edad} años</span>
          </div>
        )}
        {vinculo.fecha_nacimiento && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
            <span style={{ color: 'var(--text-muted)' }}><IcoCalendar /></span>
            <span>{formatFecha(vinculo.fecha_nacimiento)}</span>
          </div>
        )}
        {sexoLabel(vinculo.sexo) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
            <span style={{ color: 'var(--text-muted)' }}><IcoUser /></span>
            <span>{sexoLabel(vinculo.sexo)}</span>
          </div>
        )}
        {nivelLabel(vinculo.nivel_soporte) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
            <span style={{ color: 'var(--text-muted)' }}><IcoHeart /></span>
            <span>{nivelLabel(vinculo.nivel_soporte)}</span>
          </div>
        )}
      </div>

      {/* Pie: desde cuándo */}
      {vinculo.vinculado_desde && (
        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Vinculado desde {formatFecha(vinculo.vinculado_desde.slice(0, 10))}
        </div>
      )}
    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────────

export default function FamMisParientes() {
  const { authFetch } = useAuth()
  const [vinculos, setVinculos] = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  useEffect(() => {
    async function cargar() {
      setLoading(true); setError('')
      try {
        const res = await authFetch('/familiar/mis-vinculos')
        if (!res.ok) throw new Error('No se pudo cargar la información.')
        setVinculos(await res.json())
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [authFetch])

  return (
    <div style={{ padding: '24px 28px', maxWidth: 860, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Mis parientes</h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
          Personas de tu familia que están registradas en Acompañarte
        </p>
      </div>

      {/* Contenido */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)', fontSize: 14 }}>
          Cargando…
        </div>
      ) : error ? (
        <div style={{
          background: 'rgba(163,45,45,0.07)', border: '1px solid rgba(163,45,45,0.25)',
          borderRadius: 10, padding: 20, color: 'var(--red)', fontSize: 14, textAlign: 'center',
        }}>
          {error}
        </div>
      ) : vinculos.length === 0 ? (
        <div style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 14, padding: '48px 24px', textAlign: 'center',
        }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>👨‍👩‍👧</div>
          <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 6 }}>Sin parientes registrados</div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 340, margin: '0 auto' }}>
            Todavía no hay ningún pariente vinculado a tu cuenta.
            Un terapeuta de Acompañarte puede realizar el vínculo.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {vinculos.map(v => (
            <TarjetaPariente key={v.vinculo_id} vinculo={v} />
          ))}
        </div>
      )}
    </div>
  )
}
