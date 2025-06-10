@echo off
setlocal EnableDelayedExpansion

echo CP Data Analysis Tool Starting...
echo.

REM Set application directories
set "APP_DIR=%~dp0.."
set "ENV_DIR=%APP_DIR%\python_env"
set "APP_CODE_DIR=%APP_DIR%\app"

REM Check if environment is unpacked
if not exist "%ENV_DIR%\python.exe" (
    echo First run detected. Initializing Python environment...
    echo This may take a few minutes, please wait...
    echo.
    
    REM Extract Python environment
    cd /d "%ENV_DIR%"
    if exist "environment.tar.gz" (
        echo Extracting Python environment...
        tar -xzf environment.tar.gz
        if errorlevel 1 (
            echo ERROR: Environment extraction failed. Please check if tar command is available.
            echo NOTE: Windows 10 1903+ includes tar command by default.
            pause
            exit /b 1
        )
        
        REM Activate environment
        call conda-unpack.exe
        if errorlevel 1 (
            echo WARNING: Environment activation may have issues, but will try to continue.
        )
        
        echo Python environment initialization completed.
        echo.
    ) else (
        echo ERROR: Environment package file not found.
        pause
        exit /b 1
    )
)

REM Set Python paths
set "PATH=%ENV_DIR%;%ENV_DIR%\Scripts;%ENV_DIR%\Library\bin;%PATH%"
set "PYTHONPATH=%APP_CODE_DIR%;%PYTHONPATH%"

REM Change to application directory
cd /d "%APP_CODE_DIR%"

REM Start application
echo Starting CP Data Analysis Tool GUI...
python cp_data_processor_gui.py

REM Check execution result
if errorlevel 1 (
    echo.
    echo ERROR: Application execution failed.
    echo Please check for permission issues or missing dependencies.
    pause
) else (
    echo.
    echo Application execution completed.
    pause
)
