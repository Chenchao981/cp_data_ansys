"""Lion 管芯数月度汇总界面。"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.path_preferences import (
    RecentPathPreferences,
    get_desktop_path as get_windows_desktop_path,
)


logger = logging.getLogger(__name__)


def get_desktop_path() -> str:
    return get_windows_desktop_path()


def get_default_input_path() -> str:
    return get_desktop_path()


def get_default_output_path() -> str:
    return get_desktop_path()


class LionDieCountProcessingThread(QThread):
    """Run the deterministic cleaner outside the GUI event loop."""

    progress_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_dir: str, output_parent: str):
        super().__init__()
        self.input_dir = input_dir
        self.output_parent = output_parent
        self.output_dir = ""
        self.output_file = ""

    def run(self):
        try:
            from lion.lion_die_count_processor import process_lion_die_count_directory

            result = process_lion_die_count_directory(
                self.input_dir,
                self.output_parent,
                progress=self.progress_updated.emit,
            )
            self.output_dir = str(result["output_dir"])
            self.output_file = str(result["output_file"])
            message = (
                "Lion管芯数清洗完成：\n"
                f"- 源文件: {result['file_count']} 个\n"
                f"- NCE品名: {result['product_count']} 个\n"
                f"- LOT: {result['lot_count']} 个\n"
                f"- Wafer记录: {result['wafer_count']} 条\n"
                f"- 输出文件: {Path(self.output_file).name}\n"
                f"- 输出文件夹: {self.output_dir}"
            )
            self.finished.emit(True, message)
        except Exception as exc:
            logger.error("Lion管芯数清洗失败: %s", exc, exc_info=True)
            self.finished.emit(False, str(exc))


class LionDieCountWidget(QWidget):
    """Lion 管芯数数据源、输出和日志页面。"""

    def __init__(self, path_preferences=None):
        super().__init__()
        self.setObjectName("companyPage")
        self.path_preferences = path_preferences or RecentPathPreferences(
            "lion_die_count"
        )
        self.input_dir = ""
        self.output_dir = ""
        self.processing_thread = None
        self.init_ui()
        self.set_default_paths()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        title_label = QLabel("lion-管芯数")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setProperty("role", "pageTitle")
        main_layout.addWidget(title_label)

        description = QLabel(
            "递归读取目录内 Lion .xlsx 报表，汇总为 NCE品名、LOT、Wafer、PASS、Good Die（源 DIE）。"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setProperty("role", "description")
        main_layout.addWidget(description)

        input_layout = QHBoxLayout()
        input_label = QLabel("数据源目录:")
        input_label.setMinimumWidth(125)
        input_label.setFont(QFont("", 12))
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择包含多个产品子目录的月度数据目录...")
        self.input_path_edit.setMinimumHeight(35)
        self.input_path_edit.setFont(QFont("", 11))
        self.input_browse_btn = QPushButton("选择文件夹...")
        self.input_browse_btn.setMinimumHeight(35)
        self.input_browse_btn.setMinimumWidth(125)
        self.input_browse_btn.clicked.connect(self.browse_input_dir)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path_edit)
        input_layout.addWidget(self.input_browse_btn)
        main_layout.addLayout(input_layout)

        output_layout = QHBoxLayout()
        output_label = QLabel("输出父目录:")
        output_label.setMinimumWidth(125)
        output_label.setFont(QFont("", 12))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出父目录，将自动创建“首个批次号+时间”文件夹...")
        self.output_path_edit.setMinimumHeight(35)
        self.output_path_edit.setFont(QFont("", 11))
        self.output_browse_btn = QPushButton("选择文件夹...")
        self.output_browse_btn.setMinimumHeight(35)
        self.output_browse_btn.setMinimumWidth(125)
        self.output_browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_btn)
        main_layout.addLayout(output_layout)

        self.clean_btn = QPushButton("开始清洗")
        self.clean_btn.setMinimumHeight(60)
        self.clean_btn.setProperty("role", "primary")
        self.clean_btn.clicked.connect(self.start_cleaning)
        main_layout.addWidget(self.clean_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        status_label = QLabel("处理日志:")
        status_label.setFont(QFont("", 12))
        main_layout.addWidget(status_label)
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(280)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("等待用户操作...")
        self.status_text.setProperty("role", "log")
        main_layout.addWidget(self.status_text)

        self.input_path_edit.textChanged.connect(self.on_input_path_changed)

    def set_default_paths(self):
        sources = self.path_preferences.initial_input_sources()
        self.input_path_edit.setText(sources[0] if sources else get_desktop_path())
        self.output_path_edit.setText(self.path_preferences.output_directory())

    def browse_input_dir(self):
        start_dir = self.path_preferences.input_start_directory(
            [self.input_path_edit.text().strip()]
        )
        selected = QFileDialog.getExistingDirectory(
            self, "选择 Lion管芯数月度数据目录", start_dir
        )
        if selected:
            self.input_path_edit.setText(selected)
            self.path_preferences.remember_input_sources([selected])

    def browse_output_dir(self):
        start_dir = self.path_preferences.output_start_directory(
            self.output_path_edit.text().strip()
        )
        selected = QFileDialog.getExistingDirectory(
            self, "选择 Lion管芯数输出父目录", start_dir
        )
        if selected:
            self.output_path_edit.setText(selected)
            self.path_preferences.remember_output_directory(selected)

    def on_input_path_changed(self):
        self.input_dir = self.input_path_edit.text().strip().strip('"')
        self.clean_btn.setEnabled(bool(self.input_dir))

    def start_cleaning(self):
        self.input_dir = self.input_path_edit.text().strip().strip('"')
        output_parent = self.output_path_edit.text().strip().strip('"')
        if not self.input_dir:
            QMessageBox.warning(self, "警告", "请先选择 Lion管芯数数据源目录！")
            return
        if not output_parent:
            QMessageBox.warning(self, "警告", "请先选择输出父目录！")
            return

        input_path = Path(self.input_dir).expanduser()
        output_path = Path(output_parent).expanduser()
        if not input_path.is_dir():
            QMessageBox.warning(self, "输入无效", f"数据源目录不存在: {input_path}")
            return
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            self.path_preferences.remember_input_sources([input_path])
            self.path_preferences.remember_output_directory(output_path)
        except Exception as exc:
            QMessageBox.critical(self, "错误", f"无法创建输出父目录: {exc}")
            return

        self.log_message("开始 Lion管芯数清洗流程...")
        self.log_message(f"数据源目录: {input_path}")
        self.log_message(f"输出父目录: {output_path}")
        self.set_processing_state(True)
        self.processing_thread = LionDieCountProcessingThread(
            str(input_path), str(output_path)
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_cleaning_finished)
        self.processing_thread.start()

    def on_cleaning_finished(self, success: bool, message: str):
        self.set_processing_state(False)
        if success and self.processing_thread:
            self.output_dir = self.processing_thread.output_dir
        self.log_message(message)
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "错误", f"Lion管芯数清洗失败：\n{message}")

    def set_processing_state(self, is_processing: bool):
        self.clean_btn.setEnabled(not is_processing and bool(self.input_dir))
        self.input_browse_btn.setEnabled(not is_processing)
        self.output_browse_btn.setEnabled(not is_processing)
        self.input_path_edit.setEnabled(not is_processing)
        self.output_path_edit.setEnabled(not is_processing)
        self.progress_bar.setVisible(is_processing)
        if is_processing:
            self.progress_bar.setRange(0, 0)

    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        logger.info("Lion管芯数界面: %s", message)
