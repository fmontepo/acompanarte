# app/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no está definida en las variables de entorno")

# Convertir URL síncrona a async si viene como postgresql://
# asyncpg requiere: postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ---------------------------------------------------------------------------
# Engine async — pool de conexiones reutilizables
# ---------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # True solo para debug SQL — nunca en producción
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verifica conexión antes de usarla
)

# ---------------------------------------------------------------------------
# Fábrica de sesiones async
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Dependency para inyectar en los routers vía FastAPI
# Uso: db: AsyncSession = Depends(get_db)
# ---------------------------------------------------------------------------
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
