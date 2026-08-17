from __future__ import annotations

import io
import json
import zipfile

import pandas as pd
import pytest

from frontend.cockpit_artifact import (
    ArtifactSource,
    CockpitArtifactError,
    build_cockpit_artifact,
    read_cockpit_artifact,
    sources_from_paths,
)
from frontend.cp_dashboard_app import (
    get_spec_info,
    load_cockpit_dataset,
    scope_dataset_to_lot,
)


def _lion_spec(upper: float) -> bytes:
    return pd.DataFrame(
        [
            ["Parameter", "TEST_NUM", "PARAM_A"],
            ["UNIT", "", "V"],
            ["LIMIT_LOW", "", 0.0],
            ["LIMIT_HIGH", "", upper],
        ]
    ).to_csv(index=False, header=False).encode("utf-8")


def test_round_trip_preserves_standard_csv_and_multi_lot_specs(tmp_path) -> None:
    cleaned_path = tmp_path / "F10001_cleaned_20260817_1000.csv"
    yield_path = tmp_path / "F10001_yield_20260817_1000.csv"
    spec_one = tmp_path / "F10001_spec_20260817_1000.csv"
    spec_two = tmp_path / "F20002_spec_20260817_1000.csv"
    cleaned_path.write_bytes(
        b"Lot_ID,Wafer_ID,X,Y,Seq,Bin,PARAM_A\nF10001,1,0,0,1,1,1.0\nF20002,1,0,0,1,1,2.0\n"
    )
    yield_path.write_bytes(
        b"Lot_ID,Wafer_ID,Yield\nF10001,1,100.00%\nF20002,1,100.00%\n"
    )
    spec_one.write_bytes(_lion_spec(2.0))
    spec_two.write_bytes(_lion_spec(2.5))

    sources = sources_from_paths(cleaned_path, yield_path, [spec_one, spec_two])
    artifact_bytes = build_cockpit_artifact(sources)
    artifact = read_cockpit_artifact(artifact_bytes)

    assert [(item.role, item.original_name) for item in artifact.files] == [
        ("cleaned", cleaned_path.name),
        ("yield", yield_path.name),
        ("spec", spec_one.name),
        ("spec", spec_two.name),
    ]
    assert artifact.files[0].content == cleaned_path.read_bytes()

    dataset = load_cockpit_dataset(artifact_bytes, "saved.cpcockpit")
    assert set(dataset.specs) == {"F10001", "F20002"}
    scoped = scope_dataset_to_lot(dataset, "F20002")
    assert scoped.cleaned["Lot_ID"].unique().tolist() == ["F20002"]
    assert get_spec_info(scoped.spec, "PARAM_A")["limit_upper"] == 2.5


def test_rejects_tampered_data() -> None:
    artifact_bytes = build_cockpit_artifact(
        [ArtifactSource("cleaned", "LOT_cleaned_20260817_1000.csv", b"Lot_ID\nLOT\n")]
    )
    source = zipfile.ZipFile(io.BytesIO(artifact_bytes), "r")
    buffer = io.BytesIO()
    with source, zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name in source.namelist():
            content = source.read(name)
            if name.endswith(".csv"):
                content = content[:-1] + (b"X" if content[-1:] != b"X" else b"Y")
            target.writestr(name, content)

    with pytest.raises(CockpitArtifactError, match="完整性校验失败"):
        read_cockpit_artifact(buffer.getvalue())


def test_rejects_manifest_with_unsafe_archive_path() -> None:
    manifest = {
        "format": "nce-cp-cockpit",
        "version": 1,
        "created_at": "2026-08-17T00:00:00+00:00",
        "files": [],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("../outside.csv", "Lot_ID\nLOT\n")

    with pytest.raises(CockpitArtifactError, match="不安全路径"):
        read_cockpit_artifact(buffer.getvalue())
