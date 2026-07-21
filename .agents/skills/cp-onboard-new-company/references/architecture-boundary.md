# Development Plane And User Plane

## Development plane

Use Agent + Skills to inspect a previously unsupported format, prepare a human review dossier, generate deterministic code, and validate it. Store reusable deterministic tooling under `devtools/cp_onboarding/`; it is excluded from the packaged application.

## Production backend

After approval, implement company-specific parsing in a Reader and mapping/unit logic in an Adapter. Compose future company flows with `CompanyCleaningPipeline` when the standard path fits. Keep compatibility processors only when directory discovery, multi-lot merging, or established vendor behavior requires them.

## User plane

The GUI displays only supported companies with finished cleaners. Users select a company and data source, run cleaning, and receive standard CSVs and charts. Unknown formats must fail closed with a readable error; the GUI must never call an Agent to guess production data.

## Migration rule

Do not rewrite HH, JT, Lion, or Guoyu solely to make the architecture look uniform. Move a mature path only after golden-sample regression proves identical business results.
