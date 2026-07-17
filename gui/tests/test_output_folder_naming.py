from zipfile import ZipFile

from guoyu_batch_processor import generate_output_folder_name as generate_guoyu_name
from gui.widgets.huahong_widget import generate_output_folder_name as generate_hh_name
from gui.widgets.jetech_widget import generate_jt_output_folder_name
from gui.widgets.lion_widget import generate_lion_output_folder_name


SERIAL = "20260717_153045"


def test_huahong_multiple_zips_use_first_real_lot_in_processing_order(tmp_path):
    later_archive = tmp_path / "20_later.zip"
    first_archive = tmp_path / "10_first.zip"
    with ZipFile(later_archive, "w") as archive:
        archive.writestr("wrapper/wafer02.txt", "Header\nLot Number HH_LOT-B@203\n")
    with ZipFile(first_archive, "w") as archive:
        archive.writestr("wrapper/wafer01.txt", "Header\nLot Number HH_LOT-A@203\n")

    assert generate_hh_name(
        [later_archive, first_archive],
        serial=SERIAL,
    ) == f"LOT-A_{SERIAL}"


def test_jetech_multiple_zips_use_first_real_lot_in_processing_order(tmp_path):
    later_archive = tmp_path / "20_later.zip"
    first_archive = tmp_path / "10_first.zip"
    with ZipFile(later_archive, "w") as archive:
        archive.writestr("FA55-2222/wafer.xlsx", b"placeholder")
    with ZipFile(first_archive, "w") as archive:
        archive.writestr("FA44-1111/wafer.xlsx", b"placeholder")

    assert generate_jt_output_folder_name(
        [later_archive, first_archive],
        serial=SERIAL,
    ) == f"FA44-1111_{SERIAL}"


def test_jetech_product_folder_uses_first_batch_subfolder(tmp_path):
    product_dir = tmp_path / "JT_PRODUCT"
    later_batch = product_dir / "FA55-2222"
    first_batch = product_dir / "FA44-1111"
    later_batch.mkdir(parents=True)
    first_batch.mkdir()
    (later_batch / "wafer.xlsx").touch()
    (first_batch / "wafer.xlsx").touch()

    assert generate_jt_output_folder_name(
        product_dir,
        serial=SERIAL,
    ) == f"FA44-1111_{SERIAL}"


def test_lion_and_guoyu_use_the_same_naming_contract(tmp_path):
    lion_batch = tmp_path / "F25130244"
    lion_batch.mkdir()

    assert generate_lion_output_folder_name(
        lion_batch,
        serial=SERIAL,
    ) == f"F25130244_{SERIAL}"
    assert generate_guoyu_name("257375", serial=SERIAL) == f"257375_{SERIAL}"
