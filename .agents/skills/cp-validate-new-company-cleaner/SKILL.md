---
name: cp-validate-new-company-cleaner
description: Validate and reconcile a newly implemented CP wafer-fab cleaner in F:\cp_data_ansys before GUI integration. Use for source-to-cleaned row accounting, Lot_ID + Wafer_ID traceability, explicit pass-bin yield checks, Bin and coordinate reconciliation, parameter/unit/spec comparison, invalid-value and duplicate/retest behavior, fail-closed detection, standard CSV contract tests, regression tests, and a formal PASS or FAIL handoff.
---

# Validate A New CP Cleaner

## Boundary

Act as an independent quality gate between backend implementation and user GUI integration. Do not weaken validation to make a cleaner pass. Read `references/acceptance-checks.md` before declaring readiness.

## Workflow

1. Re-run approved-profile validation.
2. Run parser and Adapter tests using synthetic fixtures plus local desensitized golden samples.
3. Run the cleaner into a new output directory; never overwrite a prior acceptance run.
4. Reconcile standard outputs:

   ```powershell
   python -m devtools.cp_onboarding validate-output `
     --profile <format-profile.json> `
     --cleaned <cleaned.csv> `
     --yield-file <yield.csv> `
     --spec <spec.csv> `
     --report <acceptance-report.json>
   ```

5. Compare source and output row counts, wafer identities, Bin counts, pass counts, parameter counts, units, lower/upper limits, invalid markers, duplicate coordinates, and retest decisions.
6. Test wrong-company, damaged, incomplete, and structurally conflicting files; require readable fail-closed errors.
7. Run relevant existing vendor regression tests and `git diff --check`.
8. Return exactly one readiness status: `PASS`, `FAIL`, or `BLOCKED`.

## PASS Gate

Return `PASS` only when automated output reconciliation passes, every approved rule has a real assertion, source rows are accounted for, no unit/spec ambiguity remains, and existing supported-company behavior is unchanged. Only `PASS` may proceed to `$cp-gui-integration`.
