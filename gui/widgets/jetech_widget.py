#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JeTech公司数据分析界面组件
集成JT专用数据处理流程和图表生成
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


def get_desktop_path():
    """获取用户桌面路径"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def generate_jt_output_folder_name(input_dir):
    """生成JT输出文件夹名称：JT_Analysis_YYYYMMDD_HHMMSS"""
    try:
        # 从输入目录名称提取信息
        input_path = Path(input_dir)
        folder_name = input_path.name
        
        # 尝试从文件夹名称中提取标识信息
        if "jt" in folder_name.lower() or "jetech" in folder_name.lower():
            prefix = folder_name
        else:
            prefix = "JT_Analysis"
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 组合文件夹名称
        output_folder_name = f"{prefix}_{timestamp}"
        
        # 确保文件夹名称是有效的Windows文件名
        import re
        output_folder_name = re.sub(r'[<>:"/\\|?*]', '_', output_folder_name)
        
        return output_folder_name
        
    except Exception as e:
        logger.error(f"生成JT输出文件夹名称失败: {e}")
        # 备用方案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"JT_Analysis_{timestamp}"


class JTDataProcessingThread(QThread):
    """JeTech数据处理后台线程"""
    progress_updated = pyqtSignal(str)  # 进度更新信号
    finished = pyqtSignal(bool, str)    # 完成信号(成功/失败, 消息)
    
    def __init__(self, input_dir, output_dir, operation_type):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.operation_type = operation_type  # 'clean' 或 'generate'
    
    def run(self):
        """执行JT数据处理"""
        try:
            if self.operation_type == 'clean':
                self._process_jt_data()
            elif self.operation_type == 'generate':
                self._generate_jt_charts()
        except Exception as e:
            logger.error(f"JT数据处理失败: {e}")
            self.finished.emit(False, f"JT处理失败: {str(e)}")
    
    def _process_jt_data(self):
        """处理JT数据"""
        self.progress_updated.emit("🔍 正在扫描JT Excel文件...")
        
        # 查找Excel文件
        input_path = Path(self.input_dir)
        
        excel_files = []
        excel_files.extend(list(input_path.rglob("*.xlsx")))
        excel_files.extend(list(input_path.rglob("*.xls")))
        excel_files.extend(list(input_path.rglob("*.XLSX")))
        excel_files.extend(list(input_path.rglob("*.XLS")))
        
        excel_files = list(set(excel_files))  # 去重
        
        self.progress_updated.emit(f"📁 发现 {len(excel_files)} 个JT Excel文件")
        
        if not excel_files:
            self.finished.emit(False, "未找到JT Excel文件(.xlsx或.xls)\n请确保选择的文件夹或其子文件夹中包含JT Excel数据文件")
            return
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        self.progress_updated.emit(f"📁 JT输出文件夹已创建: {self.output_dir}")
        
        # 调用JT主处理器
        self.progress_updated.emit("🧹 正在处理JT Excel数据...")
        
        try:
            # 导入JT处理模块
            from jt_data_processor.jt_main_processor import process_jt_files
            
            # 处理JT数据 - 使用正确的函数名称
            self.progress_updated.emit("📊 调用JT数据处理器...")
            result = process_jt_files(
                input_paths=self.input_dir,
                output_dir=self.output_dir,
                pass_bin=1  # 默认合格bin为1
            )
            
            # 检查处理结果
            if result and isinstance(result, dict):
                lot_id = result.get('lot_id', 'Unknown')
                wafer_count = result.get('wafer_count', 0)
                total_chips = result.get('total_chip_count', 0)
                param_count = result.get('parameter_count', 0)
                output_files = result.get('output_files', [])
                
                self.progress_updated.emit("✅ JT数据处理完成！")
                success_msg = f"成功处理JT数据：\n" \
                             f"- 批次ID: {lot_id}\n" \
                             f"- 晶圆数: {wafer_count}\n" \
                             f"- 芯片总数: {total_chips}\n" \
                             f"- 参数数: {param_count}\n" \
                             f"- 输出文件: {len(output_files)}个"
                
                self.finished.emit(True, success_msg)
            else:
                self.finished.emit(False, "JT数据处理返回结果异常，请检查输入数据格式")
                
        except ImportError as ie:
            logger.error(f"JT模块导入失败: {ie}")
            self.progress_updated.emit("❌ JT处理模块导入失败...")
            self.finished.emit(False, f"无法导入JT处理模块: {str(ie)}\n请确保jt_data_processor模块可用")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"JT数据处理失败: {e}")
            
            # 检查是否是xlrd版本问题
            if "xlrd" in error_msg and "version" in error_msg:
                self.progress_updated.emit("❌ Excel文件读取库版本不兼容...")
                self.finished.emit(False, 
                    f"Excel文件读取失败，依赖版本问题：\n{error_msg}\n\n"
                    f"解决方案：\n"
                    f"1. 升级xlrd: pip install xlrd>=2.0.1\n"
                    f"2. 或安装openpyxl: pip install openpyxl\n"
                    f"3. 将.xls文件转换为.xlsx格式")
            elif "JT格式数据验证失败" in error_msg:
                self.progress_updated.emit("❌ JT数据格式验证失败...")
                self.finished.emit(False, 
                    f"JT数据格式验证失败，可能原因：\n"
                    f"1. Excel文件格式不正确\n"
                    f"2. 缺少必要的工作表（如DUT_DATA）\n"
                    f"3. 文件损坏或正在被其他程序使用\n\n"
                    f"建议：\n"
                    f"- 检查Excel文件是否完整\n"
                    f"- 确保文件未被其他程序打开\n"
                    f"- 尝试将.xls转换为.xlsx格式")
            else:
                self.progress_updated.emit(f"❌ JT数据处理过程中出现错误: {str(e)}")
                self.finished.emit(False, f"JT数据处理失败: {str(e)}")
    
    def _generate_jt_charts(self):
        """生成JT图表"""
        self.progress_updated.emit("📊 正在初始化JT图表生成器...")
        
        # 检查是否存在必要的数据文件
        output_path = Path(self.output_dir)
        cleaned_files = list(output_path.glob("*_cleaned_*.csv"))
        spec_files = list(output_path.glob("*_spec_*.csv"))
        yield_files = list(output_path.glob("*_yield_*.csv"))
        
        self.progress_updated.emit(f"📋 检查数据文件: {len(cleaned_files)}个清洗文件, {len(spec_files)}个规格文件, {len(yield_files)}个良率文件")
        
        if not (cleaned_files and spec_files and yield_files):
            self.finished.emit(False, f"缺少必要的数据文件进行图表生成:\n" +
                              f"清洗文件: {len(cleaned_files)}个\n" +
                              f"规格文件: {len(spec_files)}个\n" +
                              f"良率文件: {len(yield_files)}个\n" +
                              f"请先完成JT数据清洗")
            return
        
        try:
            # 导入JT图表生成器
            import sys
            project_root = str(Path(__file__).parent.parent.parent)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from jt_chart_generator import main as generate_jt_charts
            
            # 切换到输出目录（JT图表生成器期望在当前工作目录找到CSV文件）
            original_cwd = os.getcwd()
            try:
                os.chdir(self.output_dir)
                self.progress_updated.emit("📈 正在调用JT图表生成器...")
                
                # 生成JT图表
                generate_jt_charts()
                
                # 检查生成的HTML文件
                html_files = list(Path('.').glob("*.html"))
                self.progress_updated.emit(f"✅ 生成了 {len(html_files)} 个HTML图表文件")
                
                self.progress_updated.emit("🎉 JT图表生成完成！")
                chart_msg = f"JT图表生成成功：\n" \
                           f"- HTML图表文件: {len(html_files)}个\n" \
                           f"- 保存位置: {self.output_dir}"
                
                self.finished.emit(True, chart_msg)
                
            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)
                
        except ImportError as ie:
            logger.error(f"JT图表生成器导入失败: {ie}")
            self.progress_updated.emit("⚠️ 尝试使用备用JT图表生成方法...")
            try:
                # 备用方案：使用前端图表模块
                from frontend.charts.yield_chart import YieldChart
                from frontend.charts.boxplot_chart import BoxplotChart
                
                yield_chart_files = []
                boxplot_chart_files = []
                
                # 生成良率图表
                self.progress_updated.emit("📈 正在生成JT良率分析图表...")
                yield_chart = YieldChart(data_dir=self.output_dir)
                if yield_chart.load_data():
                    yield_chart_files = yield_chart.save_all_charts(output_dir=self.output_dir)
                    self.progress_updated.emit(f"✅ JT良率图表生成完成: {len(yield_chart_files)} 个文件")
                else:
                    self.progress_updated.emit("⚠️ JT良率图表数据加载失败")
                
                # 生成箱体图表
                self.progress_updated.emit("📦 正在生成JT箱体统计图表...")
                boxplot_chart = BoxplotChart(data_dir=self.output_dir)
                if boxplot_chart.load_data():
                    boxplot_chart_files = boxplot_chart.save_all_charts(output_dir=self.output_dir)
                    self.progress_updated.emit(f"✅ JT箱体图表生成完成: {len(boxplot_chart_files)} 个文件")
                else:
                    self.progress_updated.emit("⚠️ JT箱体图表数据加载失败")
                
                total_files = len(yield_chart_files) + len(boxplot_chart_files)
                if total_files > 0:
                    self.progress_updated.emit("🎉 JT图表生成完成（备用方法）！")
                    self.finished.emit(True, f"使用备用方法成功生成 {total_files} 个JT交互式HTML图表")
                else:
                    self.finished.emit(False, "JT图表生成失败：无法加载数据或生成图表")
                
            except Exception as e2:
                logger.error(f"JT备用图表生成方法失败: {e2}")
                self.finished.emit(False, f"JT图表生成失败: {str(e2)}")
                
        except Exception as e:
            logger.error(f"JT图表生成失败: {e}")
            self.finished.emit(False, f"JT图表生成失败: {str(e)}")


class JeTechWidget(QWidget):
    """JeTech公司数据分析界面组件"""
    
    def __init__(self):
        super().__init__()
        self.input_dir = ""
        self.output_dir = ""
        self.processing_thread = None
        self.init_ui()
        self.set_default_paths()
    
    def set_default_paths(self):
        """设置默认路径"""
        # 优先使用测试数据目录，如果存在的话
        test_data_path = "D:\\cp_data_ansys\\data\\C145889.00"
        if os.path.exists(test_data_path):
            self.input_path_edit.setText(test_data_path)
            self.input_dir = test_data_path
            self.input_path_edit.setPlaceholderText("JT测试数据已加载，可直接开始处理...")
        else:
            # 备用方案：使用桌面路径
            desktop_path = get_desktop_path()
            self.input_path_edit.setText(desktop_path)
            self.input_dir = desktop_path
            
        # 输出目录使用桌面
        desktop_path = get_desktop_path()
        self.output_path_edit.setText(desktop_path)
    
    def init_ui(self):
        """初始化JeTech界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title_label = QLabel("🏭 Jetech 数据分析")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # 输入文件夹选择
        input_layout = QHBoxLayout()
        input_label = QLabel("📁 数据文件夹:")
        input_label.setMinimumWidth(125)
        input_label.setFont(QFont("", 12))
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择包含JT Excel数据文件的文件夹...")
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
        self.output_path_edit.setPlaceholderText("将自动创建以JT_Analysis+时间戳命名的文件夹...")
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
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.clean_btn.clicked.connect(self.start_cleaning)
        self.clean_btn.setEnabled(True)
        
        self.generate_btn = QPushButton("📊 生成图表")
        self.generate_btn.setMinimumHeight(60)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
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
                font-size: 14px;
            }
        """)
        main_layout.addWidget(self.status_text)
        
        # 连接输入路径变化事件
        self.input_path_edit.textChanged.connect(self.on_input_path_changed)
    
    def browse_input_dir(self):
        """浏览输入目录"""
        start_dir = get_desktop_path()
        dir_path = QFileDialog.getExistingDirectory(self, "选择JT数据文件夹", start_dir)
        if dir_path:
            self.input_dir = dir_path
            self.input_path_edit.setText(dir_path)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        start_dir = get_desktop_path()
        dir_path = QFileDialog.getExistingDirectory(self, "选择JT输出文件夹", start_dir)
        if dir_path:
            self.output_path_edit.setText(dir_path)
    
    def on_input_path_changed(self):
        """输入路径变化时的处理"""
        has_input = bool(self.input_path_edit.text().strip())
        self.clean_btn.setEnabled(has_input)
        self.input_dir = self.input_path_edit.text().strip() if has_input else ""
    
    def start_cleaning(self):
        """开始JT数据清洗"""
        if not self.input_dir:
            QMessageBox.warning(self, "警告", "请先选择JT数据文件夹！")
            return
        
        # 生成输出文件夹名称
        base_output_dir = self.output_path_edit.text().strip() or get_desktop_path()
        folder_name = generate_jt_output_folder_name(self.input_dir)
        self.output_dir = os.path.join(base_output_dir, folder_name)
        
        # 确保输出目录存在
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.log_message(f"📁 JT输出文件夹已创建/确认: {self.output_dir}")
        except Exception as e:
            self.log_message(f"❌ 创建JT输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"创建JT输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始JT数据清洗流程...")
        self.log_message(f"📁 JT输入目录: {self.input_dir}")
        self.log_message(f"📁 JT输出目录: {self.output_dir}")
        self.set_processing_state(True)
        
        # 启动后台处理线程
        self.processing_thread = JTDataProcessingThread(
            self.input_dir, self.output_dir, 'clean'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_cleaning_finished)
        self.processing_thread.start()
    
    def start_generating(self):
        """开始生成JT图表"""
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先完成JT数据清洗或指定有效的输出文件夹！")
            return
        
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_message(f"❌ 确认/创建JT输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"确认/创建JT输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始JT图表生成流程...")
        self.set_processing_state(True)
        
        # 启动后台处理线程
        self.processing_thread = JTDataProcessingThread(
            self.input_dir, self.output_dir, 'generate'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_generating_finished)
        self.processing_thread.start()
    
    def on_cleaning_finished(self, success, message):
        """JT数据清洗完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            self.generate_btn.setEnabled(True)
            QMessageBox.information(self, "成功", f"JT数据清洗完成！\n{message}\n\n输出文件夹: {self.output_dir}")
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"JT数据清洗失败！\n{message}")
    
    def on_generating_finished(self, success, message):
        """JT图表生成完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            self.log_message(f"📁 JT图表保存位置: {self.output_dir}")
            
            # 询问是否打开输出文件夹
            reply = QMessageBox.question(
                self, "完成", 
                f"JT图表生成完成！\n{message}\n\n是否打开输出文件夹查看结果？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.open_output_folder()
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"JT图表生成失败！\n{message}")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        if self.output_dir and os.path.exists(self.output_dir):
            try:
                if sys.platform == "win32":
                    os.startfile(self.output_dir)
                elif sys.platform == "darwin":
                    os.system(f'open "{self.output_dir}"')
                else:
                    os.system(f'xdg-open "{self.output_dir}"')
            except Exception as e:
                logger.error(f"打开JT输出文件夹失败: {e}")
                QMessageBox.warning(self, "警告", f"无法打开JT输出文件夹: {e}")
    
    def set_processing_state(self, is_processing):
        """设置处理状态"""
        self.clean_btn.setEnabled(not is_processing and bool(self.input_dir))
        self.generate_btn.setEnabled(not is_processing and bool(self.output_dir))
        self.input_browse_btn.setEnabled(not is_processing)
        self.output_browse_btn.setEnabled(not is_processing)
        
        # 显示/隐藏进度条
        if is_processing:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
        else:
            self.progress_bar.setVisible(False)
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        logger.info(f"JT界面: {message}")
        
        # 滚动到底部
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())