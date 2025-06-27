#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT公司配置管理

基于用户确认的JT公司数据处理需求和HH公司的成熟配置管理技术。

特点：
- 禁用单位转换配置
- IQR四分位法异常值处理
- 完整的字段映射关系
- JT特有的数据验证规则

作者: CP Data Analysis Team
版本: 1.0.0
"""

from typing import Dict, Any, List


class JTConfig:
    """
    JT公司配置管理类
    
    包含JT公司数据处理的所有配置参数，
    基于用户确认的要求和HH公司的配置管理模式。
    """
    
    # JT公司基本信息
    COMPANY_NAME = 'JT公司'
    COMPANY_CODE = 'JT'
    VERSION = '1.0.0'
    
    # 支持的文件格式
    SUPPORTED_FORMATS = ['.xls', '.xlsx']
    
    # 文件命名模式
    FILE_PATTERN = r'^FA\d{4}-\d{4}.*\.xls[x]?$'
    
    # 🔥 字段映射关系（用户确认）
    FIELD_MAPPING = {
        'DUT_NO': 'Seq',          # 序号映射
        'SOFT_BIN': 'Bin',        # Bin值映射
        'X_COORD': 'X',           # X坐标映射
        'Y_COORD': 'Y',           # Y坐标映射
        'TEST_NUM': 'CONT'        # 测试编号映射
    }
    
    # 🔥 单位转换配置（JT数据禁用）
    UNIT_CONVERSION = {}  # 空字典 - JT数据无需单位转换
    DISABLE_UNIT_CONVERSION = True  # 明确标记禁用单位转换
    
    # 🔥 数据清洗配置（用户确认使用IQR）
    CLEANING_CONFIG = {
        'default_outlier_method': 'iqr',     # 使用IQR四分位法
        'outlier_threshold': None,           # IQR方法不需要阈值
        'replace_outliers_with_nan': True,   # 异常值替换为NaN（不删除）
        'preserve_data_integrity': True      # 保持数据完整性
    }
    
    # 数据验证配置
    DATA_VALIDATION = {
        'required_fields': ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y'],
        'optional_fields': ['CONT'],
        'min_chip_count': 1,
        'max_chip_count': 50000,
        'coordinate_validation': True
    }
    
    # Excel工作表配置
    EXCEL_SHEET_CONFIG = {
        'summary_sheet': 'Summary information',
        'data_sheet': 'DUT_DATA',
        'skip_sheet': 'Statistics Information',  # 直接跳过
        'lot_id_row': 8,     # 第8行获取Lot ID（用户确认）
        'wafer_id_row': 9,   # 第9行获取Wafer ID（用户确认）
        'header_row': 1,     # 第1行为表头
        'unit_row': 2,       # 第2行为单位信息
        'limit_u_row': 3,    # 第3行为上限
        'limit_l_row': 4,    # 第4行为下限
        'data_start_row': 6  # 第6行开始为数据（用户确认）
    }
    
    # 规格文件生成配置
    SPEC_FILE_CONFIG = {
        'include_testcond': False,  # JT公司没有测试条件信息
        'testcond_value': '',       # 测试条件设为空
        'unit_source': 'unit_row',  # 单位来源于第2行
        'limit_u_source': 'limit_u_row',  # 上限来源于第3行
        'limit_l_source': 'limit_l_row',  # 下限来源于第4行
        'param_source': 'CONT_and_right'  # CONT及右侧所有参数
    }
    
    # 输出格式配置
    OUTPUT_CONFIG = {
        'csv_encoding': 'utf-8-sig',
        'excel_engine': 'openpyxl',
        'include_index': False,
        'na_rep': '',
        'date_format': '%Y-%m-%d %H:%M:%S'
    }
    
    # 日志配置
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'include_debug': True,
        'log_file_prefix': 'jt_processor'
    }
    
    # 性能配置
    PERFORMANCE_CONFIG = {
        'chunk_size': 10000,
        'memory_threshold': 0.8,
        'parallel_processing': False,  # JT数据量通常不大，暂不使用并行
        'cache_enabled': True
    }
    
    @classmethod
    def get_complete_config(cls) -> Dict[str, Any]:
        """
        获取完整的JT配置字典
        
        Returns:
            Dict[str, Any]: 完整的JT配置
        """
        return {
            'name': cls.COMPANY_NAME,
            'code': cls.COMPANY_CODE,
            'version': cls.VERSION,
            'supported_formats': cls.SUPPORTED_FORMATS,
            'file_pattern': cls.FILE_PATTERN,
            'field_mapping': cls.FIELD_MAPPING,
            'unit_conversion': cls.UNIT_CONVERSION,
            'disable_unit_conversion': cls.DISABLE_UNIT_CONVERSION,
            'cleaning_config': cls.CLEANING_CONFIG,
            'data_validation': cls.DATA_VALIDATION,
            'excel_sheet_config': cls.EXCEL_SHEET_CONFIG,
            'spec_file_config': cls.SPEC_FILE_CONFIG,
            'output_config': cls.OUTPUT_CONFIG,
            'logging_config': cls.LOGGING_CONFIG,
            'performance_config': cls.PERFORMANCE_CONFIG
        }
    
    @classmethod
    def get_field_mapping(cls) -> Dict[str, str]:
        """
        获取字段映射配置
        
        Returns:
            Dict[str, str]: 字段映射字典
        """
        return cls.FIELD_MAPPING.copy()
    
    @classmethod
    def get_cleaning_config(cls) -> Dict[str, Any]:
        """
        获取数据清洗配置
        
        Returns:
            Dict[str, Any]: 清洗配置字典
        """
        return cls.CLEANING_CONFIG.copy()
    
    @classmethod
    def get_excel_config(cls) -> Dict[str, Any]:
        """
        获取Excel工作表配置
        
        Returns:
            Dict[str, Any]: Excel配置字典
        """
        return cls.EXCEL_SHEET_CONFIG.copy()
    
    @classmethod
    def is_unit_conversion_disabled(cls) -> bool:
        """
        检查单位转换是否被禁用
        
        Returns:
            bool: True表示禁用单位转换
        """
        return cls.DISABLE_UNIT_CONVERSION
    
    @classmethod
    def get_supported_file_extensions(cls) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            List[str]: 支持的文件扩展名列表
        """
        return cls.SUPPORTED_FORMATS.copy()
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        验证配置的完整性和有效性
        
        Returns:
            bool: 配置有效返回True
        """
        try:
            # 检查必要的配置项
            required_configs = [
                'COMPANY_NAME', 'FIELD_MAPPING', 'CLEANING_CONFIG',
                'DATA_VALIDATION', 'EXCEL_SHEET_CONFIG'
            ]
            
            for config_name in required_configs:
                if not hasattr(cls, config_name):
                    return False
                    
                config_value = getattr(cls, config_name)
                if not config_value:
                    return False
            
            # 检查字段映射不为空
            if not cls.FIELD_MAPPING:
                return False
            
            # 检查单位转换确实被禁用
            if not cls.DISABLE_UNIT_CONVERSION:
                return False
            
            # 检查清洗方法为IQR
            if cls.CLEANING_CONFIG.get('default_outlier_method') != 'iqr':
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def print_config_summary(cls) -> None:
        """
        打印配置摘要信息
        """
        print(f"=== {cls.COMPANY_NAME} 配置摘要 ===")
        print(f"公司代码: {cls.COMPANY_CODE}")
        print(f"版本: {cls.VERSION}")
        print(f"支持格式: {', '.join(cls.SUPPORTED_FORMATS)}")
        print(f"单位转换: {'禁用' if cls.DISABLE_UNIT_CONVERSION else '启用'}")
        print(f"异常值处理: {cls.CLEANING_CONFIG['default_outlier_method'].upper()}")
        print(f"字段映射数: {len(cls.FIELD_MAPPING)}")
        print(f"配置有效性: {'有效' if cls.validate_config() else '无效'}")
        print("=" * 40)


# JT配置的默认实例
DEFAULT_JT_CONFIG = JTConfig.get_complete_config()

# 用于外部导入的配置字典
JT_COMPANY_CONFIG = {
    'JT': DEFAULT_JT_CONFIG
}


if __name__ == "__main__":
    # 测试和演示代码
    print("JT配置模块测试")
    print()
    
    # 打印配置摘要
    JTConfig.print_config_summary()
    
    # 验证配置
    if JTConfig.validate_config():
        print("✅ JT配置验证通过")
    else:
        print("❌ JT配置验证失败")
    
    # 显示关键配置
    print("\n=== 关键配置详情 ===")
    print("字段映射:")
    for jt_field, std_field in JTConfig.get_field_mapping().items():
        print(f"  {jt_field} -> {std_field}")
    
    print(f"\n单位转换状态: {'禁用' if JTConfig.is_unit_conversion_disabled() else '启用'}")
    
    print("\nExcel配置:")
    excel_config = JTConfig.get_excel_config()
    for key, value in excel_config.items():
        print(f"  {key}: {value}")
    
    print("\n🔥 JT特有配置验证:")
    print(f"  - 单位转换禁用: {JTConfig.is_unit_conversion_disabled()}")
    print(f"  - 异常值处理方法: {JTConfig.get_cleaning_config()['default_outlier_method']}")
    print(f"  - 测试条件包含: {not JTConfig.get_complete_config()['spec_file_config']['include_testcond']}")
    
    print("\n✅ JT配置模块初始化完成") 