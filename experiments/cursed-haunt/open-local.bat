@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set PORT=4173
set URL=http://127.0.0.1:4173/

REM Check if server already responds
curl -s -o nul -m 1 %URL% 2>nul
if %ERRORLEVEL%==0 goto OPEN

where python >nul 2>&1
if errorlevel 1 (
  echo Python not found. Install Python or open index.html manually.
  pause
  exit /b 1
)

echo Starting cursed-haunt on port %PORT% ...
start "cursed-haunt-server" /min python -m http.server %PORT%
ping -n 2 127.0.0.1 >nul

:OPEN
start "" "%URL%"
echo Opened %URL%
endlocal
