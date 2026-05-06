# ============================================================
#  verificar_entorno.ps1 — Acompañarte
#  Verifica e instala las herramientas necesarias para
#  ejecutar la aplicación en Windows.
#
#  Cómo ejecutarlo (abrir PowerShell como Administrador):
#    cd "ruta\a\acompañarte"
#    Set-ExecutionPolicy -Scope Process Bypass -Force
#    .\verificar_entorno.ps1
# ============================================================

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# ── Colores ──────────────────────────────────────────────────
function Write-OK    { param($m) Write-Host "  [OK] $m" -ForegroundColor Green  }
function Write-MISS  { param($m) Write-Host "  [!!] $m" -ForegroundColor Red    }
function Write-INFO  { param($m) Write-Host "  [->] $m" -ForegroundColor Cyan   }
function Write-WARN  { param($m) Write-Host "  [~]  $m" -ForegroundColor Yellow }
function Write-TITLE { param($m) Write-Host "`n$m" -ForegroundColor White       }

# ── Helpers ──────────────────────────────────────────────────
function Test-Command { param($cmd) return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Install-WingetPackage {
    param($id, $name)
    Write-INFO "Instalando $name con winget..."
    winget install --id $id --accept-package-agreements --accept-source-agreements -e
}

function Wait-DockerRunning {
    Write-INFO "Esperando que Docker Desktop arranque (puede tardar 30-60 segundos)..."
    $max = 60; $i = 0
    while ($i -lt $max) {
        try {
            $null = docker info 2>&1
            if ($LASTEXITCODE -eq 0) { return $true }
        } catch {}
        Start-Sleep -Seconds 3
        $i += 3
        Write-Host "." -NoNewline
    }
    Write-Host ""
    return $false
}

# ============================================================
#  CABECERA
# ============================================================
Clear-Host
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║      Acompañarte — Verificación de entorno    ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$faltantes = @()

# ============================================================
#  1. DOCKER DESKTOP
# ============================================================
Write-TITLE "1. Docker Desktop"

$dockerInstalled = Test-Command "docker"
if (-not $dockerInstalled) {
    # Buscar también por ruta directa (Windows coloca Docker en Program Files)
    $dockerExe = "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe"
    $dockerInstalled = Test-Path $dockerExe
}

if ($dockerInstalled) {
    Write-OK "Docker Desktop está instalado."

    # Verificar que el daemon esté corriendo
    try {
        $info = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Docker Desktop está corriendo."
        } else {
            Write-WARN "Docker está instalado pero no está corriendo."
            Write-INFO "Abriendo Docker Desktop..."
            Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
            $running = Wait-DockerRunning
            if ($running) {
                Write-OK "Docker Desktop arrancó correctamente."
            } else {
                Write-MISS "Docker Desktop no arrancó en el tiempo esperado."
                Write-INFO "Por favor inicialo manualmente desde el escritorio y volvé a ejecutar este script."
                $faltantes += "Docker Desktop no está corriendo"
            }
        }
    } catch {
        Write-WARN "No se pudo verificar el estado del daemon Docker."
        $faltantes += "Docker daemon no responde"
    }
} else {
    Write-MISS "Docker Desktop NO está instalado."
    $faltantes += "Docker Desktop"

    $resp = Read-Host "  ¿Querés instalarlo ahora? (s/n)"
    if ($resp -match "^[sS]") {
        # Intentar con winget (disponible en Windows 10 1809+ y Windows 11)
        if (Test-Command "winget") {
            Install-WingetPackage "Docker.DockerDesktop" "Docker Desktop"
            Write-OK "Instalación completada."
            Write-WARN "Reiniciá la PC y volvé a ejecutar este script para verificar."
        } else {
            Write-INFO "Abriendo el sitio de descarga de Docker Desktop..."
            Start-Process "https://www.docker.com/products/docker-desktop/"
            Write-INFO "Descargá e instalá Docker Desktop, luego volvé a ejecutar este script."
        }
        exit 0
    }
}

# ============================================================
#  2. OLLAMA  (motor de IA — corre en Windows, no en Docker)
# ============================================================
Write-TITLE "2. Ollama (motor de IA local)"

$ollamaInstalled = Test-Command "ollama"
if (-not $ollamaInstalled) {
    # Buscar en ruta común de instalación
    $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    $ollamaInstalled = Test-Path $ollamaExe
}

if ($ollamaInstalled) {
    Write-OK "Ollama está instalado."

    # Verificar que el servidor esté corriendo
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-OK "El servidor Ollama está corriendo (puerto 11434)."
        } else {
            Write-WARN "Ollama instalado pero el servidor no responde."
            $faltantes += "Servidor Ollama no está corriendo"
        }
    } catch {
        Write-WARN "El servidor Ollama no está corriendo."
        Write-INFO "Iniciando Ollama en segundo plano..."
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 4
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-OK "Ollama arrancó correctamente."
        } catch {
            Write-MISS "No se pudo iniciar Ollama automáticamente."
            Write-INFO "Abri una terminal y ejecutá: ollama serve"
            $faltantes += "Servidor Ollama no está corriendo"
        }
    }
} else {
    Write-MISS "Ollama NO está instalado."
    Write-INFO "Ollama es necesario para el Asistente IA de la aplicación."
    $faltantes += "Ollama"

    $resp = Read-Host "  ¿Querés instalarlo ahora? (s/n)"
    if ($resp -match "^[sS]") {
        if (Test-Command "winget") {
            Install-WingetPackage "Ollama.Ollama" "Ollama"
            Write-OK "Ollama instalado."
            Write-INFO "Iniciando el servidor Ollama..."
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 4
        } else {
            Write-INFO "Abriendo el sitio de descarga de Ollama..."
            Start-Process "https://ollama.com/download/windows"
            Write-INFO "Descargá e instalá Ollama, luego volvé a ejecutar este script."
            exit 0
        }
    }
}

# ============================================================
#  3. MODELO DE IA  (qwen2.5:3b — requerido por el backend)
# ============================================================
Write-TITLE "3. Modelo de IA (qwen2.5:3b)"

# Leer el modelo configurado en .env si existe
$modeloConfigurado = "qwen2.5:3b"
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    $linea = Get-Content $envFile | Where-Object { $_ -match "^OLLAMA_MODEL=" }
    if ($linea) {
        $modeloConfigurado = ($linea -split "=", 2)[1].Trim()
    }
}

try {
    $modelosRaw = ollama list 2>&1
    if ($modelosRaw -match $modeloConfigurado.Split(":")[0]) {
        Write-OK "Modelo '$modeloConfigurado' ya está descargado."
    } else {
        Write-MISS "El modelo '$modeloConfigurado' NO está descargado."
        Write-INFO "Tamaño aproximado: ~2 GB (qwen2.5:3b)"
        $faltantes += "Modelo Ollama '$modeloConfigurado'"

        $resp = Read-Host "  ¿Querés descargarlo ahora? (s/n)"
        if ($resp -match "^[sS]") {
            Write-INFO "Descargando modelo (esto puede tardar varios minutos según la velocidad de internet)..."
            ollama pull $modeloConfigurado
            if ($LASTEXITCODE -eq 0) {
                Write-OK "Modelo descargado correctamente."
                $faltantes = $faltantes | Where-Object { $_ -ne "Modelo Ollama '$modeloConfigurado'" }
            } else {
                Write-MISS "Error al descargar el modelo."
                Write-INFO "Podés descargarlo manualmente ejecutando: ollama pull $modeloConfigurado"
            }
        } else {
            Write-INFO "Podés descargarlo después con: ollama pull $modeloConfigurado"
            Write-WARN "Sin el modelo, el Asistente IA no funcionará."
        }
    }
} catch {
    Write-WARN "No se pudo verificar los modelos descargados (¿está corriendo Ollama?)."
    $faltantes += "Modelo Ollama no verificado"
}

# ============================================================
#  4. ARCHIVO .env
# ============================================================
Write-TITLE "4. Archivo de configuración (.env)"

$envPath = Join-Path $PSScriptRoot ".env"
if (Test-Path $envPath) {
    Write-OK "Archivo .env encontrado."
} else {
    Write-MISS "No existe el archivo .env en la raíz del proyecto."
    Write-INFO "Creando .env desde .env.example..."
    $examplePath = Join-Path $PSScriptRoot ".env.example"
    if (Test-Path $examplePath) {
        Copy-Item $examplePath $envPath
        Write-OK "Archivo .env creado. IMPORTANTE: revisá y editá las claves SECRET_KEY y ENCRYPTION_KEY."
    } else {
        Write-WARN "Tampoco existe .env.example. Creá el archivo .env manualmente."
        $faltantes += "Archivo .env"
    }
}

# ============================================================
#  RESUMEN FINAL
# ============================================================
Write-Host ""
Write-Host "  ═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor White
Write-Host "  ═══════════════════════════════════════════════" -ForegroundColor Cyan

if ($faltantes.Count -eq 0) {
    Write-Host ""
    Write-OK "Entorno completo. Todo listo para iniciar la aplicación."
    Write-Host ""
    Write-Host "  Para iniciar Acompañarte ejecutá:" -ForegroundColor White
    Write-Host "    docker compose up --build" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Luego abrí en tu navegador:" -ForegroundColor White
    Write-Host "    http://localhost:5173   (Aplicación)" -ForegroundColor Yellow
    Write-Host "    http://localhost:5050   (pgAdmin — admin de BD)" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-MISS "Hay $($faltantes.Count) elemento(s) pendiente(s):"
    foreach ($f in $faltantes) {
        Write-Host "    • $f" -ForegroundColor Red
    }
    Write-Host ""
    Write-INFO "Resolvé los puntos pendientes y volvé a ejecutar este script."
    Write-Host ""
}
