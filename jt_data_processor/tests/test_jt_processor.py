#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT数据处理器测试模块

用于验证JT数据处理器的功能和配置正确性。

作者: CP Data Analysis Team
版本: 1.0.0
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

# 导入JT模块
try:
    from jt_data_processor.config.jt_config import JTConfig, DEFAULT_JT_CONFIG
    from jt_data_processor.adapters.jt_adapter import JTAdapter
except ImportError as e:
    print(f"导入JT模块失败: {e}")
    print("请确保运行测试前已正确设置Python路径")


class TestJTConfig(unittest.TestCase):
    """JT配置测试类"""
    
    def test_config_validation(self):
        """测试配置验证"""
        self.assertTrue(JTConfig.validate_config(), "JT配置验证应该通过")
    
    def test_unit_conversion_disabled(self):
        """测试单位转换禁用"""
        self.assertTrue(JTConfig.is_unit_conversion_disabled(), "单位转换应该被禁用")
    
    def test_field_mapping(self):
        """测试字段映射"""
        mapping = JTConfig.get_field_mapping()
        expected_mappings = {
            'DUT_NO': 'Seq',
            'SOFT_BIN': 'Bin',
            'X_COORD': 'X',
            'Y_COORD': 'Y',
            'TEST_NUM': 'CONT'
        }
        
        for jt_field, std_field in expected_mappings.items():
            self.assertIn(jt_field, mapping, f"字段映射应包含 {jt_field}")
            self.assertEqual(mapping[jt_field], std_field, f"{jt_field} 应映射到 {std_field}")
    
    def test_cleaning_config(self):
        """测试清洗配置"""
        cleaning_config = JTConfig.get_cleaning_config()
        self.assertEqual(cleaning_config['default_outlier_method'], 'iqr', "默认异常值处理方法应为IQR")
    
    def test_excel_config(self):
        """测试Excel配置"""
        excel_config = JTConfig.get_excel_config()
        self.assertEqual(excel_config['lot_id_row'], 8, "Lot ID应从第8行读取")
        self.assertEqual(excel_config['wafer_id_row'], 9, "Wafer ID应从第9行读取")
        self.assertEqual(excel_config['data_start_row'], 6, "数据应从第6行开始")


class TestJTAdapter(unittest.TestCase):
    """JT适配器测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = JTAdapter('JT', DEFAULT_JT_CONFIG)
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertEqual(self.adapter.company_name, 'JT', "公司名称应为JT")
        self.assertTrue(self.adapter.unit_conversion_disabled, "单位转换应被禁用")
        self.assertEqual(self.adapter.outlier_method, 'iqr', "异常值处理方法应为IQR")
    
    def test_field_mapping_retrieval(self):
        """测试字段映射获取"""
        mapping = self.adapter.get_field_mapping()
        self.assertIsInstance(mapping, dict, "字段映射应为字典类型")
        self.assertGreater(len(mapping), 0, "字段映射不应为空")
    
    def test_unit_conversion_override(self):
        """测试单位转换重写"""
        import pandas as pd
        test_data = pd.DataFrame({'param1': [1, 2, 3], 'param2': [4, 5, 6]})
        result = self.adapter.convert_units(test_data)
        
        # 应该返回原始数据，不进行任何转换
        pd.testing.assert_frame_equal(result, test_data, "单位转换应返回原始数据")
    
    def test_processing_summary(self):
        """测试处理摘要"""
        summary = self.adapter.get_processing_summary()
        self.assertIn('company', summary, "摘要应包含公司信息")
        self.assertIn('unit_conversion_disabled', summary, "摘要应包含单位转换状态")
        self.assertTrue(summary['unit_conversion_disabled'], "摘要中单位转换应为禁用状态")


class TestJTConfigIntegration(unittest.TestCase):
    """JT配置集成测试类"""
    
    def test_complete_config_structure(self):
        """测试完整配置结构"""
        config = JTConfig.get_complete_config()
        
        required_keys = [
            'name', 'field_mapping', 'unit_conversion', 'disable_unit_conversion',
            'cleaning_config', 'data_validation', 'excel_sheet_config'
        ]
        
        for key in required_keys:
            self.assertIn(key, config, f"配置应包含 {key}")
    
    def test_jt_specific_requirements(self):
        """测试JT特定需求"""
        config = JTConfig.get_complete_config()
        
        # 检查单位转换配置
        self.assertEqual(config['unit_conversion'], {}, "JT单位转换应为空字典")
        self.assertTrue(config['disable_unit_conversion'], "JT应禁用单位转换")
        
        # 检查异常值处理
        self.assertEqual(
            config['cleaning_config']['default_outlier_method'], 'iqr',
            "JT应使用IQR异常值处理方法"
        )
        
        # 检查规格文件配置
        spec_config = config['spec_file_config']
        self.assertFalse(spec_config['include_testcond'], "JT不应包含测试条件")
        self.assertEqual(spec_config['testcond_value'], '', "JT测试条件值应为空")


def run_jt_config_test():
    """运行JT配置测试的便捷函数"""
    print("=== JT配置测试 ===")
    
    try:
        # 验证配置
        if JTConfig.validate_config():
            print("✅ JT配置验证通过")
        else:
            print("❌ JT配置验证失败")
        
        # 打印配置摘要
        JTConfig.print_config_summary()
        
        # 验证关键配置
        print("\n🔥 关键配置验证:")
        print(f"  - 单位转换禁用: {JTConfig.is_unit_conversion_disabled()}")
        print(f"  - 异常值处理方法: {JTConfig.get_cleaning_config()['default_outlier_method']}")
        print(f"  - 字段映射数量: {len(JTConfig.get_field_mapping())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def run_jt_adapter_test():
    """运行JT适配器测试的便捷函数"""
    print("\n=== JT适配器测试 ===")
    
    try:
        adapter = JTAdapter('JT', DEFAULT_JT_CONFIG)
        summary = adapter.get_processing_summary()
        
        print("✅ JT适配器初始化成功")
        print(f"  - 公司: {summary['company']}")
        print(f"  - 异常值方法: {summary['outlier_method']}")
        print(f"  - 单位转换禁用: {summary['unit_conversion_disabled']}")
        print(f"  - 字段映射数: {len(summary['field_mapping'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        return False


if __name__ == "__main__":
    print("JT数据处理器测试套件")
    print("=" * 50)
    
    # 运行简单的功能测试
    config_test_passed = run_jt_config_test()
    adapter_test_passed = run_jt_adapter_test()
    
    print("\n" + "=" * 50)
    print("测试结果摘要:")
    print(f"  - 配置测试: {'通过' if config_test_passed else '失败'}")
    print(f"  - 适配器测试: {'通过' if adapter_test_passed else '失败'}")
    
    if config_test_passed and adapter_test_passed:
        print("\n✅ 所有基础测试通过！JT数据处理器配置正确。")
        exit_code = 0
    else:
        print("\n❌ 部分测试失败，请检查配置。")
        exit_code = 1
    
    print("\n提示：要运行完整的单元测试，请使用:")
    print("python -m unittest jt_data_processor.tests.test_jt_processor")
    
    # 运行unittest（如果作为主程序运行）
    print("\n" + "=" * 50)
    print("运行完整单元测试...")
    
    try:
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # 添加测试类
        suite.addTests(loader.loadTestsFromTestCase(TestJTConfig))
        suite.addTests(loader.loadTestsFromTestCase(TestJTAdapter))
        suite.addTests(loader.loadTestsFromTestCase(TestJTConfigIntegration))
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("\n✅ 所有单元测试通过！")
        else:
            print(f"\n❌ {len(result.failures + result.errors)} 个测试失败")
            exit_code = 1
    
    except Exception as e:
        print(f"\n❌ 运行单元测试时出错: {e}")
        exit_code = 1
    
    sys.exit(exit_code) 