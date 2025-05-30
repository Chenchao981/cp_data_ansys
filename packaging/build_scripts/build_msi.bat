
@echo off
chcp 65001 >nul
echo 🚀 CP数据分析工具 - MSI安装包构建
echo ======================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请确保已安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 进入packaging目录
cd /d "%~dp0.."

REM 运行MSI构建脚本
echo 🔨 开始MSI构建过程...
python build_scripts/msi_builder.py

if errorlevel 1 (
    echo.
    echo ❌ MSI构建失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo 🎉 MSI构建完成！
echo 📁 检查 distribution 目录获取MSI安装包
echo 💡 将MSI文件复制到其他Windows电脑直接安装
pause 