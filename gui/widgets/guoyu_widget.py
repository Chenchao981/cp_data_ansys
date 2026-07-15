"""国宇 FRD CP 数据清洗界面。"""

import logging
import os
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
logger = logging.getLogger(__name__)


def get_desktop_path() -> str:
    """获取当前 Windows 用户的桌面路径。"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def get_default_input_path() -> str:
    return get_desktop_path()


def get_default_output_path() -> str:
    return get_desktop_path()


class GuoyuDataProcessingThread(QThread):
    """后台执行国宇 FRD 标准 CSV 清洗。"""

    progress_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_dir: str, output_dir: str):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir

    def run(self):
        try:
            from guoyu_batch_processor import process_guoyu_directory

            self.progress_updated.emit("正在递归识别产品、批次及 EDS 数据目录...")
            result = process_guoyu_directory(self.input_dir, self.output_dir)
            files = result["files"]
            self.output_dir = result["output_dir"]
            self.progress_updated.emit(
                f"已识别产品 {result['product_name']}、{result['batch_count']} 个批次、"
                f"{result['wafer_count']} 片 Wafer。"
            )
            self.progress_updated.emit("已完成工程单位转换，明细参数均为纯数值。")
            self.progress_updated.emit("已生成 cleaned、yield、spec 标准 CSV。")
            message = "国宇FRD数据清洗完成：\n" + "\n".join(
                f"- {file_type}: {Path(file_path).name}"
                for file_type, file_path in files.items()
            )
            message += f"\n- 输出文件夹: {self.output_dir}"
            message += f"\n- 产品名称: {result['product_name']}"
            self.finished.emit(True, message)
        except Exception as exc:
            logger.error("国宇FRD数据清洗失败: %s", exc, exc_info=True)
            self.finished.emit(False, str(exc))


class GuoyuWidget(QWidget):
    """国宇 FRD 数据清洗操作页面。"""

    cockpit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.input_dir = ""
        self.output_dir = ""
        self.processing_thread = None
        self.init_ui()
        self.set_default_paths()

    def set_default_paths(self):
        """设置默认输入、输出路径。"""
        input_path = get_default_input_path()
        self.input_path_edit.setText(input_path)
        self.input_dir = input_path
        self.output_path_edit.setText(get_default_output_path())

    def init_ui(self):
        """初始化国宇 FRD 清洗界面。"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        title_label = QLabel("国宇FRD数据清洗")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        input_layout = QHBoxLayout()
        input_label = QLabel("数据文件夹:")
        input_label.setMinimumWidth(125)
        input_label.setFont(QFont("", 12))
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择批次目录，或包含批次/EDS多层目录的产品目录...")
        self.input_path_edit.setMinimumHeight(35)
        self.input_path_edit.setFont(QFont("", 11))
        self.input_browse_btn = QPushButton("选择文件夹...")
        self.input_browse_btn.setMinimumHeight(35)
        self.input_browse_btn.setMinimumWidth(120)
        self.input_browse_btn.setFont(QFont("", 11))
        self.input_browse_btn.clicked.connect(self.browse_input_dir)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path_edit)
        input_layout.addWidget(self.input_browse_btn)
        main_layout.addLayout(input_layout)

        output_layout = QHBoxLayout()
        output_label = QLabel("输出文件夹:")
        output_label.setMinimumWidth(125)
        output_label.setFont(QFont("", 12))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出父目录，将自动创建“首个批次号+流水号”文件夹...")
        self.output_path_edit.setMinimumHeight(35)
        self.output_path_edit.setFont(QFont("", 11))
        self.output_browse_btn = QPushButton("选择文件夹...")
        self.output_browse_btn.setMinimumHeight(35)
        self.output_browse_btn.setMinimumWidth(120)
        self.output_browse_btn.setFont(QFont("", 11))
        self.output_browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_btn)
        main_layout.addLayout(output_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)

        self.clean_btn = QPushButton("开始清洗数据")
        self.clean_btn.setMinimumHeight(60)
        self.clean_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #CCCCCC; }
            """
        )
        self.clean_btn.clicked.connect(self.start_cleaning)

        self.cockpit_btn = QPushButton("📊 CP Cockpit")
        self.cockpit_btn.setMinimumHeight(60)
        self.cockpit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #CCCCCC; }
            """
        )
        self.cockpit_btn.clicked.connect(
            lambda _checked=False: self.cockpit_requested.emit()
        )

        button_layout.addWidget(self.clean_btn)
        button_layout.addWidget(self.cockpit_btn)
        main_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        status_label = QLabel("处理状态:")
        status_label.setFont(QFont("", 12))
        main_layout.addWidget(status_label)

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(250)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("等待用户操作...")
        self.status_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
            """
        )
        main_layout.addWidget(self.status_text)

        self.input_path_edit.textChanged.connect(self.on_input_path_changed)

    def browse_input_dir(self):
        """浏览国宇单批次或产品级输入目录。"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择国宇FRD数据文件夹", self.input_dir or get_default_input_path()
        )
        if dir_path:
            self.input_path_edit.setText(dir_path)

    def browse_output_dir(self):
        """浏览标准 CSV 输出父目录。"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择国宇FRD输出父目录", self.output_path_edit.text() or get_default_output_path()
        )
        if dir_path:
            self.output_path_edit.setText(dir_path)

    def on_input_path_changed(self):
        """输入路径变化时更新清洗按钮状态。"""
        self.input_dir = self.input_path_edit.text().strip()
        self.clean_btn.setEnabled(bool(self.input_dir))

    def start_cleaning(self):
        """启动国宇 FRD 数据清洗。"""
        self.input_dir = self.input_path_edit.text().strip()
        self.output_dir = self.output_path_edit.text().strip()
        if not self.input_dir:
            QMessageBox.warning(self, "警告", "请先选择国宇FRD数据文件夹！")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先选择国宇FRD输出父目录！")
            return

        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.log_message(f"创建输出文件夹失败: {exc}")
            QMessageBox.critical(self, "错误", f"创建输出文件夹失败: {exc}")
            return

        self.log_message("开始国宇FRD数据清洗流程...")
        self.log_message(f"输入目录: {self.input_dir}")
        self.log_message(f"输出父目录: {self.output_dir}")
        self.set_processing_state(True)

        self.processing_thread = GuoyuDataProcessingThread(self.input_dir, self.output_dir)
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_cleaning_finished)
        self.processing_thread.start()

    def on_cleaning_finished(self, success: bool, message: str):
        """处理清洗完成信号。"""
        self.set_processing_state(False)
        if success and self.processing_thread:
            self.output_dir = self.processing_thread.output_dir
        self.log_message(message)
        if success:
            QMessageBox.information(
                self, "成功", f"{message}\n\n输出文件夹: {self.output_dir}"
            )
        else:
            QMessageBox.critical(self, "错误", f"国宇FRD数据清洗失败：\n{message}")

    def set_processing_state(self, is_processing: bool):
        """更新处理期间控件状态。"""
        self.clean_btn.setEnabled(not is_processing and bool(self.input_dir))
        self.cockpit_btn.setEnabled(not is_processing)
        self.input_browse_btn.setEnabled(not is_processing)
        self.output_browse_btn.setEnabled(not is_processing)
        self.input_path_edit.setEnabled(not is_processing)
        self.output_path_edit.setEnabled(not is_processing)
        self.progress_bar.setVisible(is_processing)
        if is_processing:
            self.progress_bar.setRange(0, 0)

    def log_message(self, message: str):
        """在处理状态区域记录带时间戳的信息。"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        logger.info("国宇FRD界面: %s", message)
