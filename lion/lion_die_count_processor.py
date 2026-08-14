"""Lion wafer-level Good Die report cleaner.

This module handles the small ``WAFER PROBE FAIL COUNTER REPORT`` workbooks
used for monthly die-count consolidation.  It is intentionally separate from
the existing Lion CP die-level V1/V2 pipelines because its output is a
four-column business summary rather than the standard cleaned/yield/spec CSV
contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from cp_data_processor.processing.output_naming import create_output_run_dir


OUTPUT_COLUMNS = ("NCE品名", "LOT", "Wafer", "Good Die")
REPORT_MARKER = "WAFER PROBE FAIL COUNTER REPORT"


class LionDieCountError(ValueError):
    """Raised when a source workbook does not match the approved format."""


@dataclass(frozen=True)
class LionDieCountRecord:
    product: str
    lot_id: str
    wafer_id: int
    good_die: int
    source_file: Path


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def discover_workbooks(input_dir: str | Path) -> tuple[list[Path], list[Path]]:
    """Recursively find source workbooks and separate Excel lock files."""

    root = Path(input_dir).expanduser()
    if not root.exists():
        raise LionDieCountError(f"输入目录不存在: {root}")
    if not root.is_dir():
        raise LionDieCountError(f"输入必须是目录: {root}")

    all_xlsx = sorted(
        root.rglob("*.xlsx"), key=lambda path: str(path.relative_to(root)).casefold()
    )
    temporary = [path for path in all_xlsx if path.name.startswith("~$")]
    workbooks = [path for path in all_xlsx if not path.name.startswith("~$")]
    if not workbooks:
        raise LionDieCountError(f"目录中未找到有效的 Lion 管芯数 .xlsx 文件: {root}")
    return workbooks, temporary


def _extract_identity(metadata_row: Iterable[object], source_file: Path) -> tuple[str, str]:
    values = [_text(value) for value in metadata_row if _text(value)]
    device_values = [
        value.split("=", 1)[1].strip()
        for value in values
        if value.upper().startswith("DEVICE=")
    ]
    lot_values = [
        value.split("=", 1)[1].strip()
        for value in values
        if value.upper().startswith("LOT#=")
    ]
    if len(device_values) != 1 or not device_values[0]:
        raise LionDieCountError(
            f"{source_file.name}: 第2行必须且只能包含一个有效 DEVICE="
        )
    if len(lot_values) != 1 or not lot_values[0]:
        raise LionDieCountError(
            f"{source_file.name}: 第2行必须且只能包含一个有效 LOT#="
        )
    return device_values[0], lot_values[0]


def _as_non_negative_integer(value: object, field: str, source_file: Path, row_no: int) -> int:
    try:
        number = float(value)
        integer = int(number)
    except (TypeError, ValueError, OverflowError) as exc:
        raise LionDieCountError(
            f"{source_file.name}: 第{row_no}行 {field} 不是整数: {value!r}"
        ) from exc
    if number != integer or integer < 0:
        raise LionDieCountError(
            f"{source_file.name}: 第{row_no}行 {field} 必须是非负整数: {value!r}"
        )
    return integer


def read_workbook(source_file: str | Path) -> list[LionDieCountRecord]:
    """Read one approved Lion die-count workbook and reconcile its summary."""

    source = Path(source_file)
    try:
        workbook = load_workbook(source, read_only=True, data_only=True)
    except Exception as exc:
        raise LionDieCountError(f"无法读取 {source.name}: {exc}") from exc

    try:
        if workbook.sheetnames != ["Sheet"]:
            raise LionDieCountError(
                f"{source.name}: Sheet 结构不受支持: {workbook.sheetnames}"
            )
        worksheet = workbook["Sheet"]
        rows = list(worksheet.iter_rows(values_only=True))
    finally:
        workbook.close()

    if len(rows) < 4:
        raise LionDieCountError(f"{source.name}: 文件行数不足")
    product, lot_id = _extract_identity(rows[1], source)
    if source.stem != lot_id:
        raise LionDieCountError(
            f"{source.name}: LOT#={lot_id} 与文件名不一致"
        )

    if not any(REPORT_MARKER in _text(value).upper() for row in rows for value in row):
        raise LionDieCountError(f"{source.name}: 未找到 {REPORT_MARKER} 格式标识")

    header_matches: list[tuple[int, list[str]]] = []
    for index, row in enumerate(rows):
        normalized = [_text(value).upper() for value in row]
        if "WAFER#" in normalized and "PASS" in normalized:
            header_matches.append((index, normalized))
    if len(header_matches) != 1:
        raise LionDieCountError(
            f"{source.name}: 应唯一找到包含 WAFER# 和 PASS 的表头，实际 {len(header_matches)} 个"
        )

    header_index, header = header_matches[0]
    wafer_index = header.index("WAFER#")
    pass_index = header.index("PASS")
    records: list[LionDieCountRecord] = []
    summary_index: int | None = None

    for row_index, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        wafer_value = row[wafer_index] if wafer_index < len(row) else None
        wafer_text = _text(wafer_value)
        if wafer_text.upper() == "SUMMARY":
            summary_index = row_index - 1
            break
        if not wafer_text or set(wafer_text) <= {"-"}:
            continue
        pass_value = row[pass_index] if pass_index < len(row) else None
        wafer_id = _as_non_negative_integer(wafer_value, "WAFER#", source, row_index)
        good_die = _as_non_negative_integer(pass_value, "PASS", source, row_index)
        if wafer_id <= 0:
            raise LionDieCountError(
                f"{source.name}: 第{row_index}行 WAFER# 必须大于0"
            )
        records.append(LionDieCountRecord(product, lot_id, wafer_id, good_die, source))

    if not records:
        raise LionDieCountError(f"{source.name}: 未找到 Wafer 数据行")
    if summary_index is None:
        raise LionDieCountError(f"{source.name}: 未找到 SUMMARY 行")

    summary_data = None
    for row_index in range(summary_index + 1, len(rows)):
        row = rows[row_index]
        first = _text(row[wafer_index] if wafer_index < len(row) else None)
        if first and not set(first) <= {"-"}:
            summary_data = (row_index + 1, row)
            break
    if summary_data is None:
        raise LionDieCountError(f"{source.name}: SUMMARY 后缺少汇总数据")

    summary_row_no, summary_row = summary_data
    summary_wafer_count = _as_non_negative_integer(
        summary_row[wafer_index], "SUMMARY WAFER#", source, summary_row_no
    )
    summary_good_die = _as_non_negative_integer(
        summary_row[pass_index], "SUMMARY PASS", source, summary_row_no
    )
    if summary_wafer_count != len(records):
        raise LionDieCountError(
            f"{source.name}: SUMMARY Wafer数={summary_wafer_count}，明细行数={len(records)}"
        )
    actual_good_die = sum(record.good_die for record in records)
    if summary_good_die != actual_good_die:
        raise LionDieCountError(
            f"{source.name}: SUMMARY PASS={summary_good_die}，明细合计={actual_good_die}"
        )

    wafer_ids = [record.wafer_id for record in records]
    if len(wafer_ids) != len(set(wafer_ids)):
        raise LionDieCountError(f"{source.name}: 存在重复 WAFER#")
    return records


def write_output(records: list[LionDieCountRecord], output_file: str | Path) -> Path:
    """Write the exact four-column business workbook shown in the requirement."""

    target = Path(output_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Lion管芯数"
    worksheet.append(OUTPUT_COLUMNS)
    for record in records:
        worksheet.append(
            (record.product, record.lot_id, record.wafer_id, record.good_die)
        )

    header_fill = PatternFill("solid", fgColor="D9EAF7")
    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row in worksheet.iter_rows():
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(horizontal="center", vertical="center")

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.column_dimensions["A"].width = 24
    worksheet.column_dimensions["B"].width = 18
    worksheet.column_dimensions["C"].width = 12
    worksheet.column_dimensions["D"].width = 14
    workbook.save(target)
    workbook.close()
    return target


def process_lion_die_count_directory(
    input_dir: str | Path,
    output_parent: str | Path,
    *,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Clean all monthly Lion die-count workbooks into one Excel report."""

    emit = progress or (lambda _message: None)
    workbooks, temporary_files = discover_workbooks(input_dir)
    emit(f"已发现 {len(workbooks)} 个有效 .xlsx 文件。")
    if temporary_files:
        emit(f"已忽略 {len(temporary_files)} 个 Excel 临时锁文件（~$...）。")

    all_records: list[LionDieCountRecord] = []
    seen_keys: dict[tuple[str, str, int], Path] = {}
    for index, source_file in enumerate(workbooks, start=1):
        records = read_workbook(source_file)
        for record in records:
            key = (record.product, record.lot_id, record.wafer_id)
            previous = seen_keys.get(key)
            if previous is not None:
                raise LionDieCountError(
                    f"重复的 NCE品名+LOT+Wafer: {key}；来源 {previous.name} 和 {source_file.name}"
                )
            seen_keys[key] = source_file
        all_records.extend(records)
        if index == 1 or index == len(workbooks) or index % 25 == 0:
            emit(f"已校验 {index}/{len(workbooks)} 个文件。")

    first_lot_id = all_records[0].lot_id
    output_dir = create_output_run_dir(output_parent, first_lot_id)
    output_file = write_output(all_records, output_dir / "Lion_管芯数.xlsx")
    emit(f"已生成 {len(all_records)} 条 Wafer 记录。")
    return {
        "output_dir": str(output_dir),
        "output_file": str(output_file),
        "file_count": len(workbooks),
        "ignored_temp_file_count": len(temporary_files),
        "product_count": len({record.product for record in all_records}),
        "lot_count": len({record.lot_id for record in all_records}),
        "wafer_count": len(all_records),
        "first_lot_id": first_lot_id,
    }
