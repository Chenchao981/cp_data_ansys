"""Backward-compatible HuaHong wrapper around the shared archive input layer."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from cp_data_processor.processing.archive_input import (
    ArchiveInputError,
    PreparedArchiveInput,
    discover_archives,
    discover_source_files,
    normalize_input_paths,
    prepare_archive_input,
    read_first_archive_data_member_head,
)


DATA_FILE_SUFFIXES = (".txt", ".dcp")
ARCHIVE_SUFFIXES = (".zip", ".7z")
ZipInputError = ArchiveInputError
PreparedDCPInput = PreparedArchiveInput


def discover_data_files(directory: Path) -> tuple[Path, ...]:
    """Find candidate DCP/TXT files below a directory."""
    return discover_source_files(directory, DATA_FILE_SUFFIXES)


def discover_dcp_archives(
    input_paths: str | Path | Sequence[str | Path],
) -> tuple[Path, ...]:
    """Find supported HH ZIP/7z archives in deterministic processing order."""

    return discover_archives(input_paths, ARCHIVE_SUFFIXES)


def read_first_dcp_member_head(
    archive: str | Path,
    *,
    max_bytes: int = 16384,
) -> tuple[str, bytes] | None:
    """Read a bounded head from the first HH data member in ZIP or 7z."""

    return read_first_archive_data_member_head(
        archive,
        allowed_suffixes=DATA_FILE_SUFFIXES,
        source_label="华虹DCP/TXT",
        max_bytes=max_bytes,
    )


# Historical import name used by existing callers and tests.
discover_zip_archives = discover_dcp_archives


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
        archive_suffixes=ARCHIVE_SUFFIXES,
        progress=progress,
        prefer_common_root=_looks_like_hh_batch_name,
        temporary_prefix="cp_hh_zip_",
    ) as prepared:
        yield prepared
