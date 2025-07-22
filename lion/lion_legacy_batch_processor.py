#!/usr/bin/env python3
"""
Lion公司批次处理器 [遗留版本]

== 注意 ==
这是Lion模块内的遗留批次处理器。
推荐使用项目根目录的 ../lion_batch_processor.py，它提供了更完整的功能。

原功能：支持处理整个批次文件夹下所有晶圆的数据，递归处理2层目录结构
新版优势：
- 自动发现批次目录
- 更好的错误处理和日志
- 统一的输出格式
- 详细的进度显示

保留原因：
- 包含特定的批次处理逻辑
- 可作为开发参考
- 某些特殊场景可能需要定制

建议：除非有特殊需求，否则使用 ../lion_batch_processor.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging
from typing import List, Dict, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lion.lion_reader import LionExcelReader
from lion.lion_adapter import LionAdapter
from cp_data_processor.readers.company_adapters.company_config import get_company_config

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LionBatchProcessor:
    """Lion公司批次处理器"""
    
    def __init__(self, data_root_dir: str = None, output_root_dir: str = None):
        """
        初始化批次处理器
        
        Args:
            data_root_dir: 数据根目录（包含批次文件夹）
            output_root_dir: 输出根目录
        """
        self.project_root = Path(__file__).parent.parent
        self.data_root_dir = Path(data_root_dir) if data_root_dir else self.project_root / "data"
        self.output_root_dir = Path(output_root_dir) if output_root_dir else self.project_root / "output_lion_models"
        self.reader = LionExcelReader()
        
        # 获取Lion适配器配置
        config = get_company_config('LION')
        if not config:
            raise ValueError("未找到Lion公司配置")
        self.adapter = LionAdapter(config)
        
        self.logger = logging.getLogger(f"{__name__}.LionBatchProcessor")
    
    def discover_batches(self) -> List[Tuple[str, Path]]:
        """
        发现所有批次文件夹
        
        Returns:
            List[Tuple[str, Path]]: (批次ID, 批次路径) 的列表
        """
        batches = []
        
        if not self.data_root_dir.exists():
            self.logger.error(f"数据根目录不存在: {self.data_root_dir}")
            return batches
        
        # 遍历根目录下的所有子目录
        for batch_dir in self.data_root_dir.iterdir():
            if batch_dir.is_dir():
                # 检查是否包含Excel文件
                excel_files = list(batch_dir.glob("*.xlsx")) + list(batch_dir.glob("*.xls"))
                if excel_files:
                    batch_id = batch_dir.name
                    batches.append((batch_id, batch_dir))
                    self.logger.info(f"发现批次: {batch_id} -> {len(excel_files)} 个文件")
        
        return batches
    
    def discover_wafers_in_batch(self, batch_dir: Path) -> List[Tuple[str, str, Path]]:
        """
        发现批次中的所有晶圆文件
        
        Args:
            batch_dir: 批次目录路径
            
        Returns:
            List[Tuple[str, str, Path]]: (批次ID, 晶圆ID, 文件路径) 的列表
        """
        wafers = []
        
        # 获取所有Excel文件
        excel_files = list(batch_dir.glob("*.xlsx")) + list(batch_dir.glob("*.xls"))
        
        for file_path in excel_files:
            if self.reader.can_read(str(file_path)):
                # 从文件名提取批次ID和晶圆ID
                filename = file_path.stem
                if '_' in filename:
                    lot_id, wafer_id = filename.split('_', 1)
                else:
                    lot_id = filename
                    wafer_id = "1"
                
                wafers.append((lot_id, wafer_id, file_path))
        
        # 按晶圆ID排序
        wafers.sort(key=lambda x: int(x[1]) if x[1].isdigit() else 0)
        
        return wafers
    
    def process_batch(self, batch_id: str, batch_dir: Path) -> bool:
        """
        处理单个批次的所有晶圆数据
        
        Args:
            batch_id: 批次ID
            batch_dir: 批次目录路径
            
        Returns:
            bool: 处理成功返回True
        """
        self.logger.info(f"开始处理批次: {batch_id}")
        
        try:
            # 发现批次中的所有晶圆文件
            wafers = self.discover_wafers_in_batch(batch_dir)
            if not wafers:
                self.logger.warning(f"批次 {batch_id} 中未找到有效的晶圆文件")
                return False
            
            self.logger.info(f"批次 {batch_id} 包含 {len(wafers)} 个晶圆文件")
            
            # 处理所有晶圆文件
            all_wafer_data = []
            batch_summary = {
                'batch_id': batch_id,
                'total_wafers': len(wafers),
                'processed_wafers': 0,
                'failed_wafers': 0,
                'wafer_summaries': []
            }
            
            for lot_id, wafer_id, file_path in wafers:
                try:
                    self.logger.info(f"  处理晶圆: {wafer_id} ({file_path.name})")
                    
                    # 读取单个晶圆数据
                    lot = self.reader.read_single_file(str(file_path))
                    
                    # 应用适配器
                    standardized_lot = self.adapter.standardize_data(lot)
                    
                    if standardized_lot.wafers:
                        wafer = standardized_lot.wafers[0]
                        
                        # 提取summary数据
                        summary_data = getattr(wafer, 'summary_data', {})
                        
                        wafer_summary = {
                            'lot_id': lot_id,
                            'wafer_id': wafer_id,
                            'gross_die': summary_data.get('gross_die', 0),
                            'good_die': summary_data.get('good_die', 0),
                            'yield': summary_data.get('yield', '0%'),
                            'param_counts': summary_data.get('param_counts', {}),
                            'file_path': str(file_path)
                        }
                        
                        all_wafer_data.append(wafer_summary)
                        batch_summary['wafer_summaries'].append(wafer_summary)
                        batch_summary['processed_wafers'] += 1
                        
                        self.logger.info(f"    晶圆 {wafer_id}: {wafer_summary['good_die']}/{wafer_summary['gross_die']} ({wafer_summary['yield']})")
                    
                except Exception as e:
                    self.logger.error(f"  处理晶圆 {wafer_id} 失败: {e}")
                    batch_summary['failed_wafers'] += 1
            
            # 生成批次汇总的yield.csv
            if all_wafer_data:
                yield_file = self.generate_batch_yield_csv(batch_id, all_wafer_data)
                self.logger.info(f"批次 {batch_id} yield文件已生成: {yield_file}")
            
            # 生成批次汇总报告
            self.generate_batch_summary_report(batch_id, batch_summary)
            
            self.logger.info(f"批次 {batch_id} 处理完成: {batch_summary['processed_wafers']} 成功, {batch_summary['failed_wafers']} 失败")
            return True
            
        except Exception as e:
            self.logger.error(f"处理批次 {batch_id} 失败: {e}")
            return False
    
    def generate_batch_yield_csv(self, batch_id: str, wafer_data: List[Dict]) -> Path:
        """
        生成批次级别的yield.csv文件
        
        Args:
            batch_id: 批次ID
            wafer_data: 所有晶圆的数据列表
            
        Returns:
            Path: 生成的文件路径
        """
        yield_data = []
        
        # 期望的参数列表
        expected_params = ['IR_35V', 'IR_1000V', 'IR_1200V', 'IR_1300V', 
                          'VBR_0P25mA', 'VBR_1mA', 'VF_10A', 'VF_20A', 'IR_1200V_Retest']
        
        for wafer_summary in wafer_data:
            # 基本信息
            yield_row = {
                'lot_id': wafer_summary['lot_id'],
                'wafer_id': wafer_summary['wafer_id'],
                'gross_die': wafer_summary['gross_die'],
                'good_die': wafer_summary['good_die'],
                'yield': wafer_summary['yield']
            }
            
            # 添加参数失败计数
            param_counts = wafer_summary['param_counts']
            for param in expected_params:
                yield_row[param] = param_counts.get(param, 0)
            
            yield_data.append(yield_row)
        
        # 创建DataFrame
        yield_df = pd.DataFrame(yield_data)
        
        # 确保列顺序正确
        columns_order = ['lot_id', 'wafer_id', 'gross_die', 'good_die', 'yield'] + expected_params
        yield_df = yield_df.reindex(columns=columns_order, fill_value=0)
        
        # 保存文件
        self.output_root_dir.mkdir(exist_ok=True)
        yield_file = self.output_root_dir / f"{batch_id}_batch_yield.csv"
        yield_df.to_csv(yield_file, index=False)
        
        self.logger.info(f"生成批次yield文件: {yield_file} ({len(yield_data)} 条记录)")
        return yield_file
    
    def generate_batch_summary_report(self, batch_id: str, batch_summary: Dict):
        """
        生成批次汇总报告
        
        Args:
            batch_id: 批次ID
            batch_summary: 批次汇总信息
        """
        report_file = self.output_root_dir / f"{batch_id}_batch_summary.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"批次处理汇总报告\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"批次ID: {batch_summary['batch_id']}\n")
            f.write(f"总晶圆数: {batch_summary['total_wafers']}\n")
            f.write(f"成功处理: {batch_summary['processed_wafers']}\n")
            f.write(f"处理失败: {batch_summary['failed_wafers']}\n")
            f.write(f"成功率: {batch_summary['processed_wafers']/batch_summary['total_wafers']*100:.1f}%\n\n")
            
            f.write(f"晶圆详情:\n")
            f.write(f"-" * 50 + "\n")
            for wafer in batch_summary['wafer_summaries']:
                f.write(f"晶圆 {wafer['wafer_id']:>2}: {wafer['good_die']:>4}/{wafer['gross_die']:<4} ({wafer['yield']:>7}) - {Path(wafer['file_path']).name}\n")
        
        self.logger.info(f"生成批次汇总报告: {report_file}")
    
    def process_all_batches(self) -> Dict[str, bool]:
        """
        处理所有批次
        
        Returns:
            Dict[str, bool]: 各批次的处理结果
        """
        self.logger.info("开始处理所有批次...")
        
        # 发现所有批次
        batches = self.discover_batches()
        if not batches:
            self.logger.warning("未发现任何批次数据")
            return {}
        
        results = {}
        
        for batch_id, batch_dir in batches:
            try:
                result = self.process_batch(batch_id, batch_dir)
                results[batch_id] = result
            except Exception as e:
                self.logger.error(f"处理批次 {batch_id} 时发生异常: {e}")
                results[batch_id] = False
        
        # 汇总结果
        successful_batches = [batch_id for batch_id, success in results.items() if success]
        failed_batches = [batch_id for batch_id, success in results.items() if not success]
        
        self.logger.info(f"批次处理完成: {len(successful_batches)} 成功, {len(failed_batches)} 失败")
        if successful_batches:
            self.logger.info(f"成功批次: {', '.join(successful_batches)}")
        if failed_batches:
            self.logger.warning(f"失败批次: {', '.join(failed_batches)}")
        
        return results


def main():
    """主函数"""
    print("=" * 60)
    print("Lion公司批次数据处理器")
    print("=" * 60)
    
    processor = LionBatchProcessor()
    results = processor.process_all_batches()
    
    print("=" * 60)
    print(f"处理完成，结果: {results}")
    print("=" * 60)


if __name__ == "__main__":
    main()