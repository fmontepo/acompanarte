# tests/unit/conftest.py
# ─────────────────────────────────────────────────────────────────────────────
# Conftest para tests unitarios puros (sin BD, sin servidor HTTP).
#
# Mockea las dependencias pesadas (sentence_transformers, pgvector models)
# antes de importar cualquier módulo de app/ para que los tests puedan
# correr sin instalar torch (530 MB) en el entorno de sandbox.
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
from unittest.mock import MagicMock

# ── Mock de sentence_transformers ANTES de importar app ──────────────────────
# Necesario porque ia_service.py hace "from sentence_transformers import SentenceTransformer"
# a nivel módulo. Sin este mock, el import falla si torch no está instalado.
_st_mock = MagicMock()
_st_mock.SentenceTransformer = MagicMock
sys.modules.setdefault("sentence_transformers", _st_mock)

# ── Ajuste de sys.path para encontrar el paquete app/ ────────────────────────
_CANDIDATES = [
    "/app",
    os.path.join(os.path.dirname(__file__), "..", "..", "backend"),
]
for _candidate in _CANDIDATES:
    if os.path.isdir(os.path.join(_candidate, "app")):
        if os.path.abspath(_candidate) not in sys.path:
            sys.path.insert(0, os.path.abspath(_candidate))
        break
