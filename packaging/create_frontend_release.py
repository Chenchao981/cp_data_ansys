#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the primary GUI + CP Cockpit release in packaging/release."""

from __future__ import annotations

import fnmatch
import os
import shutil
import sys
import zipapp
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_DIR = Path(__file__).resolve().parent
RELEASE_DIR = PACKAGING_DIR / "release"
TARGET_PYZ = RELEASE_DIR / "app.pyz"
TEMP_BUILD_DIR = PACKAGING_DIR / "_temp_frontend_build_src"
MAIN_ENTRY_POINT = "gui.multi_company_main:main"

PACKAGES_TO_INCLUDE = [
    "cp_data_processor",
    "gui",
    "python_cp",
    "frontend",
    "jt_data_processor",
    "lion",
    "guoyu",
]

ROOT_FILES_TO_INCLUDE = [
    "runtime_paths.py",
    "clean_dcp_data.py",
    "clean_csv_data.py",
    "clean_lion_data.py",
    "lion_batch_processor.py",
    "guoyu_batch_processor.py",
    "dcp_spec_extractor.py",
    "cp_unit_converter.py",
]

EXCLUDE_PATTERNS = [
    "*.md",
    "*.MD",
    "*.log",
    "*.txt",
    "README*",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git*",
    "tests",
    "test_*",
    "*_test.py",
]

EXCLUDE_RELATIVE_PATHS = {
    "frontend/main.py",
    "frontend/utils/data_loader.py",
}

FRONTEND_SCRIPTS = [
    "frontend/cp_dashboard_app.py",
    "frontend/yield_analyzer_app.py",
]

DOCS_TO_COPY = [
    "README.md",
    "docs/frontend-business-requirements.md",
    "docs/frontend-system-design.md",
    "docs/frontend-desktop-deployment.md",
    "docs/frontend-user-quickstart.md",
    "docs/data-contracts.md",
    "docs/operations.md",
    "docs/release-user-manual.md",
    "docs/release-quick-reference.md",
]

RUNTIME_REQUIREMENTS = """# CP Data Analysis Tool - GUI + CP Cockpit frontend runtime dependencies
#
# Keep this file ASCII-only. Some Windows Python/pip installations decode
# requirements files with the system CP936/GBK code page.

pandas>=1.3.0
numpy>=1.21.0
openpyxl>=3.0.0
xlrd>=2.0.1
matplotlib>=3.0.0
seaborn>=0.10.0
plotly>=5.0.0
streamlit>=1.28.0
PyQt5>=5.15.0
"""

START_BAT = r"""@echo off
setlocal

cd /d "%~dp0"

if not defined CP_DATA_ROOT set "CP_DATA_ROOT=D:\CPData"
if not defined CP_LOG_DIR set "CP_LOG_DIR=%CP_DATA_ROOT%\logs"
if not defined CP_CONFIG_DIR set "CP_CONFIG_DIR=%CP_DATA_ROOT%\config"

for %%D in (
    "%CP_DATA_ROOT%\raw\HH"
    "%CP_DATA_ROOT%\raw\JT"
    "%CP_DATA_ROOT%\raw\Lion"
    "%CP_DATA_ROOT%\raw\Guoyu"
    "%CP_DATA_ROOT%\output\HH"
    "%CP_DATA_ROOT%\output\JT"
    "%CP_DATA_ROOT%\output\Lion"
    "%CP_DATA_ROOT%\output\Guoyu"
    "%CP_LOG_DIR%"
    "%CP_CONFIG_DIR%"
) do (
    if not exist "%%~D" mkdir "%%~D" >nul 2>&1
    if not exist "%%~D" (
        echo ERROR: Cannot create required data directory:
        echo   "%%~D"
        goto :failed
    )
)

if exist "%SystemRoot%\System32\chcp.com" (
    "%SystemRoot%\System32\chcp.com" 65001 >nul
)

echo Starting CP Data Analysis Tool - GUI + CP Cockpit Frontend Release...
echo Supporting HuaHong(HH), JeTech(JT), Lion, Guoyu FRD, and CP Cockpit.
echo.

set "PYTHON_EXE="
if exist "D:\ProgramData\anaconda3\python.exe" (
    set "PYTHON_EXE=D:\ProgramData\anaconda3\python.exe"
)

if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('"%SystemRoot%\System32\where.exe" python 2^>nul') do (
        if not defined PYTHON_EXE (
            "%%P" -c "import PyQt5, streamlit" >nul 2>&1
            if not errorlevel 1 set "PYTHON_EXE=%%P"
        )
    )
)

if not defined PYTHON_EXE (
    echo ERROR: No Python environment with PyQt5 and Streamlit was found.
    echo.
    echo Expected Anaconda Python:
    echo   D:\ProgramData\anaconda3\python.exe
    echo.
    echo Install dependencies with:
    echo   D:\ProgramData\anaconda3\python.exe -m pip install -r requirements_anaconda.txt
    goto :failed
)

echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" -c "import PyQt5, pandas, numpy, openpyxl, xlrd, plotly, streamlit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required packages are missing from:
    echo   "%PYTHON_EXE%"
    echo.
    echo Run:
    echo   "%PYTHON_EXE%" -m pip install -r requirements_anaconda.txt
    goto :failed
)

if not exist "app.pyz" (
    echo ERROR: app.pyz was not found in:
    REM Keep the expanded path quoted. An unquoted ')' in a directory name
    REM would otherwise terminate this IF block during CMD parsing.
    echo   "%CD%"
    goto :failed
)

if not exist "frontend\yield_analyzer_app.py" (
    echo ERROR: frontend Streamlit entry was not found.
    goto :failed
)

if /i "%~1"=="--check" (
    "%PYTHON_EXE%" -c "import sys; sys.path.insert(0, 'app.pyz'); import gui.multi_company_main; import frontend.cp_dashboard_app; print('Application package import check passed.')"
    if errorlevel 1 goto :failed
    echo Startup environment check passed.
    endlocal
    exit /b 0
)

"%PYTHON_EXE%" "app.pyz"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo ERROR: Application exited with code %EXIT_CODE%.
    goto :failed
)

endlocal
exit /b 0

:failed
echo.
pause
endlocal
exit /b 1
"""

START_SH = """#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

export CP_DATA_ROOT="${CP_DATA_ROOT:-D:/CPData}"
export CP_LOG_DIR="${CP_LOG_DIR:-$CP_DATA_ROOT/logs}"
export CP_CONFIG_DIR="${CP_CONFIG_DIR:-$CP_DATA_ROOT/config}"

echo "Starting CP Data Analysis Tool - GUI + CP Cockpit Frontend Release..."
echo "Supporting HuaHong(HH), JeTech(JT), Lion, Guoyu FRD, and CP Cockpit."
echo

PYTHON_EXE=""
if [[ -x /d/ProgramData/anaconda3/python.exe ]]; then
    PYTHON_EXE=/d/ProgramData/anaconda3/python.exe
elif [[ -x /mnt/d/ProgramData/anaconda3/python.exe ]]; then
    PYTHON_EXE=/mnt/d/ProgramData/anaconda3/python.exe
elif command -v python >/dev/null 2>&1; then
    PYTHON_EXE="$(command -v python)"
fi

if [[ -z "$PYTHON_EXE" ]]; then
    echo "ERROR: Python was not found."
    exit 1
fi

if ! "$PYTHON_EXE" -c "import PyQt5, pandas, numpy, openpyxl, xlrd, plotly, streamlit" >/dev/null 2>&1; then
    echo "ERROR: Required packages are missing."
    echo "Run: $PYTHON_EXE -m pip install -r requirements_anaconda.txt"
    exit 1
fi

if [[ ! -f app.pyz ]]; then
    echo "ERROR: app.pyz was not found in $(pwd)"
    exit 1
fi

if [[ ! -f frontend/yield_analyzer_app.py ]]; then
    echo "ERROR: frontend Streamlit entry was not found."
    exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
    "$PYTHON_EXE" -c "import sys; sys.path.insert(0, 'app.pyz'); import gui.multi_company_main; import frontend.cp_dashboard_app; print('Application package import check passed.')"
    exit $?
fi

"$PYTHON_EXE" app.pyz
"""

INSTALL_ANACONDA_BAT = r"""@echo off
setlocal
cd /d "%~dp0"

REM Force UTF-8 for Python and pip on Windows systems using CP936/GBK.
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if exist "%SystemRoot%\System32\chcp.com" (
    "%SystemRoot%\System32\chcp.com" 65001 >nul
)

echo CP Data Analysis Tool - Dependency Setup
echo.

set "PYTHON_EXE="
if exist "D:\ProgramData\anaconda3\python.exe" (
    set "PYTHON_EXE=D:\ProgramData\anaconda3\python.exe"
)

if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('"%SystemRoot%\System32\where.exe" python 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo ERROR: Python was not found.
    echo Install Anaconda under D:\ProgramData\anaconda3 or add Python to PATH.
    goto :failed
)

echo Using Python:
"%PYTHON_EXE%" -c "import sys; print(sys.executable); print(sys.version)"
echo.

echo Installing required packages...
"%PYTHON_EXE%" -m pip install -r "requirements_anaconda.txt"
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    goto :failed
)

echo.
echo Verifying runtime dependencies...
"%PYTHON_EXE%" -c "import PyQt5, pandas, numpy, openpyxl, xlrd, plotly, matplotlib, seaborn, streamlit; print('All runtime dependencies are available.')"
if errorlevel 1 (
    echo ERROR: Dependency verification failed.
    goto :failed
)

echo.
echo Environment setup completed. Run start.bat to launch the application.
pause
endlocal
exit /b 0

:failed
echo.
pause
endlocal
exit /b 1
"""


def normalize(path: Path) -> str:
    return path.as_posix()


def should_exclude(path: Path) -> bool:
    rel_path = normalize(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else path.name
    if rel_path in EXCLUDE_RELATIVE_PATHS:
        return True
    name = path.name
    if name == "requirements.txt":
        return False
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel_path, pattern):
            return True
    return False


def copy_directory_filtered(src: Path, dst: Path) -> tuple[int, int]:
    included = 0
    excluded = 0
    for root, dirs, files in os.walk(src):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_exclude(root_path / d)]
        for file_name in files:
            source_file = root_path / file_name
            if should_exclude(source_file):
                excluded += 1
                continue
            rel_path = source_file.relative_to(src)
            target_file = dst / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            included += 1
    return included, excluded


def prepare_clean_dirs() -> None:
    if not str(RELEASE_DIR.resolve()).startswith(str(PACKAGING_DIR.resolve())):
        raise RuntimeError(f"Unsafe release directory: {RELEASE_DIR}")
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    if TEMP_BUILD_DIR.exists():
        shutil.rmtree(TEMP_BUILD_DIR)
    RELEASE_DIR.mkdir(parents=True)
    TEMP_BUILD_DIR.mkdir(parents=True)


def build_pyz() -> tuple[int, int]:
    total_included = 0
    total_excluded = 0
    for package_name in PACKAGES_TO_INCLUDE:
        src = PROJECT_ROOT / package_name
        if not src.is_dir():
            print(f"WARNING: package not found, skipped: {package_name}")
            continue
        included, excluded = copy_directory_filtered(src, TEMP_BUILD_DIR / package_name)
        total_included += included
        total_excluded += excluded
        print(f"Copied {package_name}: included={included}, excluded={excluded}")

    for file_name in ROOT_FILES_TO_INCLUDE:
        src = PROJECT_ROOT / file_name
        if not src.is_file():
            print(f"WARNING: file not found, skipped: {file_name}")
            continue
        if should_exclude(src):
            total_excluded += 1
            continue
        shutil.copy2(src, TEMP_BUILD_DIR / file_name)
        total_included += 1

    zipapp.create_archive(
        source=TEMP_BUILD_DIR,
        target=TARGET_PYZ,
        interpreter="/usr/bin/env python",
        main=MAIN_ENTRY_POINT,
        compressed=True,
    )
    return total_included, total_excluded


def copy_release_assets() -> None:
    (RELEASE_DIR / "frontend").mkdir(parents=True, exist_ok=True)
    for rel_path in FRONTEND_SCRIPTS:
        src = PROJECT_ROOT / rel_path
        dst = RELEASE_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    (RELEASE_DIR / "docs").mkdir(parents=True, exist_ok=True)
    for rel_path in DOCS_TO_COPY:
        src = PROJECT_ROOT / rel_path
        if not src.exists():
            continue
        dst = RELEASE_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    (RELEASE_DIR / "requirements_anaconda.txt").write_text(RUNTIME_REQUIREMENTS, encoding="utf-8")
    (RELEASE_DIR / "start.bat").write_text(START_BAT, encoding="utf-8", newline="\r\n")
    (RELEASE_DIR / "start.sh").write_text(START_SH, encoding="utf-8", newline="\n")
    (RELEASE_DIR / "install_anaconda.bat").write_text(
        INSTALL_ANACONDA_BAT,
        encoding="utf-8",
        newline="\r\n",
    )
    (RELEASE_DIR / "USAGE_FRONTEND_RELEASE.md").write_text(
        """# CP 数据分析工具 - GUI + CP Cockpit 主发布版

## 启动与检查

- 首次部署：运行 `install_anaconda.bat`
- 启动程序：运行 `start.bat`
- 仅检查环境与发布包：运行 `start.bat --check`

## 数据输入

- 华虹、Jetech、Lion、国宇FRD均保留“选择文件夹”和“选择ZIP”两个入口。
- “选择ZIP”支持一次选择一个或多个ZIP；“选择文件夹”也可选择只包含ZIP的目录。
- ZIP仅解压到临时目录，处理结束后自动清理。

## 输出命名

输出路径填写父目录，程序自动创建“首个真实批次号_YYYYMMDD_HHMMSS”文件夹。

## CP Cockpit

清洗完成后点击公司页面中的 `CP Cockpit`，打开当前输出目录的交互分析页面。

## 数据安全

发布目录不包含原始CP数据、生成的CSV/HTML结果、日志或账号密钥。
""",
        encoding="utf-8",
    )


def audit_release() -> list[Path]:
    forbidden_patterns = ["*.csv", "*.xlsx", "*.xls", "*.log", "*.pyc", "*.pyo"]
    allowed = {
        "requirements_anaconda.txt",
    }
    findings: list[Path] = []
    for path in RELEASE_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.name in allowed:
            continue
        for pattern in forbidden_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                findings.append(path)
                break
    return findings


def main() -> int:
    print("Building GUI + CP Cockpit frontend release...")
    prepare_clean_dirs()
    try:
        included, excluded = build_pyz()
        copy_release_assets()
    finally:
        if TEMP_BUILD_DIR.exists():
            shutil.rmtree(TEMP_BUILD_DIR)

    findings = audit_release()
    print(f"Release directory: {RELEASE_DIR}")
    print(f"app.pyz size: {TARGET_PYZ.stat().st_size:,} bytes")
    print(f"Archive inputs: included={included}, excluded={excluded}")
    print(f"Forbidden release files: {len(findings)}")
    for finding in findings[:20]:
        print(f"  {finding.relative_to(RELEASE_DIR)}")
    if findings:
        return 1
    print("Release build completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
