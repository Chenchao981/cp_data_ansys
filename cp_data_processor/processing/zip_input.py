"""Backward-compatible HuaHong wrapper around the shared ZIP input layer."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from cp_data_processor.processing.archive_input import (
    ArchiveInputError,
    PreparedArchiveInput,
    discover_source_files,
    discover_zip_archives,
    normalize_input_paths,
    prepare_archive_input,
)


DATA_FILE_SUFFIXES = (".txt", ".dcp")
ZipInputError = ArchiveInputError
PreparedDCPInput = PreparedArchiveInput


def discover_data_files(directory: Path) -> tuple[Path, ...]:
    """Find candidate DCP/TXT files below a directory."""
    return discover_source_files(directory, DATA_FILE_SUFFIXES)


def _looks_like_hh_batch_name(name: str) -> bool:
    underscore_pos = name.find("_")
    at_pos = name.find("@", underscore_pos + 1)
    return underscore_pos > 0 and at_pos > underscore_pos + 1


@contextmanager
def prepare_dcp_input(
    input_paths: str | Path | Sequence[str | Path],
    progress=None,
) -> Iterator[PreparedDCPInput]:
    """Prepare HH DCP/TXT input using the shared vendor archive workflow."""

    with prepare_archive_input(
        input_paths,
        allowed_suffixes=DATA_FILE_SUFFIXES,
        source_label="华虹DCP/TXT",
        progress=progress,
        prefer_common_root=_looks_like_hh_batch_name,
        temporary_prefix="cp_hh_zip_",
    ) as prepared:
        yield prepared
