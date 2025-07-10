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
        self.logger.info(f"开始生成{lot_id}的标准CSV文件")
        
        file_paths = {}
        
        try:
            # 1. 生成清洗数据CSV
            cleaned_path = self.generate_cleaned_csv(lot, output_dir)
            file_paths['cleaned'] = cleaned_path
            
            # 2. 生成良率数据CSV
            yield_path = self.generate_yield_csv(lot, output_dir)
            file_paths['yield'] = yield_path
            
            # 3. 生成规格数据CSV
            spec_path = self.generate_spec_csv(lot, output_dir)
            file_paths['spec'] = spec_path
            
            self.logger.info(f"标准CSV文件生成完成: {lot_id}")
            return file_paths
            
        except Exception as e:
            self.logger.error(f"生成标准CSV文件失败 {lot_id}: {e}")
            raise
    
    def generate_cleaned_csv(self, lot: CPLot, output_dir: str) -> str:
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
        
        # 确保列顺序：基本字段在前，测试参数在后
        basic_columns = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']
        param_columns = [col for col in combined_data.columns if col not in basic_columns]
        ordered_columns = [col for col in basic_columns if col in combined_data.columns] + param_columns
        combined_data = combined_data[ordered_columns]
        
        # 生成文件路径
        filename = f"{lot.lot_id}_cleaned.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        combined_data.to_csv(file_path, index=False)
        self.logger.info(f"生成清洗数据CSV: {file_path} ({len(combined_data)}行)")
        
        return file_path
    
    def generate_yield_csv(self, lot: CPLot, output_dir: str) -> str:
        """
        生成良率统计数据CSV
        
        格式: Lot_ID,Wafer_ID,Total_Chips,Good_Chips,Yield_Rate,Bin_1,Bin_2,...
        
        Args:
            lot: CPLot对象
            output_dir: 输出目录
            
        Returns:
            str: 生成的文件路径
        """
        if not lot.wafers:
            raise ValueError("CPLot中没有晶圆数据")
        
        yield_data = []
        
        for wafer in lot.wafers:
            # 计算晶圆级良率统计
            wafer_stats = self._calculate_wafer_yield(wafer, lot.lot_id)
            yield_data.append(wafer_stats)
        
        # 创建DataFrame
        yield_df = pd.DataFrame(yield_data)
        
        # 确保Wafer_ID为整数类型
        if 'Wafer_ID' in yield_df.columns:
            yield_df['Wafer_ID'] = self._standardize_wafer_id(yield_df['Wafer_ID'])
        
        # 按Wafer_ID排序
        yield_df = yield_df.sort_values('Wafer_ID')
        
        # 生成文件路径
        filename = f"{lot.lot_id}_yield.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        yield_df.to_csv(file_path, index=False)
        self.logger.info(f"生成良率数据CSV: {file_path} ({len(yield_df)}行)")
        
        return file_path
    
    def generate_spec_csv(self, lot: CPLot, output_dir: str) -> str:
        """
        生成参数规格数据CSV
        
        格式: Parameter,Unit,LimitL,LimitU,LSL,USL,Target
        
        Args:
            lot: CPLot对象
            output_dir: 输出目录
            
        Returns:
            str: 生成的文件路径
        """
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
        
        # 生成文件路径
        filename = f"{lot.lot_id}_spec.csv"
        file_path = os.path.join(output_dir, filename)
        
        # 保存文件
        spec_df.to_csv(file_path, index=False)
        self.logger.info(f"生成规格数据CSV: {file_path} ({len(spec_df)}行)")
        
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
            'Total_Chips': 0,
            'Good_Chips': 0,
            'Yield_Rate': 0.0
        }
        
        if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
            chip_data = wafer.chip_data
            total_chips = len(chip_data)
            
            if 'Bin' in chip_data.columns:
                # 计算各个Bin的数量
                bin_counts = chip_data['Bin'].value_counts()
                
                # 计算good chips (通常Bin=1是良品)
                good_chips = bin_counts.get(1, 0)
                
                # 更新统计信息
                stats['Total_Chips'] = total_chips
                stats['Good_Chips'] = good_chips
                stats['Yield_Rate'] = (good_chips / total_chips * 100) if total_chips > 0 else 0.0
                
                # 添加各个Bin的统计
                for bin_num in sorted(bin_counts.index):
                    stats[f'Bin_{bin_num}'] = bin_counts[bin_num]
        
        return stats
    
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