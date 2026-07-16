from pathlib import Path
from zipfile import ZipFile

import pytest

from cp_data_processor.processing.zip_input import (
    ZipInputError,
    discover_zip_archives,
    prepare_dcp_input,
)


def write_zip(path: Path, members: dict[str, str]) -> None:
    with ZipFile(path, "w") as archive:
        for member_name, content in members.items():
            archive.writestr(member_name, content)


def test_direct_data_folder_is_passed_through(tmp_path):
    batch_dir = tmp_path / "PRODUCT_LOT-001@202"
    batch_dir.mkdir()
    data_file = batch_dir / "wafer_001.TXT"
    data_file.write_text("test-data", encoding="utf-8")

    with prepare_dcp_input(batch_dir) as prepared:
        assert prepared.directory == batch_dir
        assert prepared.data_files == (data_file,)
        assert prepared.archives == ()
        assert prepared.is_temporary is False


def test_single_zip_is_normalized_to_one_batch_directory(tmp_path):
    archive_path = tmp_path / "PRODUCT_LOT-001@202.zip"
    write_zip(
        archive_path,
        {
            "wafer_001.TXT": "first",
            "nested/wafer_002.txt": "second",
            "notes/readme.md": "ignored",
        },
    )

    with prepare_dcp_input(archive_path) as prepared:
        temporary_root = prepared.directory.parent
        assert prepared.directory.name == "PRODUCT_LOT-001@202"
        assert len(prepared.data_files) == 2
        assert {path.name for path in prepared.data_files} == {
            "wafer_001.TXT",
            "wafer_002.txt",
        }
        assert prepared.archives == (archive_path,)
        assert prepared.is_temporary is True
        assert all(path.parent == prepared.directory for path in prepared.data_files)

    assert not temporary_root.exists()


def test_folder_with_multiple_zips_becomes_multi_batch_directory(tmp_path):
    source_dir = tmp_path / "zip_source"
    source_dir.mkdir()
    first_archive = source_dir / "PRODUCT_LOT-001@202.zip"
    second_archive = source_dir / "delivery.zip"
    write_zip(first_archive, {"wafer_001.TXT": "first"})
    write_zip(
        second_archive,
        {"PRODUCT_LOT-002@202/wafer_002.TXT": "second"},
    )

    assert set(discover_zip_archives(source_dir)) == {first_archive, second_archive}

    with prepare_dcp_input(source_dir) as prepared:
        assert prepared.directory.name.startswith("cp_hh_zip_")
        assert len(prepared.data_files) == 2
        assert {path.parent.name for path in prepared.data_files} == {
            "PRODUCT_LOT-001@202",
            "PRODUCT_LOT-002@202",
        }
        assert set(prepared.archives) == {first_archive, second_archive}


def test_zip_path_traversal_is_rejected(tmp_path):
    archive_path = tmp_path / "PRODUCT_LOT-001@202.zip"
    write_zip(archive_path, {"../outside.TXT": "unsafe"})

    with pytest.raises(ZipInputError, match="不安全路径"):
        with prepare_dcp_input(archive_path):
            pass

    assert not (tmp_path / "outside.TXT").exists()


def test_zip_without_dcp_files_is_rejected(tmp_path):
    archive_path = tmp_path / "empty.zip"
    write_zip(archive_path, {"readme.md": "no data"})

    with pytest.raises(ZipInputError, match="未找到华虹DCP/TXT文件"):
        with prepare_dcp_input(archive_path):
            pass


def test_mixed_loose_data_and_zip_folder_is_rejected(tmp_path):
    source_dir = tmp_path / "mixed_source"
    source_dir.mkdir()
    (source_dir / "wafer_001.TXT").write_text("loose", encoding="utf-8")
    write_zip(source_dir / "PRODUCT_LOT-001@202.zip", {"wafer_002.TXT": "zipped"})

    with pytest.raises(ZipInputError, match="避免重复处理"):
        with prepare_dcp_input(source_dir):
            pass
