@echo off
REM ================================================================
REM ARGO v10 - Iniciador Automatico para Windows
REM ================================================================

echo.
echo ========================================
echo   ARGO v10 - Iniciando Sistema
echo ========================================
echo.

REM Verificar que se instalo
if not exist venv (
    echo ERROR: No se encontro el entorno virtual
    echo Por favor ejecuta primero: INSTALAR.bat
    pause
    exit /b 1
)

REM Verificar .env
if not exist .env (
    echo ERROR: No se encontro archivo .env
    echo Por favor ejecuta primero: INSTALAR.bat
    pause
    exit /b 1
)

REM Verificar API key
findstr /C:"sk-proj-" .env >nul 2>&1
if %errorlevel% neq 0 (
    findstr /C:"sk-" .env >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo AVISO: No se detecto OpenAI API key en .env
        echo Por favor edita .env y agrega tu API key
        echo.
        pause
    )
)

echo [1/2] Iniciando Backend (FastAPI)...
echo.
start "ARGO Backend" cmd /k "cd /d %~dp0 && venv\Scripts\activate.bat && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Esperar 5 segundos para que el backend inicie
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando Frontend (React)...
echo.
start "ARGO Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Esperar 8 segundos para que el frontend inicie
timeout /t 8 /nobreak >nul

REM Abrir navegador
echo.
echo Abriendo navegador...
start http://localhost:5173

echo.
echo ========================================
echo   ARGO v10 Iniciado Correctamente
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Para detener ARGO, cierra las ventanas de Backend y Frontend
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
