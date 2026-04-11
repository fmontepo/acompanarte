import { useNavigate } from 'react-router-dom'
export default function NotFound() {
  const nav = useNavigate()
  return (
    <div style={{ minHeight:'100vh', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:16 }}>
      <div style={{ fontSize:48, fontWeight:700, color:'var(--text3)' }}>404</div>
      <div style={{ fontSize:16, color:'var(--text2)' }}>Página no encontrada</div>
      <button className="btn btn-p" onClick={() => nav(-1)}>← Volver</button>
    </div>
  )
}
