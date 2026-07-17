from datetime import datetime

import pytest

from cp_data_processor.processing.output_naming import (
    OutputNamingError,
    build_output_folder_name,
    create_output_run_dir,
)


def test_builds_first_lot_plus_time_serial():
    name = build_output_folder_name(
        "FA54-5342",
        now=datetime(2026, 7, 17, 15, 30, 45),
    )

    assert name == "FA54-5342_20260717_153045"


def test_sanitizes_windows_invalid_characters_without_company_fallback():
    assert (
        build_output_folder_name("LOT:25/01", serial="20260717_153045")
        == "LOT_25_01_20260717_153045"
    )


def test_rejects_missing_real_lot_id():
    with pytest.raises(OutputNamingError, match="首个真实批次号"):
        build_output_folder_name("", serial="20260717_153045")


def test_create_output_run_dir_avoids_silent_overwrite(tmp_path):
    first = create_output_run_dir(
        tmp_path,
        "F25130244",
        serial="20260717_153045",
    )
    second = create_output_run_dir(
        tmp_path,
        "F25130244",
        serial="20260717_153045",
    )

    assert first.name == "F25130244_20260717_153045"
    assert second.name == "F25130244_20260717_153045_001"
