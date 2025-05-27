#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据快速分析脚本
一键完成从数据清洗到图表生成的全流程
"""

import sys
import subprocess
from pathlib import Path
import os

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n🔄 {description}...")
    print(f"执行命令: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print(f"✅ {description}完成")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()}")
        else:
            print(f"❌ {description}失败")
            if result.stderr.strip():
                print(f"错误: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        return False
    
    return True

def check_data_files():
    """检查数据文件是否存在"""
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ output目录不存在，请确保已放置原始数据文件")
        return False
    
    # 检查原始数据文件
    dcp_files = list(output_dir.glob("*.txt"))
    csv_files = list(output_dir.glob("*.csv"))
    
    if not dcp_files and not csv_files:
        print("❌ 未在output目录中找到数据文件(.txt或.csv)")
        return False
    
    print(f"✅ 找到数据文件: {len(dcp_files)} 个DCP文件, {len(csv_files)} 个CSV文件")
    return True

def check_processed_files():
    """检查是否已有处理后的文件"""
    output_dir = Path("output")
    
    yield_files = list(output_dir.glob("*_yield_*.csv"))
    spec_files = list(output_dir.glob("*_spec_*.csv"))
    cleaned_files = list(output_dir.glob("*_cleaned_*.csv"))
    
    has_yield = len(yield_files) > 0
    has_spec = len(spec_files) > 0
    has_cleaned = len(cleaned_files) > 0
    
    print(f"\n📊 当前处理状态:")
    print(f"   Yield数据: {'✅' if has_yield else '❌'} ({len(yield_files)} 文件)")
    print(f"   Spec数据: {'✅' if has_spec else '❌'} ({len(spec_files)} 文件)")
    print(f"   Cleaned数据: {'✅' if has_cleaned else '❌'} ({len(cleaned_files)} 文件)")
    
    return has_yield, has_spec, has_cleaned

def main():
    """主分析流程"""
    print("🚀 CP数据快速分析工具")
    print("=" * 50)
    
    # 检查数据文件
    if not check_data_files():
        print("\n💡 请将原始数据文件放入output目录后重新运行")
        return
    
    # 检查处理状态
    has_yield, has_spec, has_cleaned = check_processed_files()
    
    # 询问是否需要重新处理数据
    if has_yield and has_spec and has_cleaned:
        choice = input("\n📋 已存在处理后的数据文件，是否重新处理？(y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("⏭️ 跳过数据处理步骤")
            skip_processing = True
        else:
            skip_processing = False
    else:
        skip_processing = False
    
    success_steps = []
    
    # 第一阶段：数据清洗和处理
    if not skip_processing:
        print(f"\n📋 第一阶段：数据清洗和处理")
        print("-" * 30)
        
        # 1. 清洗DCP数据
        if run_command("python clean_dcp_data.py", "清洗DCP数据"):
            success_steps.append("DCP数据清洗")
        
        # 2. 清洗CSV数据
        if run_command("python clean_csv_data.py", "清洗CSV数据"):
            success_steps.append("CSV数据清洗")
        
        # 3. 提取规格信息
        if run_command("python dcp_spec_extractor.py", "提取规格信息"):
            success_steps.append("规格信息提取")
    
    # 第二阶段：生成交互式图表
    print(f"\n📊 第二阶段：生成交互式图表")
    print("-" * 30)
    
    # 4. 生成良率分析图表
    if run_command("python demo_yield_chart.py", "生成良率分析图表"):
        success_steps.append("良率分析图表")
    
    # 5. 生成箱体图分析
    choice = input("\n📦 是否生成箱体图分析？(Y/n): ").strip().lower()
    if choice not in ['n', 'no']:
        if run_command("python test_boxplot.py", "生成箱体图分析"):
            success_steps.append("箱体图分析")
    
    # 第三阶段：结果展示
    print(f"\n🎉 分析完成！")
    print("=" * 30)
    
    print(f"✅ 成功完成的步骤 ({len(success_steps)}):")
    for i, step in enumerate(success_steps, 1):
        print(f"   {i}. {step}")
    
    # 显示生成的文件
    print(f"\n📁 生成的图表文件:")
    
    output_dirs = ["demo_output", "test_charts"]
    total_files = 0
    
    for output_dir in output_dirs:
        output_path = Path(output_dir)
        if output_path.exists():
            html_files = list(output_path.rglob("*.html"))
            if html_files:
                print(f"\n📊 {output_dir}/ ({len(html_files)} 文件):")
                for html_file in html_files[:5]:  # 只显示前5个
                    rel_path = html_file.relative_to(output_path)
                    print(f"   - {rel_path}")
                if len(html_files) > 5:
                    print(f"   ... 还有 {len(html_files) - 5} 个文件")
                total_files += len(html_files)
    
    print(f"\n📈 总计生成 {total_files} 个HTML图表文件")
    
    # 使用建议
    print(f"\n💡 下一步建议:")
    print(f"   1. 在浏览器中打开HTML文件查看交互式图表")
    print(f"   2. 运行 'python test_yield_chart.py' 进行详细测试")
    print(f"   3. 查看 README.md 了解更多高级功能")
    
    # 询问是否打开输出目录
    if total_files > 0:
        choice = input(f"\n📂 是否打开输出目录查看文件？(Y/n): ").strip().lower()
        if choice not in ['n', 'no']:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile("demo_output")
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", "demo_output"])
            except Exception as e:
                print(f"无法自动打开目录: {e}")
                print(f"请手动打开: {Path('demo_output').absolute()}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc() 