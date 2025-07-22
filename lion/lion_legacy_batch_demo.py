#!/usr/bin/env python3
"""
Lion公司批次处理演示脚本 [遗留版本]

== 注意 ==
这是遗留的演示脚本，配合lion_legacy_batch_processor.py使用。
推荐使用项目根目录的 ../lion_batch_processor.py 进行批量处理。

原功能：演示如何使用批次处理器处理整个批次的所有晶圆数据
新版优势：
- 更简单的使用方式（一行命令）
- 自动发现和处理所有批次
- 更详细的输出和错误信息

建议：直接运行 python ../lion_batch_processor.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lion.batch_processor import LionBatchProcessor


def main():
    """主演示函数"""
    print("=" * 60)
    print("Lion公司批次数据处理演示")
    print("=" * 60)
    print()
    
    # 创建批次处理器
    processor = LionBatchProcessor()
    
    print("1. 发现批次...")
    batches = processor.discover_batches()
    
    if not batches:
        print("   未发现任何批次数据")
        return
    
    for batch_id, batch_path in batches:
        wafers = processor.discover_wafers_in_batch(batch_path)
        print(f"   批次 {batch_id}: {len(wafers)} 个晶圆文件")
    
    print()
    print("2. 处理所有批次...")
    results = processor.process_all_batches()
    
    print()
    print("3. 处理结果:")
    for batch_id, success in results.items():
        status = "✓ 成功" if success else "✗ 失败"
        print(f"   批次 {batch_id}: {status}")
        
        if success:
            # 显示生成的文件
            output_files = list(processor.output_root_dir.glob(f"{batch_id}_batch_*"))
            for file_path in output_files:
                print(f"     -> {file_path.name}")
    
    print()
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()