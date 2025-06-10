@echo off
chcp 65001 >nul
echo 🚀 CP数据分析工具 - 快速构建脚本
echo ========================================
echo.

REM 检查conda环境
conda --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到conda，请确保已安装Anaconda/Miniconda
    pause
    exit /b 1
)

REM 检查conda-pack
conda list conda-pack >nul 2>&1
if errorlevel 1 (
    echo 📦 安装conda-pack...
    conda install conda-pack -y
    if errorlevel 1 (
        echo ❌ conda-pack安装失败
        pause
        exit /b 1
    )
)

REM 检查PyYAML
python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo 📦 安装PyYAML...
    conda install pyyaml -y
    if errorlevel 1 (
        echo ❌ PyYAML安装失败
        pause
        exit /b 1
    )
)

echo ✅ 环境检查完成
echo.

REM 运行Python构建脚本
echo 🔨 开始构建过程...
python build_scripts\conda_pack_builder.py

if errorlevel 1 (
    echo.
    echo ❌ 构建失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo 🎉 构建完成！
echo 📁 检查 distribution 目录获取安装包
pause 