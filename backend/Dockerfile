# backend/Dockerfile
# Imagen optimizada para producción:
#   - Versión fija de Python (reproducibilidad)
#   - Separación de dependencias y código (caché eficiente)
#   - Usuario no-root (seguridad)
#   - Sin archivos innecesarios (.dockerignore recomendado)

FROM python:3.11-slim

# Evitar archivos .pyc y buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- Instalar dependencias del sistema necesarias para llama-cpp y asyncpg ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Copiar e instalar dependencias Python PRIMERO (aprovecha caché de Docker) ---
# Si requirements.txt no cambia, esta capa no se reconstruye
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt

# --- Copiar el código fuente ---
COPY . .

# --- Crear usuario no-root para seguridad ---
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

# --- Directorio de cache para HuggingFace (modelo de embeddings) ---
# Creado aquí con el owner correcto para que el volumen Docker sea escribible por appuser
RUN mkdir -p /hf_cache && chown appuser:appgroup /hf_cache

USER appuser

# --- Puerto expuesto (documentación) ---
EXPOSE 8000

# --- Comando de producción ---
# En desarrollo, docker-compose sobreescribe este CMD con --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
