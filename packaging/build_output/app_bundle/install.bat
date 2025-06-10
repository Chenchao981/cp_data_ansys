@echo off
echo CP Data Analysis Tool Installer
echo ===============================
echo.

REM Check administrator privileges
net session >nul 2>&1
if errorlevel 1 (
    echo WARNING: Administrator privileges recommended for best experience.
    echo You can continue with normal installation...
    echo.
    pause
)

set "INSTALL_DIR=%ProgramFiles%\CP Data Analysis Tool"
set "CURRENT_DIR=%~dp0"

echo Install Directory: %INSTALL_DIR%
echo Source Directory: %CURRENT_DIR%
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ERROR: Cannot create installation directory. Administrator privileges may be required.
        set "INSTALL_DIR=%USERPROFILE%\CP Data Analysis Tool"
        echo Switching to user directory installation: !INSTALL_DIR!
        mkdir "!INSTALL_DIR!"
    )
)

REM Copy files
echo Copying application files...
xcopy "%CURRENT_DIR%*" "%INSTALL_DIR%\" /E /I /Y /Q
if errorlevel 1 (
    echo ERROR: File copy failed.
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
set "SHORTCUT=%USERPROFILE%\Desktop\CP Data Analysis Tool.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\scripts\start_app.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP Data Analysis Tool'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\CP Data Analysis Tool" mkdir "%START_MENU%\CP Data Analysis Tool"
set "START_SHORTCUT=%START_MENU%\CP Data Analysis Tool\CP Data Analysis Tool.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\scripts\start_app.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP Data Analysis Tool'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo Install Location: %INSTALL_DIR%
echo Desktop Shortcut: CP Data Analysis Tool
echo Start Menu: CP Data Analysis Tool
echo.
echo NOTE: First run will automatically initialize Python environment. Please be patient.
pause
