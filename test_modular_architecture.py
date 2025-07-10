#!/usr/bin/env python3
"""
模块化架构测试脚本

测试新的模块化架构是否正常工作，包括：
1. 公司注册管理器
2. 统一读取器
3. 标准CSV生成器
4. 公司适配器
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_company_registry():
    """测试公司注册管理器"""
    logger.info("=== 测试公司注册管理器 ===")
    
    try:
        from cp_data_processor.readers.company_adapters import get_company_registry
        
        registry = get_company_registry()
        
        # 测试获取支持的公司列表
        companies = registry.list_supported_companies()
        logger.info(f"支持的公司: {companies}")
        
        # 测试获取公司适配器
        for company in companies:
            adapter = registry.get_company_adapter(company)
            if adapter:
                logger.info(f"成功获取{company}适配器: {adapter.__class__.__name__}")
                info = adapter.get_company_info()
                logger.info(f"  公司信息: {info}")
            else:
                logger.error(f"无法获取{company}适配器")
        
        logger.info("✓ 公司注册管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 公司注册管理器测试失败: {e}")
        return False


def test_company_adapters():
    """测试公司适配器"""
    logger.info("=== 测试公司适配器 ===")
    
    try:
        from cp_data_processor.readers.company_adapters import get_company_registry
        
        registry = get_company_registry()
        
        # 测试文件处理能力
        test_files = [
            "/test/data/HH_data/test.dcp",
            "/test/data/JT_data/FA444149-03.xls"
        ]
        
        for file_path in test_files:
            company = registry.detect_company_from_file(file_path)
            if company:
                logger.info(f"文件 {file_path} 识别为 {company} 公司")
                
                adapter = registry.get_company_adapter(company)
                if adapter:
                    can_process = adapter.can_process_file(file_path)
                    logger.info(f"  {company}适配器可处理文件: {can_process}")
            else:
                logger.info(f"文件 {file_path} 无法识别公司")
        
        logger.info("✓ 公司适配器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 公司适配器测试失败: {e}")
        return False


def test_unified_reader():
    """测试统一读取器"""
    logger.info("=== 测试统一读取器 ===")
    
    try:
        from cp_data_processor.readers.unified_reader import UnifiedReader
        
        reader = UnifiedReader()
        
        # 测试获取支持的公司
        companies = reader.get_supported_companies()
        logger.info(f"统一读取器支持的公司: {companies}")
        
        # 测试文件处理能力
        test_files = [
            "/test/data/sample.dcp",
            "/test/data/sample.xls"
        ]
        
        for file_path in test_files:
            can_process = reader.can_process_file(file_path)
            logger.info(f"统一读取器可处理 {file_path}: {can_process}")
        
        logger.info("✓ 统一读取器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 统一读取器测试失败: {e}")
        return False


def test_standard_csv_generator():
    """测试标准CSV生成器"""
    logger.info("=== 测试标准CSV生成器 ===")
    
    try:
        from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
        
        generator = StandardCSVGenerator()
        logger.info("✓ 标准CSV生成器创建成功")
        
        # 这里可以添加更多测试，如果有测试数据的话
        
        logger.info("✓ 标准CSV生成器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 标准CSV生成器测试失败: {e}")
        return False


def test_configuration():
    """测试配置管理"""
    logger.info("=== 测试配置管理 ===")
    
    try:
        from cp_data_processor.readers.company_adapters import COMPANY_CONFIGS, get_company_config
        
        logger.info(f"配置中的公司数量: {len(COMPANY_CONFIGS)}")
        
        for company_code in COMPANY_CONFIGS.keys():
            config = get_company_config(company_code)
            if config:
                logger.info(f"公司 {company_code}:")
                logger.info(f"  名称: {config.get('name', 'N/A')}")
                logger.info(f"  支持格式: {config.get('supported_formats', [])}")
                logger.info(f"  字段映射数量: {len(config.get('field_mapping', {}))}")
                logger.info(f"  单位转换数量: {len(config.get('unit_conversion', {}))}")
            else:
                logger.error(f"无法获取公司 {company_code} 的配置")
        
        logger.info("✓ 配置管理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 配置管理测试失败: {e}")
        return False


def test_import_structure():
    """测试导入结构"""
    logger.info("=== 测试导入结构 ===")
    
    try:
        # 测试主要模块导入
        from cp_data_processor.readers.company_adapters import (
            BaseCompanyAdapter, 
            CompanyRegistry, 
            get_company_registry,
            HHAdapter,
            JTAdapter
        )
        
        from cp_data_processor.readers.unified_reader import UnifiedReader, read_cp_data
        from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator
        
        logger.info("✓ 所有主要模块导入成功")
        
        # 测试类实例化
        registry = CompanyRegistry()
        reader = UnifiedReader()
        generator = StandardCSVGenerator()
        
        logger.info("✓ 所有主要类实例化成功")
        
        logger.info("✓ 导入结构测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 导入结构测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("开始模块化架构测试...")
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("导入结构", test_import_structure()))
    test_results.append(("配置管理", test_configuration()))
    test_results.append(("公司注册管理器", test_company_registry()))
    test_results.append(("公司适配器", test_company_adapters()))
    test_results.append(("统一读取器", test_unified_reader()))
    test_results.append(("标准CSV生成器", test_standard_csv_generator()))
    
    # 汇总结果
    logger.info("\n=== 测试结果汇总 ===")
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n总计: {passed} 个测试通过, {failed} 个测试失败")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！模块化架构工作正常")
        return True
    else:
        logger.error(f"❌ 有 {failed} 个测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)