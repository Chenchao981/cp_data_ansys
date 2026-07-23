"""Per-user recent input and output locations for the multi-company GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PyQt5.QtCore import QSettings, QStandardPaths

from gui.theme import THEME_SETTINGS_APPLICATION, THEME_SETTINGS_ORGANIZATION


PATH_SETTINGS_PREFIX = "paths"


def get_desktop_path() -> str:
    """Return the Windows known Desktop location, including redirected desktops."""

    known_desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    candidates = [known_desktop, str(Path.home() / "Desktop"), str(Path.home())]
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().is_dir():
            return str(Path(candidate).expanduser())
    return str(Path.home())


def _as_string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _existing_source_directory(source: str | Path | None) -> Path | None:
    if not source:
        return None
    candidate = Path(str(source).strip().strip('"')).expanduser()
    if candidate.is_file():
        candidate = candidate.parent
    return candidate if candidate.is_dir() else None


class RecentPathPreferences:
    """Persist one company's last paths in the current Windows user profile."""

    def __init__(
        self,
        company_id: str,
        *,
        settings: QSettings | None = None,
        default_directory: str | Path | None = None,
    ) -> None:
        normalized_id = str(company_id).strip().casefold()
        if not normalized_id or "/" in normalized_id or "\\" in normalized_id:
            raise ValueError(f"Invalid company id: {company_id!r}")

        self.company_id = normalized_id
        self.settings = settings or QSettings(
            THEME_SETTINGS_ORGANIZATION,
            THEME_SETTINGS_APPLICATION,
        )
        requested_default = Path(default_directory).expanduser() if default_directory else None
        self.default_directory = (
            requested_default
            if requested_default is not None and requested_default.is_dir()
            else Path(get_desktop_path())
        )

    def _key(self, name: str) -> str:
        return f"{PATH_SETTINGS_PREFIX}/{self.company_id}/{name}"

    def initial_input_sources(self) -> tuple[str, ...]:
        """Return the complete saved selection, or the Desktop fallback."""

        sources = _as_string_list(self.settings.value(self._key("input_sources"), []))
        paths = [Path(source).expanduser() for source in sources]
        if paths and all(path.exists() for path in paths):
            directories = [path for path in paths if path.is_dir()]
            zip_files = [
                path
                for path in paths
                if path.is_file() and path.suffix.casefold() == ".zip"
            ]
            if (len(directories) == 1 and len(paths) == 1) or len(zip_files) == len(paths):
                return tuple(str(path) for path in paths)
        return (str(self.default_directory),)

    def input_start_directory(
        self, current_sources: Sequence[str | Path] = ()
    ) -> str:
        """Return an existing directory for opening the input-source selector."""

        saved = _existing_source_directory(
            self.settings.value(self._key("input_directory"), "")
        )
        for source in current_sources:
            directory = _existing_source_directory(source)
            if directory is not None:
                is_default_fallback = directory == self.default_directory
                if not is_default_fallback or saved is None:
                    return str(directory)

        return str(saved or self.default_directory)

    def output_directory(self) -> str:
        """Return the saved output parent, or the Desktop fallback."""

        saved = _existing_source_directory(
            self.settings.value(self._key("output_directory"), "")
        )
        return str(saved or self.default_directory)

    def output_start_directory(self, current_path: str | Path | None = None) -> str:
        """Return an existing directory for opening the output selector."""

        current = _existing_source_directory(current_path)
        return str(current) if current is not None else self.output_directory()

    def remember_input_sources(self, sources: Sequence[str | Path]) -> None:
        """Save the accepted source selection and its containing directory."""

        normalized = [
            str(Path(str(source).strip().strip('"')).expanduser())
            for source in sources
            if str(source).strip().strip('"')
        ]
        if not normalized:
            return

        self.settings.setValue(self._key("input_sources"), normalized)
        directory = _existing_source_directory(normalized[0])
        if directory is not None:
            self.settings.setValue(self._key("input_directory"), str(directory))
        self.settings.sync()

    def remember_output_directory(self, directory: str | Path) -> None:
        """Save the selected output parent for the next application run."""

        text = str(directory).strip().strip('"')
        if not text:
            return
        self.settings.setValue(
            self._key("output_directory"),
            str(Path(text).expanduser()),
        )
        self.settings.sync()
