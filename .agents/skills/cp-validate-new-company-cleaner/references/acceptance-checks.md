# Acceptance Checks

## Facts

- Source file count, lot count, wafer count, row count, Bin counts, parameter count, and source specs.
- Output cleaned/yield/spec paths and schema.

## Calculations

- `Gross_die` equals retained Die rows per `Lot_ID + Wafer_ID`.
- `Good_die` equals rows whose `Bin == approved pass_bin`.
- `Yield = Good_die / Gross_die` within display rounding.
- Unit conversion is applied equally to measurements and specs.

## Rules

- Every removed row matches an approved filter.
- Missing coordinates/specs follow the approved explicit policy.
- Duplicate Die and retest behavior matches the approved policy.
- Original row-level `Lot_ID` remains intact in merged runs.

## Regression

- Existing HH/JT/Lion/Guoyu tests pass.
- Standard CSV chart loaders accept the new outputs.
- The packaged runtime contains deterministic cleaner code but no Agent or onboarding artifacts.
