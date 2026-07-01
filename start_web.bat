@echo off
setlocal
cd /d "%~dp0"

set "APP_URL=http://127.0.0.1:8501"
set "APP_PORT=8501"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

set "PYTHON_EXE=D:\ProgramData\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo Checking CP Raw Data Analyzer...
set "PYTHONDONTWRITEBYTECODE=1"
"%PYTHON_EXE%" -c "import streamlit, pandas, plotly" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit dependencies are missing.
    echo Run: "%PYTHON_EXE%" -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM Return 0 when this project is already listening, 1 when the port is free,
REM and 2 when another application owns the port.
"%POWERSHELL_EXE%" -NoProfile -Command "$c=Get-NetTCPConnection -LocalPort %APP_PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if(-not $c){exit 1}; $p=Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $c.OwningProcess) -ErrorAction SilentlyContinue; if($p.CommandLine -like '*streamlit*web_app\app.py*'){exit 0}else{exit 2}" >nul 2>&1
set "PORT_STATE=%ERRORLEVEL%"

if "%PORT_STATE%"=="0" (
    echo CP Raw Data Analyzer is already running.
    if /i "%~1"=="--check" exit /b 0
    start "" "%APP_URL%"
    exit /b 0
)

if "%PORT_STATE%"=="2" (
    echo ERROR: Port %APP_PORT% is occupied by another application.
    echo Close that application or change APP_PORT in start_web.bat.
    pause
    exit /b 1
)

if /i "%~1"=="--check" (
    echo Startup prerequisites passed. Port %APP_PORT% is available.
    exit /b 0
)

echo Starting CP Raw Data Analyzer...
REM Open the browser after Streamlit has had time to bind the local port.
start "" "%POWERSHELL_EXE%" -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process '%APP_URL%'"

"%PYTHON_EXE%" -m streamlit run web_app\app.py --server.address 127.0.0.1 --server.port %APP_PORT% --server.headless true
if errorlevel 1 (
    echo.
    echo ERROR: CP Raw Data Analyzer stopped unexpectedly.
    pause
    exit /b 1
)

endlocal
