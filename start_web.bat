@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=D:\ProgramData\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo Starting CP Data Cockpit...
"%PYTHON_EXE%" -c "import streamlit, pandas, plotly" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit dependencies are missing.
    echo Run: "%PYTHON_EXE%" -m pip install -r requirements.txt
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m streamlit run web_app\app.py --server.address 127.0.0.1 --server.port 8501

endlocal
