---
name: cp-onboard-new-company
description: Orchestrate the complete backend onboarding of a previously unsupported CP wafer fab in F:\cp_data_ansys. Use when a new fab or new stable raw-data format must move through sample profiling, human approval, deterministic Reader/Adapter development, CSV reconciliation, GUI integration, chart reuse, packaging, and packaged verification without putting Agent logic in the user runtime.
---

# Onboard A New CP Company

## Boundary

Act as the development-plane coordinator. Keep Agent prompts, format dossiers, raw samples, and development reports out of the production GUI and `.pyz`. The final GUI must call deterministic, reviewed Python code only.

Read `references/architecture-boundary.md` before changing production code.

## Required Stage Order

1. **Profile** — use `$cp-profile-new-company-format` to create a sanitized sample inventory and draft format profile.
2. **Approve** — stop until product, `Lot_ID`, `Wafer_ID`, coordinates, `Seq`, `Bin`, `pass_bin`, units, specs, invalid markers, duplicate Die, retest, and filtering rules are explicitly resolved.
3. **Build** — use `$cp-build-new-company-cleaner` only with an approved profile.
4. **Validate** — use `$cp-validate-new-company-cleaner`; require `PASS` plus real assertions before GUI work.
5. **Integrate** — use `$cp-gui-integration` to expose the stable cleaner to users. Do not expose Agent controls, confidence scores, or mapping editors.
6. **Chart** — use `$cp-chart-generation` to prove the standard cleaned/yield/spec outputs are reusable.
7. **Release** — use `$cp-release-packaging`; inspect and smoke-test the packaged `app.pyz`.

Do not skip a gate because sample output looks plausible. If a stage fails, return to the owning stage and keep later stages blocked.

## Source Of Truth

- Production backend: `cp_data_processor/` and any approved company Reader/Adapter/processor.
- Development backend: `devtools/cp_onboarding/`.
- Project workflow: `.agents/skills/` and `.codex/agents/`.
- User workflow: `gui/widgets/`.
- Business contract: `docs/data-contracts.md`.

## Handoff Record

Keep the onboarding case outside Git and record:

- current stage and status;
- format-profile path and approval identity;
- source row/Bin/wafer counts;
- generated code and tests;
- validation report path;
- GUI/chart/release evidence;
- unresolved risks.

Never commit source CP files, generated CSVs, reports containing measurements, logs, or customer-sensitive paths.
