"""
读取器工厂模块，用于创建适合特定文件格式的读取器实例。
"""

import os
import logging
from typing import Union, List, Optional

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.readers.cw_reader import CWReader
from cp_data_processor.readers.dcp_reader import DCPReader
from cp_data_processor.readers.mex_reader import MEXReader
from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader

# 获取日志记录器
logger = logging.getLogger(__name__)


def create_reader(file_paths: Union[str, List[str]], 
                  format_type: Optional[str] = None, 
                  pass_bin: int = 1, 
                  multi_wafer: bool = False) -> BaseReader:
    """
    根据文件格式或指定的格式类型创建对应的读取器。
    
    Args:
        file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
        format_type: 指定的格式类型 ('CW', 'CWSW', 'CWMW', 'DCP', 'MEX', 'ETXT')，如果为 None 则自动判断
        pass_bin: 表示通过的 Bin 值，默认为 1
        multi_wafer: 对于 CW 格式，是否为多晶圆模式
        
    Returns:
        BaseReader: 对应格式的读取器实例
    
    Raises:
        ValueError: 如果无法确定格式或格式不支持
    """
    # 标准化为列表
    paths = [file_paths] if isinstance(file_paths, str) else file_paths
    
    # 确保format_type是大写并且是有效类型
    valid_formats = ['CW', 'CWSW', 'CWMW', 'DCP', 'MEX', 'ETXT']
    
    # 如果指定了格式类型，直接使用
    if format_type is not None:
        format_type = format_type.upper()
        # 特殊处理一些简化的格式名
        if format_type == 'CW':
            format_type = 'CWSW' if not multi_wafer else 'CWMW' 
        if format_type == 'CMSW':  # 兼容旧格式名
            format_type = 'CWSW'
            
        logger.info(f"使用指定的格式类型: {format_type}")
    # 如果未指定格式，尝试根据文件扩展名判断
    else:
        if not paths:
            raise ValueError("文件路径列表为空，无法自动判断格式")
        
        # 确保正确获取文件扩展名
        file_path = str(paths[0])  # 确保是字符串
        logger.info(f"尝试从文件路径判断格式: {file_path}")
        
        base_name = os.path.basename(file_path)
        extension = os.path.splitext(base_name)[1].lower()
        
        if not extension:
            # 如果没有获取到扩展名，尝试直接从文件名判断
            if '.txt' in file_path.lower():
                extension = '.txt'
                logger.info(f"从文件名中提取扩展名: {extension}")
            elif '.csv' in file_path.lower():
                extension = '.csv'
                logger.info(f"从文件名中提取扩展名: {extension}")
            elif '.xls' in file_path.lower() or '.xlsx' in file_path.lower():
                extension = '.xlsx'
                logger.info(f"从文件名中提取扩展名: {extension}")
            else:
                error_msg = f"无法从文件路径 '{file_path}' 确定格式。源文件扩展名是txt格式"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        if extension == '.csv':
            format_type = 'CWMW' if multi_wafer else 'CWSW'
        elif extension == '.txt':
            # 检查是否为Excel格式的TXT文件
            if ExcelTXTReader.is_excel_format(file_path):
                format_type = 'ETXT'
                logger.info("检测到Excel格式的TXT文件")
            else:
                format_type = 'DCP'
        elif extension in ['.xls', '.xlsx']:
            format_type = 'MEX'
        else:
            error_msg = f"无法从文件扩展名 '{extension}' 确定格式"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"根据文件扩展名确定格式类型: {format_type}")
    
    # 创建对应的读取器
    logger.info(f"创建读取器: {format_type}")
    
    if format_type == 'CWSW' or format_type == 'CWMW':
        is_multi = format_type == 'CWMW' or multi_wafer
        return CWReader(paths, pass_bin, is_multi)
    elif format_type == 'DCP':
        return DCPReader(paths, pass_bin)
    elif format_type == 'MEX':
        return MEXReader(paths, pass_bin)
    elif format_type == 'ETXT':
        return ExcelTXTReader(paths, pass_bin)
    else:
        error_msg = f"不支持的格式类型: {format_type}"
        logger.error(error_msg)
        raise ValueError(error_msg) 