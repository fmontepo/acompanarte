# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Acompañarte** is a therapeutic support platform connecting patients, families, and professional teams with embedded AI. Built for Autism Spectrum Disorder (TEA) support in Spanish-speaking contexts.

**Key Characteristics:**
- Role-based access (Familia, Terapeuta-Interno, Terapeuta-Externo, Administrador)
- AI assistant powered by local Ollama (qwen2.5:3b) — no cloud API calls
- Clinical data encrypted at application level (PII protection)
- Internal RAG (Retrieval-Augmented Generation) with embeddings for therapists
- PostgreSQL with pgvector for vector search
- Full audit trail for compliance (Ley 25.326 Argentina)

---

## Architecture

### High-Level Overview

```
Frontend (React 19 + Vite) ──── CORS ──── Backend (FastAPI)
  ↓                                          ↓
Tailwind CSS                            PostgreSQL + pgvector
Local Auth Context                            ↓
                                        Ollama (Local IA)
                                        HuggingFace embeddings
```

### Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, lifespan hooks, role seeding
│   ├── api/                    # API v1 routers (22+ modules)
│   │   ├── auth_router.py      # JWT login/register, token validation
│   │   ├── paciente_router.py  # Patient CRUD + linked family/teams
│   │   ├── sesion_ia_router.py # Chat sessions, RAG pipeline
│   │   ├── dashboard_router.py # Role-specific analytics
│   │   └── ...                 # Other domain routers
│   ├── models/                 # SQLAlchemy async models (15+ tables)
│   │   ├── usuario.py          # Base user (polymorphic)
│   │   ├── paciente.py         # Patient (name/clinical data encrypted)
│   │   ├── ia.py               # SesionIA, MensajeIA
│   │   ├── registro.py         # Clinical follow-up records
│   │   └── ...
│   ├── schemas/                # Pydantic v2 validation
│   ├── services/               # Business logic (inherit from BaseService)
│   ├── db/
│   │   ├── session.py          # AsyncSessionLocal, engine config
│   │   └── base.py             # Declarative base
│   └── core/
│       ├── config.py           # Settings (database URL)
│       └── security.py         # Encryption utilities
├── migrations/                 # Alembic (SQLAlchemy migrations)
├── requirements.txt            # Production dependencies
├── requirements-test.txt       # Test-only dependencies
└── Dockerfile                  # Multi-stage optimized for prod
```

### Frontend Structure

```
frontend/src/
├── App.jsx                     # AuthProvider wrapper
├── main.jsx                    # React DOM entry
├── router/index.jsx            # React Router (ProtectedRoute, PublicRoute)
├── context/AuthContext.jsx     # Global session state + JWT token management
├── pages/
│   ├── LoginPage.jsx           # Unified login (role-based redirect)
│   ├── familiar/               # Family panel (4 pages)
│   ├── terapeuta/interno/      # Internal therapist (6 pages)
│   ├── terapeuta/externo/      # External therapist (2 pages)
│   ├── admin/                  # Admin panel (6 pages)
│   └── AsistentePublico.jsx    # Public AI chat (no auth)
├── components/layout/AppShell.jsx  # Nav sidebar + Outlet (role-aware icons)
├── styles/
│   ├── tokens.css              # Design tokens (colors, spacing, etc.)
│   ├── global.css              # Reset + base styles
│   └── shell.css               # Layout shell styles
└── assets/                     # Images, icons
```

### Data Flow

1. **Authentication:** Browser login → `/api/v1/auth/login` → JWT token + user object stored in localStorage
2. **Protected Routes:** ProtectedRoute checks token validity against `/api/v1/auth/me`
3. **API Calls:** AuthContext provides fetch wrapper with Authorization header
4. **Role Navigation:** Backend returns `nav_config` per role; AppShell renders dynamically
5. **AI Interaction:** Chat messages → `/api/v1/sesiones-ia` + `/api/v1/mensajes-ia` → Ollama inference + RAG pipeline

---

## Development Commands

### Backend

```bash
# Setup
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run development server (hot reload)
docker-compose up backend

# Run with existing database (skip migrations)
docker-compose up backend -d

# Lint
cd backend
python -m pylint app/ --rcfile=.pylintrc

# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test function
pytest tests/unit/test_auth.py::test_login_success

# Run tests with asyncio support
pytest tests/ -v --asyncio-mode=auto

# Integration tests only
pytest tests/integration/ -v

# E2E tests (requires services running)
pytest tests/e2e/ -v
```

**Database Migrations:**
```bash
# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Create new migration after model change
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

**Reset Database (Development Only):**
```bash
python reset_db.py
# This tears down and recreates the database, runs all migrations, seeds initial data
```

### Frontend

```bash
# Setup
cd frontend
npm install

# Development server (hot reload via Vite)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# E2E tests (Playwright)
npm run test:e2e

# Run specific E2E test
npm run test:e2e:auth

# Interactive test UI
npm run test:e2e:ui

# View test report
npm run test:e2e:report
```

### Full Stack (Docker)

```bash
# Start all services (frontend, backend, postgres, pgadmin)
docker-compose up --build

# Stop services
docker-compose down

# View logs from all services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f backend

# Access pgAdmin (Postgres UI)
# http://localhost:5050
# Email: admin@gmail.com | Password: admin123
```

---

## Key Architectural Patterns

### 1. **Async SQLAlchemy**
- All database operations are async (`AsyncSession`, `asyncpg`)
- Pool size: 10 connections, max overflow: 20
- Models use `lazy="selectin"` to eagerly load relations (prevent N+1)
- Every endpoint receives `db: AsyncSession = Depends(get_db)`

### 2. **JWT Authentication**
- Token issued by `/auth/login` contains: `sub` (user_id), `rol_key`, `exp`, `iat`
- OAuth2PasswordBearer scheme (standard FastAPI)
- `get_current_user()` dependency validates token + loads user with role
- Frontend stores token + user object in localStorage
- AuthContext validates token on app start via `/auth/me`

### 3. **Dependency Injection (FastAPI)**
```python
# app/api/deps.py defines reusable dependencies:
DBDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]

# Usage in router:
@router.get("/me")
async def get_me(user: CurrentUser):
    return user
```

### 4. **Service Layer Pattern**
- `BaseService(Generic)` provides CRUD operations
- Each domain (Usuario, Paciente, SesionIA, etc.) inherits from `BaseService`
- Services encapsulate business logic; routers are thin

### 5. **Pydantic Schemas (v2)**
- Request bodies validated automatically by FastAPI
- Response schemas define output contracts
- `model_dump(exclude_unset=True)` for partial updates

### 6. **RBAC (Role-Based Access Control)**
- Roles stored in DB: familia, ter-int, ter-ext, admin
- Each role has `nav_config` (dynamic menu structure) + `default_path` (redirect post-login)
- Routers check role membership via `CurrentUser.rol_key`
- Frontend route protection: `ProtectedRoute` checks `allowedRoles`

### 7. **AI/RAG Pipeline**
- **Local Inference:** Ollama runs on host (port 11434)
- **Embeddings:** Sentence-transformers model cached in `/hf_cache`
- **Vector Search:** PostgreSQL pgvector extension (HNSW index)
- **Clinical Embeddings:** Batch job via APScheduler (nightly)
- **Anonimization:** User context stripped of PII before LLM call
- **RAG Rules:** Positive rules (what IA can do) + negative rules (restrictions)

### 8. **Data Encryption (PII)**
- Patient names, surnames, observations encrypted at app level (Fernet cipher)
- `encryption.py` provides `encrypt_field()` / `decrypt_field()`
- Encrypted fields stored as TEXT in DB
- Environment variable: `ENCRYPTION_KEY` (must be Fernet key)

### 9. **Lifespan Events (FastAPI)**
- `lifespan` context manager runs on startup/shutdown
- Startup: create tables, run migrations, seed roles, start scheduler
- Shutdown: stop scheduler, dispose connection pool
- Idempotent (safe to run multiple times)

### 10. **CORS Configuration**
```python
# app/main.py
CORSMiddleware(
    allow_origins=["http://localhost:5173", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
In production, restrict `allow_origins` to the actual frontend domain.

---

## Common Tasks

### Add a New API Endpoint

1. **Create Pydantic schema** → `backend/app/schemas/my_domain.py`
2. **Create router** → `backend/app/api/my_domain_router.py` with `@router.get/post/put/delete`
3. **Register in main.py** → `app.include_router(my_domain_router, prefix="/api/v1")`
4. **Use dependency injection** → `user: CurrentUser`, `db: DBDep`, `body: MySchema`

Example:
```python
# backend/app/api/my_domain_router.py
from fastapi import APIRouter
from app.api.deps import CurrentUser, DBDep

router = APIRouter(prefix="/my-domain", tags=["MyDomain"])

@router.get("/")
async def list_items(user: CurrentUser, db: DBDep):
    return {"user_id": user.id}
```

### Add a New Database Model

1. **Create model** → `backend/app/models/my_model.py` (inherit from `Base`)
2. **Update `app/db/base.py`** → import the model (for `Base.metadata.create_all()`)
3. **Create migration** → `alembic revision --autogenerate -m "add my_model table"`
4. **Apply migration** → `alembic upgrade head`

### Add a Frontend Page

1. **Create component** → `frontend/src/pages/my-role/MyPage.jsx`
2. **Add route** → `frontend/src/router/index.jsx` under the appropriate role's `<ProtectedRoute>`
3. **Add to nav config** → `backend/app/main.py` in `_ROLES_SEED` (update role's `nav_config`)
4. **Use AuthContext** → `const { user } = useAuth()` to access current user

### Debug Failed Tests

```bash
# Backend test with verbose output
pytest tests/unit/test_auth.py::test_login_success -vv -s

# Show print statements and logs
pytest tests/integration/ -s --log-cli-level=DEBUG

# Run with pdb (debugger)
pytest tests/unit/test_auth.py --pdb
```

### Check TypeScript/Linting Issues (Frontend)

```bash
npm run lint

# ESLint is configured in eslint.config.js
# Common issues: unused variables, missing dependency arrays in useEffect
```

---

## Important Files & Where to Make Changes

| Task | File |
|------|------|
| Add new API endpoint | `backend/app/api/*_router.py` |
| Add new database table | `backend/app/models/my_model.py` + `alembic revision` |
| Change role navigation menu | `backend/app/main.py` → `_ROLES_SEED` |
| Add AI rules (prompting) | `backend/app/main.py` → `_REGLAS_SEED` |
| Update CORS origins | `backend/app/main.py` → `CORSMiddleware` |
| Add frontend route | `frontend/src/router/index.jsx` |
| Add frontend page | `frontend/src/pages/my-role/MyPage.jsx` |
| Update API URL (frontend) | `.env` → `VITE_API_URL` |
| Configure Ollama model | `.env` → `OLLAMA_MODEL` |
| Configure embeddings model | `.env` → `EMBEDDING_MODEL` |
| Encrypt sensitive fields | `backend/app/core/security.py` |

---

## Environment Variables

### Development (`.env`)

```env
DATABASE_URL=postgresql+asyncpg://acomp_user:cambia_esto@db:5432/acompanarte_db
SECRET_KEY=<gen: python -c "import secrets; print(secrets.token_hex(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_BATCH_SCHEDULE=0 3 * * *
ENCRYPTION_KEY=<gen: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
VITE_API_URL=http://localhost:8000/api/v1
```

### Production (`.env.prod`)

- Use strong passwords (20+ chars) for DB
- Generate secrets with `python -c "import secrets; print(secrets.token_hex(32))"`
- `EMBEDDING_BATCH_SCHEDULE=0 6 * * *` (3 AM UTC = midnight ART)
- `VITE_API_URL=/api/v1` (relative, proxied by nginx)
- `ACCESS_TOKEN_EXPIRE_MINUTES=60` (increased for prod)

---

## Testing Strategy

### Unit Tests
- Located in `tests/unit/`
- Mock database, external services
- Fast execution (< 1s each)

### Integration Tests
- Located in `tests/integration/`
- Use real async database (SQLite in-memory or Postgres testcontainer)
- Test services + repositories layer

### E2E Tests (Playwright)
- Located in `tests/e2e/`
- Frontend automation against running services
- `auth.spec.ts` runs first (generates login state for other tests)
- State stored in `.playwright-state/`

### Running Tests in CI
```bash
# Backend
pytest tests/ --cov=app --cov-report=html

# Frontend
npm run test:e2e --reporter=html
```

---

## Deployment

### To DonWeb VPS (Ubuntu 22.04)

Reference: `DEPLOY_GUIDE.md` in repo root

1. SSH into server
2. Install Docker, Docker Compose
3. Install Ollama (system-wide, not containerized)
4. Clone repo, set up `.env.prod`
5. `docker-compose -f docker-compose.prod.yml up --build -d`
6. Run migrations: `docker-compose exec backend alembic upgrade head`
7. Configure nginx (reverse proxy for port 80 → backend:8000 + frontend:5173)

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status": "ok", "version": "1.0.0"}

# Ollama availability
curl http://localhost:11434/api/tags
# Expected: JSON with model list

# Database
docker-compose exec db pg_isready -U acomp_user -d acompanarte_db
```

---

## Notes for Future Development

1. **No external LLM APIs:** All inference runs locally via Ollama. No OpenAI/Claude API calls. Cost-effective + privacy-preserving.

2. **Async-first backend:** All database calls are async. Never use sync drivers. Pattern: `async with AsyncSessionLocal() as db:`.

3. **Role seeding is idempotent:** Changes to `_ROLES_SEED` in `main.py` are synced on every app restart. No need to reset the table.

4. **pgvector indices:** HNSW indices on embedding columns for fast approximate nearest-neighbor search. Keep embedding dimension consistent (384 for MiniLM).

5. **Encryption at rest:** Patient names/diagnoses encrypted before DB insert. Key must be Fernet-compliant (from `cryptography` library).

6. **Frontend state:** AuthContext is the single source of truth for user session. Always check `isLoading` before rendering protected routes.

7. **CORS in prod:** Restrict origins to your domain. Current config allows localhost only.

8. **Audit trail:** All user actions logged in `auditoria` table via middleware or explicit service calls.
