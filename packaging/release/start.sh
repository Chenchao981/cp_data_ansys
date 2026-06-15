#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

echo "Starting CP Data Analysis Tool - Multi-Company Edition..."
echo "Supporting HuaHong(HH), JeTech(JT), Lion, and Guoyu FRD data processing"
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

if ! "$PYTHON_EXE" -c "import PyQt5, pandas, numpy, openpyxl, xlrd, plotly" >/dev/null 2>&1; then
    echo "ERROR: Required packages are missing."
    echo "Run install_anaconda.bat first."
    exit 1
fi

if [[ ! -f app.pyz ]]; then
    echo "ERROR: app.pyz was not found in $(pwd)"
    exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
    "$PYTHON_EXE" -c "import sys; sys.path.insert(0, 'app.pyz'); import gui.multi_company_main; print('Application package import check passed.')"
    exit $?
fi

"$PYTHON_EXE" app.pyz
