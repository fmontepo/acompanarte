import { useNavigate } from 'react-router-dom'
export default function OnboardingPage() {
  const nav = useNavigate()
  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ textAlign:'center', marginBottom:20 }}>
          <div style={{ fontSize:18, fontWeight:700 }}>Registrarse como familiar</div>
          <div className="txs tm" style={{ marginTop:4 }}>Próximamente disponible</div>
        </div>
        <button className="btn btn-s btn-full" onClick={() => nav('/login')}>← Volver al login</button>
      </div>
    </div>
  )
}
