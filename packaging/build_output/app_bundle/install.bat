@echo off
echo 🛠️ CP数据分析工具安装程序
echo ===============================
echo.

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 建议以管理员身份运行以获得最佳体验
    echo 但也可以继续普通安装...
    echo.
    pause
)

set "INSTALL_DIR=%ProgramFiles%\CP数据分析工具"
set "CURRENT_DIR=%~dp0"

echo 📁 安装目录: %INSTALL_DIR%
echo 📁 源目录: %CURRENT_DIR%
echo.

REM 创建安装目录
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ❌ 无法创建安装目录，可能需要管理员权限
        set "INSTALL_DIR=%USERPROFILE%\CP数据分析工具"
        echo 🔄 改为用户目录安装: !INSTALL_DIR!
        mkdir "!INSTALL_DIR!"
    )
)

REM 复制文件
echo 📋 复制应用程序文件...
xcopy "%CURRENT_DIR%*" "%INSTALL_DIR%\" /E /I /Y /Q
if errorlevel 1 (
    echo ❌ 文件复制失败
    pause
    exit /b 1
)

REM 创建桌面快捷方式
echo 🔗 创建桌面快捷方式...
set "SHORTCUT=%USERPROFILE%\Desktop\CP数据分析工具.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\scripts\start_app.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP数据分析工具'; $Shortcut.Save()"

REM 创建开始菜单快捷方式
echo 📋 创建开始菜单快捷方式...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\CP数据分析工具" mkdir "%START_MENU%\CP数据分析工具"
set "START_SHORTCUT=%START_MENU%\CP数据分析工具\CP数据分析工具.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\scripts\start_app.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP数据分析工具'; $Shortcut.Save()"

echo.
echo ✅ 安装完成！
echo 📍 安装位置: %INSTALL_DIR%
echo 🖥️ 桌面快捷方式: CP数据分析工具
echo 📋 开始菜单: CP数据分析工具
echo.
echo 💡 首次运行时会自动初始化Python环境，请耐心等待
pause
