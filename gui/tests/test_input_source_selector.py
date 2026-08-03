import pytest

from gui.widgets.input_source_selector import (
    InputSourceSelectionError,
    resolve_start_directory,
    validate_input_source_selection,
)


def test_accepts_one_directory(tmp_path):
    assert validate_input_source_selection([tmp_path]) == (tmp_path,)


def test_accepts_and_deduplicates_multiple_zip_files(tmp_path):
    first = tmp_path / "lot-a.zip"
    second = tmp_path / "lot-b.ZIP"
    first.touch()
    second.touch()

    assert validate_input_source_selection([first, second, first]) == (
        first,
        second,
    )


def test_accepts_7z_when_enabled_for_huahong(tmp_path):
    zip_archive = tmp_path / "lot-a.zip"
    seven_zip_archive = tmp_path / "lot-b.7Z"
    zip_archive.touch()
    seven_zip_archive.touch()

    assert validate_input_source_selection(
        [zip_archive, seven_zip_archive],
        allowed_archive_suffixes=(".zip", ".7z"),
    ) == (zip_archive, seven_zip_archive)


def test_rejects_7z_for_zip_only_vendor(tmp_path):
    archive = tmp_path / "lot.7z"
    archive.touch()

    with pytest.raises(InputSourceSelectionError, match="仅支持ZIP"):
        validate_input_source_selection([archive])


def test_rejects_folder_and_zip_mixed_selection(tmp_path):
    archive = tmp_path / "lot.zip"
    archive.touch()

    with pytest.raises(InputSourceSelectionError, match="不能同时选择"):
        validate_input_source_selection([tmp_path, archive])


def test_rejects_multiple_directories(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    with pytest.raises(InputSourceSelectionError, match="只能选择一个"):
        validate_input_source_selection([first, second])


def test_rejects_non_zip_file(tmp_path):
    workbook = tmp_path / "source.xlsx"
    workbook.touch()

    with pytest.raises(InputSourceSelectionError, match="仅支持ZIP"):
        validate_input_source_selection([workbook])


def test_resolve_start_directory_uses_parent_for_file(tmp_path):
    archive = tmp_path / "lot.zip"
    archive.touch()

    assert resolve_start_directory(archive) == tmp_path
