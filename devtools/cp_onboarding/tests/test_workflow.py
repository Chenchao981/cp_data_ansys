from __future__ import annotations

import json

import pandas as pd

from devtools.cp_onboarding.contracts import validate_profile
from devtools.cp_onboarding.output_validator import validate_output_contract
from devtools.cp_onboarding.profiler import build_sample_profile
from devtools.cp_onboarding.scaffold import create_cleaner_scaffold


def approved_profile() -> dict:
    return {
        "schema_version": 1,
        "company": {
            "code": "ACME",
            "display_name": "Acme Wafer",
            "module_name": "acme",
            "format_version": "1.0.0",
        },
        "metadata_rules": {
            "product": {"source": "filename", "rule": "approved", "status": "approved"},
            "lot_id": {"source": "filename", "rule": "approved", "status": "approved"},
            "wafer_id": {"source": "filename", "rule": "approved", "status": "approved"},
        },
        "standard_fields": {
            field: {"source": field, "transform": "identity", "status": "approved"}
            for field in ("X", "Y", "Seq", "Bin")
        },
        "parameters": {
            "discovery_rule": "numeric columns after Bin",
            "unit_rule": "source unit row",
        },
        "specifications": {"status": "approved", "layout": "row_based"},
        "cleaning_rules": {
            "pass_bin": 2,
            "invalid_value_policy": "convert approved markers to null",
            "duplicate_die_policy": "reject",
            "retest_policy": "keep last approved retest",
            "source_row_filter": "retain approved die rows",
            "missing_coordinate_policy": "reject",
        },
        "detection": {
            "required_content_signatures": ["ACME_CP_DATA"],
            "ambiguity_behavior": "fail_closed",
        },
        "approval": {
            "status": "approved",
            "reviewer": "reviewer",
            "reviewed_at": "2026-07-21T00:00:00+08:00",
            "unresolved_critical_items": [],
        },
    }


def test_profile_treats_text_disguised_as_xls_by_signature(tmp_path):
    sample = tmp_path / "LOT123456-W01.xls"
    sample.write_text("ACME_CP_DATA\tX\tY\nROW\t1\t2\n", encoding="utf-8")

    report = build_sample_profile([str(sample)])

    assert report["files"][0]["content"]["kind"] == "text"
    assert "123456" not in report["files"][0]["sanitized_name"]


def test_approved_profile_validates_and_scaffolds(tmp_path):
    profile = approved_profile()
    assert validate_profile(profile, require_approved=True) == []

    created = create_cleaner_scaffold(profile, tmp_path / "staging")

    assert len(created) == 5
    processor = (tmp_path / "staging" / "acme_processor.py").read_text(encoding="utf-8")
    assert "CompanyCleaningPipeline" in processor
    assert "pass_bin=2" in processor


def test_output_validator_reconciles_explicit_pass_bin(tmp_path):
    cleaned_path = tmp_path / "cleaned.csv"
    yield_path = tmp_path / "yield.csv"
    spec_path = tmp_path / "spec.csv"
    pd.DataFrame(
        {
            "Lot_ID": ["L1", "L1", "L1"],
            "Wafer_ID": [1, 1, 1],
            "X": [0, 1, 2],
            "Y": [0, 0, 0],
            "Seq": [1, 2, 3],
            "Bin": [2, 1, 2],
            "VTH": [1.0, 2.0, 3.0],
        }
    ).to_csv(cleaned_path, index=False)
    pd.DataFrame(
        {
            "Lot_ID": ["L1"],
            "Wafer_ID": [1],
            "Gross_die": [3],
            "Good_die": [2],
            "Yield": ["66.67%"],
        }
    ).to_csv(yield_path, index=False)
    pd.DataFrame(
        {"Parameter": ["VTH"], "Unit": ["V"], "LSL": [0], "USL": [5]}
    ).to_csv(spec_path, index=False)

    report = validate_output_contract(
        cleaned_path, yield_path, spec_path, approved_profile()
    )

    assert report["status"] == "PASS"
    assert json.loads(json.dumps(report))["pass_bin"] == 2
