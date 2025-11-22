@echo off
REM ================================================================
REM ARGO v10 - Instalador Automatico para Windows
REM ================================================================

echo.
echo ========================================
echo   ARGO v10 - Instalador Automatico
echo ========================================
echo.

REM Verificar Python 3.11
echo [1/6] Verificando Python 3.11...
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.11 no encontrado
    echo Por favor instala Python 3.11 desde: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python 3.11 encontrado

REM Verificar Node.js
echo [2/6] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no encontrado
    echo Por favor instala Node.js desde: https://nodejs.org/
    pause
    exit /b 1
)
echo OK - Node.js encontrado

REM Crear entorno virtual
echo [3/6] Creando entorno virtual Python...
if exist venv (
    echo Entorno virtual ya existe, saltando...
) else (
    py -3.11 -m venv venv
    echo OK - Entorno virtual creado
)

REM Instalar dependencias Python
echo [4/6] Instalando dependencias Python...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: Fallo al instalar dependencias Python
    pause
    exit /b 1
)
echo OK - Dependencias Python instaladas

REM Instalar dependencias Node.js
echo [5/6] Instalando dependencias Node.js (puede tardar 3-5 minutos)...
cd frontend
call npm install --silent
if %errorlevel% neq 0 (
    echo ERROR: Fallo al instalar dependencias Node.js
    cd ..
    pause
    exit /b 1
)
cd ..
echo OK - Dependencias Node.js instaladas

REM Verificar archivo .env
echo [6/6] Verificando configuracion...
if not exist .env (
    echo.
    echo AVISO: No se encontro archivo .env
    echo.
    echo Creando .env desde plantilla...
    copy .env.example .env >nul 2>&1
    if %errorlevel% neq 0 (
        echo # ARGO v10 - Configuracion> .env
        echo.>> .env
        echo # OpenAI API Key (OBLIGATORIO^)>> .env
        echo OPENAI_API_KEY=sk-tu-api-key-aqui>> .env
        echo.>> .env
        echo # Anthropic API Key (OPCIONAL^)>> .env
        echo ANTHROPIC_API_KEY=sk-ant-tu-api-key-aqui>> .env
        echo.>> .env
        echo # Configuracion>> .env
        echo ENVIRONMENT=development>> .env
        echo LOG_LEVEL=INFO>> .env
    )
    echo.
    echo IMPORTANTE: Edita el archivo .env y agrega tu OPENAI_API_KEY
    echo.
)

echo.
echo ========================================
echo   Instalacion COMPLETADA
echo ========================================
echo.
echo Para iniciar ARGO, ejecuta: INICIAR.bat
echo.
echo IMPORTANTE: Antes de iniciar, edita .env y agrega tu OpenAI API key
echo.
pause
