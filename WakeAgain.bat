@echo off
setlocal
cd /d "%~dp0"

set "URL=http://127.0.0.1:8080/"
set "APP=http://127.0.0.1:8080/app/"
set "PORT=8080"

:: Prefer project venv when present
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"

:: already up?
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL%==0 goto OPEN

echo WakeAgain local server starting on port %PORT% ...
start "WakeAgain-server" /MIN cmd /c "cd /d "%~dp0" && "%PY%" -m uvicorn server:app --host 127.0.0.1 --port %PORT%"

:: wait up to ~20s
set /a n=0
:WAIT
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL%==0 goto OPEN
set /a n+=1
if %n% GEQ 20 (
  echo Server did not start. Check Python / requirements.
  echo Try: cd /d "%~dp0" ^& "%PY%" -m pip install -r requirements.txt
  pause
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto WAIT

:OPEN
:: Home + app shell (useful while live site is offline)
start "" "%URL%"
start "" "%APP%"
endlocal
