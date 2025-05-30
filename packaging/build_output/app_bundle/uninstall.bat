@echo off
echo 🗑️ CP数据分析工具卸载程序
echo ===============================
echo.

set "INSTALL_DIR=%ProgramFiles%\CP数据分析工具"
if not exist "%INSTALL_DIR%" (
    set "INSTALL_DIR=%USERPROFILE%\CP数据分析工具"
)

echo 📁 检测到安装目录: %INSTALL_DIR%
echo.
echo ⚠️ 确定要卸载CP数据分析工具吗？
echo 这将删除所有程序文件（不包括用户数据）
pause

if exist "%INSTALL_DIR%" (
    echo 🔄 正在删除程序文件...
    rmdir /s /q "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ❌ 删除失败，可能有文件被占用
    ) else (
        echo ✅ 程序文件已删除
    )
)

REM 删除快捷方式
echo 🔗 清理快捷方式...
del "%USERPROFILE%\Desktop\CP数据分析工具.lnk" 2>nul
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\CP数据分析工具" 2>nul

echo.
echo ✅ 卸载完成！
pause
