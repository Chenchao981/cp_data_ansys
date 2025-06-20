#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 简化版GUI界面
高度自动化，操作简洁，三步完成分析流程
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFileDialog, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入项目模块
from clean_dcp_data import process_directory as clean_dcp_process_directory
from dcp_spec_extractor import generate_spec_file as extract_spec_main
from frontend.charts.yield_chart import YieldChart
from frontend.charts.boxplot_chart import BoxplotChart

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to keep track of the current file log handler
current_log_file_handler = None

def setup_file_logging(target_output_dir: str):
    """
    Sets up a file handler for logging to the specified output directory.
    Removes any existing custom file handler before adding a new one.
    """
    global current_log_file_handler
    root_logger = logging.getLogger()

    # Remove existing file handler if it exists
    if current_log_file_handler:
        root_logger.removeHandler(current_log_file_handler)
        current_log_file_handler.close()
        current_log_file_handler = None
        logger.info("Previous file log handler removed.")

    try:
        log_file_name = f"processing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path = Path(target_output_dir) / log_file_name

        # Create file handler
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the handler to the root logger
        root_logger.addHandler(file_handler)
        current_log_file_handler = file_handler
        logger.info(f"Logging to file: {log_file_path}")
    except Exception as e:
        logger.error(f"Failed to set up file logging to {target_output_dir}: {e}")


def get_desktop_path():
    """获取用户桌面路径"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def extract_lot_id_from_folder_name(folder_name: str) -> tuple[str, str]:
    """
    从标准格式的文件夹名称中提取 product_name 和 lot_id
    
    标准格式：NCETSG7120BAA_FA54-5342@203
    - product_name: _ 之前的部分 (NCETSG7120BAA)
    - lot_id: _ 后面到 @ 之间的部分 (FA54-5342)
    
    Args:
        folder_name: 文件夹名称，如 "NCETSG7120BAA_FA54-5342@203"
    
    Returns:
        tuple[str, str]: (product_name, lot_id)
        例如: ("NCETSG7120BAA", "FA54-5342")
    """
    # 所有批次都遵循标准格式，直接分割即可
    underscore_pos = folder_name.find('_')
    at_pos = folder_name.find('@')
    
    product_name = folder_name[:underscore_pos]
    lot_id = folder_name[underscore_pos + 1:at_pos]
    
    return product_name, lot_id

def extract_first_lot_id(directory_path):
    """从目录中的文件提取第一个批次号，优先使用文件夹名称规则"""
    try:
        input_path = Path(directory_path)
        
        # 优先使用文件夹名称提取规则
        folder_name = input_path.name
        product_name, lot_id = extract_lot_id_from_folder_name(folder_name)
        
        # 如果提取的lot_id与原始文件夹名不同，说明成功应用了规则
        if lot_id != folder_name:
            logger.info(f"从文件夹名 {folder_name} 提取到批次号: {lot_id}")
            return lot_id
        
        # 如果文件夹名称规则无效，尝试从文件内容提取
        logger.info(f"文件夹名称 {folder_name} 不符合提取规则，尝试从文件内容提取")
        
        # 搜索所有DCP文件
        dcp_files = []
        dcp_files.extend(list(input_path.rglob("*.txt")))
        dcp_files.extend(list(input_path.rglob("*.TXT")))
        dcp_files.extend(list(input_path.rglob("*.dcp")))
        dcp_files.extend(list(input_path.rglob("*.DCP")))
        
        if not dcp_files:
            return None
        
        # 尝试从第一个文件中提取批次号
        first_file = dcp_files[0]
        try:
            with open(first_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    # 从R2C2位置提取批次号（第二行第二列）
                    second_line = lines[1].strip()
                    logger.info(f"第二行内容: {second_line}")
                    
                    # DCP文件使用制表符分隔，先尝试制表符分割
                    if '\t' in second_line:
                        parts = second_line.split('\t')
                        logger.info(f"使用制表符分割，共{len(parts)}部分: {parts}")
                    else:
                        # 备用方案：使用空格分割
                        parts = second_line.split()
                        logger.info(f"使用空格分割，共{len(parts)}部分: {parts}")
                    
                    if len(parts) >= 2:
                        # 对于制表符分割的情况，批次号通常在最后一列
                        # 对于"Lot number\tFA54-5339-327A-250501@203"格式，批次号在索引2
                        if len(parts) >= 3 and parts[0].lower() in ['lot', 'lot number']:
                            lot_id_raw = parts[2] if len(parts) > 2 else parts[1]
                        else:
                            lot_id_raw = parts[1]  # R2C2位置的原始批次号
                            
                        logger.info(f"从文件 {first_file.name} 提取到原始批次号: {lot_id_raw}")
                        
                        # 应用新的提取规则到文件内容获取的批次号
                        file_product_name, file_extracted_lot_id = extract_lot_id_from_folder_name(lot_id_raw)
                        
                        # 如果文件内容的批次号符合提取规则，使用提取后的lot_id
                        if file_extracted_lot_id != lot_id_raw:
                            logger.info(f"从文件内容应用提取规则: {lot_id_raw} -> {file_extracted_lot_id}")
                            return file_extracted_lot_id
                        
                        # 否则去掉@后面的内容，保留完整的批次号
                        if '@' in lot_id_raw:
                            lot_id = lot_id_raw.split('@')[0]
                        else:
                            lot_id = lot_id_raw
                        
                        logger.info(f"处理后的批次号: {lot_id}")
                        return lot_id
        except Exception as e:
            logger.warning(f"无法从文件 {first_file} 提取批次号: {e}")
        
        # 最后尝试从文件夹名称中提取类似格式的批次号（保留原有逻辑作为备用）
        match = re.search(r'([A-Z]\d+\.\d+-[A-Z0-9]+-\d+-\d+)', folder_name)
        if match:
            return match.group(1)
        
        return None
        
    except Exception as e:
        logger.error(f"提取批次号失败: {e}")
        return None


def generate_output_folder_name(input_dir):
    """生成输出文件夹名称：批次号_YYYYMMDD_HHMMSS"""
    try:
        # 提取第一个批次号
        lot_id = extract_first_lot_id(input_dir)
        if not lot_id:
            lot_id = "CP_Analysis"
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 组合文件夹名称
        folder_name = f"{lot_id}_{timestamp}"
        
        # 确保文件夹名称是有效的Windows文件名
        folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
        
        return folder_name
        
    except Exception as e:
        logger.error(f"生成输出文件夹名称失败: {e}")
        # 备用方案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"CP_Analysis_{timestamp}"


class DataProcessingThread(QThread):
    """数据处理后台线程"""
    progress_updated = pyqtSignal(str)  # 进度更新信号
    finished = pyqtSignal(bool, str)    # 完成信号(成功/失败, 消息)
    
    def __init__(self, input_dir, output_dir, operation_type):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.operation_type = operation_type  # 'clean' 或 'generate'
    
    def run(self):
        """执行数据处理"""
        try:
            if self.operation_type == 'clean':
                self._clean_data()
            elif self.operation_type == 'generate':
                self._generate_charts()
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            self.finished.emit(False, f"处理失败: {str(e)}")
    
    def _clean_data(self):
        """清洗数据"""
        self.progress_updated.emit("🔍 正在扫描数据文件...")
        
        # 查找DCP文件 - 支持递归搜索子文件夹
        input_path = Path(self.input_dir)
        
        # 递归搜索所有.txt和.dcp文件
        dcp_files = []
        dcp_files.extend(list(input_path.rglob("*.txt")))  # 递归搜索.txt文件
        dcp_files.extend(list(input_path.rglob("*.TXT")))  # 递归搜索.TXT文件（大写）
        dcp_files.extend(list(input_path.rglob("*.dcp")))  # 递归搜索.dcp文件
        dcp_files.extend(list(input_path.rglob("*.DCP")))  # 递归搜索.DCP文件（大写）
        
        # 去重（防止重复文件）
        dcp_files = list(set(dcp_files))
        
        self.progress_updated.emit(f"📁 发现 {len(dcp_files)} 个DCP数据文件")
        
        if not dcp_files:
            self.finished.emit(False, "未找到DCP数据文件(.txt或.dcp)\n请确保选择的文件夹或其子文件夹中包含数据文件")
            return
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        self.progress_updated.emit(f"📁 输出文件夹已创建: {self.output_dir}")
        
        # 直接处理整个目录
        self.progress_updated.emit("🧹 正在处理所有数据文件...")
        
        try:
            # 调用process_directory函数处理整个目录
            result = clean_dcp_process_directory(
                directory_path=self.input_dir,
                output_dir=self.output_dir,
                outlier_method='iqr',
                convert_units=True
            )
            
            if result:
                self.progress_updated.emit("✅ 数据清洗完成！")
                self.finished.emit(True, f"成功处理 {len(dcp_files)} 个数据文件")
            else:
                self.finished.emit(False, "数据处理失败，请检查数据文件格式")
                
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            self.finished.emit(False, f"处理失败: {str(e)}")
    
    def _generate_charts(self):
        """生成图表"""
        self.progress_updated.emit("📊 正在初始化图表生成器...")
        
        try:
            yield_files = []
            boxplot_files = []
            summary_files = []
            
            # 生成良率图表
            self.progress_updated.emit("📈 正在生成良率分析图表...")
            yield_chart = YieldChart(data_dir=self.output_dir)
            if yield_chart.load_data():
                yield_files = yield_chart.save_all_charts(output_dir=self.output_dir)
                self.progress_updated.emit(f"✅ 良率图表生成完成: {len(yield_files)} 个文件")
            
            # 生成箱体图表
            self.progress_updated.emit("📦 正在生成箱体统计图表...")
            boxplot_chart = BoxplotChart(data_dir=self.output_dir)
            if boxplot_chart.load_data():
                boxplot_files = boxplot_chart.save_all_charts(output_dir=self.output_dir)
                self.progress_updated.emit(f"✅ 箱体图表生成完成: {len(boxplot_files)} 个文件")
            
            # 生成汇总箱体图表
            self.progress_updated.emit("📋 正在生成汇总箱体图表...")
            from frontend.charts.summary_chart import SummaryChart
            summary_chart = SummaryChart(data_dir=self.output_dir)
            if summary_chart.load_data():
                summary_file = summary_chart.save_summary_chart(output_dir=self.output_dir)
                if summary_file:
                    summary_files = [summary_file]
                    self.progress_updated.emit(f"✅ 汇总箱体图表生成完成: {summary_file}")
                else:
                    self.progress_updated.emit("⚠️ 汇总箱体图表生成失败")
            else:
                self.progress_updated.emit("⚠️ 汇总箱体图表数据加载失败")
            
            total_files = len(yield_files) + len(boxplot_files) + len(summary_files)
            self.progress_updated.emit("🎉 所有图表生成完成！")
            self.finished.emit(True, f"成功生成 {total_files} 个交互式HTML图表")
            
        except Exception as e:
            logger.error(f"图表生成失败: {e}")
            self.finished.emit(False, f"图表生成失败: {str(e)}")


class CPDataGUI(QMainWindow):
    """CP数据分析GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.input_dir = ""
        self.output_dir = ""
        self.processing_thread = None
        self.init_ui()
        self.set_default_paths()
    
    def set_default_paths(self):
        """设置默认路径为桌面"""
        desktop_path = get_desktop_path()
        self.input_path_edit.setText(desktop_path)
        self.input_dir = desktop_path
        # 输出路径暂时也设为桌面，实际使用时会创建子文件夹
        self.output_path_edit.setText(desktop_path)
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🔬 CP数据分析工具 - 简化版")
        self.setGeometry(100, 100, 1000, 750)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title_label = QLabel("🔬 CP数据分析工具")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 输入文件夹选择
        input_layout = QHBoxLayout()
        input_label = QLabel("📁 数据文件夹:")
        input_label.setMinimumWidth(125)
        input_label.setFont(QFont("", 12))
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择包含DCP数据文件的文件夹...")
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
        
        # 输出文件夹选择
        output_layout = QHBoxLayout()
        output_label = QLabel("📁 输出文件夹:")
        output_label.setMinimumWidth(125)
        output_label.setFont(QFont("", 12))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("将自动创建以批次号+时间戳命名的文件夹...")
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
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)
        
        self.clean_btn = QPushButton("🧹 开始清洗数据")
        self.clean_btn.setMinimumHeight(60)
        self.clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.clean_btn.clicked.connect(self.start_cleaning)
        self.clean_btn.setEnabled(True)  # 默认启用，因为有默认路径
        
        self.generate_btn = QPushButton("📊 生成图表")
        self.generate_btn.setMinimumHeight(60)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generating)
        self.generate_btn.setEnabled(False)
        
        button_layout.addWidget(self.clean_btn)
        button_layout.addWidget(self.generate_btn)
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 状态显示区域
        status_label = QLabel("📋 处理状态:")
        status_label.setFont(QFont("", 12))
        main_layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(250)
        self.status_text.setPlaceholderText("等待用户操作...")
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
            }
        """)
        main_layout.addWidget(self.status_text)
        
        # 连接输入路径变化事件
        self.input_path_edit.textChanged.connect(self.on_input_path_changed)
    
    def browse_input_dir(self):
        """浏览输入目录"""
        # 从桌面开始浏览
        start_dir = get_desktop_path()
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据文件夹", start_dir)
        if dir_path:
            self.input_dir = dir_path
            self.input_path_edit.setText(dir_path)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        # 从桌面开始浏览
        start_dir = get_desktop_path()
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹", start_dir)
        if dir_path:
            self.output_path_edit.setText(dir_path)
    
    def on_input_path_changed(self):
        """输入路径变化时的处理"""
        has_input = bool(self.input_path_edit.text().strip())
        self.clean_btn.setEnabled(has_input)
        self.input_dir = self.input_path_edit.text().strip() if has_input else ""
    
    def start_cleaning(self):
        """开始数据清洗"""
        if not self.input_dir:
            QMessageBox.warning(self, "警告", "请先选择数据文件夹！")
            return
        
        # 生成输出文件夹名称
        base_output_dir = self.output_path_edit.text().strip() or get_desktop_path()
        folder_name = generate_output_folder_name(self.input_dir)
        self.output_dir = os.path.join(base_output_dir, folder_name)
        
        # 确保输出目录存在
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.log_message(f"📁 输出文件夹已创建/确认: {self.output_dir}")
            # Setup file logging to the new output directory
            setup_file_logging(self.output_dir)
        except Exception as e:
            self.log_message(f"❌ 创建输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"创建输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始数据清洗流程...")
        self.log_message(f"📁 输入目录: {self.input_dir}")
        self.log_message(f"📁 输出目录: {self.output_dir}")
        self.set_processing_state(True)
        
        # 启动后台处理线程
        self.processing_thread = DataProcessingThread(
            self.input_dir, self.output_dir, 'clean'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_cleaning_finished)
        self.processing_thread.start()
    
    def start_generating(self):
        """开始生成图表"""
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先完成数据清洗或指定有效的输出文件夹！")
            return
        
        # Ensure output directory exists (it should, if cleaning was done, but good for standalone generation)
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            # Setup file logging to the output directory for chart generation
            # This ensures logs are captured even if only chart generation is run (e.g. on existing cleaned data)
            # or if the output_dir was changed manually (if GUI would allow)
            setup_file_logging(self.output_dir)
        except Exception as e:
            self.log_message(f"❌ 确认/创建输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"确认/创建输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始图表生成流程...")
        self.set_processing_state(True)
        
        # 启动后台处理线程
        self.processing_thread = DataProcessingThread(
            self.input_dir, self.output_dir, 'generate'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_generating_finished)
        self.processing_thread.start()
    
    def on_cleaning_finished(self, success, message):
        """数据清洗完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            self.generate_btn.setEnabled(True)
            QMessageBox.information(self, "成功", f"数据清洗完成！\n{message}\n\n输出文件夹: {self.output_dir}")
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"数据清洗失败！\n{message}")
    
    def on_generating_finished(self, success, message):
        """图表生成完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            self.log_message(f"📁 图表保存位置: {self.output_dir}")
            
            # 询问是否打开输出文件夹
            reply = QMessageBox.question(
                self, "完成", 
                f"图表生成完成！\n{message}\n\n输出文件夹: {self.output_dir}\n\n是否打开输出文件夹？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                os.startfile(self.output_dir)  # Windows系统打开文件夹
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"图表生成失败！\n{message}")
    
    def set_processing_state(self, processing):
        """设置处理状态"""
        self.clean_btn.setEnabled(not processing and bool(self.input_dir))
        self.generate_btn.setEnabled(not processing and bool(self.output_dir))
        self.progress_bar.setVisible(processing)
        
        if processing:
            self.progress_bar.setRange(0, 0)  # 无限进度条
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
    
    def log_message(self, message):
        """记录日志消息"""
        self.status_text.append(message)
        # 自动滚动到底部
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.End)
        self.status_text.setTextCursor(cursor)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("CP数据分析工具")
    app.setApplicationVersion("1.0")
    
    # 创建并显示主窗口
    window = CPDataGUI()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 