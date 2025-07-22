"""
标准CSV生成器

将标准化的CPLot数据生成3个标准CSV文件：
1. *_cleaned.csv - 清洗后的测试数据
2. *_yield.csv - 良率统计数据  
3. *_spec.csv - 参数规格数据
"""

import os
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter

logger = logging.getLogger(__name__)


class StandardCSVGenerator:
    """
    标准CSV生成器
    
    将标准化的CPLot对象转换为3个标准CSV文件，
    为后续的图表生成提供统一的数据格式。
    """
    
    def __init__(self):
        """初始化CSV生成器"""
        self.logger = logging.getLogger(__name__)
    
    def _generate_timestamp(self) -> str:
        """
        生成时间戳字符串
        
        Returns:
            str: 格式为YYYYMMDD_HHMM的时间戳
        """
        return datetime.now().strftime("%Y%m%d_%H%M")
    
    def generate_standard_csvs(self, lot: CPLot, output_dir: str) -> Dict[str, str]:
        """
        生成所有标准CSV文件
        
        Args:
            lot: 标准化的CPLot对象
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 生成的文件路径字典 {'cleaned': path, 'yield': path, 'spec': path}
        """
        if not lot or not lot.lot_id:
            raise ValueError("CPLot对象无效或缺少lot_id")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        lot_id = lot.lot_id
        timestamp = self._generate_timestamp()
        self.logger.info(f"开始生成{lot_id}的标准CSV文件 (时间戳: {timestamp})")
        
        file_paths = {}
        
        try:
            # 1. 生成清洗数据CSV
            cleaned_path = self.generate_cleaned_csv(lot, output_dir, timestamp)
            file_paths['cleaned'] = cleaned_path
            
            # 2. 生成良率数据CSV
            yield_path = self.generate_yield_csv(lot, output_dir, timestamp)
            file_paths['yield'] = yield_path
            
            # 3. 生成规格数据CSV
            spec_path = self.generate_spec_csv(lot, output_dir, timestamp)
            file_paths['spec'] = spec_path
            
            self.logger.info(f"标准CSV文件生成完成: {lot_id}")
            return file_paths
            
        except Exception as e:
            self.logger.error(f"生成标准CSV文件失败 {lot_id}: {e}")
            raise
    
    def generate_cleaned_csv(self, lot: CPLot, output_dir: str, timestamp: str = None) -> str:
        """
        生成清洗后的测试数据CSV
        
        格式: Lot_ID,Wafer_ID,X,Y,Seq,Bin,Param1,Param2,...
        
        Args:
            lot: CPLot对象
            output_dir: 输出目录
            
        Returns:
            str: 生成的文件路径
        """
        if not lot.wafers:
            raise ValueError("CPLot中没有晶圆数据")
        
        # 收集所有晶圆的芯片数据
        all_chip_data = []
        
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                # 确保包含基本字段
                chip_data = wafer.chip_data.copy()
                
                # 添加或验证必需字段
                if 'Lot_ID' not in chip_data.columns:
                    chip_data['Lot_ID'] = lot.lot_id
                if 'Wafer_ID' not in chip_data.columns:
                    chip_data['Wafer_ID'] = wafer.wafer_id
                
                # 标准化Wafer_ID为整数（如果是字符串）
                if 'Wafer_ID' in chip_data.columns:
                    chip_data['Wafer_ID'] = self._standardize_wafer_id(chip_data['Wafer_ID'])
                
                all_chip_data.append(chip_data)
        
        if not all_chip_data:
            raise ValueError("没有可用的芯片数据")
        
        # 合并所有数据
        combined_data = pd.concat(all_chip_data, ignore_index=True)
        
        # 标准化列名映射（将原始列名映射到标准列名）
        column_mapping = {
            'X_COORD': 'X',
            'Y_COORD': 'Y', 
            'PART_INDEX': 'Seq',
            'SOFT_BIN': 'Bin'
        }
        
        # 应用列名映射
        combined_data = combined_data.rename(columns=column_mapping)
        
        # 按批次ID然后按wafer_id进行排序（保持批次顺序）
        if 'Lot_ID' in combined_data.columns and 'Wafer_ID' in combined_data.columns:
            # 先按Lot_ID排序，再按Wafer_ID排序
            combined_data['Wafer_ID_int'] = pd.to_numeric(combined_data['Wafer_ID'], errors='coerce')
            combined_data = combined_data.sort_values(['Lot_ID', 'Wafer_ID_int'])
            combined_data = combined_data.drop('Wafer_ID_int', axis=1)
        elif 'Wafer_ID' in combined_data.columns:
            # 只按wafer_id排序
            combined_data = combined_data.sort_values('Wafer_ID', key=lambda x: pd.to_numeric(x, errors='coerce'))
        
        # 确保列顺序：基本字段在前，测试参数在后
        basic_columns = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']
        param_columns = [col for col in combined_data.columns if col not in basic_columns]
        ordered_columns = [col for col in basic_columns if col in combined_data.columns] + param_columns
        combined_data = combined_data[ordered_columns]
        
        # 生成文件路径（带时间戳）
        if timestamp:
            filename = f"{lot.lot_id}_cleaned_{timestamp}.csv"
        else:
            filename = f"{lot.lot_id}_cleaned.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        combined_data.to_csv(file_path, index=False)
        self.logger.info(f"生成清洗数据CSV: {file_path} ({len(combined_data)}行)")
        
        return file_path
    
    def generate_yield_csv(self, lot: CPLot, output_dir: str, timestamp: str = None) -> str:
        """
        生成良率统计数据CSV
        
        格式: Lot_ID,Wafer_ID,Gross_die,Good_die,Yield,Parameter_Fail_Counts...
        
        Args:
            lot: CPLot对象
            output_dir: 输出目录
            timestamp: 时间戳（可选）
            
        Returns:
            str: 生成的文件路径
        """
        if not lot.wafers:
            raise ValueError("CPLot中没有晶圆数据")
        
        yield_data = []
        
        for wafer in lot.wafers:
            # 获取晶圆的原始Lot_ID（从chip_data中获取）
            original_lot_id = lot.lot_id
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None and not wafer.chip_data.empty:
                if 'Lot_ID' in wafer.chip_data.columns:
                    original_lot_id = wafer.chip_data['Lot_ID'].iloc[0]
            
            # 计算晶圆级良率统计
            wafer_stats = self._calculate_wafer_yield(wafer, original_lot_id)
            yield_data.append(wafer_stats)
        
        # 创建DataFrame
        yield_df = pd.DataFrame(yield_data)
        
        # 确保Wafer_ID为整数类型
        if 'Wafer_ID' in yield_df.columns:
            yield_df['Wafer_ID'] = self._standardize_wafer_id(yield_df['Wafer_ID'])
        
        # 按批次ID然后按wafer_id进行排序（保持批次顺序）
        if 'Lot_ID' in yield_df.columns and 'Wafer_ID' in yield_df.columns:
            # 先按Lot_ID排序，再按Wafer_ID排序
            yield_df['Wafer_ID_int'] = pd.to_numeric(yield_df['Wafer_ID'], errors='coerce')
            yield_df = yield_df.sort_values(['Lot_ID', 'Wafer_ID_int'])
            yield_df = yield_df.drop('Wafer_ID_int', axis=1)
        elif 'Wafer_ID' in yield_df.columns:
            # 只按wafer_id排序
            yield_df = yield_df.sort_values('Wafer_ID', key=lambda x: pd.to_numeric(x, errors='coerce'))
        
        # 生成文件路径（带时间戳）
        if timestamp:
            filename = f"{lot.lot_id}_yield_{timestamp}.csv"
        else:
            filename = f"{lot.lot_id}_yield.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        yield_df.to_csv(file_path, index=False)
        self.logger.info(f"生成良率数据CSV: {file_path} ({len(yield_df)}行)")
        
        return file_path
    
    def generate_spec_csv(self, lot: CPLot, output_dir: str, timestamp: str = None) -> str:
        """
        生成参数规格数据CSV
        
        Lion格式: 
        第一行: Parameter, TEST_NUM, KELVIN_CHECK, IR_35V, ...
        第二行: UNIT, mV, mA, uA, ...
        第三行: LIMIT_LOW, 0, 0, 0, ...
        第四行: LIMIT_HIGH, 1, 10, 0.1, ...
        
        Args:
            lot: CPLot对象
            output_dir: 输出目录
            timestamp: 时间戳（可选）
            
        Returns:
            str: 生成的文件路径
        """
        
        # 检查是否是Lion数据（通过检查参数信息）
        if hasattr(lot, 'params') and lot.params:
            # 检查是否包含Lion特有的参数（如TEST_NUM等）
            param_ids = [param.id for param in lot.params]
            lion_indicators = ['TEST_NUM', 'KELVIN_CHECK', 'IR_35V', 'VBR_0P25mA', 'VBR_1mA']
            
            if any(indicator in param_ids for indicator in lion_indicators):
                # 这是Lion数据，使用Lion专用格式
                return self._generate_lion_spec_csv(lot, output_dir, timestamp)
        
        # 使用标准格式
        spec_data = []
        
        if hasattr(lot, 'params') and lot.params:
            # 从CPParameter对象生成规格数据
            for param in lot.params:
                spec_row = {
                    'Parameter': param.id,
                    'Unit': getattr(param, 'unit', ''),
                    'LimitL': getattr(param, 'sl', None),  # Spec Lower
                    'LimitU': getattr(param, 'su', None),  # Spec Upper
                    'LSL': getattr(param, 'sl', None),     # Lower Spec Limit
                    'USL': getattr(param, 'su', None),     # Upper Spec Limit
                    'Target': getattr(param, 'target', None)
                }
                spec_data.append(spec_row)
        else:
            # 从芯片数据中推断参数规格
            if lot.wafers and lot.wafers[0].chip_data is not None:
                sample_data = lot.wafers[0].chip_data
                param_columns = [col for col in sample_data.columns 
                               if col not in ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']]
                
                for param in param_columns:
                    spec_row = {
                        'Parameter': param,
                        'Unit': '',
                        'LimitL': None,
                        'LimitU': None,
                        'LSL': None,
                        'USL': None,
                        'Target': None
                    }
                    spec_data.append(spec_row)
        
        if not spec_data:
            # 创建空的规格文件
            spec_data = [{
                'Parameter': 'No_Parameters',
                'Unit': '',
                'LimitL': None,
                'LimitU': None,
                'LSL': None,
                'USL': None,
                'Target': None
            }]
        
        # 创建DataFrame
        spec_df = pd.DataFrame(spec_data)
        
        # 生成文件路径（带时间戳）
        if timestamp:
            filename = f"{lot.lot_id}_spec_{timestamp}.csv"
        else:
            filename = f"{lot.lot_id}_spec.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        spec_df.to_csv(file_path, index=False)
        self.logger.info(f"生成规格数据CSV: {file_path} ({len(spec_df)}行)")
        
        return file_path
    
    def _generate_lion_spec_csv(self, lot: CPLot, output_dir: str, timestamp: str = None) -> str:
        """
        生成Lion专用格式的规格CSV文件 - 使用实际数据中TEST_NUM右边的所有参数
        
        格式:
        第一行: Parameter, TEST_NUM, GLOBALCOND, DC_KELVIN_B1, ...
        第二行: UNIT, , V, V, ...
        第三行: LIMIT_LOW, , -0.05, -0.05, ...  
        第四行: LIMIT_HIGH, , 0.05, 0.05, ...
        
        Args:
            lot: CPLot对象
            output_dir: 输出目录
            timestamp: 时间戳（可选）
            
        Returns:
            str: 生成的文件路径
        """
        
        # 从第一个晶圆的spec_data中获取参数信息
        spec_data = None
        if lot.wafers and len(lot.wafers) > 0:
            # 查找有spec_data的晶圆
            for wafer in lot.wafers:
                if hasattr(wafer, 'spec_data') and wafer.spec_data is not None:
                    spec_data = wafer.spec_data
                    self.logger.info(f"找到规格数据，来源晶圆: {wafer.wafer_id}")
                    break
        
        if spec_data is None:
            # 如果没有spec_data，创建空文件
            self.logger.warning("没有找到Lion格式的规格数据，创建空规格文件")
            spec_df = pd.DataFrame([
                ['Parameter'],
                ['UNIT'],
                ['LIMIT_LOW'], 
                ['LIMIT_HIGH']
            ])
        else:
            # 获取TEST_NUM右边的所有参数列
            all_columns = list(spec_data.columns)
            self.logger.info(f"规格数据总列数: {len(all_columns)}")
            
            if 'TEST_NUM' in all_columns:
                test_num_index = all_columns.index('TEST_NUM')
                # TEST_NUM往右的所有列都是有效参数（包括TEST_NUM本身）
                param_columns = all_columns[test_num_index:]
                self.logger.info(f"TEST_NUM位置: {test_num_index}, 有效参数数量: {len(param_columns)}")
            else:
                # 如果没有TEST_NUM，使用所有参数列（排除基础字段）
                skip_columns = ['SITE_NUM', 'PART_INDEX', 'PASSFG', 'SOFT_BIN', 'T_TIME', 'X_COORD', 'Y_COORD']
                param_columns = [col for col in all_columns if col not in skip_columns]
                self.logger.info(f"没有找到TEST_NUM，使用所有参数列，数量: {len(param_columns)}")
            
            # 构建横向排列的数据
            param_row = ['Parameter'] + param_columns
            
            # 构建UNIT行
            unit_row = ['UNIT']
            for col in param_columns:
                if 'UNIT' in spec_data.index and pd.notna(spec_data.loc['UNIT', col]):
                    unit_val = str(spec_data.loc['UNIT', col])
                    if unit_val.lower() != 'nan':
                        unit_row.append(unit_val)
                    else:
                        unit_row.append('')
                else:
                    unit_row.append('')
            
            # 构建LIMIT_LOW行
            limit_low_row = ['LIMIT_LOW']
            for col in param_columns:
                if 'LIMIT_LOW' in spec_data.index and pd.notna(spec_data.loc['LIMIT_LOW', col]):
                    limit_val = str(spec_data.loc['LIMIT_LOW', col])
                    if limit_val.lower() != 'nan':
                        limit_low_row.append(limit_val)
                    else:
                        limit_low_row.append('')
                else:
                    limit_low_row.append('')
            
            # 构建LIMIT_HIGH行
            limit_high_row = ['LIMIT_HIGH']
            for col in param_columns:
                if 'LIMIT_HIGH' in spec_data.index and pd.notna(spec_data.loc['LIMIT_HIGH', col]):
                    limit_val = str(spec_data.loc['LIMIT_HIGH', col])
                    if limit_val.lower() != 'nan':
                        limit_high_row.append(limit_val)
                    else:
                        limit_high_row.append('')
                else:
                    limit_high_row.append('')
            
            # 创建DataFrame
            spec_df = pd.DataFrame([param_row, unit_row, limit_low_row, limit_high_row])
            self.logger.info(f"生成规格数据表格: {spec_df.shape[0]} 行 x {spec_df.shape[1]} 列")
        
        # 生成文件路径（带时间戳）
        if timestamp:
            filename = f"{lot.lot_id}_spec_{timestamp}.csv"
        else:
            filename = f"{lot.lot_id}_spec.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件（不包含index，不包含header）
        spec_df.to_csv(file_path, index=False, header=False)
        self.logger.info(f"生成Lion格式规格数据CSV: {file_path} ({len(spec_df)}行)")
        
        return file_path
    
    def _calculate_wafer_yield(self, wafer: CPWafer, lot_id: str) -> Dict[str, Any]:
        """
        计算单个晶圆的良率统计
        
        Args:
            wafer: CPWafer对象
            lot_id: 批次ID
            
        Returns:
            Dict[str, Any]: 晶圆良率统计数据
        """
        stats = {
            'Lot_ID': lot_id,
            'Wafer_ID': wafer.wafer_id,
            'Gross_die': 0,
            'Good_die': 0,
            'Yield': '0.0%'
        }
        
        # 首先尝试从summary_data中获取准确的yield数据
        if hasattr(wafer, 'summary_data') and wafer.summary_data:
            summary_data = wafer.summary_data
            
            # 从summary_data获取gross_die, good_die, yield
            if 'gross_die' in summary_data:
                stats['Gross_die'] = summary_data['gross_die']
            if 'good_die' in summary_data:
                stats['Good_die'] = summary_data['good_die']
            if 'yield' in summary_data:
                # yield格式如"99.40%"，保持百分比格式
                yield_str = str(summary_data['yield'])
                if '%' in yield_str:
                    stats['Yield'] = yield_str
                else:
                    stats['Yield'] = '0.0%'
            
            # 添加参数测量数据的平均值（从TEST_NUM字段往右的所有列都是有效参数）
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                chip_data = wafer.chip_data
                # 简化逻辑：从TEST_NUM字段往右的所有列都是有效参数
                all_columns = list(chip_data.columns)
                if 'TEST_NUM' in all_columns:
                    test_num_index = all_columns.index('TEST_NUM')
                    # TEST_NUM往右的所有列都是有效参数
                    param_columns = all_columns[test_num_index + 1:]
                else:
                    # 如果没有TEST_NUM字段，使用原有逻辑作为备用
                    basic_fields = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin', 'SITE_NUM', 'CONT', 'T_TIME', 'PASSFG']
                    param_columns = [col for col in chip_data.columns if col not in basic_fields]
                
                for param in param_columns:
                    try:
                        # 只计算好芯片（Bin=1）的参数平均值
                        if 'Bin' in chip_data.columns:
                            good_chip_data = chip_data[chip_data['Bin'] == 1]
                        else:
                            good_chip_data = chip_data
                        
                        if len(good_chip_data) > 0:
                            # 计算参数的平均值，排除异常值（NaN、inf和9999.9999等失效值）
                            param_values = pd.to_numeric(good_chip_data[param], errors='coerce').dropna()
                            param_values = param_values[~param_values.isin([float('inf'), float('-inf')])]
                            # 排除9999.9999等明显的失效值
                            param_values = param_values[param_values < 9999]
                            
                            if len(param_values) > 0:
                                # 计算平均值并保留适当的小数位数
                                mean_value = param_values.mean()
                                stats[param] = round(mean_value, 4) if pd.notna(mean_value) else 0
                            else:
                                stats[param] = 0
                        else:
                            stats[param] = 0
                    except Exception:
                        # 如果某个参数无法转换为数值，设置为0
                        stats[param] = 0
        
        # 如果summary_data中没有数据，使用chip_data计算
        if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
            chip_data = wafer.chip_data
            total_chips = len(chip_data)
            
            # 如果summary_data中没有gross_die，使用chip_data计算
            if stats['Gross_die'] == 0:
                stats['Gross_die'] = total_chips
            
            if 'Bin' in chip_data.columns:
                # 计算各个Bin的数量
                bin_counts = chip_data['Bin'].value_counts()
                
                # 如果summary_data中没有good_die，计算good chips (通常Bin=1是良品)
                if stats['Good_die'] == 0:
                    good_chips = bin_counts.get(1, 0)
                    stats['Good_die'] = good_chips
                
                # 如果summary_data中没有yield，计算yield并添加百分比符号
                if stats['Yield'] == '0.0%' and stats['Gross_die'] > 0:
                    yield_value = (stats['Good_die'] / stats['Gross_die'] * 100)
                    stats['Yield'] = f"{yield_value:.2f}%"
            
            # 如果之前没有计算参数平均值（当没有summary_data时）
            # 简化逻辑：从TEST_NUM字段往右的所有列都是有效参数
            all_columns = list(chip_data.columns)
            if 'TEST_NUM' in all_columns:
                test_num_index = all_columns.index('TEST_NUM')
                # TEST_NUM往右的所有列都是有效参数
                param_columns = all_columns[test_num_index + 1:]
            else:
                # 如果没有TEST_NUM字段，使用原有逻辑作为备用
                basic_fields = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin', 'SITE_NUM', 'CONT', 'T_TIME', 'PASSFG']
                param_columns = [col for col in chip_data.columns if col not in basic_fields]
            
            for param in param_columns:
                if param not in stats:  # 如果之前没有设置过这个参数
                    try:
                        # 只计算好芯片（Bin=1）的参数平均值
                        if 'Bin' in chip_data.columns:
                            good_chip_data = chip_data[chip_data['Bin'] == 1]
                        else:
                            good_chip_data = chip_data
                        
                        if len(good_chip_data) > 0:
                            # 计算参数的平均值，排除异常值（NaN、inf和9999.9999等失效值）
                            param_values = pd.to_numeric(good_chip_data[param], errors='coerce').dropna()
                            param_values = param_values[~param_values.isin([float('inf'), float('-inf')])]
                            # 排除9999.9999等明显的失效值
                            param_values = param_values[param_values < 9999]
                            
                            if len(param_values) > 0:
                                # 计算平均值并保留适当的小数位数
                                mean_value = param_values.mean()
                                stats[param] = round(mean_value, 4) if pd.notna(mean_value) else 0
                            else:
                                stats[param] = 0
                        else:
                            stats[param] = 0
                    except Exception:
                        # 如果某个参数无法转换为数值，设置为0
                        stats[param] = 0
        
        return stats
    
    def generate_combined_standard_csvs(self, lots: Dict[str, CPLot], output_dir: str, combined_name: str = "combined") -> Dict[str, str]:
        """
        生成合并多批次的标准CSV文件
        
        Args:
            lots: lot_id到CPLot对象的映射
            output_dir: 输出目录
            combined_name: 合并文件的名称前缀
            
        Returns:
            Dict[str, str]: 生成的合并文件路径字典
        """
        if not lots:
            raise ValueError("没有提供CPLot数据")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = self._generate_timestamp()
        self.logger.info(f"开始生成合并的标准CSV文件 (时间戳: {timestamp})")
        
        file_paths = {}
        
        try:
            # 1. 生成合并的清洗数据CSV
            cleaned_path = self._generate_combined_cleaned_csv(lots, output_dir, combined_name, timestamp)
            file_paths['cleaned'] = cleaned_path
            
            # 2. 生成合并的良率数据CSV
            yield_path = self._generate_combined_yield_csv(lots, output_dir, combined_name, timestamp)
            file_paths['yield'] = yield_path
            
            # 3. 生成合并的规格数据CSV（使用第一个批次的规格）
            spec_path = self._generate_combined_spec_csv(lots, output_dir, combined_name, timestamp)
            file_paths['spec'] = spec_path
            
            self.logger.info(f"合并标准CSV文件生成完成: {combined_name}")
            return file_paths
            
        except Exception as e:
            self.logger.error(f"生成合并标准CSV文件失败: {e}")
            raise
    
    def _generate_combined_cleaned_csv(self, lots: Dict[str, CPLot], output_dir: str, combined_name: str, timestamp: str) -> str:
        """生成合并的清洗数据CSV"""
        all_chip_data = []
        
        for lot_id, lot in lots.items():
            if not lot.wafers:
                continue
                
            for wafer in lot.wafers:
                if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                    chip_data = wafer.chip_data.copy()
                    
                    # 确保包含基本字段
                    if 'Lot_ID' not in chip_data.columns:
                        chip_data['Lot_ID'] = lot.lot_id
                    if 'Wafer_ID' not in chip_data.columns:
                        chip_data['Wafer_ID'] = wafer.wafer_id
                    
                    # 标准化Wafer_ID为整数（如果是字符串）
                    if 'Wafer_ID' in chip_data.columns:
                        chip_data['Wafer_ID'] = self._standardize_wafer_id(chip_data['Wafer_ID'])
                    
                    all_chip_data.append(chip_data)
        
        if not all_chip_data:
            raise ValueError("没有可用的芯片数据")
        
        # 合并所有数据
        combined_data = pd.concat(all_chip_data, ignore_index=True)
        
        # 标准化列名映射
        column_mapping = {
            'X_COORD': 'X',
            'Y_COORD': 'Y', 
            'PART_INDEX': 'Seq',
            'SOFT_BIN': 'Bin'
        }
        
        # 应用列名映射
        combined_data = combined_data.rename(columns=column_mapping)
        
        # 按Lot_ID和Wafer_ID进行排序
        if 'Lot_ID' in combined_data.columns and 'Wafer_ID' in combined_data.columns:
            combined_data = combined_data.sort_values(['Lot_ID', 'Wafer_ID'], 
                                                    key=lambda x: pd.to_numeric(x, errors='coerce') if x.name == 'Wafer_ID' else x)
        
        # 确保列顺序：基本字段在前，测试参数在后
        basic_columns = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']
        param_columns = [col for col in combined_data.columns if col not in basic_columns]
        ordered_columns = [col for col in basic_columns if col in combined_data.columns] + param_columns
        combined_data = combined_data[ordered_columns]
        
        # 生成文件路径
        filename = f"{combined_name}_cleaned_{timestamp}.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        combined_data.to_csv(file_path, index=False)
        self.logger.info(f"生成合并清洗数据CSV: {file_path} ({len(combined_data)}行)")
        
        return file_path
    
    def _generate_combined_yield_csv(self, lots: Dict[str, CPLot], output_dir: str, combined_name: str, timestamp: str) -> str:
        """生成合并的良率数据CSV"""
        all_yield_data = []
        
        for lot_id, lot in lots.items():
            if not lot.wafers:
                continue
                
            for wafer in lot.wafers:
                wafer_stats = self._calculate_wafer_yield(wafer, lot.lot_id)
                all_yield_data.append(wafer_stats)
        
        if not all_yield_data:
            raise ValueError("没有可用的良率数据")
        
        # 创建DataFrame
        yield_df = pd.DataFrame(all_yield_data)
        
        # 确保Wafer_ID为整数类型
        if 'Wafer_ID' in yield_df.columns:
            yield_df['Wafer_ID'] = self._standardize_wafer_id(yield_df['Wafer_ID'])
        
        # 按Lot_ID和Wafer_ID进行排序
        if 'Lot_ID' in yield_df.columns and 'Wafer_ID' in yield_df.columns:
            yield_df = yield_df.sort_values(['Lot_ID', 'Wafer_ID'], 
                                          key=lambda x: pd.to_numeric(x, errors='coerce') if x.name == 'Wafer_ID' else x)
        
        # 生成文件路径
        filename = f"{combined_name}_yield_{timestamp}.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        yield_df.to_csv(file_path, index=False)
        self.logger.info(f"生成合并良率数据CSV: {file_path} ({len(yield_df)}行)")
        
        return file_path
    
    def _generate_combined_spec_csv(self, lots: Dict[str, CPLot], output_dir: str, combined_name: str, timestamp: str) -> str:
        """生成合并的规格数据CSV（使用第一个有效批次的规格）"""
        # 找到第一个有效的批次来获取规格信息
        first_lot = None
        for lot_id, lot in lots.items():
            if lot and (hasattr(lot, 'params') and lot.params):
                first_lot = lot
                break
        
        if not first_lot:
            # 如果没有找到有params的批次，使用第一个批次
            first_lot = list(lots.values())[0]
        
        # 使用现有的规格生成逻辑，但使用合并的文件名
        if hasattr(first_lot, 'params') and first_lot.params:
            # 检查是否是Lion数据
            param_ids = [param.id for param in first_lot.params]
            lion_indicators = ['TEST_NUM', 'KELVIN_CHECK', 'IR_35V', 'VBR_0P25mA', 'VBR_1mA']
            
            if any(indicator in param_ids for indicator in lion_indicators):
                # 这是Lion数据，使用Lion专用格式
                return self._generate_combined_lion_spec_csv(first_lot, output_dir, combined_name, timestamp)
        
        # 使用标准格式
        spec_data = []
        
        if hasattr(first_lot, 'params') and first_lot.params:
            # 从CPParameter对象生成规格数据
            for param in first_lot.params:
                spec_row = {
                    'Parameter': param.id,
                    'Unit': getattr(param, 'unit', ''),
                    'LimitL': getattr(param, 'sl', None),
                    'LimitU': getattr(param, 'su', None),
                    'LSL': getattr(param, 'sl', None),
                    'USL': getattr(param, 'su', None),
                    'Target': getattr(param, 'target', None)
                }
                spec_data.append(spec_row)
        else:
            # 从芯片数据中推断参数规格
            if first_lot.wafers and first_lot.wafers[0].chip_data is not None:
                sample_data = first_lot.wafers[0].chip_data
                param_columns = [col for col in sample_data.columns 
                               if col not in ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']]
                
                for param in param_columns:
                    spec_row = {
                        'Parameter': param,
                        'Unit': '',
                        'LimitL': None,
                        'LimitU': None,
                        'LSL': None,
                        'USL': None,
                        'Target': None
                    }
                    spec_data.append(spec_row)
        
        if not spec_data:
            # 创建空的规格文件
            spec_data = [{
                'Parameter': 'No_Parameters',
                'Unit': '',
                'LimitL': None,
                'LimitU': None,
                'LSL': None,
                'USL': None,
                'Target': None
            }]
        
        # 创建DataFrame
        spec_df = pd.DataFrame(spec_data)
        
        # 生成文件路径
        filename = f"{combined_name}_spec_{timestamp}.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        spec_df.to_csv(file_path, index=False)
        self.logger.info(f"生成合并规格数据CSV: {file_path} ({len(spec_df)}行)")
        
        return file_path
    
    def _generate_combined_lion_spec_csv(self, lot: CPLot, output_dir: str, combined_name: str, timestamp: str) -> str:
        """生成合并的Lion专用格式规格CSV - 使用实际数据中TEST_NUM右边的所有参数"""
        
        # 从第一个晶圆的spec_data中获取参数信息
        spec_data = None
        if lot.wafers and len(lot.wafers) > 0:
            # 查找有spec_data的晶圆
            for wafer in lot.wafers:
                if hasattr(wafer, 'spec_data') and wafer.spec_data is not None:
                    spec_data = wafer.spec_data
                    self.logger.info(f"找到规格数据，来源晶圆: {wafer.wafer_id}")
                    break
        
        if spec_data is None:
            # 如果没有spec_data，创建空文件
            self.logger.warning("没有找到Lion格式的规格数据，创建空规格文件")
            spec_df = pd.DataFrame([
                ['Parameter'],
                ['UNIT'],
                ['LIMIT_LOW'], 
                ['LIMIT_HIGH']
            ])
        else:
            # 获取TEST_NUM右边的所有参数列
            all_columns = list(spec_data.columns)
            self.logger.info(f"规格数据总列数: {len(all_columns)}")
            
            if 'TEST_NUM' in all_columns:
                test_num_index = all_columns.index('TEST_NUM')
                # TEST_NUM往右的所有列都是有效参数（包括TEST_NUM本身）
                param_columns = all_columns[test_num_index:]
                self.logger.info(f"TEST_NUM位置: {test_num_index}, 有效参数数量: {len(param_columns)}")
            else:
                # 如果没有TEST_NUM，使用所有参数列（排除基础字段）
                skip_columns = ['SITE_NUM', 'PART_INDEX', 'PASSFG', 'SOFT_BIN', 'T_TIME', 'X_COORD', 'Y_COORD']
                param_columns = [col for col in all_columns if col not in skip_columns]
                self.logger.info(f"没有找到TEST_NUM，使用所有参数列，数量: {len(param_columns)}")
            
            # 构建横向排列的数据
            param_row = ['Parameter'] + param_columns
            
            # 构建UNIT行
            unit_row = ['UNIT']
            for col in param_columns:
                if 'UNIT' in spec_data.index and pd.notna(spec_data.loc['UNIT', col]):
                    unit_val = str(spec_data.loc['UNIT', col])
                    if unit_val.lower() != 'nan':
                        unit_row.append(unit_val)
                    else:
                        unit_row.append('')
                else:
                    unit_row.append('')
            
            # 构建LIMIT_LOW行
            limit_low_row = ['LIMIT_LOW']
            for col in param_columns:
                if 'LIMIT_LOW' in spec_data.index and pd.notna(spec_data.loc['LIMIT_LOW', col]):
                    limit_val = str(spec_data.loc['LIMIT_LOW', col])
                    if limit_val.lower() != 'nan':
                        limit_low_row.append(limit_val)
                    else:
                        limit_low_row.append('')
                else:
                    limit_low_row.append('')
            
            # 构建LIMIT_HIGH行
            limit_high_row = ['LIMIT_HIGH']
            for col in param_columns:
                if 'LIMIT_HIGH' in spec_data.index and pd.notna(spec_data.loc['LIMIT_HIGH', col]):
                    limit_val = str(spec_data.loc['LIMIT_HIGH', col])
                    if limit_val.lower() != 'nan':
                        limit_high_row.append(limit_val)
                    else:
                        limit_high_row.append('')
                else:
                    limit_high_row.append('')
            
            # 创建DataFrame
            spec_df = pd.DataFrame([param_row, unit_row, limit_low_row, limit_high_row])
            self.logger.info(f"生成规格数据表格: {spec_df.shape[0]} 行 x {spec_df.shape[1]} 列")
        
        # 生成文件路径
        filename = f"{combined_name}_spec_{timestamp}.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件（不包含index，不包含header）
        spec_df.to_csv(file_path, index=False, header=False)
        self.logger.info(f"生成Lion格式规格数据CSV: {file_path} ({len(spec_df)}行)")
        
        return file_path
    
    def _standardize_wafer_id(self, wafer_id_series) -> pd.Series:
        """
        标准化Wafer_ID为整数类型
        
        Args:
            wafer_id_series: Wafer_ID序列
            
        Returns:
            pd.Series: 标准化后的Wafer_ID序列
        """
        try:
            # 尝试转换为整数
            if wafer_id_series.dtype == 'object':
                # 如果是字符串，去除前缀后转换
                return wafer_id_series.astype(str).str.extract(r'(\d+)')[0].astype(int)
            else:
                return wafer_id_series.astype(int)
        except:
            # 如果转换失败，保持原样
            return wafer_id_series


# 便捷函数
def generate_standard_csvs(lot: CPLot, output_dir: str) -> Dict[str, str]:
    """
    生成标准CSV文件的便捷函数
    
    Args:
        lot: CPLot对象
        output_dir: 输出目录
        
    Returns:
        Dict[str, str]: 生成的文件路径字典
    """
    generator = StandardCSVGenerator()
    return generator.generate_standard_csvs(lot, output_dir)


def batch_generate_csvs(lots: Dict[str, CPLot], output_dir: str) -> Dict[str, Dict[str, str]]:
    """
    批量生成标准CSV文件的便捷函数
    
    Args:
        lots: lot_id到CPLot对象的映射
        output_dir: 输出目录
        
    Returns:
        Dict[str, Dict[str, str]]: lot_id到文件路径字典的映射
    """
    generator = StandardCSVGenerator()
    results = {}
    
    for lot_id, lot in lots.items():
        try:
            file_paths = generator.generate_standard_csvs(lot, output_dir)
            results[lot_id] = file_paths
            logger.info(f"批量生成CSV成功: {lot_id}")
        except Exception as e:
            logger.error(f"批量生成CSV失败 {lot_id}: {e}")
            results[lot_id] = {'error': str(e)}
    
    return results


def generate_combined_csvs(lots: Dict[str, CPLot], output_dir: str, combined_name: str = "combined") -> Dict[str, str]:
    """
    生成合并多批次的标准CSV文件
    
    Args:
        lots: lot_id到CPLot对象的映射
        output_dir: 输出目录
        combined_name: 合并文件的名称前缀
        
    Returns:
        Dict[str, str]: 生成的合并文件路径字典
    """
    generator = StandardCSVGenerator()
    return generator.generate_combined_standard_csvs(lots, output_dir, combined_name)