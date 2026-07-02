from __future__ import annotations

from pathlib import Path


def _dialog_root():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update()
    return root


def _initial_directory(candidate: str | Path | None) -> str:
    if candidate and Path(candidate).is_dir():
        return str(Path(candidate))
    desktop = Path.home() / "Desktop"
    return str(desktop if desktop.is_dir() else Path.home())


def pick_folder(initial_directory: str | Path | None = None) -> str | None:
    from tkinter import filedialog

    root = _dialog_root()
    try:
        selected = filedialog.askdirectory(
            parent=root,
            title="选择产品目录或 CP 批次目录",
            initialdir=_initial_directory(initial_directory),
            mustexist=True,
        )
        return selected or None
    finally:
        root.destroy()


def pick_table_file(initial_directory: str | Path | None = None) -> str | None:
    from tkinter import filedialog

    root = _dialog_root()
    try:
        selected = filedialog.askopenfilename(
            parent=root,
            title="选择要预览的表格文件",
            initialdir=_initial_directory(initial_directory),
            filetypes=(
                ("CP 与表格文件", "*.txt *.dcp *.csv *.xlsx *.xls"),
                ("CP 文本文件", "*.txt *.dcp"),
                ("CSV 文件", "*.csv"),
                ("Excel 文件", "*.xlsx *.xls"),
                ("所有文件", "*.*"),
            ),
        )
        return selected or None
    finally:
        root.destroy()
