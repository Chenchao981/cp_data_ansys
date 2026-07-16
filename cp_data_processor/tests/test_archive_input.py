from pathlib import Path
from zipfile import ZipFile

from cp_data_processor.processing.archive_input import prepare_archive_input
from guoyu_batch_processor import discover_guoyu_batches


EXCEL_SUFFIXES = (".xls", ".xlsx")


def write_zip(path: Path, members: dict[str, bytes]) -> None:
    with ZipFile(path, "w") as archive:
        for member_name, content in members.items():
            archive.writestr(member_name, content)


def test_multiple_excel_zips_are_prepared_as_batch_directories(tmp_path):
    source_dir = tmp_path / "zip_source"
    source_dir.mkdir()
    write_zip(source_dir / "FA44-4149.zip", {"FA444149-03.xls": b"jt"})
    write_zip(source_dir / "FA59-2242.ZIP", {"FA592242-01.xlsx": b"jt2"})

    with prepare_archive_input(
        source_dir,
        allowed_suffixes=EXCEL_SUFFIXES,
        source_label="JT Excel",
        temporary_prefix="cp_jt_zip_test_",
    ) as prepared:
        assert prepared.is_temporary is True
        assert len(prepared.archives) == 2
        assert len(prepared.data_files) == 2
        assert {path.parent.name for path in prepared.data_files} == {
            "FA44-4149",
            "FA59-2242",
        }


def test_preserved_single_batch_zip_keeps_archive_batch_name(tmp_path):
    archive_path = tmp_path / "25B103.zip"
    write_zip(archive_path, {"EDS/01#-759.xls": b"guoyu"})

    with prepare_archive_input(
        archive_path,
        allowed_suffixes=EXCEL_SUFFIXES,
        source_label="国宇FRD Excel",
        preserve_member_paths=True,
        temporary_prefix="cp_guoyu_zip_test_",
    ) as prepared:
        assert prepared.directory.name == "25B103"
        assert len(prepared.data_files) == 1
        assert prepared.data_files[0].parent == prepared.directory / "EDS"
        assert prepared.data_files[0].name == "01#-759.xls"
        assert list(discover_guoyu_batches(str(prepared.directory))) == ["25B103"]


def test_preserved_product_zip_keeps_multiple_batch_trees(tmp_path):
    archive_path = tmp_path / "DT8U65AS.zip"
    write_zip(
        archive_path,
        {
            "DT8U65AS/25B103/EDS/01#-759.xls": b"lot1",
            "DT8U65AS/25B148/EDS/01#-759.xls": b"lot2",
        },
    )

    with prepare_archive_input(
        archive_path,
        allowed_suffixes=EXCEL_SUFFIXES,
        source_label="国宇FRD Excel",
        preserve_member_paths=True,
        temporary_prefix="cp_guoyu_zip_test_",
    ) as prepared:
        relative_paths = {
            path.relative_to(prepared.directory).as_posix()
            for path in prepared.data_files
        }
        assert relative_paths == {
            "25B103/EDS/01#-759.xls",
            "25B148/EDS/01#-759.xls",
        }
        assert list(discover_guoyu_batches(str(prepared.directory))) == [
            "25B103",
            "25B148",
        ]


def test_preserved_generic_zip_uses_internal_batch_name(tmp_path):
    archive_path = tmp_path / "upload.zip"
    write_zip(archive_path, {"25B103/EDS/01#-759.xls": b"guoyu"})

    with prepare_archive_input(
        archive_path,
        allowed_suffixes=EXCEL_SUFFIXES,
        source_label="国宇FRD Excel",
        preserve_member_paths=True,
        temporary_prefix="cp_guoyu_zip_test_",
    ) as prepared:
        assert list(discover_guoyu_batches(str(prepared.directory))) == ["25B103"]


def test_preserved_generic_product_zip_strips_product_wrapper(tmp_path):
    archive_path = tmp_path / "upload.zip"
    write_zip(
        archive_path,
        {
            "DT8U65AS/25B103/EDS/01#-759.xls": b"lot1",
            "DT8U65AS/25B148/EDS/01#-759.xls": b"lot2",
        },
    )

    with prepare_archive_input(
        archive_path,
        allowed_suffixes=EXCEL_SUFFIXES,
        source_label="国宇FRD Excel",
        preserve_member_paths=True,
        temporary_prefix="cp_guoyu_zip_test_",
    ) as prepared:
        assert list(discover_guoyu_batches(str(prepared.directory))) == [
            "25B103",
            "25B148",
        ]


def test_multiple_preserved_batch_zips_keep_each_guoyu_batch(tmp_path):
    write_zip(tmp_path / "25B103.zip", {"EDS/01#-759.xls": b"lot1"})
    write_zip(tmp_path / "25B148.zip", {"EDS/01#-759.xls": b"lot2"})

    with prepare_archive_input(
        [tmp_path / "25B103.zip", tmp_path / "25B148.zip"],
        allowed_suffixes=EXCEL_SUFFIXES,
        source_label="国宇FRD Excel",
        preserve_member_paths=True,
        temporary_prefix="cp_guoyu_zip_test_",
    ) as prepared:
        assert list(discover_guoyu_batches(str(prepared.directory))) == [
            "25B103",
            "25B148",
        ]
