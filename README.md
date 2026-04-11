# 🤝 Acompañarte

> Plataforma web de apoyo terapéutico que conecta pacientes, familias y equipos profesionales, potenciada con Inteligencia Artificial.

---

## 📋 Descripción

**Acompañarte** es una aplicación web orientada a facilitar el seguimiento terapéutico de pacientes, permitiendo la colaboración entre terapeutas, familiares y administradores en un entorno seguro y centralizado. Integra un módulo de IA para sesiones de asistencia inteligente.

---

## 🏗️ Arquitectura del Proyecto

```
acompañarte/
├── backend/                  # API REST en Python (FastAPI)
│   ├── app/
│   │   ├── api/              # Endpoints / Rutas
│   │   ├── models/           # Modelos de base de datos (SQLAlchemy)
│   │   ├── schemas/          # Validación de datos (Pydantic)
│   │   ├── services/         # Lógica de negocio
│   │   └── db/               # Conexión a base de datos
│   ├── core/                 # Configuración y seguridad
│   ├── migrations/           # Migraciones de BD (Alembic)
│   ├── repositories/         # Capa de acceso a datos
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Interfaz de usuario (React + Vite)
│   ├── src/
│   │   ├── App.jsx
│   │   └── assets/
│   ├── public/
│   └── package.json
├── docker-compose.yml        # Orquestación de servicios
└── .env                      # Variables de entorno (NO versionado)
```

---

## 🛠️ Tecnologías utilizadas

| Capa | Tecnología |
|---|---|
| **Backend** | Python · FastAPI · SQLAlchemy · Alembic |
| **Frontend** | React · Vite · Tailwind CSS |
| **Base de datos** | PostgreSQL · pgvector |
| **IA** | Integración con modelos de lenguaje |
| **Infraestructura** | Docker · Docker Compose |

---

## ⚙️ Requisitos previos

Antes de ejecutar el proyecto, asegurate de tener instalado:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/CursosAGT/acompanarte.git
cd acompanarte
```

### 2. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo y completar con tus datos
cp .env.example .env
```

Editá el archivo `.env` con tus credenciales de base de datos y claves secretas.

### 3. Levantar los servicios con Docker

```bash
docker-compose up --build
```

Esto levanta automáticamente:
- ✅ Backend (FastAPI) → http://localhost:8000
- ✅ Frontend (React) → http://localhost:5173
- ✅ PostgreSQL + pgvector → puerto 5432

### 4. Aplicar migraciones de base de datos

```bash
docker-compose exec backend alembic upgrade head
```

---

## 📡 Endpoints principales del API

| Módulo | Ruta base |
|---|---|
| Usuarios | `/api/usuarios` |
| Pacientes | `/api/pacientes` |
| Terapeutas | `/api/terapeutas` |
| Sesiones IA | `/api/sesiones-ia` |
| Alertas | `/api/alertas` |
| Documentación interactiva | `/docs` (Swagger UI) |

---

## 👥 Roles del sistema

- **Administrador** → gestión global de la plataforma
- **Terapeuta** → seguimiento de pacientes y equipos
- **Familiar** → acompañamiento y registro de actividades
- **Paciente** → acceso a recursos y sesiones de IA

---

## 📁 Variables de entorno requeridas

Crear un archivo `.env` en la raíz con la siguiente estructura:

```env
# Base de datos
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/acompanarte

# Seguridad
SECRET_KEY=tu_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# IA
OPENAI_API_KEY=tu_api_key
```

---

## 🎓 Contexto académico

Proyecto desarrollado en el marco del curso de **IA Aplicada al Desarrollo de Software**.

---

## 👤 Autor

**fmontepo** — [@fmontepo](https://github.com/fmontepo)
