from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
from cp_data_processor.validation.standard_lot import StandardLotValidator
from lion.lion_v2_adapter import LionV2Adapter
from lion.lion_v2_reader import (
    APPROVED_PARAMETER_SCHEMAS,
    LION_V2_FORMAT,
    LionV2FormatError,
    LionV2Reader,
)
from lion_batch_processor import (
    LION_V1_FORMAT,
    create_batch_lot,
    create_combined_lot,
    detect_lion_format,
    generate_lion_run_csvs,
)


PARAMETERS = [
    "CABLE_CHECK1",
    "CABLE_CHECK2",
    "KELVIN_CHECK",
    "OS",
    "IR_35V",
    "IR_700V",
    "IR_750V",
    "IR_800V",
    "VBR_0P25mA",
    "VBR_1mA",
    "VF_10A",
    "VF_15A",
    "VF_30A",
    "IR_750V_Retest",
    "OS_END",
]
F0122A1_PARAMETERS = [
    "CABLE_CHECK1",
    "CABLE_CHECK2",
    "KELVIN_CHECK",
    "OS",
    "IR_35V",
    "IR_900V",
    "IR_1000V",
    "IR_1100V",
    "VBR_0P25mA",
    "VBR_1mA",
    "VF_30A",
    "VF_60A",
    "IR_1000V_Retest",
    "OS_END",
]
SOURCE_COLUMNS = [
    "SITE_NUM",
    "DUT_NO",
    "PART_ID",
    "PASSFG",
    "SOFT_BIN",
    "T_TIME",
    "X_COORD",
    "Y_COORD",
    "TEST_NUM",
] + PARAMETERS


def _source_frames(
    lot_id: str,
    wafer_id: str,
    *,
    vf_10a_upper: float = 2.0,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = pd.DataFrame(
        {
            0: [
                "STS8200 StationA",
                "DUT Name:DEMO_PRODUCT",
                f"Lot Id:{lot_id}--",
                f"WAFER_ID:{wafer_id}",
                "Total: 3",
                "Pass: 2 66.67%",
                "Fail: 1 33.33%",
                "SBin[1] Pass__Default 2 66.67% 1",
                "SBin[7] IR_700V__AllFail 1 33.33% 7",
            ]
        }
    )
    statistics = pd.DataFrame(
        {
            0: [
                "Statistics Information",
                "Statistice Site Index : All Sites",
                "Statistice data source: All Tested Data include Failed Data ",
                None,
                "Param name Units Min value Max value Avg Std Dev Sum Count",
            ]
        }
    )

    units = ["Unit", None, None, None, None, "ms", None, None, None]
    units += ["V", "V", "mV", "V", "mA", "uA", "uA", "uA"]
    units += ["V", "V", "V", "V", "V", "uA", "V"]
    lows = ["LimitL"] + [None] * 8 + [0.0] * len(PARAMETERS)
    highs = ["LimitU"] + [None] * 8 + [10.0] * len(PARAMETERS)
    highs[SOURCE_COLUMNS.index("VF_10A")] = vf_10a_upper

    def die_row(
        seq: int,
        passed: bool,
        x: int,
        y: int,
        measured_count: int,
    ) -> list[object]:
        values: list[object] = [
            1,
            seq,
            seq,
            passed,
            1 if passed else 7,
            1.5,
            x,
            y,
            15 if passed else 6,
        ]
        values += [float(seq + index) for index in range(measured_count)]
        values += [None] * (len(PARAMETERS) - measured_count)
        return values

    dut = pd.DataFrame(
        [
            SOURCE_COLUMNS,
            units,
            lows,
            highs,
            [None] * len(SOURCE_COLUMNS),
            die_row(1, True, 0, 0, len(PARAMETERS)),
            die_row(2, False, 1, 0, 6),
            die_row(3, True, 2, 0, len(PARAMETERS)),
        ]
    )
    return summary, statistics, dut


def _parse_lot(
    tmp_path: Path,
    lot_id: str,
    wafer_id: str,
    *,
    vf_10a_upper: float = 2.0,
):
    summary, statistics, dut = _source_frames(
        lot_id, wafer_id, vf_10a_upper=vf_10a_upper
    )
    path = tmp_path / lot_id / f"{lot_id}_{wafer_id}.xls"
    return LionV2Reader([]).parse_frames(
        path,
        summary_frame=summary,
        statistics_frame=statistics,
        dut_frame=dut,
    )


def _standard_lot(tmp_path: Path, lot_id: str, wafer_id: str, **kwargs):
    lot = LionV2Adapter().transform_to_standard_format(
        _parse_lot(tmp_path, lot_id, wafer_id, **kwargs)
    )
    StandardLotValidator().validate_or_raise(lot)
    return lot


def test_parser_metadata_specs_nulls_mapping_and_pass_bin(tmp_path):
    raw = _parse_lot(tmp_path, "F10001", "1")

    assert raw.lot_id == "F10001"
    assert raw.product == "DEMO_PRODUCT"
    assert raw.pass_bin == 1
    assert len(raw.params) == 15
    vf_param = next(parameter for parameter in raw.params if parameter.id == "VF_10A")
    assert (vf_param.unit, vf_param.sl, vf_param.su) == ("V", 0.0, 2.0)
    assert raw.wafers[0].source_lot_id == "F10001"
    assert raw.wafers[0].wafer_id == "1"
    assert pd.isna(raw.wafers[0].chip_data.loc[1, "OS_END"])
    assert raw.wafers[0].pass_chips == 2
    assert raw.wafers[0].fail_chips == 1

    standardized = LionV2Adapter().transform_to_standard_format(raw)
    StandardLotValidator().validate_or_raise(standardized)
    assert list(standardized.wafers[0].chip_data.columns[:11]) == [
        "Lot_ID",
        "Wafer_ID",
        "X",
        "Y",
        "Seq",
        "Bin",
        "SITE_NUM",
        "PART_ID",
        "CONT",
        "T_TIME",
        "TEST_NUM",
    ]
    assert standardized.wafers[0].chip_data["Lot_ID"].unique().tolist() == [
        "F10001"
    ]
    assert standardized.wafers[0].chip_data["Bin"].tolist() == [1, 7, 1]
    assert pd.isna(standardized.wafers[0].chip_data.loc[1, "OS_END"])


@pytest.mark.parametrize("duplicate_kind", ["coordinate", "seq"])
def test_duplicate_die_or_seq_fails_closed(tmp_path, duplicate_kind):
    summary, statistics, dut = _source_frames("F10001", "1")
    if duplicate_kind == "coordinate":
        dut.iloc[6, SOURCE_COLUMNS.index("X_COORD")] = 0
    else:
        dut.iloc[6, SOURCE_COLUMNS.index("DUT_NO")] = 1
        dut.iloc[6, SOURCE_COLUMNS.index("PART_ID")] = 1

    with pytest.raises(LionV2FormatError, match="Duplicate"):
        LionV2Reader([]).parse_frames(
            tmp_path / "F10001" / "F10001_1.xls",
            summary_frame=summary,
            statistics_frame=statistics,
            dut_frame=dut,
        )


def test_unapproved_text_invalid_marker_fails_closed(tmp_path):
    summary, statistics, dut = _source_frames("F10001", "1")
    dut.iloc[5, SOURCE_COLUMNS.index("IR_35V")] = "OVER"
    with pytest.raises(LionV2FormatError, match="unapproved text marker"):
        LionV2Reader([]).parse_frames(
            tmp_path / "F10001" / "F10001_1.xls",
            summary_frame=summary,
            statistics_frame=statistics,
            dut_frame=dut,
        )


def test_unapproved_non_numeric_spec_fails_closed(tmp_path):
    summary, statistics, dut = _source_frames("F10001", "1")
    dut.iloc[2, SOURCE_COLUMNS.index("VF_10A")] = "UNKNOWN"
    with pytest.raises(LionV2FormatError, match="finite numeric specification"):
        LionV2Reader([]).parse_frames(
            tmp_path / "F10001" / "F10001_1.xls",
            summary_frame=summary,
            statistics_frame=statistics,
            dut_frame=dut,
        )


def test_metadata_and_pass_bin_conflicts_fail_closed(tmp_path):
    summary, statistics, dut = _source_frames("F10001", "1")
    summary.iloc[2, 0] = "Lot Id:F99999--"
    with pytest.raises(LionV2FormatError, match="Lot identity mismatch"):
        LionV2Reader([]).parse_frames(
            tmp_path / "F10001" / "F10001_1.xls",
            summary_frame=summary,
            statistics_frame=statistics,
            dut_frame=dut,
        )

    summary, statistics, dut = _source_frames("F10001", "1")
    summary.iloc[2, 0] = "Lot Id:F10001---"
    with pytest.raises(LionV2FormatError, match="exactly the approved"):
        LionV2Reader([]).parse_frames(
            tmp_path / "F10001" / "F10001_1.xls",
            summary_frame=summary,
            statistics_frame=statistics,
            dut_frame=dut,
        )

    summary, statistics, dut = _source_frames("F10001", "1")
    dut.iloc[6, SOURCE_COLUMNS.index("PASSFG")] = True
    with pytest.raises(LionV2FormatError, match="PASSFG conflicts"):
        LionV2Reader([]).parse_frames(
            tmp_path / "F10001" / "F10001_1.xls",
            summary_frame=summary,
            statistics_frame=statistics,
            dut_frame=dut,
        )


def test_detection_is_structural_and_unknown_files_fail_closed(tmp_path):
    _, _, dut = _source_frames("F10001", "1")
    assert LionV2Reader.matches_approved_structure(dut.iloc[:5])

    invalid = dut.iloc[:5].copy()
    invalid.iloc[0, SOURCE_COLUMNS.index("DUT_NO")] = "PART_INDEX"
    assert not LionV2Reader.matches_approved_structure(invalid)

    unknown = tmp_path / "F10001_1.xls"
    unknown.write_bytes(b"not an OLE workbook")
    assert not LionV2Reader.can_read(str(unknown))
    with pytest.raises(ValueError, match="未知或不受支持"):
        detect_lion_format(str(unknown))


def _structure_preview(parameters):
    columns = list(APPROVED_PARAMETER_SCHEMAS["DATA2_15"])
    _, _, dut = _source_frames("F10001", "1")
    prefix_width = len(SOURCE_COLUMNS) - len(columns)
    rows = dut.iloc[:5, :prefix_width].values.tolist()
    parameter_rows = [
        list(parameters),
        ["V"] * len(parameters),
        [0.0] * len(parameters),
        [10.0] * len(parameters),
        [None] * len(parameters),
    ]
    return pd.DataFrame(
        [prefix + suffix for prefix, suffix in zip(rows, parameter_rows)]
    )


def test_detection_accepts_only_exact_ordered_approved_parameter_schemas():
    assert tuple(PARAMETERS) == APPROVED_PARAMETER_SCHEMAS["DATA2_15"]
    assert tuple(F0122A1_PARAMETERS) == APPROVED_PARAMETER_SCHEMAS["F0122A1_14"]
    assert LionV2Reader.matches_approved_structure(_structure_preview(PARAMETERS))
    assert LionV2Reader.matches_approved_structure(
        _structure_preview(F0122A1_PARAMETERS)
    )

    unknown_count = F0122A1_PARAMETERS + ["UNAPPROVED_EXTRA"]
    unknown_name = F0122A1_PARAMETERS.copy()
    unknown_name[5] = "IR_950V"
    unknown_order = F0122A1_PARAMETERS.copy()
    unknown_order[5], unknown_order[6] = unknown_order[6], unknown_order[5]

    assert not LionV2Reader.matches_approved_structure(
        _structure_preview(unknown_count)
    )
    assert not LionV2Reader.matches_approved_structure(
        _structure_preview(unknown_name)
    )
    assert not LionV2Reader.matches_approved_structure(
        _structure_preview(unknown_order)
    )


def test_same_lot_spec_conflict_fails_closed(tmp_path):
    first = _standard_lot(tmp_path, "F10001", "1", vf_10a_upper=2.0)
    second = _standard_lot(tmp_path, "F10001", "2", vf_10a_upper=2.5)
    with pytest.raises(ValueError, match="内部规格不一致"):
        create_batch_lot({"first": first, "second": second})


def test_multi_lot_end_to_end_emits_combined_data_and_per_lot_specs(tmp_path):
    lot_a = create_batch_lot(
        {"a": _standard_lot(tmp_path, "F10001", "1", vf_10a_upper=2.0)}
    )
    lot_b = create_batch_lot(
        {"b": _standard_lot(tmp_path, "F20002", "1", vf_10a_upper=2.5)}
    )

    outputs = generate_lion_run_csvs([lot_a, lot_b], str(tmp_path / "output"))
    assert set(outputs) == {"cleaned", "yield", "specs"}
    assert set(outputs["specs"]) == {"F10001", "F20002"}

    cleaned = pd.read_csv(outputs["cleaned"])
    yield_data = pd.read_csv(outputs["yield"])
    assert len(cleaned) == 6
    assert set(cleaned["Lot_ID"]) == {"F10001", "F20002"}
    assert len(yield_data) == 2
    assert set(yield_data["Good_die"]) == {2}

    spec_limits = {}
    for lot_id, path in outputs["specs"].items():
        spec = pd.read_csv(path, header=None)
        assert spec.shape == (4, 17)
        assert spec.iloc[0].tolist() == ["Parameter", "TEST_NUM"] + PARAMETERS
        assert spec.iloc[:, 0].tolist() == [
            "Parameter",
            "UNIT",
            "LIMIT_LOW",
            "LIMIT_HIGH",
        ]
        vf_column = spec.iloc[0].tolist().index("VF_10A")
        spec_limits[lot_id] = float(spec.iloc[3, vf_column])
    assert spec_limits == {"F10001": 2.0, "F20002": 2.5}


def test_mixed_lion_versions_fail_closed(tmp_path):
    v2_lot = create_batch_lot({"v2": _standard_lot(tmp_path, "F10001", "1")})
    v1_lot = create_batch_lot({"v1": _standard_lot(tmp_path, "F20002", "1")})
    v1_lot.source_format = LION_V1_FORMAT
    with pytest.raises(ValueError, match="不同格式版本"):
        create_combined_lot([v2_lot, v1_lot])


def test_v1_output_orchestration_keeps_legacy_generator_path(tmp_path, monkeypatch):
    old_lot = create_batch_lot({"old": _standard_lot(tmp_path, "F10001", "1")})
    old_lot.source_format = LION_V1_FORMAT
    expected = {"cleaned": "old-cleaned", "yield": "old-yield", "spec": "old-spec"}

    monkeypatch.setattr(
        StandardCSVGenerator,
        "generate_standard_csvs",
        lambda self, lot, output_dir: expected,
    )
    assert generate_lion_run_csvs([old_lot], str(tmp_path)) == expected


def test_source_format_constant_is_propagated(tmp_path):
    lot = create_batch_lot({"one": _standard_lot(tmp_path, "F10001", "1")})
    assert lot.source_format == LION_V2_FORMAT
    assert create_combined_lot([lot]).source_format == LION_V2_FORMAT
