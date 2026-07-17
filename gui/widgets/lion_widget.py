#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lion公司数据分析界面组件
集成Lion专用数据处理流程和图表生成
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import re
from typing import Sequence
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

from cp_data_processor.processing.archive_input import (
    ArchiveInputError,
    normalize_input_paths,
    prepare_archive_input,
)
from cp_data_processor.processing.output_naming import (
    build_output_folder_name,
    create_output_run_dir,
)
from gui.widgets.input_source_selector import select_input_sources


LION_EXCEL_SUFFIXES = (".xls", ".xlsx")


def get_desktop_path():
    """获取当前 Windows 用户的桌面路径。"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def get_default_input_path():
    return get_desktop_path()


def get_default_output_path():
    return get_desktop_path()


def extract_lion_lot_id_from_folder(input_dir):
    """从Lion输入文件夹中提取批次号（Lion公司的文件夹名称就是完整的lot_id）"""
    try:
        input_path = Path(input_dir)
        
        # Lion公司的文件夹名称就是lot_id，直接使用文件夹名称
        # 支持格式: F25130244, F25260021.01 等
        folder_name = input_path.name
        
        logger.info(f"从Lion文件夹名提取完整批次号: {folder_name}")
        return folder_name
        
    except Exception as e:
        logger.error(f"提取Lion批次号失败: {e}")
        return "Lion_Analysis"


def generate_lion_output_folder_name(input_dir, *, serial: str | None = None):
    """生成统一的“首个真实批次号_流水号”文件夹名称。"""
    return build_output_folder_name(
        extract_lion_lot_id_from_folder(input_dir),
        serial=serial,
    )


class LionDataProcessingThread(QThread):
    """Lion数据处理后台线程"""
    progress_updated = pyqtSignal(str)  # 进度更新信号
    finished = pyqtSignal(bool, str)    # 完成信号(成功/失败, 消息)
    output_dir_created = pyqtSignal(str)  # 输出目录创建信号
    
    def __init__(self, input_paths, base_output_dir, operation_type):
        super().__init__()
        self.input_paths = normalize_input_paths(input_paths)
        self.input_dir = str(self.input_paths[0])
        self.base_output_dir = base_output_dir  # 基础输出目录
        self.output_dir = None  # 实际输出目录，会在处理过程中确定
        self.operation_type = operation_type  # 'clean' 或 'generate'
    
    def run(self):
        """执行Lion数据处理"""
        try:
            if self.operation_type == 'clean':
                self._process_lion_data()
            elif self.operation_type == 'generate':
                self._generate_lion_charts()
        except Exception as e:
            logger.error(f"Lion数据处理失败: {e}")
            self.finished.emit(False, f"Lion处理失败: {str(e)}")
    
    def _process_lion_data(self):
        """处理Lion数据 - 直接调用完善的lion_batch_processor.py功能"""
        self.progress_updated.emit("🦁 启动Lion专用数据处理器...")

        try:
            with prepare_archive_input(
                self.input_paths,
                allowed_suffixes=LION_EXCEL_SUFFIXES,
                source_label="Lion Excel",
                progress=self.progress_updated.emit,
                temporary_prefix="cp_lion_zip_",
            ) as prepared_input:
                if prepared_input.archives:
                    self.progress_updated.emit(
                        f"📦 已准备 {len(prepared_input.archives)} 个Lion ZIP文件"
                    )
                self._process_lion_directory(prepared_input.directory)
        except ArchiveInputError as exc:
            logger.error("Lion ZIP输入准备失败: %s", exc)
            self.finished.emit(False, str(exc))
        except ImportError as exc:
            logger.error("Lion批次处理器导入失败: %s", exc)
            self.progress_updated.emit("❌ Lion批次处理器导入失败...")
            self.finished.emit(
                False,
                f"无法导入Lion批次处理器: {exc}\n请确保lion_batch_processor模块可用",
            )
        except Exception as exc:
            logger.error("Lion数据处理失败: %s", exc, exc_info=True)
            self.progress_updated.emit(f"❌ Lion数据处理失败: {exc}")
            self.finished.emit(False, f"Lion数据处理失败: {exc}")

    def _process_lion_directory(self, input_path: Path):
        """使用既有Lion处理器处理已准备好的目录。"""
        from lion_batch_processor import (
            create_combined_lot,
            discover_batch_files,
            process_lion_batch_files,
        )
        from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator

        base_output_path = Path(self.base_output_dir)

        try:
            self.progress_updated.emit(f"📁 输入目录: {input_path}")
            self.progress_updated.emit(f"📁 基础输出目录: {base_output_path}")
            
            # 1. 发现所有批次文件
            self.progress_updated.emit("🔍 扫描Lion批次文件...")
            batch_files = discover_batch_files(input_path)
            
            if not batch_files:
                self.finished.emit(False, "未发现任何Lion批次数据\n请确保选择的文件夹包含Lion Excel文件")
                return
            
            # 统计文件信息
            total_files = sum(len(files) for files in batch_files.values())
            self.progress_updated.emit(f"✅ 发现 {len(batch_files)} 个批次，共 {total_files} 个文件")
            
            # 2. 处理所有批次数据
            self.progress_updated.emit("🚀 开始批量处理Lion数据...")
            
            all_batch_lots = []
            success_count = 0
            failed_batches = []
            first_lot_id = None  # 记录第一个成功处理的批次的lot_id
            
            for batch_id, file_paths in batch_files.items():
                try:
                    self.progress_updated.emit(f"📦 处理批次: {batch_id} ({len(file_paths)} 个文件)")
                    
                    # 处理该批次的所有文件
                    batch_results = process_lion_batch_files(file_paths)
                    
                    if batch_results:
                        # 收集成功处理的CPLot对象
                        batch_lots = [lot for lot in batch_results.values() if lot is not None]
                        all_batch_lots.extend(batch_lots)
                        success_count += 1
                        
                        # 记录第一个成功处理的批次的lot_id，并创建输出文件夹
                        if first_lot_id is None and batch_lots:
                            first_lot_id = batch_lots[0].lot_id
                            
                            # 按公共规则创建首批次号+流水号输出文件夹
                            output_path = create_output_run_dir(
                                base_output_path,
                                first_lot_id,
                            )
                            self.output_dir = str(output_path)  # 设置实际输出目录
                            self.progress_updated.emit(f"📋 首个真实批次号: {first_lot_id}")
                            self.progress_updated.emit(f"📁 创建输出文件夹: {output_path}")
                            
                            # 发送输出目录创建信号
                            self.output_dir_created.emit(str(output_path))
                        
                        # 如果输出目录已确定，但还未设置到类变量
                        elif first_lot_id and not hasattr(self, 'output_path'):
                            output_path = Path(self.output_dir)
                        
                        self.progress_updated.emit(f"✅ 批次 {batch_id} 处理完成，获得 {len(batch_lots)} 个批次对象")
                    else:
                        failed_batches.append(batch_id)
                        self.progress_updated.emit(f"❌ 批次 {batch_id} 处理失败")
                        
                except Exception as e:
                    failed_batches.append(batch_id)
                    self.progress_updated.emit(f"❌ 批次 {batch_id} 处理异常: {str(e)}")
            
            if not all_batch_lots:
                self.finished.emit(False, f"所有批次处理失败\n失败批次: {', '.join(failed_batches)}")
                return
            
            # 3. 合并所有批次数据，使用第一个批次的lot_id
            self.progress_updated.emit("🔄 合并所有批次数据...")
            merged_lot = create_combined_lot(all_batch_lots)
            
            # 如果合并成功，将lot_id改为第一个文件的lot_id以用于文件命名
            if merged_lot and first_lot_id:
                merged_lot.lot_id = first_lot_id
                self.progress_updated.emit(f"📝 设置合并数据lot_id为: {first_lot_id}")
            
            if not merged_lot:
                self.finished.emit(False, "批次数据合并失败")
                return
            
            # 4. 生成标准CSV文件
            self.progress_updated.emit("📊 生成标准CSV文件...")
            csv_generator = StandardCSVGenerator()
            
            # 确保使用正确的输出路径
            final_output_path = Path(self.output_dir)
            csv_result = csv_generator.generate_standard_csvs(merged_lot, str(final_output_path))
            if csv_result:
                # 统计生成的文件
                csv_files = list(final_output_path.glob("*.csv"))
                
                self.progress_updated.emit("✅ Lion数据处理完成！")
                success_msg = f"Lion数据处理成功：\n" \
                             f"- 处理批次: {success_count} 个成功, {len(failed_batches)} 个失败\n" \
                             f"- 合并数据: {len(merged_lot.wafers)} 个晶圆\n" \
                             f"- 生成文件: {len(csv_files)} 个CSV文件\n" \
                             f"- 输出目录: {self.output_dir}"
                
                if failed_batches:
                    success_msg += f"\n- 失败批次: {', '.join(failed_batches)}"
                
                self.finished.emit(True, success_msg)
            else:
                self.finished.emit(False, "CSV文件生成失败")
                
        except Exception as e:
            logger.error(f"Lion数据处理失败: {e}")
            self.progress_updated.emit(f"❌ Lion数据处理失败: {str(e)}")
            self.finished.emit(False, f"Lion数据处理失败: {str(e)}")
    
    def _generate_lion_charts(self):
        """生成Lion图表"""
        self.progress_updated.emit("📊 正在初始化Lion图表生成器...")
        
        # 检查是否存在必要的数据文件
        output_path = Path(self.output_dir)
        cleaned_files = list(output_path.glob("*_cleaned_*.csv"))
        spec_files = list(output_path.glob("*_spec_*.csv"))
        yield_files = list(output_path.glob("*_yield_*.csv"))
        
        self.progress_updated.emit(f"📋 检查数据文件: {len(cleaned_files)}个清洗文件, {len(spec_files)}个规格文件, {len(yield_files)}个良率文件")
        self.progress_updated.emit(f"📁 检查目录: {self.output_dir}")
        
        # 列出目录中的所有文件用于调试
        all_files = list(output_path.glob("*"))
        self.progress_updated.emit(f"📋 目录中的所有文件: {[f.name for f in all_files if f.is_file()]}")
        
        if not (cleaned_files and spec_files and yield_files):
            self.finished.emit(False, f"缺少必要的数据文件进行图表生成:\n" +
                              f"清洗文件: {len(cleaned_files)}个\n" +
                              f"规格文件: {len(spec_files)}个\n" +
                              f"良率文件: {len(yield_files)}个\n" +
                              f"请先完成Lion数据清洗")
            return
        
        try:
            # 直接调用Lion专用图表生成器
            self.progress_updated.emit("📈 正在启动Lion专用图表生成器...")
            
            # 导入Lion图表生成器
            from lion.lion_chart_generator import main as generate_lion_charts
            
            # 调用Lion图表生成器，传入GUI创建的文件夹路径
            self.progress_updated.emit(f"🦁 调用Lion图表生成器，数据目录: {self.output_dir}")
            success = generate_lion_charts(data_dir=self.output_dir)
            
            if success:
                # 统计生成的HTML文件
                html_files = list(output_path.glob("*.html"))
                
                self.progress_updated.emit("🎉 Lion图表生成完成！")
                chart_msg = f"Lion图表生成成功：\n" \
                           f"- 使用Lion专用图表生成器\n" \
                           f"- 生成图表: {len(html_files)}个HTML文件\n" \
                           f"- 良率趋势图: Wafer良率分析\n" \
                           f"- 参数箱体图: 各测试参数分析\n" \
                           f"- 汇总图表: 综合分析报告\n" \
                           f"- 保存位置: {self.output_dir}"
                
                self.finished.emit(True, chart_msg)
            else:
                self.finished.emit(False, "Lion图表生成失败：Lion专用图表生成器返回失败状态")
                
        except Exception as e:
            logger.error(f"Lion图表生成失败: {e}")
            self.progress_updated.emit(f"❌ Lion图表生成过程中出现错误: {str(e)}")
            self.finished.emit(False, f"Lion图表生成失败: {str(e)}")
    
    def _standardize_lion_csv_columns(self, data_dir):
        """
        标准化Lion的CSV列名以匹配HH的格式
        转换: LotID -> Lot_ID, WaferID -> Wafer_ID
        """
        try:
            import pandas as pd
            
            # 确保data_dir是Path对象
            if isinstance(data_dir, str):
                data_dir = Path(data_dir)
            
            # 找到cleaned文件
            cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
            if not cleaned_files:
                logger.warning("⚠️ 未找到需要标准化的cleaned文件")
                logger.warning(f"在目录中查找: {data_dir}")
                # 列出目录中的所有CSV文件以便调试
                all_csv_files = list(data_dir.glob("*.csv"))
                logger.info(f"目录中的所有CSV文件: {[f.name for f in all_csv_files]}")
                return
            
            cleaned_file = cleaned_files[0]
            logger.info(f"🔄 标准化CSV列名: {cleaned_file.name}")
            
            # 读取CSV
            df = pd.read_csv(cleaned_file)
            logger.info(f"📊 CSV文件形状: {df.shape}")
            logger.info(f"📋 原始列名: {list(df.columns)}")
            
            # 检查并转换列名
            column_mapping = {
                'LotID': 'Lot_ID',
                'WaferID': 'Wafer_ID'
            }
            
            renamed_columns = {}
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    renamed_columns[old_name] = new_name
            
            if renamed_columns:
                df.rename(columns=renamed_columns, inplace=True)
                logger.info(f"✅ 列名转换: {renamed_columns}")
                logger.info(f"📋 转换后列名: {list(df.columns)}")
                
                # 保存标准化后的文件
                df.to_csv(cleaned_file, index=False)
                logger.info(f"✅ 标准化完成: {cleaned_file.name}")
            else:
                logger.info("ℹ️ 无需列名转换")
                logger.info(f"📋 当前列名已标准化: {list(df.columns)}")
                
        except Exception as e:
            logger.error(f"❌ 列名标准化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise


class LionWidget(QWidget):
    """Lion公司数据分析界面组件"""

    cockpit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("companyPage")
        self.input_dir = ""
        self.input_paths = []
        self._updating_input_path = False
        self.output_dir = ""
        self.processing_thread = None
        self.init_ui()
        self.set_default_paths()
    
    def set_default_paths(self):
        """设置 Lion 业务数据的默认输入、输出路径。"""
        self.set_input_sources([get_default_input_path()])
        self.output_path_edit.setText(get_default_output_path())
    
    def init_ui(self):
        """初始化Lion界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title_label = QLabel("🦁 立昂微CP数据分析")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setProperty("role", "pageTitle")
        main_layout.addWidget(title_label)
        
        # 输入文件夹或ZIP选择
        input_layout = QHBoxLayout()
        input_label = QLabel("📁 数据来源:")
        input_label.setMinimumWidth(125)
        input_label.setFont(QFont("", 12))
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText(
            "选择Lion数据文件夹，或选择一个/多个ZIP文件..."
        )
        self.input_path_edit.setMinimumHeight(35)
        self.input_path_edit.setFont(QFont("", 11))
        self.input_browse_btn = QPushButton("选择数据源...")
        self.input_browse_btn.setMinimumHeight(35)
        self.input_browse_btn.setMinimumWidth(125)
        self.input_browse_btn.setFont(QFont("", 11))
        self.input_browse_btn.clicked.connect(self.browse_input_sources)
        
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
        self.clean_btn.setProperty("role", "primary")
        self.clean_btn.clicked.connect(self.start_cleaning)
        self.clean_btn.setEnabled(True)
        
        self.cockpit_btn = QPushButton("📊 CP Cockpit")
        self.cockpit_btn.setMinimumHeight(60)
        self.cockpit_btn.setProperty("role", "success")
        self.cockpit_btn.clicked.connect(
            lambda _checked=False: self.cockpit_requested.emit()
        )
        self.cockpit_btn.setEnabled(True)
        
        button_layout.addWidget(self.clean_btn)
        button_layout.addWidget(self.cockpit_btn)
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
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("等待用户操作...")
        self.status_text.setProperty("role", "log")
        main_layout.addWidget(self.status_text)
        
        # 连接输入路径变化事件
        self.input_path_edit.textChanged.connect(self.on_input_path_changed)
    
    def browse_input_sources(self):
        """在同一窗口选择一个数据目录或一个/多个Lion ZIP文件。"""
        current_sources = self.get_input_sources()
        selected_paths = select_input_sources(
            self,
            title="选择Lion数据来源",
            start_path=current_sources[0] if current_sources else get_default_input_path(),
        )
        if selected_paths:
            self.set_input_sources(selected_paths)

    def set_input_sources(self, paths: Sequence[str | Path]):
        """设置输入来源并显示可编辑的多路径预览。"""
        self.input_paths = [str(path) for path in paths if str(path).strip()]
        self.input_dir = self.input_paths[0] if self.input_paths else ""
        self._updating_input_path = True
        try:
            self.input_path_edit.setText("; ".join(self.input_paths))
        finally:
            self._updating_input_path = False
        self.clean_btn.setEnabled(bool(self.input_paths))

    def get_input_sources(self):
        """读取输入框中的单路径或分号分隔多路径。"""
        return [
            item.strip().strip('"')
            for item in self.input_path_edit.text().split(";")
            if item.strip().strip('"')
        ]
    
    def browse_output_dir(self):
        """浏览输出父目录；处理时再创建批次号+流水号文件夹。"""
        start_dir = self.output_path_edit.text().strip() or get_default_output_path()
        parent_dir = QFileDialog.getExistingDirectory(self, "选择Lion输出文件夹的父目录", start_dir)
        if parent_dir:
            self.output_path_edit.setText(parent_dir)
    
    def on_input_path_changed(self):
        """输入路径变化时的处理"""
        if self._updating_input_path:
            return
        self.input_paths = self.get_input_sources()
        self.input_dir = self.input_paths[0] if self.input_paths else ""
        self.clean_btn.setEnabled(bool(self.input_paths))
    
    def start_cleaning(self):
        """开始Lion数据清洗"""
        input_sources = self.get_input_sources()
        if not input_sources:
            QMessageBox.warning(self, "警告", "请先选择Lion数据文件夹或ZIP文件！")
            return

        try:
            normalized_sources = normalize_input_paths(input_sources)
            for source in normalized_sources:
                if not source.exists():
                    raise ArchiveInputError(f"输入路径不存在: {source}")
                if source.is_file() and source.suffix.casefold() != ".zip":
                    raise ArchiveInputError(
                        f"不支持的输入文件类型（仅支持ZIP）: {source.name}"
                    )
        except ArchiveInputError as exc:
            QMessageBox.warning(self, "输入无效", str(exc))
            return

        base_output_dir = self.output_path_edit.text().strip() or get_default_output_path()

        self.log_message("🚀 开始Lion数据清洗流程...")
        if len(normalized_sources) == 1:
            self.log_message(f"📁 Lion输入来源: {normalized_sources[0]}")
        else:
            self.log_message(f"📦 已选择 {len(normalized_sources)} 个Lion ZIP文件")
            for source in normalized_sources:
                self.log_message(f"  - {source}")
        self.log_message(f"📁 基础输出目录: {base_output_dir}")
        self.log_message("📋 输出文件夹名称将根据第一个处理文件的lot_id确定")
        self.set_processing_state(True)
        
        # 启动后台处理线程，传入基础输出目录，让线程自己创建具体文件夹
        self.processing_thread = LionDataProcessingThread(
            normalized_sources, base_output_dir, 'clean'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_cleaning_finished)
        self.processing_thread.output_dir_created.connect(self.on_output_dir_created)
        self.processing_thread.start()
    
    def on_output_dir_created(self, output_dir):
        """处理输出目录创建事件"""
        self.output_dir = output_dir
        self.log_message(f"📁 实际输出目录已确定: {output_dir}")
    
    def start_generating(self):
        """开始生成Lion图表"""
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先完成Lion数据清洗或指定有效的输出文件夹！")
            return
        
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_message(f"❌ 确认/创建Lion输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"确认/创建Lion输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始Lion图表生成流程...")
        self.set_processing_state(True)
        
        # 启动后台处理线程（对于generate操作，直接使用已确定的output_dir）
        self.processing_thread = LionDataProcessingThread(
            self.input_paths or [self.input_dir], os.path.dirname(self.output_dir), 'generate'
        )
        self.processing_thread.output_dir = self.output_dir  # 直接设置输出目录
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_generating_finished)
        self.processing_thread.start()
    
    def on_cleaning_finished(self, success, message):
        """Lion数据清洗完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            QMessageBox.information(self, "成功", f"Lion数据清洗完成！\n{message}\n\n输出文件夹: {self.output_dir}")
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"Lion数据清洗失败！\n{message}")
    
    def on_generating_finished(self, success, message):
        """Lion图表生成完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            self.log_message(f"📁 Lion图表保存位置: {self.output_dir}")
            
            # 询问是否打开输出文件夹
            reply = QMessageBox.question(
                self, "完成", 
                f"Lion图表生成完成！\n{message}\n\n是否打开输出文件夹查看结果？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.open_output_folder()
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"Lion图表生成失败！\n{message}")
    
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
                logger.error(f"打开Lion输出文件夹失败: {e}")
                QMessageBox.warning(self, "警告", f"无法打开Lion输出文件夹: {e}")
    
    def set_processing_state(self, is_processing):
        """设置处理状态"""
        self.clean_btn.setEnabled(not is_processing and bool(self.input_dir))
        self.cockpit_btn.setEnabled(not is_processing)
        self.input_browse_btn.setEnabled(not is_processing)
        self.output_browse_btn.setEnabled(not is_processing)
        self.input_path_edit.setEnabled(not is_processing)
        self.output_path_edit.setEnabled(not is_processing)
        
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
        logger.info(f"Lion界面: {message}")
        
        # 滚动到底部
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
