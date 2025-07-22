"""
厂商配置管理

统一管理不同厂商的数据格式配置，包括字段映射、单位转换、格式识别等。
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 厂商配置字典
COMPANY_CONFIGS: Dict[str, Dict[str, Any]] = {
    'HH': {
        'name': 'HH公司',
        'description': 'HH公司CP测试数据格式（基准格式）',
        'supported_formats': ['DCP', 'CW', 'MEX', 'ETXT'],
        'default_format': 'DCP',
        'version': '1.0.0',
        
        # HH格式作为标准格式，不需要字段映射
        'field_mapping': {
            # HH -> HH (恒等映射)
            'Lot_ID': 'Lot_ID',
            'Wafer_ID': 'Wafer_ID', 
            'Seq': 'Seq',
            'Bin': 'Bin',
            'X': 'X',
            'Y': 'Y',
            'CONT': 'CONT'
        },
        
        # HH格式不需要单位转换
        'unit_conversion': {},
        
        # 文件识别特征
        'file_patterns': {
            'path_patterns': ['/HH_data/', '/hh/', '_hh_'],
            'filename_patterns': ['*_HH_*', 'HH_*'],
            'content_signatures': ['# HH Format', 'HH_VERSION'],
            'file_extensions': ['.dcp', '.cw', '.mex', '.txt']
        },
        
        # 数据质量配置
        'data_validation': {
            'required_fields': ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y'],
            'optional_fields': ['CONT'],
            'bin_values': {
                'pass_bins': [1],
                'fail_bins': [2, 3, 4, 5, 6, 7, 8, 9]
            }
        }
    },
    
    'JT': {
        'name': 'JT-Semiconductor',
        'description': 'Jetech公司Excel格式CP测试数据',
        'supported_formats': ['JT_EXCEL'],
        'default_format': 'JT_EXCEL',
        'version': '1.0.0',
        
        # JT字段到标准字段的映射
        'field_mapping': {
            'SOFT_BIN': 'Bin',
            'X_COORD': 'X', 
            'Y_COORD': 'Y',
            'DUT_NO': 'Seq',
            'LOT_ID': 'Lot_ID',
            'WAFER_ID': 'Wafer_ID'
        },
        
        # 单位转换配置
        'unit_conversion': {
            'RDSON1': {'factor': 0.001, 'offset': 0.0}  # mOhm to Ohm
        },
        
        # 文件识别特征
        'file_patterns': {
            'path_patterns': ['/JT_data/', '/jt/', '_jt_', '/jetech/'],
            'filename_patterns': ['*_JT_*', 'JT_*', 'FA*-*.xls*'],
            'content_signatures': [],
            'file_extensions': ['.xls', '.xlsx']
        },
        
        # 数据质量配置
        'data_validation': {
            'required_fields': ['LOT_ID', 'WAFER_ID', 'DUT_NO', 'SOFT_BIN', 'X_COORD', 'Y_COORD'],
            'optional_fields': [],
            'bin_values': {
                'pass_bins': [1],
                'fail_bins': [2, 3, 4, 5, 6, 7, 8, 9]
            }
        }
    },
    
    'LION': {
        'name': 'Lion公司',
        'description': 'Lion公司Excel格式CP测试数据',
        'supported_formats': ['LION_EXCEL'],
        'default_format': 'LION_EXCEL',
        'version': '1.0.0',
        
        # Lion字段到标准字段的映射
        'field_mapping': {
            'PART_INDEX': 'Seq',
            'SOFT_BIN': 'Bin', 
            'X_COORD': 'X',
            'Y_COORD': 'Y',
            'PASSFG': 'CONT'
        },
        
        # 单位转换配置（如需要）
        'unit_conversion': {
            # 示例：如果需要单位转换
            # 'VF_10A': {'factor': 1.0, 'offset': 0.0}
        },
        
        # 文件识别特征
        'file_patterns': {
            'path_patterns': ['/data/', '/lion/', '_lion_'],
            'filename_patterns': ['F*.xlsx', '*_lion_*', 'LION_*'],
            'content_signatures': [],
            'file_extensions': ['.xlsx', '.xls']
        },
        
        # 数据质量配置
        'data_validation': {
            'required_fields': ['PART_INDEX', 'SOFT_BIN', 'X_COORD', 'Y_COORD'],
            'optional_fields': ['PASSFG', 'T_TIME', 'SITE_NUM'],
            'bin_values': {
                'pass_bins': [1],
                'fail_bins': [2, 3, 4, 5, 6, 7, 8, 9]
            }
        }
    }
}


def get_company_config(company_name: str) -> Optional[Dict[str, Any]]:
    """
    获取指定厂商的配置
    
    Args:
        company_name: 厂商名称 ('HH', 'JT')
        
    Returns:
        Dict[str, Any]: 厂商配置字典，如果厂商不存在返回None
    """
    config = COMPANY_CONFIGS.get(company_name.upper())
    if config is None:
        logger.warning(f"未找到厂商 '{company_name}' 的配置")
    return config


def get_all_company_names() -> list[str]:
    """
    获取所有支持的厂商名称列表
    
    Returns:
        List[str]: 厂商名称列表
    """
    return list(COMPANY_CONFIGS.keys())


def get_company_display_name(company_name: str) -> str:
    """
    获取厂商显示名称
    
    Args:
        company_name: 厂商代码
        
    Returns:  
        str: 厂商显示名称
    """
    config = get_company_config(company_name)
    if config:
        return config.get('name', company_name)
    return company_name


def validate_company_config(company_name: str) -> bool:
    """
    验证厂商配置的完整性
    
    Args:
        company_name: 厂商名称
        
    Returns:
        bool: 配置有效返回True，否则返回False
    """
    config = get_company_config(company_name)
    if not config:
        return False
        
    # 检查必需字段
    required_fields = ['name', 'supported_formats', 'field_mapping']
    for field in required_fields:
        if field not in config:
            logger.error(f"厂商 {company_name} 配置缺少必需字段: {field}")
            return False
            
    # 检查字段映射是否为空
    if not config['field_mapping']:
        logger.error(f"厂商 {company_name} 的字段映射为空")
        return False
        
    logger.info(f"厂商 {company_name} 配置验证通过")
    return True


def detect_company_from_path(file_path: str) -> Optional[str]:
    """
    从文件路径检测厂商
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[str]: 检测到的厂商名称，未检测到返回None
    """
    file_path_lower = file_path.lower()
    
    for company_name, config in COMPANY_CONFIGS.items():
        patterns = config.get('file_patterns', {}).get('path_patterns', [])
        for pattern in patterns:
            if pattern.lower() in file_path_lower:
                logger.info(f"从路径 '{file_path}' 检测到厂商: {company_name}")
                return company_name
                
    return None


def detect_company_from_filename(filename: str) -> Optional[str]:
    """
    从文件名检测厂商
    
    Args:
        filename: 文件名
        
    Returns:
        Optional[str]: 检测到的厂商名称，未检测到返回None
    """
    filename_lower = filename.lower()
    
    for company_name, config in COMPANY_CONFIGS.items():
        patterns = config.get('file_patterns', {}).get('filename_patterns', [])
        for pattern in patterns:
            # 简单的通配符匹配
            pattern_lower = pattern.lower().replace('*', '')
            if pattern_lower in filename_lower:
                logger.info(f"从文件名 '{filename}' 检测到厂商: {company_name}")
                return company_name
                
    return None


# 配置更新函数（用于运行时动态配置）
def update_company_config(company_name: str, updates: Dict[str, Any]) -> bool:
    """
    更新厂商配置
    
    Args:
        company_name: 厂商名称
        updates: 更新内容字典
        
    Returns:
        bool: 更新成功返回True，否则返回False
    """
    if company_name not in COMPANY_CONFIGS:
        logger.error(f"厂商 {company_name} 不存在，无法更新配置")
        return False
        
    try:
        COMPANY_CONFIGS[company_name].update(updates)
        logger.info(f"已更新厂商 {company_name} 的配置")
        return True
    except Exception as e:
        logger.error(f"更新厂商 {company_name} 配置时出错: {e}")
        return False 