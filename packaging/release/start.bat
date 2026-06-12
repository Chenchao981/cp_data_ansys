@echo off
setlocal

REM Always run from the release directory.
cd /d "%~dp0"

REM Do not depend on System32 being present in PATH.
if exist "%SystemRoot%\System32\chcp.com" (
    "%SystemRoot%\System32\chcp.com" 65001 >nul
)

echo Starting CP Data Analysis Tool - Multi-Company Edition...
echo Supporting HuaHong(HH), JeTech(JT), and Lion data processing
echo.

REM Prefer the standard Anaconda installation used by this project.
set "PYTHON_EXE="
if exist "D:\ProgramData\anaconda3\python.exe" (
    set "PYTHON_EXE=D:\ProgramData\anaconda3\python.exe"
)

REM Fall back to a Python on PATH only when it has PyQt5.
if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('"%SystemRoot%\System32\where.exe" python 2^>nul') do (
        if not defined PYTHON_EXE (
            "%%P" -c "import PyQt5" >nul 2>&1
            if not errorlevel 1 set "PYTHON_EXE=%%P"
        )
    )
)

if not defined PYTHON_EXE (
    echo ERROR: No Python environment with PyQt5 was found.
    echo.
    echo Expected Anaconda Python:
    echo   D:\ProgramData\anaconda3\python.exe
    echo.
    echo Run install_anaconda.bat first, or install dependencies with:
    echo   D:\ProgramData\anaconda3\python.exe -m pip install -r requirements_anaconda.txt
    goto :failed
)

echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" -c "import PyQt5, pandas, numpy, openpyxl, plotly" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required packages are missing from:
    echo   %PYTHON_EXE%
    echo.
    echo Run install_anaconda.bat to install the required packages.
    goto :failed
)

if not exist "app.pyz" (
    echo ERROR: app.pyz was not found in:
    echo   %CD%
    goto :failed
)

if /i "%~1"=="--check" (
    "%PYTHON_EXE%" -c "import sys; sys.path.insert(0, 'app.pyz'); import gui.multi_company_main; print('Application package import check passed.')"
    if errorlevel 1 goto :failed
    echo Startup environment check passed.
    endlocal
    exit /b 0
)

"%PYTHON_EXE%" "app.pyz"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo ERROR: Application exited with code %EXIT_CODE%.
    goto :failed
)

endlocal
exit /b 0

:failed
echo.
pause
endlocal
exit /b 1
