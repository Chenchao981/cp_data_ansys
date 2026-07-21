"""Reconcile standard cleaned, yield, and spec CSV outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


BASE_FIELDS = ("Lot_ID", "Wafer_ID", "X", "Y", "Seq", "Bin")


@dataclass(frozen=True)
class OutputFinding:
    code: str
    message: str
    severity: str = "error"


def _yield_percent(value: Any) -> float | None:
    text = str(value).strip()
    try:
        return float(text[:-1]) if text.endswith("%") else float(text)
    except ValueError:
        return None


def validate_output_contract(
    cleaned_path: str | Path,
    yield_path: str | Path,
    spec_path: str | Path,
    profile: Mapping[str, Any],
) -> dict[str, Any]:
    cleaned = pd.read_csv(cleaned_path)
    yield_data = pd.read_csv(yield_path)
    spec = pd.read_csv(spec_path)
    findings: list[OutputFinding] = []

    missing_cleaned = [field for field in BASE_FIELDS if field not in cleaned.columns]
    if missing_cleaned:
        findings.append(
            OutputFinding("cleaned.fields", f"missing cleaned fields: {missing_cleaned}")
        )
    required_yield = ["Lot_ID", "Wafer_ID", "Gross_die", "Good_die", "Yield"]
    missing_yield = [field for field in required_yield if field not in yield_data.columns]
    if missing_yield:
        findings.append(
            OutputFinding("yield.fields", f"missing yield fields: {missing_yield}")
        )

    pass_bin = profile.get("cleaning_rules", {}).get("pass_bin")
    if not missing_cleaned and not missing_yield:
        cleaned_groups = cleaned.groupby(["Lot_ID", "Wafer_ID"], dropna=False)
        yield_keys = {
            (str(row.Lot_ID), str(row.Wafer_ID)): row
            for row in yield_data.itertuples(index=False)
        }
        for (lot_id, wafer_id), frame in cleaned_groups:
            key = (str(lot_id), str(wafer_id))
            row = yield_keys.get(key)
            if row is None:
                findings.append(
                    OutputFinding("yield.missing_wafer", f"yield row missing for {key}")
                )
                continue
            gross = len(frame)
            good = int((frame["Bin"] == pass_bin).sum())
            if int(row.Gross_die) != gross:
                findings.append(
                    OutputFinding(
                        "yield.gross_mismatch",
                        f"{key}: Gross_die={row.Gross_die}, expected {gross}",
                    )
                )
            if int(row.Good_die) != good:
                findings.append(
                    OutputFinding(
                        "yield.good_mismatch",
                        f"{key}: Good_die={row.Good_die}, expected {good}",
                    )
                )
            actual_yield = _yield_percent(row.Yield)
            expected_yield = good / gross * 100 if gross else 0.0
            if actual_yield is None or abs(actual_yield - expected_yield) > 0.011:
                findings.append(
                    OutputFinding(
                        "yield.percent_mismatch",
                        f"{key}: Yield={row.Yield}, expected {expected_yield:.2f}%",
                    )
                )

    spec_status = profile.get("specifications", {}).get("status")
    if spec_status == "approved" and profile.get("specifications", {}).get("layout") == "row_based":
        if "Parameter" not in spec.columns:
            findings.append(OutputFinding("spec.fields", "Parameter column is missing"))
        else:
            params = [field for field in cleaned.columns if field not in BASE_FIELDS]
            missing_params = sorted(set(params) - set(spec["Parameter"].astype(str)))
            if missing_params:
                findings.append(
                    OutputFinding(
                        "spec.parameters",
                        f"parameters missing from spec: {missing_params}",
                    )
                )

    errors = [finding for finding in findings if finding.severity == "error"]
    return {
        "status": "PASS" if not errors else "FAIL",
        "pass_bin": pass_bin,
        "cleaned_rows": int(len(cleaned)),
        "yield_rows": int(len(yield_data)),
        "spec_rows": int(len(spec)),
        "findings": [asdict(finding) for finding in findings],
    }
