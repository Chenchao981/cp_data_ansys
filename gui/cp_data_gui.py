#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 简化版GUI界面
高度自动化，操作简洁，三步完成分析流程
"""

import sys
import os
from pathlib import Path
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
            
            total_files = len(yield_files) + len(boxplot_files) if 'yield_files' in locals() and 'boxplot_files' in locals() else 0
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
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🔬 CP数据分析工具 - 简化版")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("🔬 CP数据分析工具")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 输入文件夹选择
        input_layout = QHBoxLayout()
        input_label = QLabel("📁 数据文件夹:")
        input_label.setMinimumWidth(100)
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择包含DCP数据文件的文件夹...")
        self.input_browse_btn = QPushButton("选择文件夹...")
        self.input_browse_btn.clicked.connect(self.browse_input_dir)
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path_edit)
        input_layout.addWidget(self.input_browse_btn)
        main_layout.addLayout(input_layout)
        
        # 输出文件夹选择
        output_layout = QHBoxLayout()
        output_label = QLabel("📁 输出文件夹:")
        output_label.setMinimumWidth(100)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("默认与输入文件夹相同...")
        self.output_browse_btn = QPushButton("选择文件夹...")
        self.output_browse_btn.clicked.connect(self.browse_output_dir)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_btn)
        main_layout.addLayout(output_layout)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.clean_btn = QPushButton("🧹 开始清洗数据")
        self.clean_btn.setMinimumHeight(50)
        self.clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
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
        self.clean_btn.setEnabled(False)
        
        self.generate_btn = QPushButton("📊 生成图表")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
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
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 状态显示区域
        status_label = QLabel("📋 处理状态:")
        main_layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setPlaceholderText("等待用户操作...")
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        main_layout.addWidget(self.status_text)
        
        # 连接输入路径变化事件
        self.input_path_edit.textChanged.connect(self.on_input_path_changed)
    
    def browse_input_dir(self):
        """浏览输入目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据文件夹")
        if dir_path:
            self.input_dir = dir_path
            self.input_path_edit.setText(dir_path)
            
            # 默认输出目录与输入目录相同
            if not self.output_dir:
                self.output_dir = dir_path
                self.output_path_edit.setText(dir_path)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if dir_path:
            self.output_dir = dir_path
            self.output_path_edit.setText(dir_path)
    
    def on_input_path_changed(self):
        """输入路径变化时的处理"""
        has_input = bool(self.input_path_edit.text().strip())
        self.clean_btn.setEnabled(has_input)
        
        if has_input and not self.output_path_edit.text().strip():
            # 自动设置输出路径
            self.output_dir = self.input_path_edit.text().strip()
            self.output_path_edit.setText(self.output_dir)
    
    def start_cleaning(self):
        """开始数据清洗"""
        if not self.input_dir:
            QMessageBox.warning(self, "警告", "请先选择数据文件夹！")
            return
        
        if not self.output_dir:
            self.output_dir = self.input_dir
            self.output_path_edit.setText(self.output_dir)
        
        self.log_message("🚀 开始数据清洗流程...")
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
            QMessageBox.warning(self, "警告", "请先完成数据清洗！")
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
            QMessageBox.information(self, "成功", f"数据清洗完成！\n{message}")
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
                f"图表生成完成！\n{message}\n\n是否打开输出文件夹？",
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