---
name: cp-build-new-company-cleaner
description: Build and integrate a deterministic backend cleaner for a new CP wafer fab in F:\cp_data_ansys from an explicitly approved JSON format profile. Use to generate a staging Reader, CompanyAdapter, processor, configuration fragment, and tests; implement conservative content detection, standard CPLot mapping, explicit pass_bin, units/specs, and cleaned/yield/spec output while keeping Agent logic out of the GUI and release runtime.
---

# Build A New CP Cleaner

## Approval Gate

Do not edit production code until the format dossier passes:

```powershell
python -m devtools.cp_onboarding validate-profile --profile <format-profile.json> --require-approved
```

Stop if the command fails. Read `references/repo-integration.md` before integration.

## Workflow

1. Check Git status and keep raw samples/output outside Git.
2. Generate a staging scaffold outside the production package:

   ```powershell
   python -m devtools.cp_onboarding scaffold --profile <format-profile.json> --output-dir <empty_staging_dir>
   ```

3. Treat every generated `NotImplementedError` and failing test as an intentional gate, not a TODO to suppress.
4. Implement the Reader from approved evidence. Preserve `file_path`, `source_lot_id`, original `Lot_ID`, `Wafer_ID`, `X`, `Y`, `Seq`, `Bin`, parameters, units, limits, and test conditions.
5. Put mapping and unit conversion in the Adapter. Use conservative content signatures and fail closed on ambiguity.
6. Use `CompanyCleaningPipeline` for future-company flows that fit Reader -> Adapter -> validation -> standard CSV. Add a company-specific batch processor only for justified discovery or merge behavior.
7. Replace the scaffold test with parser, metadata, parameter/spec, invalid-value, unit, pass-bin/yield, duplicate/retest, detection, and end-to-end assertions.
8. Run targeted tests and `git diff --check`.
9. Hand off to `$cp-validate-new-company-cleaner`; do not add a GUI page yet.

## Non-negotiable Evidence

- Every source Die row is retained or excluded by an approved rule.
- `Lot_ID + Wafer_ID` remains traceable in multi-lot output.
- `pass_bin` is explicit and used by yield calculations.
- Units and specs use the same approved conversion.
- Unknown or conflicting files fail with a readable error.
- Tests assert real business results and do not pass through skips or mocks alone.
