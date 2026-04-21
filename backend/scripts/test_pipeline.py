#!/usr/bin/env python3
"""
scripts/test_pipeline.py
Testea el pipeline RAG completo de punta a punta.

Uso:
    docker compose exec backend python scripts/test_pipeline.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar todos los modelos para evitar circular imports
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

from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.services.ia_service import (
    buscar_contexto_rag,
    procesar_consulta_publica,
    detectar_alerta,
)

SEP  = "═" * 60
SEP2 = "─" * 60

CONSULTAS = [
    {
        "label":   "Señales tempranas (debería encontrar fuentes RAG)",
        "mensaje": "¿Cuáles son las señales tempranas de autismo en un bebé?",
        "espera_alerta": False,
        "espera_fuentes": True,
    },
    {
        "label":   "Manejo de crisis (debería encontrar fuentes RAG)",
        "mensaje": "¿Qué hago cuando mi hijo tiene una crisis de conducta?",
        "espera_alerta": False,
        "espera_fuentes": True,
    },
    {
        "label":   "Mensaje con señal de alerta (debe detectar alerta)",
        "mensaje": "Mi hijo se golpea la cabeza cuando se frustra y a veces se hace daño",
        "espera_alerta": True,
        "espera_fuentes": True,
    },
    {
        "label":   "Pregunta fuera del dominio (puede no tener fuentes)",
        "mensaje": "¿Cuál es la capital de Francia?",
        "espera_alerta": False,
        "espera_fuentes": False,
    },
]


async def main():
    print()
    print(SEP)
    print("  🧪  Test Pipeline RAG — Acompañarte IA")
    print(SEP)

    async with AsyncSessionLocal() as db:

        # ── Estado de la base de conocimiento ──────────────────────────
        print()
        print("📚 Estado de la base de conocimiento:")
        total_q = await db.execute(
            select(func.count(RecursoProfesional.id))
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.activo == True)
        )
        total = total_q.scalar_one()

        con_emb_q = await db.execute(
            select(func.count(RecursoProfesional.id))
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.activo == True)
            .where(RecursoProfesional.embedding.is_not(None))
        )
        con_emb = con_emb_q.scalar_one()

        estado = "✅" if con_emb == total else "⚠️ "
        print(f"   {estado} {con_emb}/{total} recursos validados con embedding")
        print()

        if con_emb == 0:
            print("❌ No hay embeddings. Correr primero: python scripts/generar_embeddings.py")
            return

        # ── Tests individuales ──────────────────────────────────────────
        resultados = []

        for i, caso in enumerate(CONSULTAS, 1):
            print(f"{SEP2}")
            print(f"  Test {i}: {caso['label']}")
            print(f"  Consulta: \"{caso['mensaje']}\"")
            print()

            try:
                resultado = await procesar_consulta_publica(db=db, mensaje=caso["mensaje"])

                fuentes   = resultado.get("fuentes", [])
                alerta    = resultado.get("alerta", False)
                respuesta = resultado.get("respuesta", "")
                filtro    = resultado.get("filtro_aplicado", False)

                # Mostrar fuentes encontradas
                if fuentes:
                    print(f"  📎 Fuentes RAG encontradas ({len(fuentes)}):")
                    for f in fuentes:
                        print(f"     • {f['titulo'][:55]:<55} score: {f['score']:.3f}")
                else:
                    print("  📎 Sin fuentes RAG (consulta fuera del dominio o threshold alto)")

                # Mostrar alerta
                alerta_icon = "🚨" if alerta else "✅"
                print(f"  {alerta_icon} Alerta: {'SÍ' if alerta else 'No'}")

                if filtro:
                    print("  🔒 Filtro anti-diagnóstico aplicado")

                # Mostrar respuesta (primeras 200 chars)
                print(f"  💬 Respuesta (extracto):")
                print(f"     {respuesta[:200].replace(chr(10), ' ')}{'...' if len(respuesta) > 200 else ''}")

                # Verificaciones
                ok_fuentes = (len(fuentes) > 0) == caso["espera_fuentes"] or not caso["espera_fuentes"]
                ok_alerta  = alerta == caso["espera_alerta"]

                veredicto = "✅ PASS" if (ok_alerta and len(respuesta) > 20) else "⚠️  REVISAR"
                print(f"  {veredicto}")
                resultados.append(veredicto.startswith("✅"))

            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                resultados.append(False)

            print()

        # ── Resumen ─────────────────────────────────────────────────────
        print(SEP)
        pasados = sum(resultados)
        total_t = len(resultados)
        icon = "✅" if pasados == total_t else "⚠️ "
        print(f"  {icon} Resultado: {pasados}/{total_t} tests pasados")
        if pasados == total_t:
            print("  🎯 Pipeline RAG funcionando correctamente.")
        else:
            print("  Revisar los tests marcados como REVISAR.")
        print(SEP)
        print()


if __name__ == "__main__":
    asyncio.run(main())
