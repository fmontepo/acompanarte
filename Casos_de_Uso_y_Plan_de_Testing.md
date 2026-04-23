# Acompañarte — Casos de uso y plan de testing

_Documento de trabajo — inventario por rol, priorización por riesgo y propuesta de casos de testing._

---

## 1. Roles del sistema

Según el router (`frontend/src/router/index.jsx`) existen cuatro roles autenticados más un acceso público:

| Rol | `rol_key` | Ruta base |
|---|---|---|
| Público (sin auth) | — | `/login`, `/onboarding`, `/asistente` |
| Familia | `familia` | `/familiar/*` |
| Terapeuta interno | `ter-int` | `/terapeuta/interno/*` |
| Terapeuta externo | `ter-ext` | `/terapeuta/externo/*` |
| Administrador | `admin` | `/admin/*` |

---

## 2. Inventario de casos de uso por rol

Cada caso se numera (`CU-<rol>-<n>`) para poder referenciarlo después desde los casos de testing. Columna **Riesgo**: **A** (alto — bloquea operación o compromete datos), **M** (medio — degrada experiencia pero hay workaround), **B** (bajo — cosmético o flujo secundario).

### 2.1 Público / Autenticación

| ID | Caso de uso | Endpoints / pantalla | Riesgo |
|---|---|---|---|
| CU-PUB-01 | Ingresar credenciales válidas y ser redirigido a `default_path` según rol | `POST /auth/login`, `LoginPage` | **A** |
| CU-PUB-02 | Credenciales inválidas: ver mensaje de error, permanecer en login | `POST /auth/login` | A |
| CU-PUB-03 | Completar onboarding (alta de usuario nuevo) | `OnboardingPage`, `POST /usuarios` | A |
| CU-PUB-04 | Acceder al Asistente TEA público sin cuenta | `AsistentePublico`, `POST /terapeuta-ia` | M |
| CU-PUB-05 | Acceso a ruta protegida sin sesión → redirect a `/login` con `from` | `ProtectedRoute` | A |
| CU-PUB-06 | Acceso a ruta de otro rol → redirect a `/404` | `ProtectedRoute` | A |

### 2.2 Familia (`familia`)

| ID | Caso de uso | Endpoints / pantalla | Riesgo |
|---|---|---|---|
| CU-FAM-01 | Ver Dashboard con panorama del paciente vinculado | `GET /dashboard/familiar`, `Dashboard` | A |
| CU-FAM-02 | Listar seguimientos/registros del paciente | `GET /registros?...`, `Seguimientos` | A |
| CU-FAM-03 | Ver actividades asignadas y su progreso | `GET /actividades`, `GET /progreso`, `Actividades` | A |
| CU-FAM-04 | Marcar actividad/etapa completada | `PATCH /progreso/...`, `Actividades` | A |
| CU-FAM-05 | Interactuar con el asistente IA del familiar | `POST /sesion-ia` o similar, `Asistente` | M |
| CU-FAM-06 | Ver y atender alertas | `GET /alertas`, `Alertas` | M |

### 2.3 Terapeuta interno (`ter-int`)

| ID | Caso de uso | Endpoints / pantalla | Riesgo |
|---|---|---|---|
| CU-TI-01 | Ver Dashboard con pacientes y pendientes | `GET /dashboard/terapeuta`, `Dashboard` | A |
| CU-TI-02 | Listar y cargar registros clínicos | `GET/POST /registros`, `Registros` | A |
| CU-TI-03 | Crear actividad con N etapas (fix reciente de `total_etapas`) | `POST /actividades`, `Actividades` | **A** |
| CU-TI-04 | Asignar actividad a paciente | `POST /actividades/.../asignar`, `Actividades` | A |
| CU-TI-05 | Consultar base de conocimiento (listar recursos) | `GET /recursos`, `Conocimiento` | M |
| CU-TI-06 | Ver contenido completo de un recurso (modal reciente) | `GET /recursos/{id}`, `Conocimiento` | M |
| CU-TI-07 | Atender alertas generadas por el sistema | `GET/PATCH /alertas`, `Alertas` | M |
| CU-TI-08 | Usar el asistente IA interno | `POST /terapeuta-ia`, `Asistente` | M |

### 2.4 Terapeuta externo (`ter-ext`)

| ID | Caso de uso | Endpoints / pantalla | Riesgo |
|---|---|---|---|
| CU-TE-01 | Ver Dashboard (vista reducida) | `GET /dashboard/terapeuta-externo`, `Dashboard` | M |
| CU-TE-02 | Consultar registros compartidos | `GET /registros?...`, `Registros` | M |

### 2.5 Administrador (`admin`)

| ID | Caso de uso | Endpoints / pantalla | Riesgo |
|---|---|---|---|
| CU-AD-01 | Ver Dashboard con métricas y "Recursos pendientes" (widget reciente) | `GET /dashboard/admin`, `Dashboard` | **A** |
| CU-AD-02 | Validar un recurso pendiente desde el widget | `POST /recursos/{id}/validar`, `Dashboard` | **A** |
| CU-AD-03 | Gestionar usuarios (alta, edición, baja, cambio de rol) | `GET/POST/PATCH/DELETE /usuarios`, `Usuarios` | A |
| CU-AD-04 | Gestionar reglas IA | `GET/POST/PATCH /reglas-ia`, `ReglasIA` | A |
| CU-AD-05 | Consultar auditoría | `GET /auditoria`, `Auditoria` | M |
| CU-AD-06 | Ver/editar contactos públicos | `GET/PATCH /contactos-publicos`, `ContactosPublicos` | B |

---

## 3. Priorización (lo que tocamos primero)

**Top-10 de flujos críticos** (todos **A**) que deberían tener cobertura de test antes que cualquier otra cosa:

1. CU-PUB-01 — Login con credenciales válidas + redirect por rol.
2. CU-PUB-05 / CU-PUB-06 — Guardas de `ProtectedRoute` (sin sesión / rol inválido).
3. CU-AD-01 + CU-AD-02 — Dashboard admin cargando pendientes y validación (código recién tocado).
4. CU-TI-03 — Crear actividad con `total_etapas` (regresión del fix reciente).
5. CU-TI-04 — Asignar actividad a paciente.
6. CU-FAM-04 — Marcar etapa completada (cadena progreso → dashboard).
7. CU-FAM-01 — Dashboard del familiar carga datos correctos.
8. CU-TI-06 — Modal de `contenido_texto` (feature nueva) abre, muestra texto, cierra.
9. CU-AD-03 — Alta/baja de usuarios (si falla queda el sistema sin administradores).
10. CU-AD-04 — Creación/edición de reglas IA (impacta directamente la salida del asistente).

Todo lo demás queda para una segunda tanda de cobertura (riesgos M/B).

---

## 4. Propuesta de estrategia de testing

### 4.1 Capas

- **E2E (navegador real)** — happy path + un error path de los 10 casos críticos. Rápido de valor.
- **Integración backend** — endpoints que tocamos o que son pivote: `/auth/login`, `/dashboard/*`, `/actividades`, `/recursos/{id}/validar`. Con base de datos de test.
- **Unitario** — solo donde la lógica lo amerita: `normalizeRecurso` del frontend, generación de `total_etapas`, reglas de permisos del backend, parsers del asistente IA.

### 4.2 Herramientas sugeridas

| Capa | Tool | Por qué |
|---|---|---|
| E2E | **Playwright** | Mejor soporte multi-rol (múltiples `storageState`), screenshots, trazas. Fixtures sencillas para logear cada rol una vez. |
| Integración backend | **pytest + httpx + testcontainers / SQLite-memory** | El backend es FastAPI; `pytest` + `TestClient` es estándar. Testcontainers si la app depende de extensiones de Postgres. |
| Unit frontend | **Vitest + @testing-library/react** | Consistente con Vite; liviano. |
| Unit backend | **pytest** | Ya implícito. |

### 4.3 Estructura propuesta

```
/tests
  /e2e                  ← Playwright
    auth.spec.ts
    admin.dashboard.spec.ts
    terapeuta.actividades.spec.ts
    familiar.progreso.spec.ts
  /integration          ← pytest (backend)
    test_auth.py
    test_dashboard_admin.py
    test_actividades.py
    test_recursos_validar.py
  /unit
    frontend/           ← Vitest
    backend/            ← pytest
/fixtures
  seed_test.sql         ← datasets mínimos por rol
```

### 4.4 Primeros 5 tests a implementar (orden sugerido)

1. **`e2e/auth.spec.ts`** — CU-PUB-01/05/06. Login por rol + redirect + ruta prohibida. Setea `storageState` reutilizable.
2. **`integration/test_dashboard_admin.py`** — CU-AD-01/02. GET devuelve `recursos_pendientes`; POST valida y reduce el conteo.
3. **`integration/test_actividades.py`** — CU-TI-03/04. Crear actividad con 3 etapas ⇒ `total_etapas == 3`. Asignar a paciente y que aparezca en el GET del familiar.
4. **`e2e/admin.dashboard.spec.ts`** — CU-AD-01/02. Abrir widget, ver item pendiente, clickear "Ver contenido" (modal), "Validar", toast, item desaparece.
5. **`unit/frontend/normalizeRecurso.test.ts`** — mapea `contenido_texto` desde la API al shape del estado.

### 4.5 Qué necesitamos antes de arrancar

- **Seed de datos de test** con al menos: 1 admin, 1 ter-int, 1 ter-ext, 1 familia + 1 paciente + 1 recurso pendiente + 1 actividad asignada.
- Un **entorno de test** separado (DB distinta, o schema efímero por corrida).
- Una **variable `VITE_API_URL`** apuntando al backend de test en los E2E.
- Scripts `npm run test`, `npm run test:e2e`, `pytest` enganchados en el repo.

---

## 5. Próximo paso concreto sugerido

Arrancar por el item 1 de 4.4 (`e2e/auth.spec.ts`) porque desbloquea a todos los demás tests E2E al dejar listos los `storageState` por rol. En paralelo, el item 2 de integración (backend) sirve de red de seguridad para la Opción A que acabamos de implementar.

> Decime si te cierra este plan y arranco con el scaffold de Playwright + el primer spec, o si querés ajustar algo del inventario antes (agregar casos, mover prioridades, etc.).
