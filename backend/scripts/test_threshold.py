#!/usr/bin/env python3
"""
scripts/test_threshold.py
Muestra los scores de similaridad reales para calibrar el threshold.

Uso:
    docker compose exec backend python scripts/test_threshold.py
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base                                    # noqa
from app.models.rol import Rol                                  # noqa
from app.models.usuario import Usuario                          # noqa
from app.models.familiar import Familiar                        # noqa
from app.models.terapeuta import Terapeuta                      # noqa
from app.models.administrador import Administrador              # noqa
from app.models.paciente import Paciente                        # noqa
from app.models.parentesco import Parentesco                    # noqa
from app.models.vinculoPaciente import VinculoPaciente          # noqa
from app.models.actividadFamiliar import ActividadFamiliar      # noqa
from app.models.registroSeguimiento import RegistroSeguimiento  # noqa
from app.models.alerta import Alerta                            # noqa
from app.models.ia import SesionIA, MensajeIA                  # noqa
from app.models.recursoProfesional import RecursoProfesional

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.services.ia_service import get_embedding_model

CONSULTAS = [
    "¿Cuáles son las señales tempranas de autismo en un bebé?",
    "¿Qué hago cuando mi hijo tiene una crisis de conducta?",
    "Mi hijo se golpea la cabeza cuando se frustra",
    "¿Cómo puedo comunicarme mejor con mi hijo con TEA?",
    "¿Cuál es la capital de Francia?",
]

async def main():
    print()
    print("═" * 70)
    print("  Calibración de threshold — scores de similaridad reales")
    print("═" * 70)

    model = get_embedding_model()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RecursoProfesional)
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.embedding.is_not(None))
        )
        recursos = result.scalars().all()
        print(f"\n  Recursos con embedding: {len(recursos)}\n")

        for consulta in CONSULTAS:
            print(f"  Consulta: \"{consulta}\"")
            emb = model.encode(consulta).tolist()

            scores = []
            for r in recursos:
                # Calcular cosine similarity manualmente
                import numpy as np
                a = np.array(emb)
                b = np.array(r.embedding)
                sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
                scores.append((sim, r.titulo))

            scores.sort(reverse=True)
            for sim, titulo in scores[:3]:
                barra = "█" * int(sim * 20)
                flag = " ← ✅ pasa" if sim >= 0.65 else (" ← ⚠️  pasa c/0.40" if sim >= 0.40 else " ← ❌ no pasa")
                print(f"    {sim:.3f} {barra:<20} {titulo[:45]}{flag}")
            print()

    print("  Threshold actual: 0.65")
    print("  Recomendación:    bajar a 0.40 para capturar consultas relevantes")
    print("                    sin incluir resultados irrelevantes (ej: capital de Francia)")
    print()

if __name__ == "__main__":
    asyncio.run(main())
