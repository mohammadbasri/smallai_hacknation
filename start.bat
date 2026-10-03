@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo.
echo === Small AI for Development (Windows) ===
echo.

rem Usage:  start.bat            install anything missing, then run both servers
rem         start.bat setup      install only, do not start the servers
set "SETUP_ONLY="
if /i "%~1"=="setup" set "SETUP_ONLY=1"

rem ---------- Locate Python 3.11+ ----------
set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1 && set "PY=python3"
if not defined PY (
  for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
  )
)
if not defined PY (
  echo [ERROR] Python 3.11 or newer was not found.
  echo         Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  goto :fail
)
echo Using Python: %PY%

rem ---------- Locate Node.js / npm ----------
call npm --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js / npm was not found.
  echo         Install Node 18 or newer from https://nodejs.org/
  goto :fail
)
for /f "delims=" %%V in ('node --version') do echo Using Node:   %%V

rem ---------- Backend ----------
echo.
echo [1/3] Backend: virtual environment + Python packages
if not exist "backend\.venv\Scripts\python.exe" (
  %PY% -m venv "backend\.venv" || goto :fail
)
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements-dev.txt" --quiet || goto :fail

echo.
echo [2/3] Backend: .env file
if not exist "backend\.env" (
  copy /y "backend\.env.example" "backend\.env" >nul
  echo       Created backend\.env from .env.example
) else (
  echo       backend\.env already exists, leaving it alone
)

rem ---------- Frontend ----------
echo.
echo [3/3] Frontend: npm packages
pushd frontend
call npm install --no-audit --no-fund
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo.
echo === Setup complete ===
if defined SETUP_ONLY exit /b 0

rem ---------- Run ----------
echo.
echo === Starting Small AI for Development ===
echo   Backend  : http://localhost:8000   (OpenAPI UI: http://localhost:8000/docs)
echo   Frontend : http://localhost:5173
echo.
echo Two console windows will open. Close them (or press Ctrl+C inside) to stop.
echo.

start "SmallAI backend (FastAPI :8000)" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
start "SmallAI frontend (Vite :5173)"   /D "%~dp0frontend" cmd /k "npm run dev"

rem Give Vite a moment to bind the port, then open the browser.
timeout /t 4 /nobreak >nul
start "" http://localhost:5173
exit /b 0

:fail
echo.
echo *** Failed. See the messages above. ***
exit /b 1
