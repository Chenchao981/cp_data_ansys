"""
读取器工厂模块，用于创建适合特定文件格式的读取器实例。
"""

import os
from typing import Union, List, Optional

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.readers.cw_reader import CWReader
from cp_data_processor.readers.dcp_reader import DCPReader
from cp_data_processor.readers.mex_reader import MEXReader


def create_reader(file_paths: Union[str, List[str]], 
                  format_type: Optional[str] = None, 
                  pass_bin: int = 1, 
                  multi_wafer: bool = False) -> BaseReader:
    """
    根据文件格式或指定的格式类型创建对应的读取器。
    
    Args:
        file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
        format_type: 指定的格式类型 ('CW', 'CWSW', 'CWMW', 'DCP', 'MEX')，如果为 None 则自动判断
        pass_bin: 表示通过的 Bin 值，默认为 1
        multi_wafer: 对于 CW 格式，是否为多晶圆模式
        
    Returns:
        BaseReader: 对应格式的读取器实例
    
    Raises:
        ValueError: 如果无法确定格式或格式不支持
    """
    # 标准化为列表
    paths = [file_paths] if isinstance(file_paths, str) else file_paths
    
    # 如果未指定格式，尝试根据文件扩展名判断
    if format_type is None:
        if not paths:
            raise ValueError("文件路径列表为空，无法自动判断格式")
        
        extension = os.path.splitext(paths[0])[1].lower()
        
        if extension == '.csv':
            format_type = 'CWMW' if multi_wafer else 'CWSW'
        elif extension == '.txt':
            format_type = 'DCP'
        elif extension in ['.xls', '.xlsx']:
            format_type = 'MEX'
        else:
            raise ValueError(f"无法从文件扩展名 '{extension}' 确定格式")
    
    # 创建对应的读取器
    format_type = format_type.upper()
    
    if format_type in ['CW', 'CWSW', 'CWMW']:
        is_multi = format_type == 'CWMW' or multi_wafer
        return CWReader(paths, pass_bin, is_multi)
    elif format_type == 'DCP':
        return DCPReader(paths, pass_bin)
    elif format_type == 'MEX':
        return MEXReader(paths, pass_bin)
    else:
        raise ValueError(f"不支持的格式类型: {format_type}") 