# Guía de Despliegue — Acompañarte en DonWeb Cloud Server

> **Servidor:** Ubuntu 22.04 LTS · 4 vCPU · 8 GB RAM · 50 GB SSD  
> **Proveedor:** DonWeb Cloud Server (con acceso root SSH)  
> **Tiempo estimado:** 30–45 minutos (+ ~10 min descarga del modelo IA)

---

## Antes de empezar

Necesitás tener a mano:
- La **IP pública** del servidor (aparece en el Área de Cliente de DonWeb)
- La **contraseña root** (DonWeb te la envía por email al crear el servidor)
- Tu **repositorio en GitHub** con el código de Acompañarte
- Un **dominio** apuntando a esa IP (opcional, pero necesario para SSL)

---

## PASO 1 — Conectarse al servidor por SSH

Desde tu PC (Windows), abrí PowerShell o la terminal y ejecutá:

```bash
ssh root@IP-DEL-SERVIDOR
```

> Si es la primera vez, te pregunta si confiás en el host. Escribí `yes` y Enter.

**Alternativa:** DonWeb también ofrece una consola web desde el Área de Cliente si no podés usar SSH local.

---

## PASO 2 — Actualizar el sistema

Una vez dentro del servidor:

```bash
apt update && apt upgrade -y
```

Esto actualiza todos los paquetes del sistema. Puede tardar 2–3 minutos.

---

## PASO 3 — Instalar Docker

Un solo comando instala Docker y lo deja listo:

```bash
curl -fsSL https://get.docker.com | sh
```

Verificar que quedó bien instalado:

```bash
docker --version
docker compose version
```

Deberías ver algo como `Docker version 27.x.x` y `Docker Compose version v2.x.x`.

---

## PASO 4 — Instalar Ollama (módulo de IA)

Ollama se instala directamente en el sistema operativo del servidor (NO dentro de Docker):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Activar Ollama como servicio (se inicia automáticamente con el servidor):

```bash
systemctl enable ollama
systemctl start ollama
```

Verificar que está corriendo:

```bash
curl http://localhost:11434/api/tags
```

Deberías ver una respuesta JSON. Si da error, esperá 10 segundos y volvé a intentar.

---

## PASO 5 — Clonar el repositorio

```bash
mkdir -p /opt/acompanarte
cd /opt/acompanarte
git clone https://github.com/TU-USUARIO/acompanarte.git .
```

> Reemplazá `TU-USUARIO` con tu usuario real de GitHub.

Si el repositorio es privado, necesitás autenticarte. La forma más simple es con un Personal Access Token de GitHub:

```bash
git clone https://TU-USUARIO:TU-TOKEN@github.com/TU-USUARIO/acompanarte.git .
```

---

## PASO 6 — Crear el archivo de configuración de producción

Copiá el template y completalo con valores reales:

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

**Generá las claves secretas** (ejecutá estos comandos, copiá la salida):

```bash
# Para SECRET_KEY:
python3 -c "import secrets; print(secrets.token_hex(32))"

# Para ENCRYPTION_KEY:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Contenido que debés completar en `.env.prod`:

```env
COMPOSE_PROJECT_NAME=acompanarte_prod

# Base de datos
DB_USER=acomp_user
DB_PASSWORD=UNA-CONTRASENA-MUY-LARGA-Y-SEGURA
DB_NAME=acompanarte_db

# Seguridad (pegar la salida de los comandos de arriba)
SECRET_KEY=PEGAR-RESULTADO-DEL-PRIMER-COMANDO
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Cifrado
ENCRYPTION_KEY=PEGAR-RESULTADO-DEL-SEGUNDO-COMANDO

# Módulo de IA
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Frontend
VITE_API_URL=/api/v1
```

Guardá con `Ctrl+O`, Enter, y salí con `Ctrl+X`.

---

## PASO 7 — Configurar el firewall

Abrí solo los puertos necesarios:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

Verificar:

```bash
ufw status
```

Deberías ver `80/tcp`, `443/tcp` y `22/tcp` (SSH) en estado `ALLOW`.

---

## PASO 8 — Primer despliegue

Este comando hace todo: construye las imágenes Docker, levanta los servicios, inicializa la base de datos y descarga el modelo de IA:

```bash
cd /opt/acompanarte
bash scripts/deploy.sh --first
```

> **La descarga del modelo de IA tarda entre 5 y 15 minutos** según la velocidad del servidor. Es normal que parezca que se colgó. Esperá.

Al finalizar deberías ver:

```
[OK]    ═══════════════════════════════════════════
[OK]     Acompañarte desplegado correctamente ✅
[OK]    ═══════════════════════════════════════════
```

---

## PASO 9 — Verificar que todo funciona

Comprobá que la API responde:

```bash
curl http://localhost/api/v1/health
```

Comprobá que los contenedores están corriendo:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
```

Deberías ver los tres servicios (`frontend`, `backend`, `db`) en estado `running`.

Si algo falla, revisá los logs:

```bash
# Logs de todos los servicios:
docker compose -f docker-compose.prod.yml --env-file .env.prod logs --tail=50

# Solo el backend:
docker compose -f docker-compose.prod.yml --env-file .env.prod logs backend --tail=50
```

---

## PASO 10 — Configurar backup automático de base de datos

El script ya está listo. Solo hay que programarlo para que se ejecute todos los días a las 3:00 AM:

```bash
crontab -e
```

Se abre un editor. Al final del archivo agregá esta línea:

```
0 3 * * * cd /opt/acompanarte && bash scripts/backup_db.sh >> /var/log/acompanarte_backup.log 2>&1
```

Guardá y salí. Verificar que se registró:

```bash
crontab -l
```

> Nota: DonWeb ya hace backups diarios del servidor completo (snapshot), pero este script hace un backup a nivel base de datos (pg_dump), que es más limpio y restaurable. Tenés doble cobertura.

---

## PASO 11 (opcional) — Activar HTTPS con SSL

Necesitás tener un dominio apuntando a la IP del servidor antes de este paso.

**Instalar Certbot:**

```bash
apt install certbot python3-certbot-nginx -y
```

**Obtener el certificado** (reemplazá con tu dominio real):

```bash
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

Seguí las instrucciones en pantalla. Certbot modifica la configuración de Nginx automáticamente.

**Activar el bloque HTTPS en nginx.prod.conf:**

Editá `nginx/nginx.prod.conf`, descomentá el bloque `server HTTPS` (líneas 77–116) y reemplazá `tu-dominio.com` con tu dominio real. Luego reiniciá el frontend:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod restart frontend
```

**Renovación automática** (Certbot lo configura solo, pero podés verificar):

```bash
certbot renew --dry-run
```

---

## Comandos de mantenimiento diario

```bash
# Ver estado de los servicios
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f

# Actualizar la aplicación (después de un git push)
cd /opt/acompanarte && bash scripts/deploy.sh

# Reiniciar servicios sin rebuild
bash scripts/deploy.sh --restart

# Hacer backup manual ahora
bash scripts/backup_db.sh

# Ver backups disponibles
ls -lh /opt/acompanarte/backups/
```

---

## Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `curl localhost` no responde | Nginx no levantó | `docker compose ... logs frontend` |
| Error 502 Bad Gateway | Backend caído | `docker compose ... logs backend` |
| IA no responde | Ollama detenido | `systemctl status ollama` y `systemctl start ollama` |
| Base de datos no conecta | Postgres iniciando | Esperá 30 segundos y volvé a intentar |
| Sin espacio en disco | Imágenes viejas acumuladas | `docker system prune -f` |

---

## Resumen de archivos importantes en el servidor

```
/opt/acompanarte/          → raíz del proyecto
├── .env.prod              → configuración de producción (NO commitear)
├── docker-compose.prod.yml
├── scripts/
│   ├── deploy.sh          → despliegue
│   └── backup_db.sh       → backup de base de datos
└── nginx/
    └── nginx.prod.conf    → configuración del reverse proxy

/opt/acompanarte/backups/  → backups de la base de datos (7 días)
/var/log/acompanarte_backup.log  → log del cron de backups
```
