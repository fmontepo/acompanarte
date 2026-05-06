# app/services/scheduler.py
# Scheduler de tareas periódicas usando APScheduler.
#
# Configuración vía variable de entorno EMBEDDING_BATCH_SCHEDULE:
#   - Expresión cron estándar, ej: "0 3 * * *" (3am todos los días)
#   - "disabled" → no se programa ninguna tarea automática
#   - Si la variable no está definida, el default es "0 3 * * *"
#
# Tip: para correr el batch en horario local argentino en un servidor UTC,
#   usar "0 6 * * *" (3am ART = 6am UTC).
#
# Trigger manual disponible vía endpoint POST /api/v1/ia/terapeuta/batch/embedding

import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone="UTC")

DEFAULT_SCHEDULE = "0 3 * * *"  # 3am UTC diariamente


def setup_scheduler() -> None:
    """
    Inicializa y arranca el scheduler.
    Lee EMBEDDING_BATCH_SCHEDULE del entorno para determinar el cron.
    Llamar desde el lifespan de FastAPI en startup.
    """
    schedule = os.getenv("EMBEDDING_BATCH_SCHEDULE", DEFAULT_SCHEDULE).strip()

    if schedule.lower() == "disabled":
        log.info("[Scheduler] EMBEDDING_BATCH_SCHEDULE=disabled — batch automático desactivado")
        return

    from app.services.embedding_batch import ejecutar_batch_embedding

    try:
        trigger = CronTrigger.from_crontab(schedule, timezone="UTC")
    except Exception as e:
        log.error(
            "[Scheduler] Expresión cron inválida %r — usando default %r. Error: %s",
            schedule, DEFAULT_SCHEDULE, e,
        )
        trigger = CronTrigger.from_crontab(DEFAULT_SCHEDULE, timezone="UTC")

    _scheduler.add_job(
        ejecutar_batch_embedding,
        trigger=trigger,
        id="embedding_batch_clinico",
        replace_existing=True,
        # Si el servidor estuvo apagado durante el horario programado,
        # permite ejecutarlo hasta 1 hora después del horario perdido.
        misfire_grace_time=3600,
        coalesce=True,  # si hubo varios disparos perdidos, ejecutar solo uno
    )

    _scheduler.start()
    log.info("[Scheduler] Batch de embeddings clínicos programado: %r", schedule)


def shutdown_scheduler() -> None:
    """Detiene el scheduler limpiamente. Llamar desde el lifespan en shutdown."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[Scheduler] Detenido correctamente")


async def trigger_manual() -> dict:
    """
    Ejecuta el batch de embeddings inmediatamente (trigger manual).
    Retorna las estadísticas del run. Llamado desde el endpoint de la API.
    """
    from app.services.embedding_batch import ejecutar_batch_embedding
    log.info("[Scheduler] Trigger manual del batch de embeddings clínicos")
    return await ejecutar_batch_embedding()
