@echo off
setlocal
cd /d "%~dp0"

if exist "%SystemRoot%\System32\chcp.com" (
    "%SystemRoot%\System32\chcp.com" 65001 >nul
)

echo CP Data Analysis Tool - Dependency Setup
echo.

set "PYTHON_EXE="
if exist "D:\ProgramData\anaconda3\python.exe" (
    set "PYTHON_EXE=D:\ProgramData\anaconda3\python.exe"
)

if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('"%SystemRoot%\System32\where.exe" python 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo ERROR: Python was not found.
    echo Install Anaconda under D:\ProgramData\anaconda3 or add Python to PATH.
    goto :failed
)

echo Using Python:
"%PYTHON_EXE%" -c "import sys; print(sys.executable); print(sys.version)"
echo.

echo Installing required packages...
"%PYTHON_EXE%" -m pip install -r "requirements_anaconda.txt"
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    goto :failed
)

echo.
echo Verifying runtime dependencies...
"%PYTHON_EXE%" -c "import PyQt5, pandas, numpy, openpyxl, plotly, matplotlib, seaborn; print('All runtime dependencies are available.')"
if errorlevel 1 (
    echo ERROR: Dependency verification failed.
    goto :failed
)

echo.
echo Environment setup completed. Run start.bat to launch the application.
pause
endlocal
exit /b 0

:failed
echo.
pause
endlocal
exit /b 1
