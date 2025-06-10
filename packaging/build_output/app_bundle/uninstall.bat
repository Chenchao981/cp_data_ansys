@echo off
echo CP Data Analysis Tool Uninstaller
echo ===============================
echo.

set "INSTALL_DIR=%ProgramFiles%\CP Data Analysis Tool"
if not exist "%INSTALL_DIR%" (
    set "INSTALL_DIR=%USERPROFILE%\CP Data Analysis Tool"
)

echo Detected installation directory: %INSTALL_DIR%
echo.
echo WARNING: Are you sure you want to uninstall CP Data Analysis Tool?
echo This will remove all program files (user data will be preserved)
pause

if exist "%INSTALL_DIR%" (
    echo Removing program files...
    rmdir /s /q "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ERROR: Deletion failed, some files may be in use
    ) else (
        echo Program files removed successfully
    )
)

REM Remove shortcuts
echo Cleaning up shortcuts...
del "%USERPROFILE%\Desktop\CP Data Analysis Tool.lnk" 2>nul
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\CP Data Analysis Tool" 2>nul

echo.
echo Uninstallation completed!
pause
