@echo off
echo 🔬 启动CP数据分析工具 - 多公司版GUI...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查PyQt5是否安装
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo 📦 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖包安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo ✅ 环境检查完成，启动多公司版GUI...
echo 🏭 支持的公司: HuaHong, JeTech
echo.

REM 启动多公司版GUI程序
python multi_company_main.py

if errorlevel 1 (
    echo.
    echo ❌ 多公司版GUI启动失败，尝试启动单公司版本...
    echo.
    python cp_data_gui.py
    if errorlevel 1 (
        echo ❌ GUI启动失败，请检查错误信息
        pause
    )
) 