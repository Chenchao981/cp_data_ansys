"""
CP数据处理应用主入口。
一个现代化的、基于argparse的命令行工具，用于处理多厂商CP数据。
"""
import os
import argparse
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加项目根路径以便导入模块
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cp_data_processor.readers import create_reader
from cp_data_processor.readers.company_adapters.company_config import get_company_config
from cp_data_processor.readers.company_adapters.base_company_adapter import BaseCompanyAdapter
from cp_data_processor.analysis.yield_analyzer import YieldAnalyzer
from cp_data_processor.analysis.stats_analyzer import StatsAnalyzer

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_adapter_class(company_name: str):
    """根据公司名称动态获取适配器类"""
    if company_name == 'HH':
        from cp_data_processor.readers.company_adapters.hh_adapter import HHAdapter
        return HHAdapter
    elif company_name == 'JT':
        from cp_data_processor.readers.company_adapters.jt_adapter import JTAdapter
        return JTAdapter
    # 在此添加更多公司的适配器
    else:
        raise ValueError(f"未找到公司 '{company_name}' 的适配器。")

def main():
    """主函数：解析参数并执行数据处理流程"""
    parser = argparse.ArgumentParser(description="多厂商CP数据处理工具")
    parser.add_argument('--input-dir', required=True, help="包含输入文件的目录路径。")
    parser.add_argument('--output-dir', required=True, help="输出CSV文件的目录路径。")
    parser.add_argument('--company', required=True, help="公司名称 (例如: HH, JT)。")
    
    args = parser.parse_args()

    # --- 1. 设置路径和文件列表 ---
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = get_company_config(args.company)
    if not config:
        logger.error(f"找不到公司 '{args.company}' 的配置。")
        return

    file_paths = [str(p) for p in input_dir.glob('**/*') if p.is_file()]
    if not file_paths:
        logger.error(f"输入目录 '{input_dir}' 中没有找到任何文件。")
        return

    logger.info(f"找到 {len(file_paths)} 个文件，将使用 '{args.company}' 的配置进行处理。")

    # --- 2. 读取数据 ---
    reader = create_reader(file_paths=file_paths, company=args.company)
    raw_lot = reader.read()
    if not raw_lot.wafers:
        logger.error("读取数据失败，未能获取任何晶圆信息。")
        return
    logger.info(f"成功读取 Lot ID: {raw_lot.lot_id}，包含 {len(raw_lot.wafers)} 个晶圆。")

    # --- 3. 应用适配器转换数据 ---
    AdapterClass = get_adapter_class(args.company)
    adapter = AdapterClass(args.company, config)
    processed_lot = adapter.transform_to_standard_format(raw_lot)
    logger.info("数据已通过适配器转换为标准格式。")

    # --- 4. 数据分析 ---
    # 获取合并后的数据
    final_df = processed_lot.combined_data
    if final_df is None or final_df.empty:
        logger.error("经过转换后，没有有效的芯片数据可供分析。")
        return

    # 良率分析
    yield_analyzer = YieldAnalyzer(processed_lot)
    yield_results = yield_analyzer.analyze()
    logger.info(f"良率分析完成。总良率: {yield_results.get('total_yield', 0):.2f}%")

    # 规格/统计分析
    stats_analyzer = StatsAnalyzer(processed_lot)
    stats_summary = stats_analyzer.get_summary()
    logger.info("统计分析完成。")

    # --- 5. 保存输出文件 ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{processed_lot.lot_id}_{timestamp}"

    # a. 保存 cleaned_data.csv
    cleaned_path = output_dir / f"{base_filename}_cleaned.csv"
    final_df.to_csv(cleaned_path, index=False)
    logger.info(f"已保存清洗后的数据到: {cleaned_path}")

    # b. 保存 yield.csv
    yield_path = output_dir / f"{base_filename}_yield.csv"
    wafer_yields = yield_results.get('wafer_yields', {})
    yield_df = pd.DataFrame(list(wafer_yields.items()), columns=['Wafer_ID', 'Yield'])
    yield_df['Yield'] = yield_df['Yield'].apply(lambda x: f"{x:.2f}%")
    total_yield = f"{yield_results.get('total_yield', 0):.2f}%"
    total_row = pd.DataFrame([{'Wafer_ID': 'Total', 'Yield': total_yield}])
    yield_df = pd.concat([yield_df, total_row], ignore_index=True)
    yield_df.to_csv(yield_path, index=False)
    logger.info(f"已保存良率数据到: {yield_path}")

    # c. 保存 spec.csv
    spec_path = output_dir / f"{base_filename}_spec.csv"
    stats_summary.to_csv(spec_path, index=True)
    logger.info(f"已保存规格统计数据到: {spec_path}")
    
    logger.info("数据处理全部完成！")

if __name__ == "__main__":
    main() 