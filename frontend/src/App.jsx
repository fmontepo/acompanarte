import { useEffect, useState } from "react";

function App() {
  const [mensaje, setMensaje] = useState("Cargando...");

  useEffect(() => {
    fetch("http://localhost:8000")
      .then((res) => res.json())
      .then((data) => {
        setMensaje(data.mensaje);
      })
      .catch((error) => {
        console.error(error);
        setMensaje("Error al conectar con backend");
      });
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Frontend conectado 🚀</h1>
      <p>{mensaje}</p>
    </div>
  );
}

export default App;