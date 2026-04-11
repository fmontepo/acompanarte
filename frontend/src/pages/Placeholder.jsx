export default function Placeholder({ title }) {
  return (
    <div style={{ padding: 40, textAlign: "center", color: "var(--text3)" }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>🚧</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: "var(--text)" }}>{title}</div>
      <div style={{ fontSize: 13, marginTop: 6 }}>En construcción</div>
    </div>
  )
}
