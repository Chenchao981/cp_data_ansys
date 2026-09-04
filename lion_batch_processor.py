#!/usr/bin/env python3
"""
Lion公司多批次数据批量处理器

自动发现./data目录下的所有批次数据，合并为3个汇总CSV文件。

使用方法:
    python lion_batch_processor.py

输出:
    ./output/{第一个批次号}_cleaned.csv  - 所有批次合并的测试数据
    ./output/{第一个批次号}_yield.csv   - 所有批次合并的良率数据  
    ./output/{第一个批次号}_spec.csv    - 所有批次合并的参数规格数据
"""

import os
import sys
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import logging
from copy import deepcopy

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接导入Lion专用模块，无需通用识别
from lion.lion_reader import LionExcelReader
from lion.lion_v2_adapter import LionV2Adapter
from lion.lion_v2_reader import LION_V2_FORMAT, LionV2Reader
from cp_data_processor.readers.company_adapters.company_config import get_company_config
from cp_data_processor.readers.company_adapters.lion_adapter import LIONAdapter
from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
from cp_data_processor.data_models.cp_data import CPLot, CPParameter

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LION_V1_FORMAT = "LION_V1"


def discover_batch_files(data_dir: Path) -> Dict[str, List[str]]:
    """
    发现单批次目录或产品目录下的多个批次文件。

    单批次：输入目录直接包含 Excel，输入目录名作为批次 ID。
    多批次：输入目录的第一层子目录分别包含 Excel。
    
    Args:
        data_dir: 数据根目录
        
    Returns:
        Dict[str, List[str]]: 批次ID -> 文件路径列表的映射
    """
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise ValueError(f"Lion输入目录不存在: {data_dir}")

    batch_files = defaultdict(list)

    print(f"扫描Lion数据目录: {data_dir}")

    direct_files = list(data_dir.glob("*.xlsx"))
    direct_files.extend(data_dir.glob("*.xls"))
    direct_files = sorted(
        (path for path in direct_files if not path.name.startswith("~$")),
        key=lambda path: path.name.lower(),
    )
    if direct_files:
        batch_files[data_dir.name] = [str(path) for path in direct_files]
        print(f"发现Lion单批次 {data_dir.name}: {len(direct_files)} 个文件")
        return dict(batch_files)

    # 输入目录不直接包含文件时，扫描第一层批次子目录。
    for batch_dir in sorted(
        (path for path in data_dir.iterdir() if path.is_dir()),
        key=lambda path: path.name.lower(),
    ):
        if not batch_dir.is_dir():
            continue

        print(f"  检查批次目录: {batch_dir.name}")

        # 查找Excel文件
        excel_files = list(batch_dir.glob("*.xlsx"))
        excel_files.extend(list(batch_dir.glob("*.xls")))

        # 过滤掉临时文件
        excel_files = [f for f in excel_files if not f.name.startswith("~$")]

        if excel_files:
            # 使用文件夹名称作为批次ID（Lion公司的文件夹名称就是lot_id）
            batch_id = batch_dir.name

            # 按文件名排序确保处理顺序一致
            sorted_files = [
                str(path)
                for path in sorted(excel_files, key=lambda path: path.name.lower())
            ]
            batch_files[batch_id] = sorted_files

            print(f"    发现Lion批次 {batch_id}: {len(sorted_files)} 个文件")
        else:
            print(f"    目录 {batch_dir.name} 中没有找到Excel文件")

    return dict(batch_files)


def detect_lion_format(file_path: str) -> str:
    """Detect one approved Lion format, failing closed on unknown/ambiguity."""

    v1_match = LionExcelReader().can_read(file_path)
    v2_match = LionV2Reader.can_read(file_path)
    matches = [
        format_name
        for format_name, matched in (
            (LION_V1_FORMAT, v1_match),
            (LION_V2_FORMAT, v2_match),
        )
        if matched
    ]
    if len(matches) != 1:
        if not matches:
            raise ValueError(
                f"未知或不受支持的 Lion 文件格式: {Path(file_path).name}"
            )
        raise ValueError(f"Lion 文件格式识别歧义: {Path(file_path).name}")
    return matches[0]


def process_lion_batch_files(file_paths: List[str]) -> Dict[str, CPLot]:
    """
    直接使用Lion读取器处理文件列表，无需通用识别
    
    Args:
        file_paths: Lion Excel文件路径列表
        
    Returns:
        Dict[str, CPLot]: 文件路径到CPLot对象的映射
    """
    if not file_paths:
        raise ValueError("没有提供 Lion 文件")

    detected_formats = {detect_lion_format(file_path) for file_path in file_paths}
    if len(detected_formats) != 1:
        raise ValueError(
            "同一 Lion 批次包含不同格式版本，已按 fail-closed 规则停止"
        )
    source_format = next(iter(detected_formats))

    if source_format == LION_V2_FORMAT:
        adapter = LionV2Adapter()
    else:
        lion_config = get_company_config('LION')
        adapter = LIONAdapter(lion_config)

    results = {}
    for file_path in file_paths:
        try:
            print(f"    📄 处理: {Path(file_path).name}")

            if source_format == LION_V2_FORMAT:
                raw_lot = LionV2Reader([file_path]).read()
            else:
                reader = LionExcelReader([file_path])
                raw_lot = reader.read_file(file_path)

            # 使用Lion适配器标准化
            standardized_lot = adapter.transform_to_standard_format(raw_lot)
            standardized_lot.source_format = source_format
            standardized_lot.parameter_schema = tuple(
                getattr(raw_lot, "parameter_schema", ())
            )
            results[file_path] = standardized_lot
            if source_format == LION_V1_FORMAT:
                print(
                    f"    ✓ 成功（动态参数 {len(standardized_lot.parameter_schema)} 个）"
                )
            else:
                print(f"    ✓ 成功")

        except Exception as e:
            print(f"    ❌ 失败: {e}")
            logger.error(f"处理文件失败 {file_path}: {e}")
            raise ValueError(
                f"Lion 批次处理失败，未返回部分结果: {Path(file_path).name}: {e}"
            ) from e

    return results


def _lot_spec_signature(lot: CPLot) -> tuple:
    return tuple(
        (
            parameter.id,
            parameter.unit,
            parameter.sl,
            parameter.su,
            tuple(getattr(parameter, "test_cond", []) or []),
        )
        for parameter in lot.params
    )


def _parameter_spec_signature(parameter: CPParameter) -> tuple:
    unit = parameter.unit
    if unit is not None:
        unit = str(unit).strip()
    return (
        unit,
        parameter.sl,
        parameter.su,
        tuple(getattr(parameter, "test_cond", []) or []),
    )


def _merge_dynamic_parameters(
    labeled_lots,
    *,
    context: str,
) -> List[CPParameter]:
    """Merge additive Lion V1 schemas while blocking same-name spec conflicts."""

    merged: Dict[str, CPParameter] = {}
    sources: Dict[str, str] = {}
    for source_label, lot in labeled_lots:
        for parameter in lot.params:
            existing = merged.get(parameter.id)
            if existing is None:
                merged[parameter.id] = deepcopy(parameter)
                sources[parameter.id] = source_label
                continue
            if _parameter_spec_signature(existing) != _parameter_spec_signature(
                parameter
            ):
                raise ValueError(
                    f"{context} 参数 {parameter.id} 规格冲突: "
                    f"{sources[parameter.id]}={_parameter_spec_signature(existing)}, "
                    f"{source_label}={_parameter_spec_signature(parameter)}"
                )
    return list(merged.values())


def _collect_parameter_union(lots: List[CPLot]) -> List[CPParameter]:
    """Collect parameter names across Lots without treating specs as global.

    Specifications are authoritative only inside their source Lot.  The returned
    objects provide a stable column union for the combined in-memory lot; they
    must not be used to emit a cross-Lot spec file.
    """

    merged: Dict[str, CPParameter] = {}
    for lot in lots:
        for parameter in lot.params:
            if parameter.id not in merged:
                merged[parameter.id] = deepcopy(parameter)
    return list(merged.values())


def _lion_spec_frame(parameters: List[CPParameter]) -> pd.DataFrame:
    """Build the existing horizontal Lion spec from a merged parameter union."""

    columns = [parameter.id for parameter in parameters]
    values = {
        parameter.id: {
            "UNIT": ""
            if parameter.unit in (None, "Unknown")
            else str(parameter.unit).strip(),
            "LIMIT_LOW": parameter.sl,
            "LIMIT_HIGH": parameter.su,
        }
        for parameter in parameters
    }
    return pd.DataFrame(values, index=["UNIT", "LIMIT_LOW", "LIMIT_HIGH"])[
        columns
    ]


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
    
    # 获取批次信息；格式、身份和 Pass Bin 必须片内一致。V2 仍要求
    # 完整规格一致；V1 允许参数增减，但同名参数的规格必须一致。
    first_lot = next(iter(individual_lots.values()))
    lot_id = first_lot.lot_id
    source_format = getattr(first_lot, "source_format", LION_V1_FORMAT)
    spec_signature = _lot_spec_signature(first_lot)
    for lot in individual_lots.values():
        if getattr(lot, "source_format", LION_V1_FORMAT) != source_format:
            raise ValueError("同一 Lion 批次包含不同格式版本")
        if lot.lot_id != lot_id or lot.product != first_lot.product:
            raise ValueError("同一 Lion 批次的 Lot_ID 或 product 不一致")
        if lot.pass_bin != first_lot.pass_bin:
            raise ValueError("同一 Lion 批次的 pass_bin 不一致")
        if (
            source_format != LION_V1_FORMAT
            and _lot_spec_signature(lot) != spec_signature
        ):
            raise ValueError(f"Lion 批次 {lot_id} 内部规格不一致")

    wafer_sources: Dict[str, str] = {}
    for file_path, lot in individual_lots.items():
        for wafer in lot.wafers:
            wafer_id = str(wafer.wafer_id)
            if wafer_id in wafer_sources:
                raise ValueError(
                    f"Lion 批次 {lot_id} 存在重复 Wafer_ID {wafer_id}: "
                    f"{Path(wafer_sources[wafer_id]).name}, {Path(file_path).name}"
                )
            wafer_sources[wafer_id] = file_path

    if source_format == LION_V1_FORMAT:
        merged_params = _merge_dynamic_parameters(
            [
                (Path(file_path).name, lot)
                for file_path, lot in individual_lots.items()
            ],
            context=f"Lion 批次 {lot_id}",
        )
    else:
        merged_params = deepcopy(first_lot.params)
    
    # 创建合并后的CPLot
    batch_lot = CPLot(
        lot_id=lot_id,
        product=first_lot.product,
        wafer_count=len(individual_lots),
        pass_bin=first_lot.pass_bin,
    )
    batch_lot.source_format = source_format
    
    # 收集所有晶圆和参数
    all_wafers = []
    all_params = merged_params
    all_chip_data = []
    
    for file_path, lot in individual_lots.items():
        # 添加晶圆
        all_wafers.extend(lot.wafers)
        
        # 收集芯片数据
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                all_chip_data.append(wafer.chip_data)
    
    batch_lot.wafers = all_wafers
    batch_lot.params = all_params
    if source_format == LION_V1_FORMAT:
        batch_lot.lion_spec_data = _lion_spec_frame(all_params)
        batch_lot.parameter_schemas = tuple(
            tuple(getattr(lot, "parameter_schema", ()))
            for lot in individual_lots.values()
        )
    
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
    
    source_formats = {
        getattr(lot, "source_format", LION_V1_FORMAT) for lot in all_batch_lots
    }
    if len(source_formats) != 1:
        raise ValueError("同一次 Lion 运行包含不同格式版本，已停止合并")
    pass_bins = {lot.pass_bin for lot in all_batch_lots}
    if len(pass_bins) != 1:
        raise ValueError("同一次 Lion 运行包含不同 pass_bin，已停止合并")
    products = {lot.product for lot in all_batch_lots}
    if len(products) != 1:
        raise ValueError("同一次 Lion 运行包含不同 product，已停止合并")

    # 创建合并后的CPLot，使用"COMBINED"作为lot_id（仅用于文件名生成）
    first_lot = all_batch_lots[0]
    combined_lot = CPLot(
        lot_id="COMBINED",
        product=first_lot.product,
        wafer_count=sum(lot.wafer_count for lot in all_batch_lots),
        pass_bin=first_lot.pass_bin,
    )
    combined_lot.source_format = next(iter(source_formats))
    
    # 收集所有晶圆和参数（按批次顺序）
    all_wafers = []
    if next(iter(source_formats)) == LION_V1_FORMAT:
        # 不同 Lot 可以使用不同产品规格；这里只收集 cleaned 的列并集，
        # 每个 Lot 的权威规格由 generate_lion_run_csvs 分别输出。
        all_params = _collect_parameter_union(all_batch_lots)
    else:
        all_params = deepcopy(first_lot.params)
    all_chip_data = []
    
    # 按批次顺序处理，确保排序正确
    for batch_lot in all_batch_lots:
        print(f"   合并批次: {batch_lot.lot_id} ({len(batch_lot.wafers)} 个晶圆)")
        
        # 对当前批次的晶圆按wafer_id排序
        sorted_wafers = sorted(batch_lot.wafers, key=lambda w: int(w.wafer_id))
        all_wafers.extend(sorted_wafers)
        
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
    if combined_lot.source_format == LION_V1_FORMAT and len(all_batch_lots) == 1:
        combined_lot.lion_spec_data = _lion_spec_frame(all_params)
    
    # 合并所有芯片数据（按批次顺序）
    if all_chip_data:
        combined_lot.combined_data = pd.concat(all_chip_data, ignore_index=True)
    
    return combined_lot


def generate_lion_run_csvs(
    all_batch_lots: List[CPLot], output_dir: str
) -> Dict[str, object]:
    """Generate the approved outputs for one homogeneous Lion run.

    A single V1 Lot retains the mature three-file behavior.  Multi-Lot V1 and
    V2 runs emit one combined cleaned file, one combined yield file, and one
    horizontal spec file per Lot so different Lot specifications are isolated.
    """

    if not all_batch_lots:
        raise ValueError("没有提供 Lion 批次数据")
    os.makedirs(output_dir, exist_ok=True)
    combined_lot = create_combined_lot(all_batch_lots)
    source_format = getattr(combined_lot, "source_format", LION_V1_FORMAT)
    first_lot_id = all_batch_lots[0].lot_id
    combined_lot.lot_id = first_lot_id
    generator = StandardCSVGenerator()

    if source_format == LION_V1_FORMAT and len(all_batch_lots) == 1:
        return generator.generate_standard_csvs(combined_lot, output_dir)
    if source_format not in {LION_V1_FORMAT, LION_V2_FORMAT}:
        raise ValueError(f"未知 Lion 输出格式版本: {source_format}")

    lot_ids = [lot.lot_id for lot in all_batch_lots]
    if len(lot_ids) != len(set(lot_ids)):
        raise ValueError("同一次 Lion 运行包含重复 Lot_ID")

    timestamp = generator._generate_timestamp()
    cleaned_path = generator.generate_cleaned_csv(
        combined_lot, output_dir, timestamp
    )
    yield_path = generator.generate_yield_csv(combined_lot, output_dir, timestamp)
    spec_paths = {
        lot.lot_id: generator.generate_spec_csv(lot, output_dir, timestamp)
        for lot in all_batch_lots
    }
    return {
        "cleaned": cleaned_path,
        "yield": yield_path,
        "specs": spec_paths,
    }



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
    output_succeeded = False
    
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
            break

    if failed_batches:
        print("\n❌ 输入中存在失败或未知格式批次，已停止本次运行且不生成部分输出")
    
    # 3. 生成汇总CSV文件
    if all_batch_lots and not failed_batches:
        print(f"\n🔄 生成汇总CSV文件...")
        
        try:
            file_paths_generated = generate_lion_run_csvs(
                all_batch_lots, str(output_dir)
            )
            
            print(f"   ✅ 汇总CSV文件生成完成!")
            output_succeeded = True
            print(f"   📁 生成的文件:")
            for csv_type, path in file_paths_generated.items():
                if csv_type == "specs":
                    for lot_id, spec_path in path.items():
                        filename = Path(spec_path).name
                        file_size = Path(spec_path).stat().st_size / 1024
                        print(
                            f"     spec[{lot_id}]: {filename} ({file_size:.1f} KB)"
                        )
                    continue
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
    csv_files = list(output_dir.glob("*_cleaned.csv")) + list(output_dir.glob("*_yield.csv")) + list(output_dir.glob("*_spec.csv"))
    if csv_files:
        print(f"📄 生成的汇总CSV文件:")
        for csv_file in sorted(csv_files):
            file_size = csv_file.stat().st_size / 1024  # KB
            print(f"     {csv_file.name} ({file_size:.1f} KB)")
    
    print("\n🎉 批量汇总处理完成!")
    
    if success_count > 0 and output_succeeded and not failed_batches:
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
