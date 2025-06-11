@echo off
chcp 65001 >nul
echo CP Data Analysis Tool - Anaconda Environment Setup Script
echo.

REM Set script directory as base
set "SCRIPT_DIR=%~dp0"

echo Detecting Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found, please ensure Anaconda is properly installed and added to PATH
    echo Suggestion: Reinstall Anaconda and check "Add Anaconda to PATH" option
    pause
    exit /b 1
)

REM Display Python environment information
echo Current Python environment:
python --version
python -c "import sys; print('Python path:', sys.executable)"

REM Check if it's Anaconda environment
python -c "import sys; 'anaconda' in sys.version.lower() or 'conda' in sys.executable.lower()" >nul 2>&1
if %errorlevel% equ 0 (
    echo Anaconda environment detected
) else (
    echo Anaconda environment not clearly detected, but will continue installation...
)
echo.

echo Checking if core packages are installed...

REM Check numpy
python -c "import numpy; print('numpy version:', numpy.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo numpy not installed, please check Anaconda installation
)

REM Check pandas  
python -c "import pandas; print('pandas version:', pandas.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo pandas not installed, please check Anaconda installation
)

REM Check matplotlib
python -c "import matplotlib; print('matplotlib version:', matplotlib.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo matplotlib not installed, please check Anaconda installation
)

echo.
echo Checking and installing additional dependencies...

REM Check openpyxl
echo Checking Excel support package (openpyxl)...
python -c "import openpyxl; print('openpyxl already installed, version:', openpyxl.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo Installing openpyxl...
    python -m pip install openpyxl>=3.0.0
    if %errorlevel% equ 0 (
        echo openpyxl installation successful
    ) else (
        echo openpyxl installation failed
    )
) else (
    echo openpyxl already exists, skipping installation
)

REM Check seaborn
echo Checking statistical charts package (seaborn)...
python -c "import seaborn; print('seaborn already installed, version:', seaborn.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo Installing seaborn...
    python -m pip install seaborn>=0.10.0
    if %errorlevel% equ 0 (
        echo seaborn installation successful
    ) else (
        echo seaborn installation failed
    )
) else (
    echo seaborn already exists, skipping installation
)

REM Check PyQt5
echo Checking GUI interface package (PyQt5)...
python -c "import PyQt5; print('PyQt5 already installed, version:', PyQt5.QtCore.QT_VERSION_STR)" 2>nul
if %errorlevel% neq 0 (
    echo Installing PyQt5...
    python -m pip install PyQt5>=5.15.0
    if %errorlevel% equ 0 (
        echo PyQt5 installation successful
    ) else (
        echo PyQt5 installation failed
    )
) else (
    echo PyQt5 already exists, skipping installation
)

echo.
echo Final environment verification...
python -c "
try:
    import numpy, pandas, matplotlib, openpyxl, seaborn, PyQt5
    print('All dependency packages verification successful!')
    print('numpy:', numpy.__version__)
    print('pandas:', pandas.__version__)  
    print('matplotlib:', matplotlib.__version__)
    print('openpyxl:', openpyxl.__version__)
    print('seaborn:', seaborn.__version__)
    print('PyQt5:', PyQt5.QtCore.QT_VERSION_STR)
except ImportError as e:
    print('Verification failed:', e)
    exit(1)
"

if %errorlevel% equ 0 (
    echo.
    echo Environment setup completed! You can now double-click start.bat to launch the program
    echo.
    echo Anaconda advantages:
    echo    - Pre-installed scientific computing packages
    echo    - Better version compatibility
    echo    - More stable package management
    
    echo.
    echo Creating desktop shortcut...
    
    REM Try to create icon first
    if exist "%SCRIPT_DIR%create_icon_simple.py" (
        echo Generating program icon...
        python "%SCRIPT_DIR%create_icon_simple.py" >nul 2>&1
        if exist "%SCRIPT_DIR%cp_data_icon.ico" (
            echo Icon created successfully
        ) else (
            REM Try the advanced version if simple version fails
            if exist "%SCRIPT_DIR%create_icon.py" (
                python "%SCRIPT_DIR%create_icon.py" >nul 2>&1
                if exist "%SCRIPT_DIR%cp_data_icon.ico" (
                    echo Icon created successfully (advanced)
                ) else (
                    echo Icon creation skipped
                )
            )
        )
    ) else if exist "%SCRIPT_DIR%create_icon.py" (
        echo Generating program icon...
        python "%SCRIPT_DIR%create_icon.py" >nul 2>&1
        if exist "%SCRIPT_DIR%cp_data_icon.ico" (
            echo Icon created successfully
        ) else (
            echo Icon creation skipped (Pillow not installed)
        )
    )
    
    REM Create desktop shortcut
    if exist "%SCRIPT_DIR%create_desktop_shortcut.vbs" (
        echo Creating desktop shortcut...
        cscript //nologo "%SCRIPT_DIR%create_desktop_shortcut.vbs"
        if %errorlevel% equ 0 (
            echo.
            echo ✅ Desktop shortcut created successfully!
            echo You can now launch the program from your desktop
        ) else (
            echo Desktop shortcut creation failed, but you can still run start.bat directly
        )
    ) else (
        echo Desktop shortcut script not found, skipping...
    )
) else (
    echo.
    echo Environment verification failed
    echo Suggested solutions:
    echo 1. Reinstall Anaconda3-2024.10-1
    echo 2. Make sure to check "Add Anaconda to PATH" during installation
    echo 3. Restart command line and run this script again
)

echo.
pause 