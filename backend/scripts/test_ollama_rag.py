#!/usr/bin/env python3
"""
scripts/test_ollama_rag.py
Testea Ollama con un prompt RAG real y muestra el error exacto si falla.

Uso:
    docker compose exec backend python scripts/test_ollama_rag.py
"""
import asyncio, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

PROMPT_CORTO = "Respondé en una oración: ¿qué es el autismo?"

PROMPT_RAG = """Eres un asistente de apoyo para familias con niños en el espectro autista.
Tu rol es orientar y acompañar, NUNCA diagnosticar.
Basá tu respuesta EXCLUSIVAMENTE en la siguiente bibliografía validada:

--- BIBLIOGRAFÍA ---
[Fuente: Señales tempranas del TEA]
Las señales de alerta para TEA pueden observarse desde los primeros meses de vida.
A los 6 meses: no sonríe ampliamente, no responde a sonidos, ausencia de balbuceo.
A los 12 meses: no señala, no responde al nombre, pérdida de habilidades.
A los 24 meses: no usa frases de dos palabras, no imita acciones.
--- FIN BIBLIOGRAFÍA ---

Consulta del familiar:
¿Cuáles son las señales tempranas de autismo en un bebé?

Respondé en español, con empatía y claridad."""


async def test(descripcion, prompt, timeout=300):
    print(f"\n  📤 Test: {descripcion}")
    print(f"     Prompt: {len(prompt)} chars | Timeout: {timeout}s")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 256, "num_ctx": 4096},
                }
            )
            r.raise_for_status()
            data = r.json()
            elapsed = time.time() - t0
            respuesta = data.get("response", "").strip()
            print(f"  ✅ OK en {elapsed:.1f}s")
            print(f"     Respuesta: {respuesta[:200]}")
            return True
    except httpx.TimeoutException:
        print(f"  ❌ TIMEOUT después de {time.time()-t0:.0f}s — el modelo tarda demasiado")
        print(f"     Solución: aumentar timeout o usar un modelo más liviano (gemma2:2b)")
        return False
    except httpx.HTTPStatusError as e:
        print(f"  ❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
        return False
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")
        return False


async def main():
    print()
    print("═" * 55)
    print("  Diagnóstico Ollama — prompt RAG")
    print(f"  Modelo: {OLLAMA_MODEL}")
    print("═" * 55)

    ok1 = await test("Prompt corto (baseline)", PROMPT_CORTO, timeout=60)
    ok2 = await test("Prompt RAG completo", PROMPT_RAG, timeout=300)

    print()
    if ok1 and ok2:
        print("  🎯 Ollama funciona con prompts RAG. El pipeline debería estar OK.")
    elif ok1 and not ok2:
        print("  ⚠️  Ollama responde prompts cortos pero falla con RAG.")
        print("     Causa probable: timeout o contexto demasiado largo.")
        print("     Probá con: ollama pull gemma2:2b  (más rápido)")
    else:
        print("  ❌ Ollama no responde. Verificar que está corriendo.")
    print()

if __name__ == "__main__":
    asyncio.run(main())
