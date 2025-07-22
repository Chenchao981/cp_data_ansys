#!/usr/bin/env python3
"""
Lion公司多批次数据批量处理器

自动发现./data目录下的所有批次数据，按批次分组处理，
为每个批次生成包含所有晶圆数据的标准CSV文件。

使用方法:
    python lion_batch_processor.py

输出:
    ./output/批次ID_cleaned.csv  - 该批次所有晶圆的测试数据
    ./output/批次ID_yield.csv   - 该批次所有晶圆的良率数据  
    ./output/批次ID_spec.csv    - 该批次的参数规格数据
"""

import os
import sys
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cp_data_processor.readers.unified_reader import batch_read_cp_data
from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
from cp_data_processor.data_models.cp_data import CPLot

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def discover_batch_files(data_dir: Path) -> Dict[str, List[str]]:
    """
    发现数据目录中的所有批次文件
    
    Args:
        data_dir: 数据根目录
        
    Returns:
        Dict[str, List[str]]: 批次ID -> 文件路径列表的映射
    """
    batch_files = defaultdict(list)
    
    print(f"🔍 扫描数据目录: {data_dir}")
    
    # 扫描所有子目录
    for batch_dir in data_dir.iterdir():
        if not batch_dir.is_dir():
            continue
            
        print(f"  📁 检查批次目录: {batch_dir.name}")
        
        # 查找Excel文件
        excel_files = list(batch_dir.glob("*.xlsx"))
        excel_files.extend(list(batch_dir.glob("*.xls")))
        
        # 过滤掉临时文件
        excel_files = [f for f in excel_files if not f.name.startswith("~$")]
        
        if excel_files:
            # 从第一个文件提取批次ID
            first_file = excel_files[0]
            batch_id = first_file.stem.split('_')[0] if '_' in first_file.stem else first_file.stem
            
            # 按文件名排序确保处理顺序一致
            sorted_files = sorted([str(f) for f in excel_files])
            batch_files[batch_id] = sorted_files
            
            print(f"    ✓ 发现批次 {batch_id}: {len(sorted_files)} 个文件")
        else:
            print(f"    ⚠️  目录 {batch_dir.name} 中没有找到Excel文件")
    
    return dict(batch_files)


def create_batch_lot(individual_lots: Dict[str, CPLot]) -> CPLot:
    """
    将多个单晶圆CPLot合并为一个包含所有晶圆的CPLot
    
    Args:
        individual_lots: file_path -> CPLot的映射
        
    Returns:
        CPLot: 合并后的批次对象
    """
    if not individual_lots:
        raise ValueError("没有提供数据")
    
    # 获取批次信息（假设所有文件属于同一批次）
    first_lot = next(iter(individual_lots.values()))
    lot_id = first_lot.lot_id
    
    # 创建合并后的CPLot
    batch_lot = CPLot(
        lot_id=lot_id,
        product=first_lot.product,
        wafer_count=len(individual_lots)
    )
    
    # 收集所有晶圆和参数
    all_wafers = []
    all_params = []
    all_chip_data = []
    
    for file_path, lot in individual_lots.items():
        # 添加晶圆
        all_wafers.extend(lot.wafers)
        
        # 收集参数（避免重复）
        if lot.params and not all_params:
            all_params = lot.params
        
        # 收集芯片数据
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                all_chip_data.append(wafer.chip_data)
    
    batch_lot.wafers = all_wafers
    batch_lot.params = all_params
    
    # 合并所有芯片数据
    if all_chip_data:
        batch_lot.combined_data = pd.concat(all_chip_data, ignore_index=True)
    
    return batch_lot


def process_single_batch(batch_id: str, file_paths: List[str], output_dir: Path) -> bool:
    """
    处理单个批次的数据
    
    Args:
        batch_id: 批次ID
        file_paths: 该批次的文件路径列表
        output_dir: 输出目录
        
    Returns:
        bool: 处理成功返回True
    """
    try:
        print(f"\n📦 处理批次: {batch_id}")
        print(f"   文件数量: {len(file_paths)}")
        
        # 显示文件列表
        for i, file_path in enumerate(file_paths, 1):
            filename = Path(file_path).name
            print(f"     {i:2d}. {filename}")
        
        # 1. 批量读取该批次的所有文件
        print(f"   📖 读取数据...")
        individual_lots = batch_read_cp_data(file_paths)
        
        if not individual_lots:
            print(f"   ❌ 批次 {batch_id}: 没有成功读取任何文件")
            return False
        
        print(f"   ✓ 成功读取 {len(individual_lots)} 个文件")
        
        # 统计晶圆信息
        total_chips = 0
        wafer_ids = []
        for file_path, lot in individual_lots.items():
            for wafer in lot.wafers:
                wafer_ids.append(wafer.wafer_id)
                total_chips += wafer.chip_count
        
        print(f"   📊 数据统计:")
        print(f"     晶圆数: {len(wafer_ids)}")
        print(f"     晶圆ID: {sorted(wafer_ids)}")
        print(f"     总芯片数: {total_chips}")
        
        # 2. 合并为批次级别的数据
        print(f"   🔗 合并数据...")
        batch_lot = create_batch_lot(individual_lots)
        
        # 3. 生成标准CSV文件
        print(f"   📄 生成CSV文件...")
        generator = StandardCSVGenerator()
        file_paths_generated = generator.generate_standard_csvs(batch_lot, str(output_dir))
        
        print(f"   ✅ 批次 {batch_id} 处理完成!")
        print(f"   📁 生成的文件:")
        for csv_type, path in file_paths_generated.items():
            filename = Path(path).name
            file_size = Path(path).stat().st_size / 1024  # KB
            print(f"     {csv_type:8s}: {filename} ({file_size:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 批次 {batch_id} 处理失败: {e}")
        logger.error(f"处理批次 {batch_id} 失败", exc_info=True)
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🦁 Lion公司多批次数据批量处理器")
    print("=" * 60)
    
    # 设置路径
    data_dir = project_root / "data"
    output_dir = project_root / "output"
    
    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)
    
    # 检查数据目录
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        return False
    
    # 1. 发现所有批次文件
    batch_files = discover_batch_files(data_dir)
    
    if not batch_files:
        print("❌ 没有发现任何批次数据")
        return False
    
    print(f"\n📋 发现 {len(batch_files)} 个批次:")
    total_files = 0
    for batch_id, files in batch_files.items():
        print(f"  🎯 {batch_id}: {len(files)} 个文件")
        total_files += len(files)
    
    print(f"\n📊 总计: {total_files} 个文件需要处理")
    
    # 2. 逐个处理每个批次
    print(f"\n🚀 开始批量处理...")
    
    success_count = 0
    failed_batches = []
    
    for batch_id, file_paths in batch_files.items():
        success = process_single_batch(batch_id, file_paths, output_dir)
        if success:
            success_count += 1
        else:
            failed_batches.append(batch_id)
    
    # 3. 处理结果汇总
    print("\n" + "=" * 60)
    print("📈 处理结果汇总")
    print("=" * 60)
    
    print(f"✅ 成功处理: {success_count} 个批次")
    
    if failed_batches:
        print(f"❌ 失败批次: {len(failed_batches)} 个")
        for batch_id in failed_batches:
            print(f"     - {batch_id}")
    
    print(f"\n📁 输出目录: {output_dir}")
    
    # 显示生成的文件
    csv_files = list(output_dir.glob("*.csv"))
    if csv_files:
        print(f"📄 生成的CSV文件:")
        for csv_file in sorted(csv_files):
            file_size = csv_file.stat().st_size / 1024  # KB
            print(f"     {csv_file.name} ({file_size:.1f} KB)")
    
    print("\n🎉 批量处理完成!")
    
    if success_count == len(batch_files):
        print("✨ 所有批次都处理成功!")
        return True
    else:
        print(f"⚠️  {len(failed_batches)} 个批次处理失败，请检查日志")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断处理")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        logger.error("程序异常", exc_info=True)
        sys.exit(1)