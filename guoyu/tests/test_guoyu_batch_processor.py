import shutil
from pathlib import Path

import pandas as pd
import pytest

from guoyu_batch_processor import discover_guoyu_batches, process_guoyu_directory


def test_two_level_directory_combines_batches(tmp_path):
    sample_dir = Path(__file__).parents[2] / "data" / "257375"
    sample_files = sorted(sample_dir.glob("*.xls"))
    if len(sample_files) != 2:
        pytest.skip("本地未提供国宇 257375 脱敏样例")

    product_dir = tmp_path / "FRD_PRODUCT"
    for lot_id in ("257375", "257376"):
        lot_dir = product_dir / lot_id
        lot_dir.mkdir(parents=True)
        for sample_file in sample_files:
            shutil.copy2(sample_file, lot_dir / sample_file.name)

    batches = discover_guoyu_batches(str(product_dir))
    assert list(batches) == ["257375", "257376"]

    result = process_guoyu_directory(str(product_dir), str(tmp_path / "output"))
    assert result["batch_ids"] == ["257375", "257376"]
    assert result["batch_count"] == 2
    assert result["wafer_count"] == 4
    assert Path(result["output_dir"]).name.startswith("257375_")

    cleaned = pd.read_csv(result["files"]["cleaned"])
    assert len(cleaned) == 13064
    assert set(cleaned["Lot_ID"].astype(str)) == {"257375", "257376"}


def test_three_level_eds_directory_groups_by_source_lot(tmp_path):
    sample_dir = Path(__file__).parents[2] / "data" / "DT8U65AS"
    if not sample_dir.exists():
        pytest.skip("本地未提供国宇 DT8U65AS 三层目录样例")

    batches = discover_guoyu_batches(str(sample_dir))

    assert list(batches) == ["25B103", "25B148"]
    assert {lot_id: len(files) for lot_id, files in batches.items()} == {
        "25B103": 48,
        "25B148": 48,
    }
    assert all("\\EDS\\" in file_path for files in batches.values() for file_path in files)

    single_batch = discover_guoyu_batches(str(sample_dir / "25B103"))
    assert list(single_batch) == ["25B103"]
    assert len(single_batch["25B103"]) == 48
