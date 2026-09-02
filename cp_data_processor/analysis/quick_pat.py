from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook

FORMULA_CONTRACT = "AEC_Q101_MEDIAN_IQR_5SIGMA_VDMOS_V5_6"
SIGMA_MULTIPLIER = 5.0
IQR_DIVISOR = 1.349
MINIMUM_IQR = 0.0001
MINIMUM_VALUE_COUNT = 10


def generate_cleaned_csv_pat(
    *,
    cleaned_files: Sequence[str | Path],
    spec_files: Sequence[str | Path],
    output_dir: str | Path,
) -> Path:
    """Generate CP PAT statistics from this tool's standard CSV triplets."""

    cleaned = _existing_files(cleaned_files, "cleaned")
    specs = _existing_files(spec_files, "spec")
    parameters = _parameters_from_specs(specs)
    values: dict[str, list[np.ndarray]] = defaultdict(list)
    record_count = 0

    for path in cleaned:
        header = pd.read_csv(path, nrows=0, encoding="utf-8-sig")
        available = [parameter for parameter in parameters if parameter in header.columns]
        if not available:
            raise ValueError(f"cleaned CSV has no parameters declared by spec: {path}")
        for chunk in pd.read_csv(
            path,
            usecols=available,
            chunksize=100_000,
            encoding="utf-8-sig",
            low_memory=False,
        ):
            record_count += len(chunk)
            for parameter in available:
                numeric = pd.to_numeric(chunk[parameter], errors="coerce")
                array = numeric.to_numpy(dtype=np.float64, na_value=np.nan)
                finite = array[np.isfinite(array)]
                if finite.size:
                    values[parameter].append(finite)

    rows: list[dict[str, object]] = []
    for parameter in parameters:
        if parameter not in values:
            continue
        array = np.concatenate(values[parameter])
        if array.size < MINIMUM_VALUE_COUNT:
            continue
        array.sort()
        count = int(array.size)
        q1 = float(array[math.floor(count * 0.25)])
        median = float(array[math.floor(count * 0.5)])
        q3 = float(array[math.floor(count * 0.75)])
        sigma = max(MINIMUM_IQR, q3 - q1) / IQR_DIVISOR
        lcl = median - SIGMA_MULTIPLIER * sigma
        ucl = median + SIGMA_MULTIPLIER * sigma
        outlier_count = int(np.count_nonzero((array < lcl) | (array > ucl)))
        rows.append(
            {
                "parameter": parameter,
                "count": count,
                "mean": float(np.mean(array)),
                "stddev": float(np.std(array, ddof=1)) if count > 1 else 0.0,
                "minimum": float(array[0]),
                "q1": q1,
                "median": median,
                "q3": q3,
                "maximum": float(array[-1]),
                "sigma": sigma,
                "lcl_calculated": lcl,
                "ucl_calculated": ucl,
                "lcl_before": None,
                "ucl_before": None,
                "lcl_after": lcl,
                "ucl_after": ucl,
                "updated": outlier_count > 0,
                "outlier_count": outlier_count,
                "outlier_percentage": (
                    outlier_count / record_count * 100.0 if record_count else 0.0
                ),
            }
        )
    if not rows:
        raise ValueError(
            f"no CP parameter has at least {MINIMUM_VALUE_COUNT} numeric values"
        )

    target = Path(output_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    report = target / f"PAT_CP_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    _write_workbook(
        report,
        rows=rows,
        record_count=record_count,
        source_files=len(cleaned),
    )
    print(
        "TMS_CP_PAT_SUMMARY="
        + json.dumps(
            {
                "source_files": len(cleaned),
                "record_count": record_count,
                "parameter_count": len(rows),
                "formula_contract": FORMULA_CONTRACT,
                "report": str(report),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return report


def _existing_files(paths: Sequence[str | Path], role: str) -> tuple[Path, ...]:
    resolved = tuple(Path(path).resolve() for path in paths)
    if not resolved:
        raise ValueError(f"at least one {role} CSV is required")
    for path in resolved:
        if not path.is_file() or path.suffix.lower() != ".csv":
            raise FileNotFoundError(f"{role} CSV is unavailable: {path}")
    return resolved


def _parameters_from_specs(spec_files: Iterable[Path]) -> tuple[str, ...]:
    found: list[str] = []
    seen: set[str] = set()
    sentinels = {"", "NO_PARAMETERS", "UNIT", "LIMITL", "LIMITU", "LIMIT_LOW", "LIMIT_HIGH"}
    for path in spec_files:
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")
        if "Parameter" not in frame.columns:
            raise ValueError(f"spec CSV has no Parameter column: {path}")
        columns = [str(column).strip() for column in frame.columns]
        is_matrix = any(
            str(value).strip().upper() in {"UNIT", "LIMITL", "LIMITU", "LIMIT_LOW", "LIMIT_HIGH"}
            for value in frame["Parameter"].tolist()
        )
        candidates = columns[1:] if is_matrix else [str(value).strip() for value in frame["Parameter"]]
        for parameter in candidates:
            key = parameter.upper()
            if key in sentinels or key in seen:
                continue
            seen.add(key)
            found.append(parameter)
    if not found:
        raise ValueError("spec CSV contains no declared CP parameters")
    return tuple(found)


def _write_workbook(
    path: Path,
    *,
    rows: Sequence[dict[str, object]],
    record_count: int,
    source_files: int,
) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "PAT"
    sheet.append(
        [
            "CP PAT",
            FORMULA_CONTRACT,
            f"记录={record_count}",
            f"清洗文件={source_files}",
        ]
    )
    headers = (
        "parameter",
        "count",
        "mean",
        "stddev",
        "minimum",
        "q1",
        "median",
        "q3",
        "maximum",
        "sigma",
        "lcl_calculated",
        "ucl_calculated",
        "lcl_before",
        "ucl_before",
        "lcl_after",
        "ucl_after",
        "updated",
        "outlier_count",
        "outlier_percentage",
    )
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    sheet.freeze_panes = "A3"
    sheet.auto_filter.ref = f"A2:S{sheet.max_row}"
    workbook.save(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate CP PAT from standard CSV triplets")
    parser.add_argument("--cleaned", action="append", required=True)
    parser.add_argument("--spec", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    generate_cleaned_csv_pat(
        cleaned_files=args.cleaned,
        spec_files=args.spec,
        output_dir=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
