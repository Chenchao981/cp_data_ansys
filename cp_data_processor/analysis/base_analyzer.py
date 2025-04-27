from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from ..data_models.cp_data import CPParameter, CPWafer, CPLot

class BaseAnalyzer(ABC):
    """基础分析器抽象类，定义所有CP数据分析器的通用接口"""
    
    def __init__(self, data=None):
        """
        初始化分析器
        
        Args:
            data: 可以是DataFrame、CPLot或其他数据对象
        """
        self.data = data
        self.results = {}
    
    @abstractmethod
    def analyze(self):
        """执行分析，必须由子类实现"""
        pass
    
    @abstractmethod
    def get_results(self):
        """获取分析结果，必须由子类实现"""
        pass
    
    def validate_data(self):
        """验证输入数据的有效性"""
        if self.data is None:
            raise ValueError("没有提供数据进行分析")
        return True 