#!/usr/bin/env python3
"""
scripts/test_ollama.py
Verifica que Ollama responde desde dentro del contenedor Docker.

Uso:
    docker compose exec backend python scripts/test_ollama.py
"""

import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

print()
print("=" * 50)
print("  Test de conectividad con Ollama")
print("=" * 50)
print(f"  URL: {OLLAMA_URL}")
print()

try:
    r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    r.raise_for_status()
    data = r.json()
    modelos = [m["name"] for m in data.get("models", [])]

    if modelos:
        print("✅ Ollama responde. Modelos disponibles:")
        for m in modelos:
            print(f"   • {m}")
    else:
        print("⚠️  Ollama responde pero no hay modelos descargados.")
        print("   Ejecutar en Windows: ollama pull llama3.1:8b")

except httpx.ConnectError:
    print("❌ No se pudo conectar a Ollama.")
    print("   Verificar que Ollama está corriendo en Windows (ollama serve).")

except httpx.TimeoutException:
    print("❌ Timeout al conectar con Ollama.")
    print("   Ollama puede estar iniciando. Esperar 10 segundos y reintentar.")

except Exception as e:
    print(f"❌ Error inesperado: {e}")

print()

# Test de generación básica
print("-" * 50)
print("  Test de generación de texto")
print("-" * 50)
MODELO = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
print(f"  Modelo: {MODELO}")
print()

try:
    r = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODELO, "prompt": "Respondé solo: hola", "stream": False},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    respuesta = data.get("response", "").strip()
    print(f"✅ Generación OK. Respuesta: {respuesta[:80]}")

except httpx.ConnectError:
    print("❌ Ollama no disponible para generación.")

except Exception as e:
    print(f"❌ Error en generación: {e}")

print()
