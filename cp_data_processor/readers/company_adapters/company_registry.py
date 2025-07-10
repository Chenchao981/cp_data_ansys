"""
公司注册管理器

提供公司适配器的注册、发现和管理功能，支持动态加载和自动识别。
"""

import os
import importlib
from typing import Dict, List, Optional, Type, Any
import logging
from pathlib import Path

from .base_company_adapter import BaseCompanyAdapter
from .company_config import COMPANY_CONFIGS, detect_company_from_path, detect_company_from_filename

logger = logging.getLogger(__name__)


class CompanyRegistry:
    """
    公司注册管理器
    
    负责管理所有公司适配器的注册、发现和实例化。
    支持动态加载适配器类和自动公司识别。
    """
    
    def __init__(self):
        """初始化注册管理器"""
        self._adapters: Dict[str, Type[BaseCompanyAdapter]] = {}
        self._instances: Dict[str, BaseCompanyAdapter] = {}
        self.logger = logging.getLogger(__name__)
        
        # 自动加载已知的适配器
        self._auto_load_adapters()
    
    def register_company(self, company_code: str, adapter_class: Type[BaseCompanyAdapter]):
        """
        注册公司适配器
        
        Args:
            company_code: 公司代码 (如: 'HH', 'JT')
            adapter_class: 适配器类
        """
        if not issubclass(adapter_class, BaseCompanyAdapter):
            raise ValueError(f"适配器类必须继承自BaseCompanyAdapter: {adapter_class}")
        
        self._adapters[company_code.upper()] = adapter_class
        self.logger.info(f"已注册公司适配器: {company_code} -> {adapter_class.__name__}")
    
    def get_company_adapter(self, company_code: str) -> Optional[BaseCompanyAdapter]:
        """
        获取公司适配器实例
        
        Args:
            company_code: 公司代码
            
        Returns:
            BaseCompanyAdapter: 适配器实例，如果未找到返回None
        """
        company_code = company_code.upper()
        
        # 如果已有实例，直接返回
        if company_code in self._instances:
            return self._instances[company_code]
        
        # 创建新实例
        if company_code in self._adapters:
            try:
                adapter_class = self._adapters[company_code]
                config = COMPANY_CONFIGS.get(company_code, {})
                instance = adapter_class(config)
                self._instances[company_code] = instance
                self.logger.info(f"创建{company_code}适配器实例")
                return instance
            except Exception as e:
                self.logger.error(f"创建{company_code}适配器实例失败: {e}")
                return None
        
        self.logger.warning(f"未找到公司适配器: {company_code}")
        return None
    
    def list_supported_companies(self) -> List[str]:
        """
        获取支持的公司列表
        
        Returns:
            List[str]: 支持的公司代码列表
        """
        return list(self._adapters.keys())
    
    def detect_company_from_file(self, file_path: str) -> Optional[str]:
        """
        从文件路径自动识别公司
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 公司代码，如果无法识别返回None
        """
        # 1. 从路径识别
        company = detect_company_from_path(file_path)
        if company:
            self.logger.info(f"从路径识别公司: {file_path} -> {company}")
            return company
        
        # 2. 从文件名识别
        filename = os.path.basename(file_path)
        company = detect_company_from_filename(filename)
        if company:
            self.logger.info(f"从文件名识别公司: {filename} -> {company}")
            return company
        
        # 3. 尝试通过适配器的can_process_file方法识别
        for company_code in self._adapters.keys():
            adapter = self.get_company_adapter(company_code)
            if adapter and adapter.can_process_file(file_path):
                self.logger.info(f"通过适配器识别公司: {file_path} -> {company_code}")
                return company_code
        
        self.logger.warning(f"无法识别文件所属公司: {file_path}")
        return None
    
    def get_company_info(self, company_code: str) -> Optional[Dict[str, Any]]:
        """
        获取公司信息
        
        Args:
            company_code: 公司代码
            
        Returns:
            Optional[Dict[str, Any]]: 公司信息，如果未找到返回None
        """
        adapter = self.get_company_adapter(company_code)
        if adapter:
            return adapter.get_company_info()
        return None
    
    def list_company_info(self) -> List[Dict[str, Any]]:
        """
        获取所有公司信息列表
        
        Returns:
            List[Dict[str, Any]]: 所有公司信息列表
        """
        companies_info = []
        for company_code in self.list_supported_companies():
            info = self.get_company_info(company_code)
            if info:
                companies_info.append(info)
        return companies_info
    
    def _auto_load_adapters(self):
        """自动加载已知的适配器"""
        # 加载HH适配器
        try:
            from .hh_adapter import HHAdapter
            self.register_company('HH', HHAdapter)
        except ImportError as e:
            self.logger.warning(f"无法加载HH适配器: {e}")
        
        # 加载JT适配器
        try:
            from .jt_adapter import JTAdapter
            self.register_company('JT', JTAdapter)
        except ImportError as e:
            self.logger.warning(f"无法加载JT适配器: {e}")
        
        # 可以继续添加其他适配器的自动加载
        self._load_dynamic_adapters()
    
    def _load_dynamic_adapters(self):
        """动态加载适配器"""
        current_dir = Path(__file__).parent
        
        # 查找所有*_adapter.py文件
        for adapter_file in current_dir.glob("*_adapter.py"):
            if adapter_file.name in ['base_company_adapter.py', '__init__.py']:
                continue
            
            try:
                # 提取公司代码
                company_code = adapter_file.stem.replace('_adapter', '').upper()
                if company_code in ['HH', 'JT']:  # 已经手动加载的跳过
                    continue
                
                # 动态导入模块
                module_name = f".{adapter_file.stem}"
                module = importlib.import_module(module_name, package=__package__)
                
                # 查找适配器类
                adapter_class_name = f"{company_code}Adapter"
                if hasattr(module, adapter_class_name):
                    adapter_class = getattr(module, adapter_class_name)
                    self.register_company(company_code, adapter_class)
                    self.logger.info(f"动态加载适配器: {company_code}")
                
            except Exception as e:
                self.logger.warning(f"动态加载适配器失败 {adapter_file}: {e}")


# 全局注册管理器实例
_global_registry = None


def get_company_registry() -> CompanyRegistry:
    """
    获取全局公司注册管理器实例
    
    Returns:
        CompanyRegistry: 全局注册管理器实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = CompanyRegistry()
    return _global_registry


def register_company_adapter(company_code: str, adapter_class: Type[BaseCompanyAdapter]):
    """
    注册公司适配器（便捷函数）
    
    Args:
        company_code: 公司代码
        adapter_class: 适配器类
    """
    registry = get_company_registry()
    registry.register_company(company_code, adapter_class)


def get_adapter_for_file(file_path: str) -> Optional[BaseCompanyAdapter]:
    """
    为文件获取对应的公司适配器（便捷函数）
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[BaseCompanyAdapter]: 适配器实例，如果无法识别返回None
    """
    registry = get_company_registry()
    company_code = registry.detect_company_from_file(file_path)
    if company_code:
        return registry.get_company_adapter(company_code)
    return None