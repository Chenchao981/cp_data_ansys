"""Deterministic tools for onboarding a new CP wafer-fab format."""

from .contracts import load_profile, validate_profile
from .output_validator import validate_output_contract
from .profiler import build_sample_profile
from .scaffold import create_cleaner_scaffold

__all__ = [
    "build_sample_profile",
    "create_cleaner_scaffold",
    "load_profile",
    "validate_output_contract",
    "validate_profile",
]
