#!/usr/bin/env python3
"""
Lion公司数据清洗工具

专门针对Lion公司Excel数据格式的清洗处理工具。
支持单批次和多批次数据清洗，生成标准化的CSV输出文件。

Lion公司数据特点：
- Excel格式(.xlsx)，包含summary_information和dut_data工作表
- dut_data前3行为参数规格信息(UNIT, LIMIT_LOW, LIMIT_HIGH)
- 从第4行开始为实际测试数据
- 批次文件夹通常以F开头(如F25130244)

使用方法：
1. 单批次处理：python clean_lion_data.py ./data/F25130244
2. 多批次处理：python clean_lion_data.py ./data
3. 指定输出：python clean_lion_data.py ./data --output ./output_lion
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cp_data_processor.readers.unified_reader import read_cp_data
from cp_data_processor.processing.standard_csv_generator import generate_standard_csvs

class LionDataCleaner:
    """Lion公司数据清洗器"""
    
    def __init__(self, output_dir: str = "./output_lion_models"):
        """
        初始化Lion数据清洗器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.logger = self._setup_logging()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Lion数据清洗 - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('lion_data_cleaning.log', encoding='utf-8')
            ]
        )
        return logging.getLogger('LionDataCleaner')
    
    def _is_lion_batch_dir(self, path: str) -> bool:
        """
        判断是否为Lion批次目录
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 是否为Lion批次目录
        """
        if not os.path.isdir(path):
            return False
        
        dir_name = os.path.basename(path)
        # Lion批次目录通常以F开头，包含数字
        if not dir_name.startswith('F') or not any(c.isdigit() for c in dir_name):
            return False
        
        # 检查是否包含Excel文件
        excel_files = [f for f in os.listdir(path) if f.endswith('.xlsx')]
        return len(excel_files) > 0
    
    def clean_single_batch(self, batch_path: str) -> bool:
        """
        清洗单个Lion批次数据
        
        Args:
            batch_path: 批次目录路径或Excel文件路径
            
        Returns:
            bool: 清洗成功返回True
        """
        try:
            if os.path.isfile(batch_path) and batch_path.endswith('.xlsx'):
                # 处理单个Excel文件
                batch_id = Path(batch_path).stem
                excel_file = batch_path
                self.logger.info(f"开始清洗Lion Excel文件: {batch_id}")
            elif os.path.isdir(batch_path):
                # 处理批次目录
                batch_id = os.path.basename(batch_path)
                self.logger.info(f"开始清洗Lion批次目录: {batch_id}")
                
                # 查找Excel文件
                excel_files = [f for f in os.listdir(batch_path) if f.endswith('.xlsx')]
                if not excel_files:
                    self.logger.warning(f"批次目录 {batch_id} 中没有Excel文件")
                    return False
                
                # 使用第一个Excel文件（通常一个批次目录包含多个晶圆的Excel文件）
                excel_file = os.path.join(batch_path, excel_files[0])
                self.logger.info(f"批次 {batch_id} 包含 {len(excel_files)} 个Excel文件，使用: {excel_files[0]}")
            else:
                self.logger.error(f"无效的输入路径: {batch_path}")
                return False
            
            # 使用Lion适配器读取数据
            self.logger.info(f"读取Lion数据: {excel_file}")
            lot_data = read_cp_data(excel_file)
            
            if not lot_data:
                self.logger.error(f"无法读取Lion数据: {excel_file}")
                return False
            
            self.logger.info(f"成功读取Lion批次: {lot_data.lot_id} (晶圆数: {len(lot_data.wafers)})")
            
            # 显示Lion数据特征
            if lot_data.wafers:
                sample_wafer = lot_data.wafers[0]
                if hasattr(sample_wafer, 'chip_data') and sample_wafer.chip_data is not None:
                    chip_count = len(sample_wafer.chip_data)
                    param_count = len([col for col in sample_wafer.chip_data.columns 
                                     if col not in ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']])
                    self.logger.info(f"数据特征: 每晶圆约{chip_count}个芯片, {param_count}个测试参数")
            
            # 生成清洗后的标准CSV文件
            self.logger.info("开始生成清洗后的CSV文件...")
            file_paths = generate_standard_csvs(lot_data, self.output_dir)
            
            # 报告生成结果
            self.logger.info(f"Lion批次 {batch_id} 清洗完成:")
            for file_type, file_path in file_paths.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    # 计算行数
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f) - 1  # 减去表头
                    
                    self.logger.info(f"  {file_type.upper():8}: {os.path.basename(file_path)}")
                    self.logger.info(f"           大小: {file_size:,} 字节, 数据行数: {line_count:,}")
                else:
                    self.logger.error(f"  {file_type.upper():8}: 文件生成失败")
            
            return True
            
        except Exception as e:
            self.logger.error(f"清洗Lion批次失败 {batch_path}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def clean_multiple_batches(self, data_dir: str, combined: bool = True) -> dict:
        """
        清洗多个Lion批次数据
        
        Args:
            data_dir: 包含多个批次目录的数据目录
            combined: 是否合并所有批次为3个CSV文件（默认True）
            
        Returns:
            dict: 批次ID到处理结果的映射
        """
        if not os.path.exists(data_dir):
            self.logger.error(f"数据目录不存在: {data_dir}")
            return {}
        
        self.logger.info(f"扫描Lion数据目录: {data_dir}")
        
        # 查找所有Lion批次目录
        batch_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if self._is_lion_batch_dir(item_path):
                batch_dirs.append((item, item_path))
        
        if not batch_dirs:
            self.logger.error(f"在 {data_dir} 中没有找到Lion批次目录")
            self.logger.info("Lion批次目录应该:")
            self.logger.info("1. 以F开头并包含数字")
            self.logger.info("2. 包含.xlsx文件")
            return {}
        
        self.logger.info(f"发现 {len(batch_dirs)} 个Lion批次目录: {[name for name, _ in batch_dirs]}")
        
        if combined:
            # 合并模式：所有批次合并为3个CSV文件
            return self._clean_multiple_batches_combined(batch_dirs)
        else:
            # 独立模式：每个批次生成独立的3个CSV文件
            return self._clean_multiple_batches_individual(batch_dirs)
    
    def _clean_multiple_batches_combined(self, batch_dirs: list) -> dict:
        """合并模式：多个批次合并为3个CSV文件"""
        from cp_data_processor.processing.standard_csv_generator import generate_combined_csvs
        
        self.logger.info("使用合并模式处理多个Lion批次")
        
        # 收集所有批次数据
        lots = {}
        results = {}
        
        for batch_id, batch_path in batch_dirs:
            self.logger.info(f"读取Lion批次: {batch_id}")
            try:
                # 查找Excel文件
                excel_files = [f for f in os.listdir(batch_path) if f.endswith('.xlsx')]
                if not excel_files:
                    self.logger.warning(f"批次目录 {batch_id} 中没有Excel文件，跳过")
                    results[batch_id] = False
                    continue
                
                # 使用第一个Excel文件读取批次数据
                first_file = os.path.join(batch_path, excel_files[0])
                self.logger.info(f"批次 {batch_id}: {len(excel_files)} 个Excel文件，使用 {excel_files[0]}")
                
                lot_data = read_cp_data(first_file)
                if lot_data:
                    lots[batch_id] = lot_data
                    results[batch_id] = True
                    self.logger.info(f"✓ 批次 {batch_id}: 晶圆数 {len(lot_data.wafers)}")
                else:
                    self.logger.error(f"✗ 批次 {batch_id}: 数据读取失败")
                    results[batch_id] = False
                    
            except Exception as e:
                self.logger.error(f"✗ 批次 {batch_id}: {e}")
                results[batch_id] = False
        
        if not lots:
            self.logger.error("没有读取到有效的Lion批次数据")
            return results
        
        self.logger.info(f"成功读取 {len(lots)} 个批次，开始合并生成CSV文件...")
        
        try:
            # 生成合并的CSV文件
            combined_name = "lion_multi_batches_combined"
            file_paths = generate_combined_csvs(lots, self.output_dir, combined_name)
            
            self.logger.info("=" * 60)
            self.logger.info("Lion多批次合并清洗完成！")
            self.logger.info("=" * 60)
            
            # 显示生成的文件信息
            for file_type, file_path in file_paths.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f) - 1  # 减去表头
                    
                    self.logger.info(f"  {file_type.upper():8}: {os.path.basename(file_path)}")
                    self.logger.info(f"           大小: {file_size:,} 字节, 数据行数: {line_count:,}")
                else:
                    self.logger.error(f"  {file_type.upper():8}: 文件生成失败")
            
            self.logger.info(f"合并文件已保存到: {self.output_dir}")
            return results
            
        except Exception as e:
            self.logger.error(f"生成合并CSV文件失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # 将所有批次标记为失败
            for batch_id in results:
                results[batch_id] = False
            return results
    
    def _clean_multiple_batches_individual(self, batch_dirs: list) -> dict:
        """独立模式：每个批次生成独立的3个CSV文件"""
        self.logger.info("使用独立模式处理多个Lion批次")
        
        results = {}
        successful = 0
        
        for batch_id, batch_path in batch_dirs:
            self.logger.info("-" * 60)
            success = self.clean_single_batch(batch_path)
            results[batch_id] = success
            if success:
                successful += 1
                self.logger.info(f"✓ 批次 {batch_id} 清洗成功")
            else:
                self.logger.error(f"✗ 批次 {batch_id} 清洗失败")
        
        self.logger.info("=" * 60)
        self.logger.info(f"Lion多批次数据清洗完成: {successful}/{len(batch_dirs)} 成功")
        
        if successful < len(batch_dirs):
            self.logger.warning("部分批次清洗失败，请检查日志获取详细信息")
        
        return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Lion公司数据清洗工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python clean_lion_data.py ./data/F25130244              # 清洗单个批次
  python clean_lion_data.py ./data                        # 清洗多个批次（合并为3个CSV）
  python clean_lion_data.py ./data --individual           # 每个批次生成独立的3个CSV
  python clean_lion_data.py ./data --output ./lion_clean  # 指定输出目录
  python clean_lion_data.py file.xlsx                     # 清洗单个Excel文件

输出说明:
  默认合并模式: 所有批次合并为3个CSV文件:
  - lion_multi_batches_combined_cleaned_*.csv: 所有批次的芯片测试数据
  - lion_multi_batches_combined_yield_*.csv:   所有批次的良率统计和参数平均值  
  - lion_multi_batches_combined_spec_*.csv:    参数规格信息
  
  独立模式 (--individual): 每个批次生成独立的3个CSV文件
        """
    )
    
    parser.add_argument(
        'input_path',
        help='输入路径：批次目录、数据根目录或Excel文件'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='./output_lion_models',
        help='输出目录 (默认: ./output_lion_models)'
    )
    
    parser.add_argument(
        '--individual',
        action='store_true',
        help='独立模式：每个批次生成独立的3个CSV文件（默认为合并模式）'
    )
    
    args = parser.parse_args()
    
    # 创建Lion数据清洗器
    cleaner = LionDataCleaner(args.output)
    
    cleaner.logger.info("=" * 80)
    cleaner.logger.info("Lion公司数据清洗工具启动")
    cleaner.logger.info("=" * 80)
    cleaner.logger.info(f"输入路径: {args.input_path}")
    cleaner.logger.info(f"输出目录: {args.output}")
    cleaner.logger.info(f"处理模式: {'独立文件模式' if args.individual else '合并模式'}")
    
    try:
        if os.path.isfile(args.input_path) and args.input_path.endswith('.xlsx'):
            # 单个Excel文件
            cleaner.logger.info("模式: 单个Excel文件清洗")
            success = cleaner.clean_single_batch(args.input_path)
            if not success:
                sys.exit(1)
                
        elif os.path.isdir(args.input_path):
            # 检查是否为单个批次目录
            if cleaner._is_lion_batch_dir(args.input_path):
                cleaner.logger.info("模式: 单个批次清洗")
                success = cleaner.clean_single_batch(args.input_path)
                if not success:
                    sys.exit(1)
            else:
                # 多批次目录
                cleaner.logger.info("模式: 多批次清洗")
                results = cleaner.clean_multiple_batches(args.input_path, combined=not args.individual)
                if not results or not any(results.values()):
                    cleaner.logger.error("所有批次清洗都失败了！")
                    sys.exit(1)
        else:
            cleaner.logger.error(f"无效的输入路径: {args.input_path}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        cleaner.logger.info("用户中断清洗过程")
        sys.exit(1)
    except Exception as e:
        cleaner.logger.error(f"清洗过程中发生错误: {e}")
        import traceback
        cleaner.logger.error(traceback.format_exc())
        sys.exit(1)
    
    cleaner.logger.info("=" * 80)
    cleaner.logger.info("Lion公司数据清洗完成！")
    cleaner.logger.info(f"清洗后的文件已保存到: {args.output}")
    cleaner.logger.info("=" * 80)

if __name__ == "__main__":
    main()