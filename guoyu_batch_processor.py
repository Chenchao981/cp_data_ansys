#!/usr/bin/env python
"""扬州国宇 FRD CP 批次处理入口。"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
from cp_data_processor.data_models.cp_data import CPLot
from cp_data_processor.readers.company_adapters.company_config import get_company_config
from cp_data_processor.readers.company_adapters.guoyu_adapter import GUOYUAdapter
from guoyu.guoyu_reader import GuoyuFRDReader


def _find_excel_files(directory: Path, recursive: bool = False) -> List[Path]:
    """查找目录中的国宇 Excel 文件。"""
    finder = directory.rglob if recursive else directory.glob
    files = [
        path
        for pattern in ("*.xls", "*.xlsx")
        for path in finder(pattern)
        if not path.name.startswith("~$")
    ]
    return sorted(set(files), key=lambda path: str(path).lower())


def discover_guoyu_batches(input_dir: str) -> Dict[str, List[str]]:
    """
    递归识别国宇单批次或多批次目录。

    批次以目录名称分组，因此支持：
    - 批次目录 -> Excel
    - 产品目录 -> 批次目录 -> Excel
    - 产品目录 -> 批次目录 -> 一个或多个 EDS/数据子目录 -> Excel

    同一批次的 Excel 内部 LotName 可能带工艺后缀（例如 25B103-D70），
    不能用 LotName 拆分业务批次。
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise ValueError(f"国宇输入目录不存在: {input_path}")

    direct_files = _find_excel_files(input_path)
    if direct_files:
        return {input_path.name: [str(path) for path in direct_files]}

    data_dirs = [
        (child, _find_excel_files(child, recursive=True))
        for child in sorted(
            (path for path in input_path.iterdir() if path.is_dir()),
            key=lambda path: path.name.lower(),
        )
    ]
    data_dirs = [(directory, files) for directory, files in data_dirs if files]
    if not data_dirs:
        raise ValueError(
            f"国宇输入目录及其子目录中没有发现 Excel: {input_path}"
        )

    # 输入路径本身是批次目录时，其下一层通常是 EDS、EDS1 等数据目录。
    if all(directory.name.upper().startswith("EDS") for directory, _files in data_dirs):
        files = [path for _directory, paths in data_dirs for path in paths]
        return {input_path.name: [str(path) for path in sorted(files, key=str)]}

    # 输入路径是产品目录时，第一层目录名称就是业务批次号。
    return {
        directory.name: [str(path) for path in files]
        for directory, files in data_dirs
    }


def generate_output_folder_name(first_lot_id: str) -> str:
    """生成“首个批次号_流水号”输出文件夹名称。"""
    safe_lot_id = re.sub(r'[<>:"/\\|?*]', "_", first_lot_id)
    serial = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_lot_id}_{serial}"


def _read_guoyu_batch(lot_id: str, files: List[str], product_name: str) -> CPLot:
    """读取并标准化一个国宇批次。"""
    reader = GuoyuFRDReader(files, lot_id=lot_id)
    raw_lot = reader.read()
    raw_lot.product = product_name
    return GUOYUAdapter(get_company_config("GUOYU") or {}).transform_to_standard_format(
        raw_lot
    )


def process_guoyu_batch(input_dir: str, output_dir: str) -> Dict[str, str]:
    """处理一个国宇批次目录，并直接输出到指定目录。"""
    batches = discover_guoyu_batches(input_dir)
    if len(batches) != 1:
        raise ValueError("process_guoyu_batch 仅支持单批次目录")
    lot_id, files = next(iter(batches.items()))
    lot = _read_guoyu_batch(lot_id, files, Path(input_dir).name)
    return StandardCSVGenerator().generate_standard_csvs(lot, output_dir)


def process_guoyu_directory(input_dir: str, output_parent_dir: str) -> Dict[str, object]:
    """
    处理单批次或产品目录下的多个批次。

    输出目录自动命名为“第一个批次号_YYYYMMDD_HHMMSS”。
    """
    batches = discover_guoyu_batches(input_dir)
    product_name = Path(input_dir).name
    first_lot_id = next(iter(batches))
    output_dir = Path(output_parent_dir) / generate_output_folder_name(first_lot_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    lots = {
        lot_id: _read_guoyu_batch(lot_id, files, product_name)
        for lot_id, files in batches.items()
    }
    generator = StandardCSVGenerator()
    if len(lots) == 1:
        files = generator.generate_standard_csvs(next(iter(lots.values())), str(output_dir))
    else:
        files = generator.generate_combined_standard_csvs(
            lots, str(output_dir), combined_name=first_lot_id
        )

    return {
        "files": files,
        "output_dir": str(output_dir),
        "batch_ids": list(lots),
        "batch_count": len(lots),
        "wafer_count": sum(len(lot.wafers) for lot in lots.values()),
        "product_name": product_name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="扬州国宇 FRD CP 数据处理器")
    parser.add_argument("input_dir", help="单批次目录，或包含多层批次数据的产品目录")
    parser.add_argument("-o", "--output", default="output", help="输出父目录")
    args = parser.parse_args()

    result = process_guoyu_directory(args.input_dir, args.output)
    print(f"output_dir: {result['output_dir']}")
    for file_type, file_path in result["files"].items():
        print(f"{file_type}: {file_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
