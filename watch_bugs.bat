@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo WakeAgain bug-watch (Ctrl+C to stop)
echo Logs: data\test_watch\
python -u scripts\bug_watch.py --loop 300 --fix --live
if errorlevel 1 pause
