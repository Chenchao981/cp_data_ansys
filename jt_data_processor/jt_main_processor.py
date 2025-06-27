#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT数据处理主程序

集成JT读取器、适配器和配置，提供完整的JT数据处理流程。
基于HH公司的成熟处理流程，专门针对JT公司的需求定制。

功能：
- 读取JT Excel文件
- 应用字段映射
- 数据清洗（IQR四分位法）
- 生成规格文件
- 输出标准CSV格式

作者: CP Data Analysis Team
版本: 1.0.0
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import List, Union, Dict, Any, Optional

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

# 导入JT专用模块
from jt_data_processor.readers.jt_reader import JTReader
from jt_data_processor.adapters.jt_adapter import JTAdapter
from jt_data_processor.config.jt_config import JTConfig, DEFAULT_JT_CONFIG

# 导入现有的数据模型和工具
from cp_data_processor.data_models.cp_data import CPLot, CPWafer
from cp_data_processor.exporters.excel_exporter import ExcelExporter

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JTDataProcessor:
    """
    JT数据处理器主类
    
    集成JT读取器、适配器和配置管理，
    提供完整的JT数据处理流程。
    
    处理流程：
    1. 读取JT Excel文件
    2. 字段映射转换
    3. 数据清洗（IQR方法）
    4. 输出标准CSV
    5. 生成规格文件
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化JT数据处理器
        
        Args:
            config: JT配置字典，默认使用DEFAULT_JT_CONFIG
        """
        self.config = config if config else DEFAULT_JT_CONFIG
        self.logger = logging.getLogger(f"{__name__}.JTDataProcessor")
        
        # 初始化组件
        self.reader = None
        self.adapter = JTAdapter('JT', self.config)
        self.lot = None
        
        self.logger.info("JT数据处理器初始化完成")
        self.logger.info(f"单位转换禁用: {self.config.get('disable_unit_conversion', False)}")
        self.logger.info(f"异常值处理方法: {self.config.get('cleaning_config', {}).get('default_outlier_method', 'iqr')}")
    
    def process_files(self, file_paths: Union[str, List[str]], 
                     output_dir: str = "output",
                     pass_bin: int = 1) -> Dict[str, Any]:
        """
        处理JT数据文件的完整流程
        
        Args:
            file_paths: JT Excel文件路径（单个或列表）
            output_dir: 输出目录
            pass_bin: 合格bin值，默认为1
            
        Returns:
            Dict[str, Any]: 处理结果摘要
        """
        self.logger.info("=== 开始JT数据处理流程 ===")
        
        try:
            # 1. 文件验证
            validated_files = self._validate_input_files(file_paths)
            self.logger.info(f"验证通过的文件数: {len(validated_files)}")
            
            # 2. 读取数据
            self.logger.info("步骤1: 读取JT Excel文件...")
            self.reader = JTReader(validated_files, pass_bin)
            self.lot = self.reader.read()
            
            # 3. 数据转换和清洗
            self.logger.info("步骤2: 数据转换和清洗...")
            self.lot = self.adapter.transform_to_standard_format(self.lot)
            
            # 4. 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 5. 输出清洗后的数据
            self.logger.info("步骤3: 输出清洗数据...")
            csv_files = self._export_cleaned_data(output_path)
            
            # 6. 生成规格文件
            self.logger.info("步骤4: 生成规格文件...")
            spec_files = self._generate_spec_files(validated_files, output_path)
            
            # 7. 生成处理报告
            result_summary = self._generate_processing_report(
                input_files=validated_files,
                output_files=csv_files + spec_files,
                output_dir=str(output_path)
            )
            
            self.logger.info("=== JT数据处理流程完成 ===")
            return result_summary
            
        except Exception as e:
            self.logger.error(f"JT数据处理失败: {e}")
            raise
    
    def _validate_input_files(self, file_paths: Union[str, List[str]]) -> List[str]:
        """
        验证输入文件
        
        Args:
            file_paths: 文件路径
            
        Returns:
            List[str]: 验证通过的文件路径列表
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        validated_files = []
        supported_extensions = self.config.get('supported_formats', ['.xls', '.xlsx'])
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                self.logger.warning(f"文件不存在，跳过: {file_path}")
                continue
            
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in supported_extensions:
                self.logger.warning(f"不支持的文件格式 {file_ext}，跳过: {file_path}")
                continue
            
            validated_files.append(file_path)
            self.logger.debug(f"文件验证通过: {file_path}")
        
        if not validated_files:
            raise ValueError("没有找到有效的JT数据文件")
        
        return validated_files
    
    def _export_cleaned_data(self, output_dir: Path) -> List[str]:
        """
        导出清洗后的数据
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 输出文件路径列表
        """
        csv_files = []
        
        if self.lot and self.lot.combined_data is not None and not self.lot.combined_data.empty:
            # 生成CSV文件名
            lot_id = self.lot.lot_id
            csv_filename = f"{lot_id}_cleaned_data.csv"
            csv_path = output_dir / csv_filename
            
            # 直接导出数据为CSV
            self.lot.combined_data.to_csv(
                csv_path,
                index=False,
                encoding=self.config.get('output_config', {}).get('csv_encoding', 'utf-8-sig')
            )
            
            csv_files.append(str(csv_path))
            self.logger.info(f"数据导出完成: {csv_path}")
            
            # 记录数据统计
            self.logger.info(f"导出数据行数: {len(self.lot.combined_data)}")
            self.logger.info(f"导出数据列数: {len(self.lot.combined_data.columns)}")
        
        return csv_files
    
    def _generate_spec_files(self, input_files: List[str], output_dir: Path) -> List[str]:
        """
        生成规格文件
        
        Args:
            input_files: 输入文件列表
            output_dir: 输出目录
            
        Returns:
            List[str]: 规格文件路径列表
        """
        spec_files = []
        
        try:
            for file_path in input_files:
                # 获取单位和规格信息
                if self.reader:
                    unit_info = self.reader.get_unit_info(file_path)
                    spec_info = self.reader.get_spec_info(file_path)
                else:
                    self.logger.warning("Reader未初始化，跳过规格文件生成")
                    continue
                
                if unit_info and spec_info:
                    # 生成规格文件
                    spec_data = self._create_spec_dataframe(unit_info, spec_info)
                    
                    # 生成规格文件名
                    file_stem = Path(file_path).stem
                    spec_filename = f"{file_stem}_spec.csv"
                    spec_path = output_dir / spec_filename
                    
                    # 保存规格文件
                    spec_data.to_csv(
                        spec_path,
                        index=False,
                        encoding=self.config.get('output_config', {}).get('csv_encoding', 'utf-8-sig')
                    )
                    
                    spec_files.append(str(spec_path))
                    self.logger.info(f"规格文件生成完成: {spec_path}")
        
        except Exception as e:
            self.logger.error(f"生成规格文件失败: {e}")
            # 继续处理，不中断主流程
        
        return spec_files
    
    def _create_spec_dataframe(self, unit_info: Dict, spec_info: Dict) -> pd.DataFrame:
        """
        创建规格文件的DataFrame
        
        Args:
            unit_info: 单位信息字典
            spec_info: 规格信息字典
            
        Returns:
            pd.DataFrame: 规格数据
        """
        spec_config = self.config.get('spec_file_config', {})
        
        # 获取参数列表（排除基础列）
        basic_columns = ['DUT_NO', 'SOFT_BIN', 'X_COORD', 'Y_COORD', 'SITE_NUM', 'PART_ID', 'PASSFG']
        param_columns = [col for col in unit_info.keys() if col not in basic_columns]
        
        # 创建规格数据
        spec_records = []
        for param in param_columns:
            record = {
                'CONT': param,
                'Unit': unit_info.get(param, ''),
                'LimitU': spec_info.get('limit_u', {}).get(param, ''),
                'LimitL': spec_info.get('limit_l', {}).get(param, ''),
                'TestCond': spec_config.get('testcond_value', '')  # JT公司测试条件为空
            }
            spec_records.append(record)
        
        spec_df = pd.DataFrame(spec_records)
        self.logger.debug(f"创建规格文件，参数数: {len(spec_records)}")
        
        return spec_df
    
    def _generate_processing_report(self, input_files: List[str], 
                                  output_files: List[str], 
                                  output_dir: str) -> Dict[str, Any]:
        """
        生成处理报告
        
        Args:
            input_files: 输入文件列表
            output_files: 输出文件列表
            output_dir: 输出目录
            
        Returns:
            Dict[str, Any]: 处理报告
        """
        report = {
            'processing_status': 'success',
            'lot_id': self.lot.lot_id if self.lot else 'unknown',
            'input_files': input_files,
            'output_files': output_files,
            'output_directory': output_dir,
            'wafer_count': len(self.lot.wafers) if self.lot else 0,
            'total_chip_count': len(self.lot.combined_data) if self.lot and self.lot.combined_data is not None else 0,
            'parameter_count': self.lot.param_count if self.lot else 0,
            'processing_config': {
                'unit_conversion_disabled': self.config.get('disable_unit_conversion', True),
                'outlier_method': self.config.get('cleaning_config', {}).get('default_outlier_method', 'iqr'),
                'field_mapping_count': len(self.config.get('field_mapping', {}))
            },
            'processor_version': '1.0.0'
        }
        
        # 保存处理报告
        report_path = Path(output_dir) / f"{report['lot_id']}_processing_report.json"
        try:
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"处理报告保存: {report_path}")
        except Exception as e:
            self.logger.warning(f"保存处理报告失败: {e}")
        
        return report
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        获取处理器配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要
        """
        return {
            'processor_name': 'JT数据处理器',
            'version': '1.0.0',
            'config_summary': self.adapter.get_processing_summary() if self.adapter else {},
            'supported_formats': self.config.get('supported_formats', []),
            'unit_conversion_disabled': self.config.get('disable_unit_conversion', True),
            'default_outlier_method': self.config.get('cleaning_config', {}).get('default_outlier_method', 'iqr')
        }


# 便捷函数
def process_jt_files(file_paths: Union[str, List[str]], 
                    output_dir: str = "jt_output",
                    pass_bin: int = 1,
                    config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    处理JT文件的便捷函数
    
    Args:
        file_paths: JT文件路径
        output_dir: 输出目录
        pass_bin: 合格bin值
        config: 自定义配置
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    processor = JTDataProcessor(config)
    return processor.process_files(file_paths, output_dir, pass_bin)


if __name__ == "__main__":
    # 命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description='JT数据处理器')
    parser.add_argument('files', nargs='+', help='JT Excel文件路径')
    parser.add_argument('-o', '--output', default='jt_output', help='输出目录')
    parser.add_argument('-b', '--pass-bin', type=int, default=1, help='合格bin值')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理文件
    try:
        print(f"开始处理JT文件: {args.files}")
        print(f"输出目录: {args.output}")
        print(f"合格bin值: {args.pass_bin}")
        print("-" * 50)
        
        result = process_jt_files(args.files, args.output, args.pass_bin)
        
        print("\n=== 处理完成 ===")
        print(f"批次ID: {result['lot_id']}")
        print(f"晶圆数: {result['wafer_count']}")
        print(f"芯片总数: {result['total_chip_count']}")
        print(f"参数数: {result['parameter_count']}")
        print(f"输出文件数: {len(result['output_files'])}")
        print(f"输出目录: {result['output_directory']}")
        
        print("\n输出文件:")
        for file_path in result['output_files']:
            print(f"  - {file_path}")
        
        # 🔥 重要提醒
        print("\n🔥 JT数据处理特性:")
        print(f"  - 单位转换: {'禁用' if result['processing_config']['unit_conversion_disabled'] else '启用'}")
        print(f"  - 异常值处理: {result['processing_config']['outlier_method'].upper()}")
        print(f"  - 字段映射: {result['processing_config']['field_mapping_count']}个字段")
        
        print("\n✅ JT数据处理成功完成！")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        sys.exit(1) 