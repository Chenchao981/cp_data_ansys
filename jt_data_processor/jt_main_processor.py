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
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

# 导入JT专用模块
from jt_data_processor.readers.jt_reader import JTReader
from jt_data_processor.adapters.jt_adapter import JTAdapter
from jt_data_processor.config.jt_config import JTConfig, DEFAULT_JT_CONFIG
from jt_data_processor.utils.jt_directory_detector import JTDirectoryDetector

# 导入现有的数据模型和工具
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
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
            file_paths: JT Excel文件路径（单个或列表）或目录路径
            output_dir: 输出目录
            pass_bin: 合格bin值，默认为1
            
        Returns:
            Dict[str, Any]: 处理结果摘要
        """
        self.logger.info("=== 开始JT数据处理流程 ===")
        
        try:
            # 1. 智能输入处理（文件或目录）
            validated_files = self._process_input_paths(file_paths)
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
            spec_files = self._generate_spec_files(output_path)
            
            # 7. 生成良率报告
            self.logger.info("步骤5: 生成良率报告...")
            yield_files = self._generate_yield_files(output_path)
            
            # 8. 生成处理报告
            result_summary = self._generate_processing_report(
                input_files=validated_files,
                output_files=csv_files + spec_files + yield_files,
                output_dir=str(output_path)
            )
            
            self.logger.info("=== JT数据处理流程完成 ===")
            return result_summary
            
        except Exception as e:
            self.logger.error(f"JT数据处理失败: {e}")
            raise
    
    def _process_input_paths(self, input_paths: Union[str, List[str]]) -> List[str]:
        """
        智能处理输入路径（文件或目录）
        
        🔥 新增：支持HH公司风格的目录输入
        - 单批次：浏览到 .\data\jetech\FA44-4149\ 自动处理该批次
        - 多批次：浏览到 .\data\jetech\ 自动处理所有子批次
        - 文件：直接处理指定文件
        
        Args:
            input_paths: 输入路径（文件、目录或路径列表）
            
        Returns:
            List[str]: 验证通过的文件路径列表
        """
        if isinstance(input_paths, str):
            input_paths = [input_paths]
        
        all_files = []
        detector = JTDirectoryDetector()
        
        for input_path in input_paths:
            if not os.path.exists(input_path):
                self.logger.warning(f"路径不存在，跳过: {input_path}")
                continue
            
            if os.path.isfile(input_path):
                # 输入是文件，直接验证
                if self._is_valid_jt_file(input_path):
                    all_files.append(input_path)
                    self.logger.debug(f"文件验证通过: {input_path}")
                else:
                    self.logger.warning(f"无效的JT文件，跳过: {input_path}")
            
            elif os.path.isdir(input_path):
                # 输入是目录，使用智能检测
                self.logger.info(f"🔍 检测目录结构: {input_path}")
                try:
                    processing_info_list = detector.scan_and_process_directory(input_path)
                    
                    # 收集所有批次的文件
                    for processing_info in processing_info_list:
                        batch_files = processing_info['excel_files']
                        all_files.extend(batch_files)
                        self.logger.info(f"✅ 收集批次 {processing_info['batch_name']}: {len(batch_files)}个文件")
                    
                except Exception as e:
                    self.logger.error(f"目录检测失败，跳过: {input_path}, 错误: {e}")
                    continue
            
            else:
                self.logger.warning(f"无效的输入类型，跳过: {input_path}")
        
        if not all_files:
            raise ValueError("没有找到有效的JT数据文件")
        
        self.logger.info(f"🎯 输入处理完成，共收集 {len(all_files)} 个有效文件")
        return all_files
    
    def _is_valid_jt_file(self, file_path: str) -> bool:
        """
        验证文件是否为有效的JT文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为有效的JT文件
        """
        supported_extensions = self.config.get('supported_formats', ['.xls', '.xlsx'])
        file_ext = Path(file_path).suffix.lower()
        return file_ext in supported_extensions
    
    def _generate_timestamp(self) -> str:
        """
        生成符合HH格式的时间戳
        
        格式: 20250627_093853 (年月日_时分秒)
        
        Returns:
            str: 时间戳字符串
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
            # 生成标准化CSV文件名（符合HH格式）
            lot_id = self.lot.lot_id
            timestamp = self._generate_timestamp()
            csv_filename = f"{lot_id}_cleaned_{timestamp}.csv"
            csv_path = output_dir / csv_filename
            
            # 🔥 关键修正：标准化输出格式，确保与HH公司格式兼容
            standardized_data = self._standardize_output_format(self.lot.combined_data)
            
            # 导出标准化后的数据
            standardized_data.to_csv(
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
    
    def _standardize_output_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化输出格式，确保与HH公司要求一致
        
        - WaferID: 转换格式（例如, 从 3.0 变为 3）
        - Test: 重命名为 Test_d
        - X, Y: 重命名为 X, Y
        
        Args:
            df: 原始数据框
            
        Returns:
            pd.DataFrame: 标准化后的数据框
        """
        if df.empty:
            return df

        # 内部函数：安全转换WaferID
        def convert_wafer_id(wafer_id):
            """安全地将WaferID转换为整数，如果失败则返回原始值"""
            try:
                # 检查是否为 'nan' 字符串或Pandas的NA值
                if pd.isna(wafer_id) or str(wafer_id).strip().lower() == 'nan':
                    return None
                # 尝试转换为浮点数再转换为整数
                return int(float(wafer_id))
            except (ValueError, TypeError):
                return wafer_id

        # 复制以避免SettingWithCopyWarning
        df_copy = df.copy()

        # 应用转换
        if 'WaferID' in df_copy.columns:
            df_copy['WaferID'] = df_copy['WaferID'].apply(convert_wafer_id)
        
        # 🔥 标准化列名（从JT格式到HH格式）
        # 这是根据jt_config.py中的字段映射的逆操作
        # 'TEST': 'Test', 'X': 'X', 'Y': 'Y'
        rename_map = {
            'Test': 'Test_d'  # 仅重命名Test
        }
        df_copy.rename(columns=rename_map, inplace=True)

        return df_copy
    
    def _generate_spec_files(self, output_dir: Path) -> List[str]:
        """
        为整个批次生成一个统一的规格（SPEC）文件
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 生成的规格文件路径列表（仅一个文件）
        """
        spec_files = []
        
        if self.lot is None or not self.lot.params:
            self.logger.warning("批次数据或参数列表不存在，无法生成规格文件。")
            return spec_files
        
        # 1. 直接使用批次的参数列表
        params_list = self.lot.params
        
        # 2. 创建规格DataFrame
        spec_df = self._create_spec_dataframe(params_list)
        
        if spec_df.empty:
            self.logger.warning("创建的规格DataFrame为空，跳过文件生成。")
            return spec_files
            
        # 3. 生成文件名并保存
        lot_id = self.lot.lot_id
        timestamp = self._generate_timestamp()
        spec_filename = f"{lot_id}_spec_{timestamp}.csv"
        spec_path = output_dir / spec_filename
        
        spec_df.to_csv(spec_path, index=False)
        spec_files.append(str(spec_path))
        
        self.logger.info(f"✅ 成功生成统一规格文件: {spec_filename}")
        return spec_files

    def _create_spec_dataframe(self, params: List[CPParameter]) -> pd.DataFrame:
        """
        根据参数对象列表创建规格DataFrame
        
        Args:
            params: CPLot中的参数对象列表 (List[CPParameter])
            
        Returns:
            pd.DataFrame: 包含规格信息的DataFrame
        """
        spec_records = []
        
        for p in params:
            record = {
                "param": p.id,
                "unit": p.unit if p.unit is not None else "",
                "lsl": p.sl if p.sl is not None else "",
                "usl": p.su if p.su is not None else "",
                "target": ""  # 保留target列，即使为空
            }
            spec_records.append(record)

        if not spec_records:
            return pd.DataFrame()

        # 直接从记录列表创建DataFrame，避免重复表头
        spec_df = pd.DataFrame(spec_records)
        
        # 确保列的顺序符合要求
        spec_df = spec_df[["param", "unit", "lsl", "usl", "target"]]
        
        return pd.DataFrame(spec_df)
    
    def _generate_yield_files(self, output_dir: Path) -> List[str]:
        """
        生成良率报告
        
        HH格式：
        Product_Name,Lot_ID,Wafer_ID,Yield,Total,Pass,Bin3,Bin4,...
        NCETSG7120BAA,FA54-5339,1,99.30%,142,141,1,0,...
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 良率文件路径列表
        """
        yield_files = []
        
        if not self.lot or not self.lot.wafers:
            self.logger.warning("没有晶圆数据，跳过良率报告生成")
            return yield_files
        
        try:
            # 生成良率数据
            yield_data = self._calculate_yield_statistics()
            
            if yield_data:
                # 生成标准化良率文件名（符合HH格式）
                lot_id = self.lot.lot_id
                timestamp = self._generate_timestamp()
                yield_filename = f"{lot_id}_yield_{timestamp}.csv"
                yield_path = output_dir / yield_filename
                
                # 保存良率文件
                yield_df = pd.DataFrame(yield_data)
                yield_df.to_csv(
                    yield_path,
                    index=False,
                    encoding=self.config.get('output_config', {}).get('csv_encoding', 'utf-8-sig')
                )
                
                yield_files.append(str(yield_path))
                self.logger.info(f"✅ 良率报告生成完成: {yield_path}")
                self.logger.info(f"良率数据: {len(yield_data)}行晶圆统计")
        
        except Exception as e:
            self.logger.error(f"生成良率报告失败: {e}")
            # 继续处理，不中断主流程
        
        return yield_files
    
    def _calculate_yield_statistics(self) -> List[Dict]:
        """
        计算每个晶圆的良率统计数据
        
        Returns:
            List[Dict]: 每个晶圆的良率统计
        """
        yield_records = []
        
        # 产品名称：使用Lot_ID作为产品名称（简化方案）
        product_name = self.lot.lot_id
        
        for wafer in self.lot.wafers:
            if wafer.chip_data is None or wafer.chip_data.empty:
                continue
            
            # 计算晶圆良率统计
            total_chips = len(wafer.chip_data)
            
            # 统计各Bin的数量
            bin_counts = wafer.chip_data['Bin'].value_counts().to_dict()
            
            # Pass芯片数（Bin=1为合格）
            pass_chips = bin_counts.get(1, 0)
            
            # 良率计算
            yield_rate = (pass_chips / total_chips * 100) if total_chips > 0 else 0
            
            # 构建良率记录
            yield_record = {
                'Product_Name': product_name,
                'Lot_ID': self.lot.lot_id,
                'Wafer_ID': wafer.wafer_id,
                'Yield': f"{yield_rate:.2f}%",
                'Total': total_chips,
                'Pass': pass_chips
            }
            
            # 添加各个失效Bin的统计（Bin 2-9）
            for bin_num in range(2, 10):
                bin_key = f"Bin{bin_num}"
                yield_record[bin_key] = bin_counts.get(bin_num, 0)
            
            yield_records.append(yield_record)
            self.logger.debug(f"晶圆 {wafer.wafer_id}: 良率 {yield_rate:.2f}%, 总数 {total_chips}, 合格 {pass_chips}")
        
        # 添加总计行（ALL）
        if yield_records:
            total_record = self._calculate_lot_total_yield(yield_records)
            yield_records.append(total_record)
        
        self.logger.info(f"✅ 良率统计完成: {len(yield_records)}条记录（含总计）")
        return yield_records
    
    def _calculate_lot_total_yield(self, yield_records: List[Dict]) -> Dict:
        """
        计算批次总良率
        
        Args:
            yield_records: 各晶圆良率记录
            
        Returns:
            Dict: 批次总良率记录
        """
        total_chips = sum(record['Total'] for record in yield_records)
        total_pass = sum(record['Pass'] for record in yield_records)
        total_yield = (total_pass / total_chips * 100) if total_chips > 0 else 0
        
        # 总计各Bin数量
        total_record = {
            'Product_Name': self.lot.lot_id,
            'Lot_ID': 'ALL',
            'Wafer_ID': 'ALL', 
            'Yield': f"{total_yield:.2f}%",
            'Total': total_chips,
            'Pass': total_pass
        }
        
        # 统计各失效Bin总数
        for bin_num in range(2, 10):
            bin_key = f"Bin{bin_num}"
            total_record[bin_key] = sum(record.get(bin_key, 0) for record in yield_records)
        
        return total_record
    
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
def process_jt_files(input_paths: Union[str, List[str]], 
                    output_dir: str = "output",
                    pass_bin: int = 1,
                    config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    处理JT文件的便捷函数（支持HH公司风格的目录输入）
    
    Args:
        input_paths: JT文件路径或目录路径（支持混合输入）
        output_dir: 输出目录
        pass_bin: 合格bin值
        config: 自定义配置
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    processor = JTDataProcessor(config)
    return processor.process_files(input_paths, output_dir, pass_bin)


if __name__ == "__main__":
    # 命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description='JT数据处理器 - 支持HH公司风格的目录处理')
    parser.add_argument('inputs', nargs='+', help='JT Excel文件路径或目录路径\n' +
                       '  单批次: .\\data\\jetech\\FA44-4149\\\n' +
                       '  多批次: .\\data\\jetech\\\n' +
                       '  文件: .\\data\\jetech\\FA44-4149\\*.xls')
    parser.add_argument('-o', '--output', default='output', help='输出目录')
    parser.add_argument('-b', '--pass-bin', type=int, default=1, help='合格bin值')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理文件
    try:
        print(f"🔬 JT数据处理器 - HH公司风格目录处理")
        print(f"输入路径: {args.inputs}")
        print(f"输出目录: {args.output}")
        print(f"合格bin值: {args.pass_bin}")
        print("-" * 60)
        
        result = process_jt_files(args.inputs, args.output, args.pass_bin)
        
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