#!/usr/bin/env python3
"""
Lion公司数据处理快速开始脚本

最简化的Lion公司数据处理流程，专为GUI界面调用设计。

使用说明：
1. 将Lion批次数据放入指定目录
2. 调用此脚本即可完成数据清洗
3. 生成标准化的CSV文件供后续分析使用

适合场景：
- GUI界面中的Lion数据处理模块
- 快速批处理Lion数据
- 自动化数据清洗流程
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from clean_lion_data import LionDataCleaner

def process_lion_data(
    data_path: str, 
    output_dir: str = "./output_lion_models",
    log_level: str = "INFO"
) -> Tuple[bool, List[str], str]:
    """
    处理Lion公司数据的简化接口
    
    Args:
        data_path: Lion数据路径（可以是目录或Excel文件）
        output_dir: 输出目录
        log_level: 日志级别 ("DEBUG", "INFO", "WARNING", "ERROR")
        
    Returns:
        Tuple[bool, List[str], str]: (是否成功, 生成的文件列表, 错误信息)
    """
    try:
        # 设置日志级别
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO, 
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        
        logging.getLogger().setLevel(log_level_map.get(log_level.upper(), logging.INFO))
        
        # 创建Lion数据清洗器
        cleaner = LionDataCleaner(output_dir)
        
        # 检查输入路径
        if not os.path.exists(data_path):
            return False, [], f"输入路径不存在: {data_path}"
        
        generated_files = []
        
        if os.path.isfile(data_path) and data_path.endswith('.xlsx'):
            # 单个Excel文件
            success = cleaner.clean_single_batch(data_path)
            if success:
                # 查找生成的文件
                batch_id = Path(data_path).stem
                for file in os.listdir(output_dir):
                    if file.startswith(batch_id) and file.endswith('.csv'):
                        generated_files.append(os.path.join(output_dir, file))
            
        elif os.path.isdir(data_path):
            # 目录处理
            if cleaner._is_lion_batch_dir(data_path):
                # 单个批次目录
                success = cleaner.clean_single_batch(data_path)
                if success:
                    batch_id = os.path.basename(data_path)
                    for file in os.listdir(output_dir):
                        if file.startswith(batch_id) and file.endswith('.csv'):
                            generated_files.append(os.path.join(output_dir, file))
            else:
                # 多批次目录
                results = cleaner.clean_multiple_batches(data_path)
                success = any(results.values())
                if success:
                    # 收集所有生成的文件
                    for file in os.listdir(output_dir):
                        if file.endswith('.csv'):
                            file_path = os.path.join(output_dir, file)
                            # 检查文件是否是刚生成的（简单时间判断）
                            if os.path.getmtime(file_path) > (os.path.getmtime(data_path) if os.path.isfile(data_path) else 0):
                                generated_files.append(file_path)
        else:
            return False, [], f"不支持的输入类型: {data_path}"
        
        if success:
            return True, generated_files, ""
        else:
            return False, [], "数据处理失败，请查看日志获取详细信息"
            
    except Exception as e:
        return False, [], f"处理过程中发生错误: {str(e)}"

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lion公司数据处理快速开始")
    parser.add_argument("data_path", help="Lion数据路径")
    parser.add_argument("--output", "-o", default="./output_lion_models", help="输出目录")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       help="日志级别")
    
    args = parser.parse_args()
    
    print("Lion公司数据处理开始...")
    success, files, error = process_lion_data(args.data_path, args.output, args.log_level)
    
    if success:
        print(f"✓ 处理成功！生成了 {len(files)} 个文件:")
        for file_path in files:
            print(f"  - {os.path.basename(file_path)}")
        print(f"文件保存在: {args.output}")
    else:
        print(f"✗ 处理失败: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()