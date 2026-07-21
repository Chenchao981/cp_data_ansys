---
name: cp-profile-new-company-format
description: Profile desensitized CP raw files for a previously unsupported wafer fab in F:\cp_data_ansys and produce a sanitized, reviewable format dossier. Use for file signature, encoding, sheet/header/data-boundary discovery, metadata and standard-field mapping, parameter/unit/spec detection, pass-bin questions, invalid-value rules, duplicate Die and retest policy, and the human approval gate before cleaner implementation.
---

# Profile A New CP Format

## Boundary

Work only in the backend development plane. Do not modify production Readers, GUI code, company registration, charts, or packaging during this stage. Keep samples and generated reports outside Git.

## Workflow

1. Read `README.md`, `docs/architecture.md`, `docs/data-contracts.md`, `docs/company-integration.md`, and `docs/technical-debt.md`.
2. Collect 3-5 representative desensitized wafers from at least two lots when available. Record user-provided filename rules for product, lot, and wafer identity.
3. Create a case directory outside the repository or under an ignored temporary path.
4. Run:

   ```powershell
   python -m devtools.cp_onboarding profile --input <sample_paths> --output <case_dir>\sample-profile.json
   ```

5. Copy `assets/format-profile.template.json` and `assets/mapping-review.template.tsv` into the case directory. Fill observations as `fact`, `assumption`, or `question`.
6. Compare multiple files for invariant structure. Use file signatures and content fingerprints; do not trust extensions, directory names, or one sample alone.
7. Identify metadata, `X`, `Y`, `Seq`, `Bin`, parameter boundaries, units, lower/upper limits, test conditions, footer/summary rows, invalid markers, retest rows, and duplicate coordinates.
8. Run `python -m devtools.cp_onboarding validate-profile --profile <format-profile.json>`.
9. Stop at the human approval gate. Set `approval.status` to `approved` only after every critical item is confirmed and `unresolved_critical_items` is empty.

## Required Outputs

- `sample-profile.json`
- `format-profile.json`
- `mapping-review.tsv`
- `profile-report.md` with facts, assumptions, questions, risks, and recommended integration boundary

The next stage is `$cp-build-new-company-cleaner`.
