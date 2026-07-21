@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo WakeAgain bug-watch (Ctrl+C to stop)
echo Logs: data\test_watch\
echo Alerts: ntfy/Telegram/Discord if configured + data\test_watch\AGENT_ALERT.md
python -u scripts\bug_watch.py --loop 300 --fix --live --notify
if errorlevel 1 pause