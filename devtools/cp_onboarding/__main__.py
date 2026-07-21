"""Command-line interface for the new-company onboarding backend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import load_profile, validate_profile
from .output_validator import validate_output_contract
from .profiler import build_sample_profile
from .scaffold import create_cleaner_scaffold


def _write_json(path: str | Path, payload: object) -> None:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile = subparsers.add_parser("profile", help="profile desensitized samples")
    profile.add_argument("--input", nargs="+", required=True)
    profile.add_argument("--output", required=True)
    profile.add_argument("--max-files", type=int, default=20)
    profile.add_argument("--preview-rows", type=int, default=30)
    profile.add_argument("--preview-columns", type=int, default=80)

    validate = subparsers.add_parser("validate-profile", help="validate format profile")
    validate.add_argument("--profile", required=True)
    validate.add_argument("--require-approved", action="store_true")

    scaffold = subparsers.add_parser("scaffold", help="create staging cleaner files")
    scaffold.add_argument("--profile", required=True)
    scaffold.add_argument("--output-dir", required=True)

    output = subparsers.add_parser("validate-output", help="reconcile standard CSVs")
    output.add_argument("--profile", required=True)
    output.add_argument("--cleaned", required=True)
    output.add_argument("--yield-file", required=True)
    output.add_argument("--spec", required=True)
    output.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "profile":
        report = build_sample_profile(
            args.input,
            max_files=args.max_files,
            preview_rows=args.preview_rows,
            preview_columns=args.preview_columns,
        )
        _write_json(args.output, report)
        print(json.dumps({"status": "PASS", "files": report["file_count"]}))
        return 0

    profile = load_profile(args.profile)
    if args.command == "validate-profile":
        issues = validate_profile(profile, require_approved=args.require_approved)
        payload = {
            "status": "PASS" if not issues else "FAIL",
            "findings": [issue.__dict__ for issue in issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not issues else 1
    if args.command == "scaffold":
        created = create_cleaner_scaffold(profile, args.output_dir)
        print(json.dumps({"status": "PASS", "created": [str(path) for path in created]}))
        return 0
    if args.command == "validate-output":
        report = validate_output_contract(
            args.cleaned, args.yield_file, args.spec, profile
        )
        _write_json(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
