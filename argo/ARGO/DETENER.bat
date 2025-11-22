@echo off
REM ================================================================
REM ARGO v10 - Detener Sistema
REM ================================================================

echo.
echo ========================================
echo   ARGO v10 - Deteniendo Sistema
echo ========================================
echo.

REM Matar procesos de uvicorn (backend)
echo Deteniendo Backend...
taskkill /FI "WINDOWTITLE eq ARGO Backend*" /F >nul 2>&1
taskkill /IM "python.exe" /FI "WINDOWTITLE eq *uvicorn*" /F >nul 2>&1

REM Matar procesos de node (frontend)
echo Deteniendo Frontend...
taskkill /FI "WINDOWTITLE eq ARGO Frontend*" /F >nul 2>&1
taskkill /IM "node.exe" /FI "WINDOWTITLE eq *vite*" /F >nul 2>&1

echo.
echo ARGO detenido correctamente
echo.
pause
