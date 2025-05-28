#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据处理器 - 命令行界面
提供命令行方式的数据处理功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import CPDataProcessor


def cli_main():
    """命令行主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CP数据处理器 - 命令行版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m app.cli data.txt result.xlsx --format dcp --boxplot
  python -m app.cli *.csv output.xlsx --format cw --scatter --wafer-map
        """
    )
    
    parser.add_argument("input_files", nargs="+", 
                       help="输入文件路径（支持通配符）")
    parser.add_argument("output_file", 
                       help="输出Excel文件路径")
    parser.add_argument("--format", choices=["dcp", "cw", "mex"], 
                       default="dcp", help="数据格式 (默认: dcp)")
    parser.add_argument("--boxplot", action="store_true", 
                       help="生成箱形图")
    parser.add_argument("--scatter", action="store_true", 
                       help="生成散点图")
    parser.add_argument("--wafer-map", action="store_true", 
                       help="生成晶圆图")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="显示详细信息")
    
    args = parser.parse_args()
    
    if args.verbose:
        print("🔬 CP数据处理器 - 命令行版本")
        print("=" * 50)
        print(f"输入文件: {args.input_files}")
        print(f"输出文件: {args.output_file}")
        print(f"数据格式: {args.format}")
        print(f"生成图表: 箱形图={args.boxplot}, 散点图={args.scatter}, 晶圆图={args.wafer_map}")
        print("-" * 50)
    
    # 创建处理器并执行
    processor = CPDataProcessor()
    success = processor.process_files(
        file_paths=args.input_files,
        data_format=args.format,
        output_path=args.output_file,
        enable_boxplot=args.boxplot,
        enable_scatter=args.scatter,
        enable_wafer_map=args.wafer_map
    )
    
    if success:
        print("\n🎉 处理完成！")
    else:
        print("\n❌ 处理失败！")
        
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(cli_main())
