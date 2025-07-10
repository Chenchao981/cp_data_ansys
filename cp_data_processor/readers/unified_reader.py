"""
统一读取器

提供统一的数据读取接口，自动识别文件类型和公司格式，
调用相应的读取器和适配器进行数据处理。
"""

import os
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from cp_data_processor.data_models.cp_data import CPLot
from .company_adapters.company_registry import get_company_registry
from .reader_factory import create_reader_by_format

logger = logging.getLogger(__name__)


class UnifiedReader:
    """
    统一读取器
    
    整合文件格式识别、公司识别和数据标准化的完整流程。
    提供一站式的数据读取和转换服务。
    """
    
    def __init__(self):
        """初始化统一读取器"""
        self.company_registry = get_company_registry()
        self.logger = logging.getLogger(__name__)
    
    def read_data(self, file_path: str, company_code: Optional[str] = None) -> CPLot:
        """
        读取并标准化数据
        
        Args:
            file_path: 数据文件路径
            company_code: 可选的公司代码，如果不提供将自动识别
            
        Returns:
            CPLot: 标准化后的数据对象
            
        Raises:
            ValueError: 文件不存在或无法识别格式
            RuntimeError: 数据读取或转换失败
        """
        if not os.path.exists(file_path):
            raise ValueError(f"文件不存在: {file_path}")
        
        self.logger.info(f"开始处理文件: {file_path}")
        
        try:
            # 1. 识别公司
            if not company_code:
                company_code = self._detect_company(file_path)
                if not company_code:
                    raise ValueError(f"无法识别文件所属公司: {file_path}")
            
            self.logger.info(f"识别公司: {company_code}")
            
            # 2. 获取公司适配器
            adapter = self.company_registry.get_company_adapter(company_code)
            if not adapter:
                raise ValueError(f"无法获取{company_code}公司适配器")
            
            # 3. 识别文件格式并读取原始数据
            raw_lot = self._read_raw_data(file_path, company_code)
            
            # 4. 使用适配器标准化数据
            standardized_lot = adapter.standardize_data(raw_lot)
            
            self.logger.info(f"数据处理完成: {file_path}")
            return standardized_lot
            
        except Exception as e:
            self.logger.error(f"处理文件失败 {file_path}: {e}")
            raise RuntimeError(f"数据读取失败: {e}") from e
    
    def read_batch(self, file_paths: list[str]) -> Dict[str, CPLot]:
        """
        批量读取多个文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            Dict[str, CPLot]: 文件路径到CPLot对象的映射
        """
        results = {}
        failed_files = []
        
        for file_path in file_paths:
            try:
                lot = self.read_data(file_path)
                results[file_path] = lot
                self.logger.info(f"成功处理: {file_path}")
            except Exception as e:
                failed_files.append((file_path, str(e)))
                self.logger.error(f"处理失败: {file_path} - {e}")
        
        if failed_files:
            self.logger.warning(f"批量处理完成，{len(failed_files)}个文件失败")
            for file_path, error in failed_files:
                self.logger.warning(f"  失败: {file_path} - {error}")
        
        return results
    
    def can_process_file(self, file_path: str) -> bool:
        """
        检查是否能处理指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 能处理返回True，否则返回False
        """
        if not os.path.exists(file_path):
            return False
        
        # 尝试识别公司
        company_code = self._detect_company(file_path)
        if not company_code:
            return False
        
        # 检查适配器是否可用
        adapter = self.company_registry.get_company_adapter(company_code)
        if not adapter:
            return False
        
        # 检查适配器是否能处理此文件
        return adapter.can_process_file(file_path)
    
    def get_supported_companies(self) -> list[str]:
        """
        获取支持的公司列表
        
        Returns:
            list[str]: 支持的公司代码列表
        """
        return self.company_registry.list_supported_companies()
    
    def get_company_info(self, company_code: str) -> Optional[Dict[str, Any]]:
        """
        获取公司信息
        
        Args:
            company_code: 公司代码
            
        Returns:
            Optional[Dict[str, Any]]: 公司信息，如果未找到返回None
        """
        return self.company_registry.get_company_info(company_code)
    
    def _detect_company(self, file_path: str) -> Optional[str]:
        """
        检测文件所属公司
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 公司代码，如果无法识别返回None
        """
        return self.company_registry.detect_company_from_file(file_path)
    
    def _read_raw_data(self, file_path: str, company_code: str) -> CPLot:
        """
        读取原始数据
        
        Args:
            file_path: 文件路径
            company_code: 公司代码
            
        Returns:
            CPLot: 原始数据对象
        """
        # 获取文件扩展名来判断格式
        file_ext = Path(file_path).suffix.lower()
        
        # 根据公司和文件扩展名选择读取器
        if company_code == 'HH':
            if file_ext == '.dcp':
                reader = create_reader_by_format(file_path, 'DCP')
            elif file_ext == '.cw':
                reader = create_reader_by_format(file_path, 'CW')
            elif file_ext == '.mex':
                reader = create_reader_by_format(file_path, 'MEX')
            elif file_ext in ['.txt']:
                reader = create_reader_by_format(file_path, 'ETXT')
            else:
                raise ValueError(f"HH公司不支持的文件格式: {file_ext}")
                
        elif company_code == 'JT':
            if file_ext in ['.xls', '.xlsx']:
                # JT公司使用JTReader
                from .jt_reader import JTReader
                reader = JTReader([file_path])
            else:
                raise ValueError(f"JT公司不支持的文件格式: {file_ext}")
        else:
            raise ValueError(f"不支持的公司: {company_code}")
        
        # 读取数据
        lot = reader.read_file(file_path)
        self.logger.info(f"使用{reader.__class__.__name__}读取原始数据完成")
        
        return lot


# 便捷函数
def read_cp_data(file_path: str, company_code: Optional[str] = None) -> CPLot:
    """
    读取CP数据的便捷函数
    
    Args:
        file_path: 数据文件路径
        company_code: 可选的公司代码
        
    Returns:
        CPLot: 标准化后的数据对象
    """
    reader = UnifiedReader()
    return reader.read_data(file_path, company_code)


def batch_read_cp_data(file_paths: list[str]) -> Dict[str, CPLot]:
    """
    批量读取CP数据的便捷函数
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        Dict[str, CPLot]: 文件路径到CPLot对象的映射
    """
    reader = UnifiedReader()
    return reader.read_batch(file_paths)


def can_process_cp_file(file_path: str) -> bool:
    """
    检查是否能处理CP文件的便捷函数
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 能处理返回True，否则返回False
    """
    reader = UnifiedReader()
    return reader.can_process_file(file_path)