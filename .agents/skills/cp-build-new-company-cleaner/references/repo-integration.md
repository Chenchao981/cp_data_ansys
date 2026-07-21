# Repository Integration Map

## Default production locations

- Reader: `cp_data_processor/readers/<module>_reader.py`
- Adapter: `cp_data_processor/readers/company_adapters/<module>_adapter.py`
- Optional processor: a thin company entry point that composes `CompanyCleaningPipeline`
- Configuration: `cp_data_processor/readers/company_adapters/company_config.py`
- Registration: `cp_data_processor/readers/company_adapters/company_registry.py`
- Tests: the owning module test package or `cp_data_processor/tests/`

## Rules

1. Inspect actual interfaces before moving staging files.
2. Reuse `BaseReader`, `BaseCompanyAdapter`, `CPLot`, `CPWafer`, `CPParameter`, `StandardLotValidator`, and `StandardCSVGenerator`.
3. Keep company parsing in Reader/Adapter modules and shared contract logic company-neutral.
4. Do not add an LLM SDK, prompt, Skill file, raw sample, or onboarding report to packages listed by `packaging/create_frontend_release.py`.
5. Keep HH/JT/Lion/Guoyu on their current mature paths until golden-sample evidence supports migration.

After validation returns `PASS`, use the GUI, chart, and release Skills in that order.
