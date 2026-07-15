from pathlib import Path

import pytest

from lion_batch_processor import discover_batch_files


def _sample_product_dir() -> Path:
    candidates = [
        path
        for path in (Path(__file__).parents[2] / "data").iterdir()
        if path.is_dir() and path.name.startswith("lion-")
    ]
    if not candidates:
        pytest.skip("本地未提供 Lion 产品级样例")
    return candidates[0]


def test_discover_multiple_lion_batches():
    product_dir = _sample_product_dir()
    batches = discover_batch_files(product_dir)
    assert set(batches) == {"F25130244", "F25130246", "F25130247"}
    assert all(batches.values())


def test_discover_single_lion_batch():
    product_dir = _sample_product_dir()
    batch_dir = product_dir / "F25130244"
    batches = discover_batch_files(batch_dir)
    assert list(batches) == ["F25130244"]
    assert len(batches["F25130244"]) == len(list(batch_dir.glob("*.xlsx")))
