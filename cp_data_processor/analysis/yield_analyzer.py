import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer
from ..data_models.cp_data import CPParameter, CPWafer, CPLot

class YieldAnalyzer(BaseAnalyzer):
    """CP数据良率分析器，用于计算各种良率指标"""
    
    def __init__(self, data=None, bin_good=1, parameters=None):
        """
        初始化良率分析器
        
        Args:
            data: CP数据，可以是DataFrame、CPLot对象
            bin_good: 良品的bin号，默认为1
            parameters: 需要计算良率的参数列表，默认为None表示计算所有参数
        """
        super().__init__(data)
        self.bin_good = bin_good
        self.parameters = parameters
        self.results = {
            'total_yield': 0.0,
            'wafer_yields': {},
            'parameter_yields': {}
        }
    
    def analyze(self):
        """执行良率分析"""
        self.validate_data()
        
        # 处理不同类型的输入数据
        df = self._get_dataframe()
        
        # 计算总体良率（基于bin号）
        total_dies = len(df)
        good_dies = len(df[df['Bin'] == self.bin_good])
        self.results['total_yield'] = (good_dies / total_dies) * 100 if total_dies > 0 else 0
        
        # 计算每个晶圆的良率
        if 'Wafer' in df.columns:
            wafer_groups = df.groupby('Wafer')
            for wafer, group in wafer_groups:
                wafer_dies = len(group)
                wafer_good_dies = len(group[group['Bin'] == self.bin_good])
                self.results['wafer_yields'][wafer] = (wafer_good_dies / wafer_dies) * 100 if wafer_dies > 0 else 0
        
        # 计算每个参数的良率（如果有上下限）
        if self.parameters is None:
            # 排除非参数列
            exclude_cols = ['Wafer', 'Seq', 'Bin', 'X', 'Y']
            self.parameters = [col for col in df.columns if col not in exclude_cols]
        
        # 这里需要参数上下限信息才能计算参数良率
        # 后续需要完善从配置或数据中获取参数规格
        
        return self.results
    
    def get_results(self):
        """获取分析结果"""
        if not self.results['total_yield']:
            self.analyze()
        return self.results
    
    def _get_dataframe(self):
        """根据输入数据类型获取DataFrame"""
        if isinstance(self.data, pd.DataFrame):
            return self.data
        elif isinstance(self.data, CPLot):
            # 假设CPLot对象有to_dataframe方法
            return self.data.to_dataframe()
        else:
            raise TypeError("不支持的数据类型，请提供DataFrame或CPLot对象") 