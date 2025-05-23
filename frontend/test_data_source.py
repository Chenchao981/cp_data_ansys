#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据来源 - 验证混合式架构的数据读取逻辑
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.core.data_manager import DataManager
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s: %(message)s')

def test_data_sources():
    """测试不同数据源的读取情况"""
    print("=" * 60)
    print("🔍 数据源测试 - 验证实际数据来源")
    print("=" * 60)
    
    test_lot_id = "FA54-5339-327A-250501@203"
    
    # 1. 测试文件模式
    print("\n📁 1. 文件模式测试")
    print("-" * 40)
    dm_file = DataManager(data_source="file", cache_enabled=False, data_dir="output")
    
    yield_data = dm_file.get_data("yield", test_lot_id)
    if yield_data is not None:
        print(f"✓ 文件模式加载成功: {yield_data.shape}")
        print(f"  数据来源: CSV文件")
    else:
        print("✗ 文件模式加载失败")
    
    # 2. 测试内存模式
    print("\n🧠 2. 内存模式测试")
    print("-" * 40)
    dm_memory = DataManager(data_source="memory", cache_enabled=False, data_dir="output")
    
    yield_data_memory = dm_memory.get_data("yield", test_lot_id)
    if yield_data_memory is not None:
        print(f"✓ 内存模式加载成功: {yield_data_memory.shape}")
        print(f"  数据来源: 内存")
    else:
        print("✗ 内存模式加载失败 (预期结果，因为内存中没有数据)")
    
    # 3. 测试Auto模式
    print("\n🔄 3. Auto模式测试")
    print("-" * 40)
    dm_auto = DataManager(data_source="auto", cache_enabled=False, data_dir="output")
    
    yield_data_auto = dm_auto.get_data("yield", test_lot_id)
    if yield_data_auto is not None:
        print(f"✓ Auto模式加载成功: {yield_data_auto.shape}")
        print(f"  数据来源: 优先内存，实际从文件fallback")
    else:
        print("✗ Auto模式加载失败")
    
    # 4. 测试手动存储到内存后的情况
    print("\n💾 4. 手动内存存储测试")
    print("-" * 40)
    
    if yield_data is not None:
        # 手动将数据存储到内存
        dm_auto.store_data("yield", yield_data, test_lot_id)
        print("✓ 数据已手动存储到内存")
        
        # 再次测试auto模式
        yield_data_from_memory = dm_auto.get_data("yield", test_lot_id)
        if yield_data_from_memory is not None:
            print(f"✓ Auto模式从内存加载成功: {yield_data_from_memory.shape}")
            print(f"  数据来源: 内存")
        else:
            print("✗ 从内存加载失败")
    
    # 5. 内存适配器状态检查
    print("\n📊 5. 内存适配器状态")
    print("-" * 40)
    
    # 检查内存适配器中的数据
    memory_info = dm_auto.memory_adapter.get_memory_info() if dm_auto.memory_adapter else {}
    print(f"内存适配器状态: {memory_info}")
    
    if dm_auto.memory_adapter:
        stored_data = dm_auto.memory_adapter.list_stored_data()
        print("内存中存储的数据:")
        for key, info in stored_data.items():
            print(f"  {key}: {info['shape']}")
    
    return True

def demonstrate_memory_sharing():
    """演示如何实现真正的内存数据共享"""
    print("\n" + "=" * 60)
    print("💡 内存数据共享方案演示")
    print("=" * 60)
    
    print("\n方案1: 进程内数据传递")
    print("-" * 30)
    print("```python")
    print("# 在同一个脚本中，先清洗数据，再可视化")
    print("# 1. 运行清洗逻辑")
    print("# cleaned_data = run_clean_dcp_data()")
    print("# ")
    print("# 2. 直接传递给前端")
    print("# dm = DataManager(data_source='memory')")
    print("# dm.store_data('cleaned', cleaned_data, lot_id)")
    print("# ")
    print("# 3. 生成图表")
    print("# factory = ChartFactory(dm)")
    print("# charts = factory.generate_all_charts(lot_id)")
    print("```")
    
    print("\n方案2: 缓存文件优化")
    print("-" * 30)
    print("当前实际使用的方案：")
    print("- clean_dcp_data.py 保存数据到CSV文件")
    print("- 前端从CSV文件读取（首次）")
    print("- 前端自动缓存到内存（后续访问）")
    print("- 性能：首次慢，后续极快")
    
    print("\n方案3: 共享内存/数据库")
    print("-" * 30)
    print("适用于多进程/多用户场景：")
    print("- 使用Redis/Memcached共享内存")
    print("- 或使用SQLite数据库")
    print("- 支持多个前端实例同时访问")

def main():
    """主测试函数"""
    try:
        test_data_sources()
        demonstrate_memory_sharing()
        
        print("\n" + "=" * 60)
        print("🎯 结论")
        print("=" * 60)
        print("📌 当前架构行为：")
        print("  1. 独立进程运行时，实际从CSV文件读取")
        print("  2. 首次读取后会缓存到内存，后续访问极快")
        print("  3. clean_dcp_data.py的内存数据无法直接访问")
        print("")
        print("🚀 性能优化：")
        print("  1. 首次加载：从文件读取（较慢）")
        print("  2. 后续访问：从内存缓存（极快）")
        print("  3. 支持手动预加载到内存")
        print("")
        print("💡 推荐做法：")
        print("  1. 保持当前架构，性能已经很好")
        print("  2. 或者集成到统一脚本中，实现真正的内存共享")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 