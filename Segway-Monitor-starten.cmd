@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\SegwayMonitor\1.0.0\Segway-Monitor.exe" (
    start "" "%LOCALAPPDATA%\Programs\SegwayMonitor\1.0.0\Segway-Monitor.exe"
    exit /b
)
if exist "%~dp0Segway-Monitor.exe" (
    start "" "%~dp0Segway-Monitor.exe"
    exit /b
)
if exist "%~dp0dist-v1.0.0\Segway-Monitor.exe" (
    start "" "%~dp0dist-v1.0.0\Segway-Monitor.exe"
    exit /b
)
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0run_segway_monitor.py"
    exit /b
)
echo Segway-Monitor.exe wurde nicht gefunden. Bitte das gesamte Release-Paket entpacken.
pause
