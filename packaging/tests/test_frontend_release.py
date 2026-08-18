from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = PROJECT_ROOT / "packaging" / "create_frontend_release.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("frontend_release_builder", BUILD_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_pyz_vendors_xlrd_for_single_file_upgrade(tmp_path):
    builder = load_builder()
    builder.PACKAGING_DIR = tmp_path
    builder.RELEASE_DIR = tmp_path / "release"
    builder.TARGET_PYZ = builder.RELEASE_DIR / "app.pyz"
    builder.TEMP_BUILD_DIR = tmp_path / "build"

    builder.prepare_clean_dirs()
    try:
        builder.build_pyz()
    finally:
        if builder.TEMP_BUILD_DIR.exists():
            import shutil

            shutil.rmtree(builder.TEMP_BUILD_DIR)

    with zipfile.ZipFile(builder.TARGET_PYZ) as archive:
        names = set(archive.namelist())

    assert "xlrd/__init__.py" in names
    assert any(
        name.endswith(".dist-info/LICENSE") and name.startswith("xlrd-")
        for name in names
    )


def test_release_streamlit_entry_loads_dashboard_from_app_pyz(tmp_path):
    builder = load_builder()
    builder.PACKAGING_DIR = tmp_path
    builder.RELEASE_DIR = tmp_path / "release"
    builder.TARGET_PYZ = builder.RELEASE_DIR / "app.pyz"
    builder.TEMP_BUILD_DIR = tmp_path / "build"

    builder.prepare_clean_dirs()
    try:
        builder.build_pyz()
        builder.copy_release_assets()
    finally:
        if builder.TEMP_BUILD_DIR.exists():
            import shutil

            shutil.rmtree(builder.TEMP_BUILD_DIR)

    assert (builder.RELEASE_DIR / "frontend" / "yield_analyzer_app.py").is_file()
    assert not (builder.RELEASE_DIR / "frontend" / "cp_dashboard_app.py").exists()

    command = (
        "import runpy, sys; "
        "ns = runpy.run_path('frontend/yield_analyzer_app.py', "
        "run_name='release_entry_check'); "
        "module = sys.modules[ns['main'].__module__]; "
        "assert 'app.pyz' in str(module.__file__), module.__file__"
    )
    subprocess.run(
        [sys.executable, "-c", command],
        cwd=builder.RELEASE_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
