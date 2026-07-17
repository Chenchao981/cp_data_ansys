#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华虹公司数据分析界面组件
复用现有cp_data_gui.py的完整功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import re
from typing import Sequence
from zipfile import BadZipFile, ZipFile
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入项目模块
from clean_dcp_data import process_directory as clean_dcp_process_directory
from dcp_spec_extractor import generate_spec_file as extract_spec_main
from cp_data_processor.processing.zip_input import (
    ZipInputError,
    discover_zip_archives,
    normalize_input_paths,
    prepare_dcp_input,
)
from cp_data_processor.processing.output_naming import (
    OutputNamingError,
    build_output_folder_name,
    create_output_run_dir,
)
from frontend.charts.yield_chart import YieldChart
from frontend.charts.boxplot_chart import BoxplotChart
from gui.widgets.input_source_selector import select_input_sources

logger = logging.getLogger(__name__)


def get_desktop_path():
    """获取当前 Windows 用户的桌面路径。"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def get_default_input_path():
    return get_desktop_path()


def get_default_output_path():
    return get_desktop_path()


def extract_lot_id_from_folder_name(folder_name: str):
    """
    从标准格式的文件夹名称中提取 product_name 和 lot_id
    
    标准格式：NCETSG7120BAA_FA54-5342@203
    - product_name: _ 之前的部分 (NCETSG7120BAA)
    - lot_id: _ 后面到 @ 之间的部分 (FA54-5342)
    """
    underscore_pos = folder_name.find('_')
    at_pos = folder_name.find('@', underscore_pos + 1)

    if underscore_pos <= 0 or at_pos <= underscore_pos + 1:
        return folder_name, folder_name
    
    product_name = folder_name[:underscore_pos]
    lot_id = folder_name[underscore_pos + 1:at_pos]
    
    return product_name, lot_id


def extract_first_lot_id(directory_path):
    """从目录中的文件提取第一个批次号，优先使用文件夹名称规则"""
    try:
        input_path = Path(directory_path)
        
        # 优先使用文件夹名称提取规则
        folder_name = input_path.stem if input_path.is_file() else input_path.name
        product_name, lot_id = extract_lot_id_from_folder_name(folder_name)
        
        # 如果提取的lot_id与原始文件夹名不同，说明成功应用了规则
        if lot_id != folder_name:
            logger.info(f"从文件夹名 {folder_name} 提取到批次号: {lot_id}")
            return lot_id
        
        # 如果文件夹名称规则无效，尝试从文件内容提取
        logger.info(f"文件夹名称 {folder_name} 不符合提取规则，尝试从文件内容提取")
        
        # 搜索所有DCP文件
        dcp_files = []
        if input_path.is_dir():
            dcp_files.extend(list(input_path.rglob("*.txt")))
            dcp_files.extend(list(input_path.rglob("*.TXT")))
            dcp_files.extend(list(input_path.rglob("*.dcp")))
            dcp_files.extend(list(input_path.rglob("*.DCP")))
        
        dcp_files = sorted(set(dcp_files), key=lambda path: str(path).casefold())
        if not dcp_files:
            return None
        
        # 尝试从第一个文件中提取批次号
        first_file = dcp_files[0]
        try:
            with open(first_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    second_line = lines[1].strip()
                    
                    if '\t' in second_line:
                        parts = second_line.split('\t')
                    else:
                        parts = second_line.split()
                    
                    if len(parts) >= 2:
                        if len(parts) >= 3 and parts[0].lower() in ['lot', 'lot number']:
                            lot_id_raw = parts[2] if len(parts) > 2 else parts[1]
                        else:
                            lot_id_raw = parts[1]
                            
                        logger.info(f"从文件 {first_file.name} 提取到原始批次号: {lot_id_raw}")
                        
                        # 应用新的提取规则到文件内容获取的批次号
                        file_product_name, file_extracted_lot_id = extract_lot_id_from_folder_name(lot_id_raw)
                        
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
        
        # 最后尝试从文件夹名称中提取类似格式的批次号
        match = re.search(r'([A-Z]\d+\.\d+-[A-Z0-9]+-\d+-\d+)', folder_name)
        if match:
            return match.group(1)
        
        return None
        
    except Exception as e:
        logger.error(f"提取批次号失败: {e}")
        return None


def _extract_lot_id_from_dcp_text(text: str):
    """从华虹文件头提取真实批次号。"""
    lines = text.splitlines()
    if len(lines) < 2:
        return None

    parts = re.split(r"\s+", lines[1].strip())
    if len(parts) < 2:
        return None
    lowered = [part.casefold().rstrip(":") for part in parts]
    if lowered[0] == "lot" and len(parts) >= 3 and lowered[1] == "number":
        raw_lot_id = parts[2]
    elif lowered[0] == "lot":
        raw_lot_id = parts[-1]
    else:
        raw_lot_id = parts[1]

    raw_lot_id = raw_lot_id.strip().strip(":=")
    _product_name, extracted_lot_id = extract_lot_id_from_folder_name(raw_lot_id)
    return extracted_lot_id.split("@", 1)[0] if extracted_lot_id else None


def _extract_first_lot_id_from_archive(archive_path: Path):
    """按ZIP处理顺序，从目录层级或首个数据文件头识别华虹批次。"""
    try:
        with ZipFile(archive_path) as zip_file:
            members = sorted(
                (
                    info
                    for info in zip_file.infolist()
                    if not info.is_dir()
                    and Path(info.filename).suffix.casefold() in (".txt", ".dcp")
                ),
                key=lambda info: info.filename.casefold(),
            )
            if not members:
                return None

            first_member = members[0]
            member_parts = Path(first_member.filename.replace("\\", "/")).parts
            for component in member_parts[:-1]:
                _product_name, lot_id = extract_lot_id_from_folder_name(component)
                if lot_id != component:
                    return lot_id

            raw_content = zip_file.read(first_member)[:16384]
            for encoding in ("utf-8-sig", "gb18030", "latin1"):
                try:
                    lot_id = _extract_lot_id_from_dcp_text(raw_content.decode(encoding))
                except UnicodeDecodeError:
                    continue
                if lot_id:
                    return lot_id

            if len(member_parts) >= 2:
                return member_parts[-2]
    except (BadZipFile, OSError) as exc:
        logger.warning("读取华虹ZIP批次号失败 %s: %s", archive_path, exc)
    return None


def extract_first_hh_lot_id(input_paths: str | Path | Sequence[str | Path]):
    """从实际处理顺序中的第一个华虹数据来源提取真实批次号。"""
    normalized_paths = normalize_input_paths(input_paths)
    archives = discover_zip_archives(normalized_paths)
    if archives:
        lot_id = _extract_first_lot_id_from_archive(archives[0])
        if not lot_id:
            archive_name = archives[0].stem
            _product_name, extracted_lot_id = extract_lot_id_from_folder_name(
                archive_name
            )
            if extracted_lot_id != archive_name:
                lot_id = extracted_lot_id
    else:
        lot_id = extract_first_lot_id(normalized_paths[0])

    if not lot_id:
        raise OutputNamingError("无法从华虹输入中识别首个真实批次号")
    return lot_id


def generate_output_folder_name(
    input_paths: str | Path | Sequence[str | Path],
    *,
    serial: str | None = None,
):
    """生成统一的“首个真实批次号_流水号”文件夹名称。"""
    return build_output_folder_name(
        extract_first_hh_lot_id(input_paths),
        serial=serial,
    )


class HHDataProcessingThread(QThread):
    """华虹数据处理后台线程"""
    progress_updated = pyqtSignal(str)  # 进度更新信号
    finished = pyqtSignal(bool, str)    # 完成信号(成功/失败, 消息)
    
    def __init__(self, input_paths, output_dir, operation_type):
        super().__init__()
        self.input_paths = normalize_input_paths(input_paths)
        self.input_dir = str(self.input_paths[0])
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
            logger.error(f"华虹数据处理失败: {e}")
            self.finished.emit(False, f"处理失败: {str(e)}")
    
    def _clean_data(self):
        """清洗数据"""
        try:
            self.progress_updated.emit("🔍 正在扫描华虹数据来源...")
            with prepare_dcp_input(
                self.input_paths,
                progress=self.progress_updated.emit,
            ) as prepared_input:
                dcp_files = prepared_input.data_files
                self.progress_updated.emit(f"📁 发现 {len(dcp_files)} 个华虹DCP/TXT候选文件")

                os.makedirs(self.output_dir, exist_ok=True)
                self.progress_updated.emit(f"📁 华虹输出文件夹已创建: {self.output_dir}")
                self.progress_updated.emit("🧹 正在处理华虹数据文件...")

                result = clean_dcp_process_directory(
                    directory_path=str(prepared_input.directory),
                    output_dir=self.output_dir,
                    outlier_method='iqr',
                    convert_units=True
                )

                if result:
                    archive_note = (
                        f"，来源为 {len(prepared_input.archives)} 个ZIP"
                        if prepared_input.archives
                        else ""
                    )
                    self.progress_updated.emit("✅ 华虹数据清洗完成！")
                    self.finished.emit(
                        True,
                        f"成功处理 {len(dcp_files)} 个华虹数据文件{archive_note}",
                    )
                else:
                    self.finished.emit(False, "华虹数据处理失败，请检查数据文件格式")
        except ZipInputError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            logger.error(f"华虹数据处理失败: {e}")
            self.finished.emit(False, f"华虹处理失败: {str(e)}")
    
    def _generate_charts(self):
        """生成图表"""
        self.progress_updated.emit("📊 正在初始化华虹图表生成器...")
        
        try:
            yield_files = []
            boxplot_files = []
            summary_files = []
            
            # 生成良率图表（包括失效分析饼图）
            self.progress_updated.emit("📈 正在生成华虹良率分析图表...")
            yield_chart = YieldChart(data_dir=self.output_dir)
            if yield_chart.load_data():
                yield_files = yield_chart.save_all_charts(output_dir=self.output_dir)
                self.progress_updated.emit(f"✅ 华虹良率图表生成完成: {len(yield_files)} 个文件")
                logger.info(f"📊 生成的良率图表类型: 趋势图、对比图、失效分析饼图")

                # 新增：显式调用失效分析饼图的生成逻辑
                self.progress_updated.emit("🥧 正在特别生成失效分析饼图...")
                try:
                    failure_chart_path = yield_chart.save_chart('failure_analysis', output_dir=self.output_dir)
                    if failure_chart_path and failure_chart_path not in yield_files:
                        yield_files.append(failure_chart_path)
                        self.progress_updated.emit(f"✅ 单独生成失效分析饼图成功: {failure_chart_path.name}")
                        logger.info(f"📊 单独生成失效分析饼图成功: {failure_chart_path}")
                    elif failure_chart_path:
                        self.progress_updated.emit("ℹ️ 失效分析饼图已在批量保存中创建")
                    else:
                        self.progress_updated.emit("⚠️ 未能单独生成失效分析饼图，可能无失效数据")
                except Exception as e:
                    self.progress_updated.emit(f"⚠️ 生成失效分析饼图时出现异常: {e}")
                    logger.error(f"❌ 生成失效分析饼图时出现异常: {e}")
            
            # 生成箱体图表
            self.progress_updated.emit("📦 正在生成华虹箱体统计图表...")
            boxplot_chart = BoxplotChart(data_dir=self.output_dir)
            if boxplot_chart.load_data():
                boxplot_files = boxplot_chart.save_all_charts(output_dir=self.output_dir)
                self.progress_updated.emit(f"✅ 华虹箱体图表生成完成: {len(boxplot_files)} 个文件")
            
            # 生成汇总箱体图表
            self.progress_updated.emit("📋 正在生成华虹汇总箱体图表...")
            try:
                from frontend.charts.summary_chart import SummaryChart
                
                # 详细日志记录数据目录状态
                from pathlib import Path
                output_path = Path(self.output_dir)
                csv_files = list(output_path.glob("*.csv"))
                logger.info(f"🔍 华虹汇总图表生成 - 数据目录: {self.output_dir}")
                logger.info(f"📄 找到的CSV文件: {[f.name for f in csv_files]}")
                
                summary_chart = SummaryChart(data_dir=self.output_dir)
                
                # 详细记录数据加载过程
                logger.info("📊 开始加载华虹汇总图表数据...")
                load_success = summary_chart.load_data()
                
                if load_success:
                    logger.info("✅ 华虹汇总图表数据加载成功")
                    self.progress_updated.emit("📊 华虹汇总图表数据加载成功，开始生成图表...")
                    
                    summary_file = summary_chart.save_summary_chart(output_dir=self.output_dir)
                    if summary_file:
                        summary_files = [summary_file]
                        self.progress_updated.emit(f"✅ 华虹汇总箱体图表生成完成: {summary_file.name}")
                        logger.info(f"🎉 华虹汇总图表成功保存: {summary_file}")
                    else:
                        self.progress_updated.emit("⚠️ 华虹汇总箱体图表生成失败 - 图表创建过程出错")
                        logger.error("❌ 华虹汇总图表生成失败 - save_summary_chart返回None")
                else:
                    self.progress_updated.emit("⚠️ 华虹汇总箱体图表数据加载失败")
                    logger.error("❌ 华虹汇总图表数据加载失败 - load_data返回False")
                    
            except Exception as e:
                logger.error(f"❌ 华虹汇总图表生成过程中出现异常: {e}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                self.progress_updated.emit(f"⚠️ 华虹汇总箱体图表生成异常: {str(e)}")
                summary_files = []
            
            total_files = len(yield_files) + len(boxplot_files) + len(summary_files)
            self.progress_updated.emit("🎉 华虹所有图表生成完成！")
            self.finished.emit(True, f"成功生成 {total_files} 个华虹交互式HTML图表")
            
        except Exception as e:
            logger.error(f"华虹图表生成失败: {e}")
            self.finished.emit(False, f"华虹图表生成失败: {str(e)}")


class HuaHongWidget(QWidget):
    """华虹公司数据分析界面组件"""

    cockpit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("companyPage")
        self.input_dir = ""
        self.input_paths = []
        self.output_dir = ""
        self.processing_thread = None
        self._updating_input_path = False
        self.init_ui()
        self.set_default_paths()
    
    def set_default_paths(self):
        """设置华虹业务数据的默认输入、输出路径。"""
        input_path = get_default_input_path()
        self.set_input_sources([input_path])
        self.output_path_edit.setText(get_default_output_path())
    
    def init_ui(self):
        """初始化华虹界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title_label = QLabel("🔬 HuaHong数据分析")
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
        self.input_path_edit.setPlaceholderText("选择数据文件夹，或选择一个/多个ZIP文件...")
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
        """在同一窗口选择一个数据目录或一个/多个华虹ZIP文件。"""
        current_sources = self.get_input_sources()
        selected_paths = select_input_sources(
            self,
            title="选择华虹数据来源",
            start_path=current_sources[0] if current_sources else get_default_input_path(),
        )
        if selected_paths:
            self.set_input_sources(selected_paths)

    def set_input_sources(self, paths):
        """设置输入来源，并在输入框中显示可编辑的多路径预览。"""
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
        """浏览输出父目录，开始处理时再创建批次时间戳文件夹。"""
        start_dir = self.output_path_edit.text().strip() or get_default_output_path()
        parent_dir = QFileDialog.getExistingDirectory(self, "选择华虹输出文件夹的父目录", start_dir)
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
        """开始华虹数据清洗"""
        input_sources = self.get_input_sources()
        if not input_sources:
            QMessageBox.warning(self, "警告", "请先选择华虹数据文件夹或ZIP文件！")
            return

        try:
            normalized_sources = normalize_input_paths(input_sources)
            for source in normalized_sources:
                if not source.exists():
                    raise ZipInputError(f"输入路径不存在: {source}")
                if source.is_file() and source.suffix.casefold() != ".zip":
                    raise ZipInputError(f"不支持的输入文件类型（仅支持ZIP）: {source.name}")
        except ZipInputError as e:
            QMessageBox.warning(self, "输入无效", str(e))
            return
        
        # 按统一规则创建“首个真实批次号_流水号”输出文件夹
        base_output_dir = self.output_path_edit.text().strip() or get_default_output_path()
        try:
            first_lot_id = extract_first_hh_lot_id(normalized_sources)
            self.output_dir = str(create_output_run_dir(base_output_dir, first_lot_id))
            self.log_message(f"📋 首个真实批次号: {first_lot_id}")
            self.log_message(f"📁 华虹输出文件夹已创建: {self.output_dir}")
        except (OutputNamingError, OSError) as e:
            self.log_message(f"❌ 创建华虹输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"创建华虹输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始华虹数据清洗流程...")
        if len(normalized_sources) == 1:
            self.log_message(f"📁 华虹输入来源: {normalized_sources[0]}")
        else:
            self.log_message(f"📦 已选择 {len(normalized_sources)} 个华虹ZIP文件")
            for source in normalized_sources:
                self.log_message(f"  - {source}")
        self.log_message(f"📁 华虹输出目录: {self.output_dir}")
        self.set_processing_state(True)
        
        # 启动后台处理线程
        self.processing_thread = HHDataProcessingThread(
            normalized_sources, self.output_dir, 'clean'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_cleaning_finished)
        self.processing_thread.start()
    
    def start_generating(self):
        """开始生成华虹图表"""
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先完成华虹数据清洗或指定有效的输出文件夹！")
            return
        
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_message(f"❌ 确认/创建华虹输出文件夹失败: {self.output_dir} - {e}")
            QMessageBox.critical(self, "错误", f"确认/创建华虹输出文件夹失败: {e}")
            return

        self.log_message("🚀 开始华虹图表生成流程...")
        self.set_processing_state(True)
        
        # 启动后台处理线程
        self.processing_thread = HHDataProcessingThread(
            self.input_dir, self.output_dir, 'generate'
        )
        self.processing_thread.progress_updated.connect(self.log_message)
        self.processing_thread.finished.connect(self.on_generating_finished)
        self.processing_thread.start()
    
    def on_cleaning_finished(self, success, message):
        """华虹数据清洗完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            QMessageBox.information(self, "成功", f"华虹数据清洗完成！\n{message}\n\n输出文件夹: {self.output_dir}")
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"华虹数据清洗失败！\n{message}")
    
    def on_generating_finished(self, success, message):
        """华虹图表生成完成"""
        self.set_processing_state(False)
        
        if success:
            self.log_message(f"✅ {message}")
            self.log_message(f"📁 华虹图表保存位置: {self.output_dir}")
            
            # 询问是否打开输出文件夹
            reply = QMessageBox.question(
                self, "完成", 
                f"华虹图表生成完成！\n{message}\n\n是否打开输出文件夹查看结果？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.open_output_folder()
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "错误", f"华虹图表生成失败！\n{message}")
    
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
                logger.error(f"打开华虹输出文件夹失败: {e}")
                QMessageBox.warning(self, "警告", f"无法打开华虹输出文件夹: {e}")
    
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
        logger.info(f"华虹界面: {message}")
        
        # 滚动到底部
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
