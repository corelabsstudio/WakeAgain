@echo off
setlocal
cd /d "%~dp0"

set "URL=http://127.0.0.1:8080/"
set "PORT=8080"

:: already up?
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL%==0 goto OPEN

echo WakeAgain local server starting on port %PORT% ...
start "WakeAgain-server" /MIN cmd /c "cd /d "%~dp0" && python -m uvicorn server:app --host 127.0.0.1 --port %PORT%"

:: wait up to ~15s
set /a n=0
:WAIT
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL%==0 goto OPEN
set /a n+=1
if %n% GEQ 15 (
  echo Server did not start. Check Python / requirements.
  pause
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto WAIT

:OPEN
start "" "%URL%"
endlocal
