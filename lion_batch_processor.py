#!/usr/bin/env python3
"""
Lion公司多批次数据批量处理器

自动发现./data目录下的所有批次数据，合并为3个汇总CSV文件。

使用方法:
    python lion_batch_processor.py

输出:
    ./output/combined_cleaned.csv  - 所有批次合并的测试数据
    ./output/combined_yield.csv   - 所有批次合并的良率数据  
    ./output/combined_spec.csv    - 所有批次合并的参数规格数据
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

# 直接导入Lion专用模块，无需通用识别
from lion.lion_reader import LionExcelReader
from cp_data_processor.readers.company_adapters.company_config import get_company_config
from cp_data_processor.readers.company_adapters.lion_adapter import LIONAdapter
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


def process_lion_batch_files(file_paths: List[str]) -> Dict[str, CPLot]:
    """
    直接使用Lion读取器处理文件列表，无需通用识别
    
    Args:
        file_paths: Lion Excel文件路径列表
        
    Returns:
        Dict[str, CPLot]: 文件路径到CPLot对象的映射
    """
    # 获取Lion配置和适配器
    lion_config = get_company_config('LION')
    adapter = LIONAdapter(lion_config)
    
    results = {}
    failed_files = []
    
    for file_path in file_paths:
        try:
            print(f"    📄 处理: {Path(file_path).name}")
            
            # 使用Lion专用读取器
            reader = LionExcelReader([file_path])
            raw_lot = reader.read_file(file_path)
            
            # 使用Lion适配器标准化
            standardized_lot = adapter.transform_to_standard_format(raw_lot)
            
            results[file_path] = standardized_lot
            print(f"    ✓ 成功")
            
        except Exception as e:
            failed_files.append((file_path, str(e)))
            print(f"    ❌ 失败: {e}")
            logger.error(f"处理文件失败 {file_path}: {e}")
    
    if failed_files:
        print(f"   ⚠️  {len(failed_files)} 个文件处理失败")
    
    return results


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


def create_combined_lot(all_batch_lots: List[CPLot]) -> CPLot:
    """
    将多个批次的CPLot合并为一个超级CPLot
    
    保持正确的排序顺序：按批次顺序排列，每个批次内按wafer_id排序
    保持原始的Lot_ID不变
    
    Args:
        all_batch_lots: 所有批次CPLot的列表
        
    Returns:
        CPLot: 合并后的超级批次对象
    """
    if not all_batch_lots:
        raise ValueError("没有提供批次数据")
    
    # 创建合并后的CPLot，使用"COMBINED"作为lot_id（仅用于文件名生成）
    first_lot = all_batch_lots[0]
    combined_lot = CPLot(
        lot_id="COMBINED",
        product=first_lot.product,
        wafer_count=sum(lot.wafer_count for lot in all_batch_lots)
    )
    
    # 收集所有晶圆和参数（按批次顺序）
    all_wafers = []
    all_params = []
    all_chip_data = []
    
    # 按批次顺序处理，确保排序正确
    for batch_lot in all_batch_lots:
        print(f"   合并批次: {batch_lot.lot_id} ({len(batch_lot.wafers)} 个晶圆)")
        
        # 对当前批次的晶圆按wafer_id排序
        sorted_wafers = sorted(batch_lot.wafers, key=lambda w: int(w.wafer_id))
        all_wafers.extend(sorted_wafers)
        
        # 收集参数（避免重复）
        if batch_lot.params and not all_params:
            all_params = batch_lot.params
        
        # 收集芯片数据（保持批次顺序）
        if hasattr(batch_lot, 'combined_data') and batch_lot.combined_data is not None:
            # 确保芯片数据也按批次内的wafer_id排序
            batch_data = batch_lot.combined_data.copy()
            
            # 对Wafer_ID列进行数值排序
            if 'Wafer_ID' in batch_data.columns:
                batch_data['Wafer_ID_int'] = pd.to_numeric(batch_data['Wafer_ID'], errors='coerce')
                batch_data = batch_data.sort_values(['Wafer_ID_int'])
                batch_data = batch_data.drop('Wafer_ID_int', axis=1)
            
            all_chip_data.append(batch_data)
    
    combined_lot.wafers = all_wafers
    combined_lot.params = all_params
    
    # 合并所有芯片数据（按批次顺序）
    if all_chip_data:
        combined_lot.combined_data = pd.concat(all_chip_data, ignore_index=True)
    
    return combined_lot



def main():
    """主函数"""
    print("=" * 60)
    print("🦁 Lion公司多批次数据汇总处理器（简化版）")
    print("✨ 奥卡姆剃刀原则：人工确认Lion数据，无需自动识别")
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
    
    # 2. 处理所有批次并收集CPLot对象
    print(f"\n🚀 开始批量处理并汇总...")
    
    all_batch_lots = []
    success_count = 0
    failed_batches = []
    
    for batch_id, file_paths in batch_files.items():
        try:
            print(f"\n📦 处理批次: {batch_id}")
            print(f"   文件数量: {len(file_paths)}")
            
            # 显示文件列表
            for i, file_path in enumerate(file_paths, 1):
                filename = Path(file_path).name
                print(f"     {i:2d}. {filename}")
            
            # 1. 使用Lion专用处理器读取该批次的所有文件
            print(f"   📖 读取Lion数据...")
            individual_lots = process_lion_batch_files(file_paths)
            
            if not individual_lots:
                print(f"   ❌ 批次 {batch_id}: 没有成功读取任何文件")
                failed_batches.append(batch_id)
                continue
            
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
            all_batch_lots.append(batch_lot)
            
            print(f"   ✅ 批次 {batch_id} 处理完成!")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ 批次 {batch_id} 处理失败: {e}")
            logger.error(f"处理批次 {batch_id} 失败", exc_info=True)
            failed_batches.append(batch_id)
    
    # 3. 生成汇总CSV文件
    if all_batch_lots:
        print(f"\n🔄 生成汇总CSV文件...")
        
        try:
            # 合并所有批次数据
            combined_lot = create_combined_lot(all_batch_lots)
            
            # 生成汇总的标准CSV文件
            generator = StandardCSVGenerator()
            
            # 覆盖lot_id以生成combined_*的文件名
            original_lot_id = combined_lot.lot_id
            combined_lot.lot_id = "combined"
            
            file_paths_generated = generator.generate_standard_csvs(combined_lot, str(output_dir))
            
            # 恢复原始lot_id
            combined_lot.lot_id = original_lot_id
            
            print(f"   ✅ 汇总CSV文件生成完成!")
            print(f"   📁 生成的文件:")
            for csv_type, path in file_paths_generated.items():
                filename = Path(path).name
                file_size = Path(path).stat().st_size / 1024  # KB
                print(f"     {csv_type:8s}: {filename} ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"   ❌ 汇总CSV文件生成失败: {e}")
            logger.error("汇总CSV文件生成失败", exc_info=True)
    
    # 4. 处理结果汇总
    print("\n" + "=" * 60)
    print("📈 处理结果汇总")
    print("=" * 60)
    
    print(f"✅ 成功处理: {success_count} 个批次")
    
    if failed_batches:
        print(f"❌ 失败批次: {len(failed_batches)} 个")
        for batch_id in failed_batches:
            print(f"     - {batch_id}")
    
    print(f"\n📁 输出目录: {output_dir}")
    
    # 显示生成的汇总文件
    combined_csv_files = list(output_dir.glob("combined_*.csv"))
    if combined_csv_files:
        print(f"📄 生成的汇总CSV文件:")
        for csv_file in sorted(combined_csv_files):
            file_size = csv_file.stat().st_size / 1024  # KB
            print(f"     {csv_file.name} ({file_size:.1f} KB)")
    
    print("\n🎉 批量汇总处理完成!")
    
    if success_count > 0:
        print("✨ 汇总文件生成成功!")
        return True
    else:
        print("⚠️  没有成功处理任何批次")
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