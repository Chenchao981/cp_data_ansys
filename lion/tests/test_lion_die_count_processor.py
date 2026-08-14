from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from lion.lion_die_count_processor import (
    LCD235_APPROVED_HEADERS,
    LionDieCountError,
    OUTPUT_COLUMNS,
    process_lion_die_count_directory,
    read_workbook,
)


def make_source(
    path: Path,
    *,
    product="NCELFR140EB20BA",
    lot_id="F26240105",
    rows=((9, 900, 883), (10, 990, 977)),
    summary_pass=None,
    summary_die=None,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sheet"
    worksheet.append(["2026-06-01", None, None, None, f"{lot_id}.{product}"])
    worksheet.append([f"LOT#={lot_id}", None, None, None, "TESTFILE=F.pgs", None, None, None, f"DEVICE={product}"])
    worksheet.append(["WAFER PROBE FAIL COUNTER REPORT"])
    worksheet.append(["WAFER#", "#2", "PASS", "PASS%", "TOTAL", "DIE"])
    worksheet.append(["---------------", "------", "------"])
    for wafer_id, pass_count, good_die in rows:
        worksheet.append(
            [str(wafer_id), "0", str(pass_count), "99%", str(pass_count), str(good_die)]
        )
    worksheet.append(["SUMMARY", "#2", "PASS", "PASS%", "TOTAL", "DIE"])
    worksheet.append(["---------------", "------", "------"])
    worksheet.append(
        [
            str(len(rows)),
            "0",
            str(
                sum(pass_count for _, pass_count, _ in rows)
                if summary_pass is None
                else summary_pass
            ),
            None,
            None,
            str(
                sum(good_die for _, _, good_die in rows)
                if summary_die is None
                else summary_die
            ),
        ]
    )
    workbook.save(path)
    workbook.close()


def make_lcd235_source(
    path: Path,
    *,
    product="NCEVD1500XAA",
    lot_id="V25391603",
    rows=((1, 590, 1), (2, 604, 2)),
    mutate_header=None,
    summary_good_die=None,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sheet1"
    worksheet.append([])
    worksheet.append([None, "杭州立昂微电子MOSFET出货报告单"])
    worksheet.append([])
    worksheet.append([None, "打印日期: 2026-06-05 03:53:44"])
    headers = list(LCD235_APPROVED_HEADERS)
    if mutate_header is not None:
        index, value = mutate_header
        headers[index] = value
    worksheet.append(headers)
    worksheet.append([None] * len(headers))
    worksheet.append([None] * len(headers))
    for wafer_id, pass_count, qad_count in rows:
        worksheet.append(
            [
                None,
                product,
                lot_id,
                wafer_id,
                0.95,
                pass_count,
                qad_count,
                0.94,
                *([0] * (len(headers) - 8)),
            ]
        )
    worksheet.append([None] * len(headers))
    worksheet.append([None, "摘要", *([None] * (len(headers) - 2))])
    worksheet.append(
        [
            None,
            None,
            None,
            None,
            "总\n片数",
            "CP合格\n管芯总数",
            "合格\n管芯总数",
            "QAD\n平均良率",
            *([None] * (len(headers) - 8)),
        ]
    )
    expected_good_die = sum(pass_count - qad_count for _, pass_count, qad_count in rows)
    worksheet.append(
        [
            None,
            None,
            None,
            None,
            len(rows),
            sum(pass_count for _, pass_count, _ in rows),
            expected_good_die if summary_good_die is None else summary_good_die,
            0.94,
            *([None] * (len(headers) - 8)),
        ]
    )
    workbook.save(path)
    workbook.close()


def test_recursive_monthly_cleaning_writes_exact_contract(tmp_path):
    input_dir = tmp_path / "2026.6"
    make_source(input_dir / "F0100A1" / "F26240105.xlsx")
    make_source(
        input_dir / "F0200A1" / "F26240106.xlsx",
        product="NCELFR75EV40AA",
        lot_id="F26240106",
        rows=((1, 1010, 1000),),
    )
    (input_dir / "F0100A1" / "~$F26240105.xlsx").touch()

    messages = []
    result = process_lion_die_count_directory(
        input_dir, tmp_path / "output", progress=messages.append
    )

    assert result["file_count"] == 2
    assert result["ignored_temp_file_count"] == 1
    assert result["product_count"] == 2
    assert result["lot_count"] == 2
    assert result["wafer_count"] == 3
    assert Path(result["output_dir"]).name.startswith("F26240105_")
    workbook = load_workbook(result["output_file"], read_only=True, data_only=True)
    rows = list(workbook["Lion管芯数"].iter_rows(values_only=True))
    workbook.close()
    assert rows[0] == OUTPUT_COLUMNS
    assert rows[1:] == [
        ("NCELFR140EB20BA", "F26240105", 9, 900, 883),
        ("NCELFR140EB20BA", "F26240105", 10, 990, 977),
        ("NCELFR75EV40AA", "F26240106", 1, 1010, 1000),
    ]
    assert any("已忽略 1 个 Excel 临时锁文件" in message for message in messages)


def test_summary_pass_mismatch_fails_closed(tmp_path):
    source = tmp_path / "F26240105.xlsx"
    make_source(source, summary_pass=1)

    with pytest.raises(LionDieCountError, match="SUMMARY PASS"):
        read_workbook(source)


def test_summary_die_mismatch_fails_closed(tmp_path):
    source = tmp_path / "F26240105.xlsx"
    make_source(source, summary_die=1)

    with pytest.raises(LionDieCountError, match="SUMMARY DIE"):
        read_workbook(source)


def test_filename_must_match_lot_metadata(tmp_path):
    source = tmp_path / "WRONG.xlsx"
    make_source(source)

    with pytest.raises(LionDieCountError, match="LOT#=.*文件名不一致"):
        read_workbook(source)


def test_duplicate_product_lot_wafer_across_files_fails_closed(tmp_path):
    input_dir = tmp_path / "input"
    make_source(input_dir / "a" / "F26240105.xlsx")
    make_source(input_dir / "b" / "F26240105.xlsx")

    with pytest.raises(LionDieCountError, match=r"重复的 NCE品名\+LOT\+Wafer"):
        process_lion_die_count_directory(input_dir, tmp_path / "output")


def test_lcd235_maps_cp_pass_and_subtracts_qad_for_good_die(tmp_path):
    source = tmp_path / "V25391603.xlsx"
    make_lcd235_source(source)

    records = read_workbook(source)

    assert [
        (record.product, record.lot_id, record.wafer_id, record.pass_count, record.good_die)
        for record in records
    ] == [
        ("NCEVD1500XAA", "V25391603", 1, 590, 589),
        ("NCEVD1500XAA", "V25391603", 2, 604, 602),
    ]


def test_lcd235_generates_the_same_five_column_output(tmp_path):
    input_dir = tmp_path / "LCD235"
    make_lcd235_source(input_dir / "V25391603.xlsx")

    result = process_lion_die_count_directory(input_dir, tmp_path / "output")

    workbook = load_workbook(result["output_file"], read_only=True, data_only=True)
    rows = list(workbook["Lion管芯数"].iter_rows(values_only=True))
    workbook.close()
    assert rows == [
        OUTPUT_COLUMNS,
        ("NCEVD1500XAA", "V25391603", 1, 590, 589),
        ("NCEVD1500XAA", "V25391603", 2, 604, 602),
    ]


def test_lcd235_rejects_unapproved_header_order_or_name(tmp_path):
    source = tmp_path / "V25391603.xlsx"
    make_lcd235_source(source, mutate_header=(24, "DVR_BVDSS3_CHANGED"))

    with pytest.raises(LionDieCountError, match="34列表头"):
        read_workbook(source)


def test_lcd235_summary_good_die_mismatch_fails_closed(tmp_path):
    source = tmp_path / "V25391603.xlsx"
    make_lcd235_source(source, summary_good_die=1)

    with pytest.raises(LionDieCountError, match="汇总合格管芯总数"):
        read_workbook(source)
