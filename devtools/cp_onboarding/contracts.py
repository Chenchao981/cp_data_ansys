"""Format-profile contract used by the new-company development workflow."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ProfileIssue:
    code: str
    message: str
    path: str
    severity: str = "error"


def load_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path).expanduser().resolve()
    with profile_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("format profile must be a JSON object")
    return data


def _get(data: Mapping[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _required_value(
    profile: Mapping[str, Any], path: str, issues: list[ProfileIssue]
) -> Any:
    value = _get(profile, path)
    if value is None or (isinstance(value, str) and not value.strip()):
        issues.append(ProfileIssue("required", "required value is missing", path))
    return value


def validate_profile(
    profile: Mapping[str, Any], *, require_approved: bool = False
) -> list[ProfileIssue]:
    """Return deterministic findings for a new-company format profile."""

    issues: list[ProfileIssue] = []
    if profile.get("schema_version") != 1:
        issues.append(
            ProfileIssue("schema_version", "schema_version must be 1", "schema_version")
        )

    company_code = _required_value(profile, "company.code", issues)
    _required_value(profile, "company.display_name", issues)
    _required_value(profile, "company.module_name", issues)
    _required_value(profile, "company.format_version", issues)
    if company_code and not re.fullmatch(r"[A-Z][A-Z0-9_]{1,15}", str(company_code)):
        issues.append(
            ProfileIssue(
                "company_code",
                "company code must be 2-16 uppercase letters, digits, or underscores",
                "company.code",
            )
        )

    for field in ("product", "lot_id", "wafer_id"):
        status_path = f"metadata_rules.{field}.status"
        status = _get(profile, status_path)
        if status not in {"approved", "unresolved"}:
            issues.append(
                ProfileIssue("status", "status must be approved or unresolved", status_path)
            )
        if require_approved and status != "approved":
            issues.append(
                ProfileIssue("approval", "metadata rule is not approved", status_path)
            )

    missing_coordinate_policy = _get(profile, "cleaning_rules.missing_coordinate_policy")
    for field in ("X", "Y", "Seq", "Bin"):
        status_path = f"standard_fields.{field}.status"
        status = _get(profile, status_path)
        allowed = {"approved", "unresolved"}
        if field in {"X", "Y"}:
            allowed.add("not_available")
        if status not in allowed:
            issues.append(
                ProfileIssue(
                    "status",
                    f"status must be one of {sorted(allowed)}",
                    status_path,
                )
            )
        if require_approved and status == "unresolved":
            issues.append(
                ProfileIssue("approval", "standard field is unresolved", status_path)
            )
        if require_approved and status == "not_available" and not missing_coordinate_policy:
            issues.append(
                ProfileIssue(
                    "missing_policy",
                    "missing coordinates require an approved handling policy",
                    "cleaning_rules.missing_coordinate_policy",
                )
            )

    pass_bin = _get(profile, "cleaning_rules.pass_bin")
    if pass_bin is None:
        issues.append(
            ProfileIssue("pass_bin", "pass_bin must be explicit", "cleaning_rules.pass_bin")
        )
    elif isinstance(pass_bin, bool) or not isinstance(pass_bin, int):
        issues.append(
            ProfileIssue(
                "pass_bin",
                "pass_bin must be an integer",
                "cleaning_rules.pass_bin",
            )
        )

    for path in (
        "cleaning_rules.invalid_value_policy",
        "cleaning_rules.duplicate_die_policy",
        "cleaning_rules.retest_policy",
        "cleaning_rules.source_row_filter",
        "parameters.discovery_rule",
        "parameters.unit_rule",
        "specifications.status",
        "detection.ambiguity_behavior",
    ):
        value = _required_value(profile, path, issues)
        if require_approved and value == "unresolved":
            issues.append(ProfileIssue("approval", "critical rule is unresolved", path))

    signatures = _get(profile, "detection.required_content_signatures")
    if not isinstance(signatures, list) or not signatures:
        issues.append(
            ProfileIssue(
                "detection",
                "at least one conservative content signature is required",
                "detection.required_content_signatures",
            )
        )

    approval_status = _get(profile, "approval.status")
    unresolved = _get(profile, "approval.unresolved_critical_items")
    if require_approved:
        if approval_status != "approved":
            issues.append(
                ProfileIssue(
                    "approval", "approval.status must be approved", "approval.status"
                )
            )
        _required_value(profile, "approval.reviewer", issues)
        _required_value(profile, "approval.reviewed_at", issues)
        if not isinstance(unresolved, list) or unresolved:
            issues.append(
                ProfileIssue(
                    "approval",
                    "unresolved_critical_items must be an empty list",
                    "approval.unresolved_critical_items",
                )
            )

    return issues
