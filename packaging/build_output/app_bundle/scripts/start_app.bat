@echo off
setlocal EnableDelayedExpansion

echo CP Data Analysis Tool Starting...
echo.

REM Set application directory
set "APP_DIR=%~dp0.."
set "ENV_DIR=%APP_DIR%\python_env"
set "APP_CODE_DIR=%APP_DIR%\app"

REM Check if environment is already extracted
if not exist "%ENV_DIR%\python.exe" (
    echo First run - initializing Python environment...
    echo This may take a few minutes, please be patient...
    echo.
    
    REM Extract Python environment
    cd /d "%ENV_DIR%"
    if exist "environment.tar.gz" (
        echo Extracting Python environment...
        tar -xzf environment.tar.gz
        if errorlevel 1 (
            echo ERROR: Environment extraction failed, please check if tar command is available
            echo TIP: Windows 10 1903+ includes tar command by default
            pause
            exit /b 1
        )
        
        REM Activate environment
        call conda-unpack.exe
        if errorlevel 1 (
            echo WARNING: Environment activation may have issues, but will try to continue
        )
        
        echo Python environment initialization completed
        echo.
    ) else (
        echo ERROR: Environment package file not found
        pause
        exit /b 1
    )
)

REM Set Python path
set "PATH=%ENV_DIR%;%ENV_DIR%\Scripts;%ENV_DIR%\Library\bin;%PATH%"
set "PYTHONPATH=%APP_CODE_DIR%;%PYTHONPATH%"

REM Enter application directory
cd /d "%APP_CODE_DIR%"

REM Start application
echo Starting CP Data Analysis Tool GUI...
python cp_data_processor_gui.py

REM Check execution result
if errorlevel 1 (
    echo.
    echo ERROR: Application encountered an error
    echo TIP: Please check for permission issues or missing dependencies
    pause
) else (
    echo.
    echo Application completed successfully
    pause
)
