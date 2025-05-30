@echo off
setlocal EnableDelayedExpansion

echo 🔬 CP数据分析工具启动中...
echo.

REM 设置应用程序目录
set "APP_DIR=%~dp0.."
set "ENV_DIR=%APP_DIR%\python_env"
set "APP_CODE_DIR=%APP_DIR%\app"

REM 检查环境是否已解压
if not exist "%ENV_DIR%\python.exe" (
    echo 📦 首次运行，正在初始化Python环境...
    echo 这可能需要几分钟时间，请耐心等待...
    echo.
    
    REM 解压Python环境
    cd /d "%ENV_DIR%"
    if exist "environment.tar.gz" (
        echo 🔄 正在解压Python环境...
        tar -xzf environment.tar.gz
        if errorlevel 1 (
            echo ❌ 环境解压失败，请检查tar命令是否可用
            echo 💡 提示：Windows 10 1903+自带tar命令
            pause
            exit /b 1
        )
        
        REM 激活环境
        call conda-unpack.exe
        if errorlevel 1 (
            echo ⚠️ 环境激活可能有问题，但会尝试继续运行
        )
        
        echo ✅ Python环境初始化完成
        echo.
    ) else (
        echo ❌ 未找到环境包文件
        pause
        exit /b 1
    )
)

REM 设置Python路径
set "PATH=%ENV_DIR%;%ENV_DIR%\Scripts;%ENV_DIR%\Library\bin;%PATH%"
set "PYTHONPATH=%APP_CODE_DIR%;%PYTHONPATH%"

REM 进入应用程序目录
cd /d "%APP_CODE_DIR%"

REM 启动应用程序
echo 🚀 启动CP数据分析工具...
python chart_generator.py

REM 检查运行结果
if errorlevel 1 (
    echo.
    echo ❌ 应用程序运行出错
    echo 💡 请检查是否有权限问题或缺少依赖
    pause
) else (
    echo.
    echo ✅ 应用程序运行完成
    pause
)
