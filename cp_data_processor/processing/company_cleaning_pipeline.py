"""Deterministic backend pipeline for future wafer-fab integrations.

Existing HH, JT, Lion, and Guoyu GUI workflows remain on their mature paths.
New company modules can use this service after their format profile has been
approved and their Reader/Adapter have passed validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Type

from cp_data_processor.data_models.cp_data import CPLot
from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.readers.company_adapters.base_company_adapter import (
    BaseCompanyAdapter,
)
from cp_data_processor.validation.standard_lot import StandardLotValidator


@dataclass(frozen=True)
class CompanyCleaningRequest:
    """Inputs needed by a deterministic company cleaning run."""

    company_code: str
    file_paths: Sequence[str]
    output_dir: str
    pass_bin: int


@dataclass(frozen=True)
class CompanyCleaningResult:
    """Stable backend result returned to a CLI or GUI orchestration layer."""

    company_code: str
    lot: CPLot
    csv_paths: dict[str, str]
    source_files: tuple[str, ...]


class CompanyCleaningPipeline:
    """Compose one Reader, one Adapter, validation, and standard CSV output."""

    def __init__(
        self,
        reader_class: Type[BaseReader],
        adapter: BaseCompanyAdapter,
        *,
        validator: StandardLotValidator | None = None,
        csv_generator: StandardCSVGenerator | None = None,
    ):
        if not issubclass(reader_class, BaseReader):
            raise TypeError("reader_class must inherit BaseReader")
        if not isinstance(adapter, BaseCompanyAdapter):
            raise TypeError("adapter must inherit BaseCompanyAdapter")
        self.reader_class = reader_class
        self.adapter = adapter
        self.validator = validator or StandardLotValidator()
        self.csv_generator = csv_generator or StandardCSVGenerator()

    def run(self, request: CompanyCleaningRequest) -> CompanyCleaningResult:
        company_code = request.company_code.strip().upper()
        if not company_code:
            raise ValueError("company_code is required")
        if self.adapter.company_name.upper() != company_code:
            raise ValueError(
                f"adapter company {self.adapter.company_name!r} does not match "
                f"request {company_code!r}"
            )
        if not request.file_paths:
            raise ValueError("at least one source file is required")
        if isinstance(request.pass_bin, bool) or not isinstance(request.pass_bin, int):
            raise ValueError("pass_bin must be an explicit integer")

        source_files = tuple(str(Path(path).resolve()) for path in request.file_paths)
        missing = [path for path in source_files if not Path(path).is_file()]
        if missing:
            raise FileNotFoundError(f"source files do not exist: {missing}")

        reader = self.reader_class(list(source_files), pass_bin=request.pass_bin)
        raw_lot = reader.read()
        standardized_lot = self.adapter.standardize_data(raw_lot)

        if standardized_lot.pass_bin is None:
            standardized_lot.pass_bin = request.pass_bin
        if standardized_lot.pass_bin != request.pass_bin:
            raise ValueError(
                "Reader/Adapter pass_bin does not match the approved request: "
                f"{standardized_lot.pass_bin!r} != {request.pass_bin!r}"
            )

        standardized_lot.update_counts()
        standardized_lot.combine_data_from_wafers()
        self.validator.validate_or_raise(standardized_lot)

        output_dir = str(Path(request.output_dir).resolve())
        csv_paths = self.csv_generator.generate_standard_csvs(
            standardized_lot, output_dir
        )
        return CompanyCleaningResult(
            company_code=company_code,
            lot=standardized_lot,
            csv_paths=csv_paths,
            source_files=source_files,
        )
