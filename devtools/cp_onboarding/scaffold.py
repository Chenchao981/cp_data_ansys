"""Generate a staging-only cleaner scaffold from an approved profile."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from .contracts import validate_profile


def _class_stem(module_name: str) -> str:
    return "".join(part.capitalize() for part in module_name.split("_"))


def _render(template: str, values: Mapping[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{([A-Z_]+)\}\}", result)))
    if unresolved:
        raise ValueError(f"unresolved template values: {', '.join(unresolved)}")
    return result


def create_cleaner_scaffold(
    profile: Mapping[str, Any], output_dir: str | Path
) -> list[Path]:
    issues = validate_profile(profile, require_approved=True)
    if issues:
        details = "; ".join(f"{item.path}: {item.message}" for item in issues)
        raise ValueError(f"approved profile validation failed: {details}")

    company = profile["company"]
    pass_bin = profile["cleaning_rules"]["pass_bin"]
    module_name = str(company["module_name"])
    output = Path(output_dir).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"staging destination is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    values = {
        "COMPANY_CODE": str(company["code"]),
        "COMPANY_NAME": str(company["display_name"]),
        "MODULE_NAME": module_name,
        "CLASS_STEM": _class_stem(module_name),
        "PASS_BIN": repr(pass_bin),
        "FORMAT_VERSION": str(company["format_version"]),
    }
    template_dir = Path(__file__).with_name("templates")
    outputs = {
        f"{module_name}_reader.py": "reader.py.tmpl",
        f"{module_name}_adapter.py": "adapter.py.tmpl",
        f"{module_name}_processor.py": "processor.py.tmpl",
        f"test_{module_name}_reader.py": "test_reader.py.tmpl",
        "company_config.fragment.py": "company_config.fragment.py.tmpl",
    }
    created: list[Path] = []
    for filename, template_name in outputs.items():
        template = (template_dir / template_name).read_text(encoding="utf-8")
        target = output / filename
        target.write_text(_render(template, values), encoding="utf-8")
        created.append(target)
    return created
