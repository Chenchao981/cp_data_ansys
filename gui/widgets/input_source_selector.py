"""Shared selector for one data folder or one/more ZIP archives."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PyQt5.QtCore import QDir, QModelIndex, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from gui.theme import set_widget_property


class InputSourceSelectionError(ValueError):
    """Raised when a GUI selection does not match the supported source modes."""


def validate_input_source_selection(
    paths: Sequence[str | Path],
) -> tuple[Path, ...]:
    """Accept one directory or one/more ZIP files, but never a mixed selection."""

    normalized: list[Path] = []
    seen: set[str] = set()
    for raw_path in paths:
        text = str(raw_path).strip().strip('"')
        if not text:
            continue
        path = Path(text).expanduser()
        key = str(path.resolve(strict=False)).casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(path)

    if not normalized:
        raise InputSourceSelectionError("请选择一个数据文件夹，或选择一个/多个ZIP文件")

    missing = [path for path in normalized if not path.exists()]
    if missing:
        raise InputSourceSelectionError(f"输入路径不存在: {missing[0]}")

    directories = [path for path in normalized if path.is_dir()]
    zip_files = [
        path
        for path in normalized
        if path.is_file() and path.suffix.casefold() == ".zip"
    ]
    unsupported = [
        path for path in normalized if path not in directories and path not in zip_files
    ]
    if unsupported:
        raise InputSourceSelectionError(
            f"不支持的输入文件类型（仅支持ZIP）: {unsupported[0].name}"
        )

    if directories and zip_files:
        raise InputSourceSelectionError(
            "不能同时选择文件夹和ZIP文件，请选择一个文件夹，或选择一个/多个ZIP文件"
        )
    if len(directories) > 1:
        raise InputSourceSelectionError(
            "一次只能选择一个数据文件夹；如需批量处理，请选择多个ZIP文件"
        )

    return tuple(normalized)


def resolve_start_directory(start_path: str | Path | None) -> Path:
    """Resolve an existing directory suitable for opening the selector."""

    desktop = Path.home() / "Desktop"
    fallback = desktop if desktop.is_dir() else Path.home()
    if not start_path:
        return fallback

    candidate = Path(str(start_path).strip().strip('"')).expanduser()
    if candidate.is_file():
        candidate = candidate.parent
    return candidate if candidate.is_dir() else fallback


class InputSourceDialog(QDialog):
    """One-window browser that selects a folder or multiple ZIP files."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "选择数据来源",
        start_path: str | Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("inputSourceDialog")
        self.selected_sources: tuple[Path, ...] = ()
        self.current_directory = resolve_start_directory(start_path)

        self.setWindowTitle(title)
        self.resize(860, 560)
        self.setMinimumSize(720, 460)
        self._build_ui()
        self._set_current_directory(self.current_directory)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        hint = QLabel(
            "选择 1 个数据文件夹，或按 Ctrl / Shift 多选 ZIP 文件。"
            "程序会自动判断并调用对应处理流程。"
        )
        hint.setWordWrap(True)
        hint.setProperty("role", "helpText")
        layout.addWidget(hint)

        navigation = QHBoxLayout()
        self.desktop_button = QPushButton("桌面")
        self.desktop_button.clicked.connect(self._go_desktop)
        self.up_button = QPushButton("上一级")
        self.up_button.clicked.connect(self._go_up)

        self.drive_combo = QComboBox()
        self.drive_combo.setMinimumWidth(85)
        for drive in QDir.drives():
            drive_path = drive.absoluteFilePath()
            self.drive_combo.addItem(drive_path, drive_path)
        self.drive_combo.activated.connect(self._go_drive)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入文件夹路径后按 Enter")
        self.path_edit.returnPressed.connect(self._go_to_typed_path)
        self.go_button = QPushButton("转到")
        self.go_button.clicked.connect(self._go_to_typed_path)

        navigation.addWidget(self.desktop_button)
        navigation.addWidget(self.up_button)
        navigation.addWidget(self.drive_combo)
        navigation.addWidget(self.path_edit, 1)
        navigation.addWidget(self.go_button)
        layout.addLayout(navigation)

        self.model = QFileSystemModel(self)
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.model.setNameFilters(["*.zip", "*.ZIP"])
        self.model.setNameFilterDisables(False)

        self.source_view = QTreeView()
        self.source_view.setModel(self.model)
        self.source_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.source_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.source_view.setRootIsDecorated(False)
        self.source_view.setItemsExpandable(False)
        self.source_view.setAlternatingRowColors(True)
        self.source_view.setSortingEnabled(True)
        self.source_view.sortByColumn(0, Qt.AscendingOrder)
        self.source_view.setColumnWidth(0, 360)
        self.source_view.doubleClicked.connect(self._open_item)
        self.source_view.selectionModel().selectionChanged.connect(
            self._update_selection_summary
        )
        layout.addWidget(self.source_view, 1)

        self.selection_summary = QLabel("尚未选择数据来源")
        self.selection_summary.setProperty("tone", "muted")
        layout.addWidget(self.selection_summary)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.current_folder_button = self.button_box.addButton(
            "使用当前文件夹", QDialogButtonBox.ActionRole
        )
        self.current_folder_button.clicked.connect(self._use_current_folder)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setText("确定")
        self.ok_button.setEnabled(False)
        self.button_box.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(self.button_box)

    def _set_current_directory(self, directory: Path) -> None:
        directory = directory.resolve()
        self.current_directory = directory
        self.path_edit.setText(str(directory))
        root_index = self.model.setRootPath(str(directory))
        self.source_view.setRootIndex(root_index)
        self.source_view.clearSelection()
        self._update_selection_summary()

        drive_root = directory.anchor.casefold()
        for index in range(self.drive_combo.count()):
            value_root = Path(str(self.drive_combo.itemData(index))).anchor.casefold()
            if value_root == drive_root:
                self.drive_combo.blockSignals(True)
                self.drive_combo.setCurrentIndex(index)
                self.drive_combo.blockSignals(False)
                break

    def _selected_paths(self) -> list[Path]:
        return [
            Path(self.model.filePath(index))
            for index in self.source_view.selectionModel().selectedRows(0)
        ]

    def _update_selection_summary(self, *_args) -> None:
        paths = self._selected_paths()
        if not paths:
            self.selection_summary.setText("尚未选择数据来源")
            set_widget_property(self.selection_summary, "tone", "muted")
            self.ok_button.setEnabled(False)
            return

        try:
            validated = validate_input_source_selection(paths)
        except InputSourceSelectionError as exc:
            self.selection_summary.setText(str(exc))
            set_widget_property(self.selection_summary, "tone", "error")
            self.ok_button.setEnabled(False)
            return

        if validated[0].is_dir():
            summary = f"将使用文件夹：{validated[0]}"
        else:
            summary = f"已选择 {len(validated)} 个 ZIP 文件"
        self.selection_summary.setText(summary)
        set_widget_property(self.selection_summary, "tone", "success")
        self.ok_button.setEnabled(True)

    def _go_desktop(self) -> None:
        self._set_current_directory(resolve_start_directory(None))

    def _go_up(self) -> None:
        parent = self.current_directory.parent
        if parent != self.current_directory:
            self._set_current_directory(parent)

    def _go_drive(self, index: int) -> None:
        drive_path = self.drive_combo.itemData(index)
        if drive_path:
            self._set_current_directory(Path(str(drive_path)))

    def _go_to_typed_path(self) -> None:
        typed_path = Path(self.path_edit.text().strip().strip('"')).expanduser()
        if typed_path.is_dir():
            self._set_current_directory(typed_path)
            return
        QMessageBox.warning(self, "路径无效", f"文件夹不存在：\n{typed_path}")

    def _open_item(self, index: QModelIndex) -> None:
        path = Path(self.model.filePath(index))
        if path.is_dir():
            self._set_current_directory(path)
        elif path.suffix.casefold() == ".zip":
            self.selected_sources = validate_input_source_selection([path])
            super().accept()

    def _use_current_folder(self) -> None:
        self.selected_sources = validate_input_source_selection(
            [self.current_directory]
        )
        super().accept()

    def accept(self) -> None:
        try:
            self.selected_sources = validate_input_source_selection(
                self._selected_paths()
            )
        except InputSourceSelectionError as exc:
            QMessageBox.warning(self, "选择无效", str(exc))
            return
        super().accept()


def select_input_sources(
    parent: QWidget,
    *,
    title: str,
    start_path: str | Path | None = None,
) -> tuple[Path, ...]:
    """Open the shared selector and return the accepted data sources."""

    dialog = InputSourceDialog(parent, title=title, start_path=start_path)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.selected_sources
    return ()
