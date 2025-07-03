#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT公司图表生成器 - 复用HH公司前端图表模块
基于JT公司的3个清洗CSV文件(*_cleaned_*.csv, *_spec_*.csv, *_yield_*.csv)
生成与HH公司相同的前端HTML图表
"""

import logging
import sys
from pathlib import Path
import pandas as pd

# 添加项目路径以导入HH的前端模块
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入HH公司的前端图表模块
from frontend.charts.yield_chart import YieldChart
from frontend.charts.boxplot_chart import BoxplotChart

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    JT公司图表生成主函数
    复用HH公司的前端图表模块生成相同格式的HTML图表
    """
    # 1. 配置JT公司数据目录
    jt_data_dir = Path("output")  # JT公司的CSV文件目录
    jt_output_dir = Path("output")  # JT图表输出目录，与CSV文件保存在同一目录
    jt_output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📂 JT数据目录: {jt_data_dir.resolve()}")
    logger.info(f"📊 JT图表输出目录: {jt_output_dir.resolve()}")
    
    # 验证JT的3个CSV文件是否存在
    cleaned_files = list(jt_data_dir.glob("*_cleaned_*.csv"))
    spec_files = list(jt_data_dir.glob("*_spec_*.csv"))
    yield_files = list(jt_data_dir.glob("*_yield_*.csv"))
    
    if not (cleaned_files and spec_files and yield_files):
        logger.error("❌ 缺少必要的CSV文件，请确保存在：")
        logger.error("   - *_cleaned_*.csv (清洗数据)")
        logger.error("   - *_spec_*.csv (规格数据)")
        logger.error("   - *_yield_*.csv (良率数据)")
        return
    
    logger.info(f"✅ 找到JT数据文件:")
    logger.info(f"   - 清洗数据: {cleaned_files[0].name}")
    logger.info(f"   - 规格数据: {spec_files[0].name}")
    logger.info(f"   - 良率数据: {yield_files[0].name}")
    
    # 2. 使用HH的YieldChart生成良率图表
    logger.info("📈 开始生成良率图表...")
    yield_chart_dir = jt_output_dir / "yield_charts"
    generate_yield_charts(jt_data_dir, yield_chart_dir)
    
    # 3. 使用HH的BoxplotChart生成箱体图
    logger.info("📦 开始生成箱体图和散点图...")
    boxplot_chart_dir = jt_output_dir / "boxplot_charts"
    generate_boxplot_charts(jt_data_dir, boxplot_chart_dir)
    
    logger.info("🎉 JT公司图表生成完成！")
    logger.info(f"📁 所有图表已保存到: {jt_output_dir}")

def standardize_jt_csv_columns(data_dir: Path):
    """
    标准化JT的CSV列名以匹配HH的格式
    转换: LotID -> Lot_ID, WaferID -> Wafer_ID
    """
    try:
        # 找到cleaned文件
        cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
        if not cleaned_files:
            logger.warning("⚠️ 未找到需要标准化的cleaned文件")
            return
        
        cleaned_file = cleaned_files[0]
        logger.info(f"🔄 标准化CSV列名: {cleaned_file.name}")
        
        # 读取CSV
        df = pd.read_csv(cleaned_file)
        
        # 检查并转换列名
        column_mapping = {
            'LotID': 'Lot_ID',
            'WaferID': 'Wafer_ID'
        }
        
        renamed_columns = {}
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                renamed_columns[old_name] = new_name
        
        if renamed_columns:
            df.rename(columns=renamed_columns, inplace=True)
            logger.info(f"✅ 列名转换: {renamed_columns}")
            
            # 保存标准化后的文件
            df.to_csv(cleaned_file, index=False)
            logger.info(f"✅ 标准化完成: {cleaned_file.name}")
        else:
            logger.info("ℹ️ 无需列名转换")
            
    except Exception as e:
        logger.error(f"❌ 列名标准化失败: {e}")

def generate_yield_charts(data_dir: Path, output_dir: Path):
    """
    使用HH的YieldChart模块生成良率图表
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化HH的YieldChart
        yield_analyzer = YieldChart(data_dir=str(data_dir))
        
        if not yield_analyzer.load_data():
            logger.error("❌ 良率数据加载失败")
            return
        
        # 生成所有良率图表
        saved_charts = yield_analyzer.save_all_charts(output_dir=str(output_dir))
        
        if saved_charts:
            logger.info(f"✅ 良率图表已保存 ({len(saved_charts)}个):")
            for i, chart_path in enumerate(saved_charts, 1):
                logger.info(f"  {i}. {chart_path.name}")
        else:
            logger.warning("⚠️ 未能保存良率图表")
            
    except Exception as e:
        logger.error(f"❌ 良率图表生成失败: {e}")

def generate_boxplot_charts(data_dir: Path, output_dir: Path):
    """
    使用HH的BoxplotChart模块生成箱体图和散点图
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 先进行JT到HH的列名标准化转换
        standardize_jt_csv_columns(data_dir)
        
        # 初始化HH的BoxplotChart
        boxplot_analyzer = BoxplotChart(data_dir=str(data_dir))
        
        if not boxplot_analyzer.load_data():
            logger.error("❌ 箱体图数据加载失败")
            return
        
        # 获取可用参数
        available_params = boxplot_analyzer.get_available_parameters()
        if not available_params:
            logger.warning("⚠️ 未找到可用的测试参数")
            return
        
        logger.info(f"🎯 找到 {len(available_params)} 个测试参数: {available_params}")
        
        # 批量保存所有参数的箱体图
        saved_charts = boxplot_analyzer.save_all_charts(output_dir=str(output_dir))
        
        if saved_charts:
            logger.info(f"✅ 箱体图已保存 ({len(saved_charts)}个):")
            for i, chart_path in enumerate(saved_charts, 1):
                logger.info(f"  {i}. {chart_path.name}")
        else:
            logger.warning("⚠️ 未能保存箱体图")
            
    except Exception as e:
        logger.error(f"❌ 箱体图生成失败: {e}")


if __name__ == "__main__":
    print("🏭 JT公司图表生成器 - 复用HH前端模块")
    print("=" * 50)
    main()