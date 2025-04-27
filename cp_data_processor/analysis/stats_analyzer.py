import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer
from ..data_models.cp_data import CPParameter, CPWafer, CPLot

class StatsAnalyzer(BaseAnalyzer):
    """CP数据统计分析器，用于计算各种统计指标"""
    
    def __init__(self, data=None, parameters=None, by_wafer=False):
        """
        初始化统计分析器
        
        Args:
            data: CP数据，可以是DataFrame、CPLot对象
            parameters: 需要分析的参数列表，默认为None表示分析所有参数
            by_wafer: 是否按晶圆分组计算统计值，默认为False
        """
        super().__init__(data)
        self.parameters = parameters
        self.by_wafer = by_wafer
        self.results = {
            'overall': {},
            'by_wafer': {}
        }
    
    def analyze(self):
        """执行统计分析"""
        self.validate_data()
        
        # 处理不同类型的输入数据
        df = self._get_dataframe()
        
        # 确定要分析的参数列表
        if self.parameters is None:
            # 排除非参数列
            exclude_cols = ['Wafer', 'Seq', 'Bin', 'X', 'Y']
            self.parameters = [col for col in df.columns if col not in exclude_cols]
        
        # 计算整体统计量
        param_stats = {}
        for param in self.parameters:
            if param in df.columns:
                param_data = pd.to_numeric(df[param], errors='coerce')
                param_stats[param] = {
                    'mean': param_data.mean(),
                    'median': param_data.median(),
                    'std': param_data.std(),
                    'min': param_data.min(),
                    'max': param_data.max(),
                    'q1': param_data.quantile(0.25),
                    'q3': param_data.quantile(0.75),
                    'count': param_data.count(),
                    'missing': param_data.isna().sum()
                }
        
        self.results['overall'] = param_stats
        
        # 按晶圆分组计算统计量
        if self.by_wafer and 'Wafer' in df.columns:
            wafer_groups = df.groupby('Wafer')
            for wafer, group in wafer_groups:
                wafer_stats = {}
                for param in self.parameters:
                    if param in group.columns:
                        param_data = pd.to_numeric(group[param], errors='coerce')
                        wafer_stats[param] = {
                            'mean': param_data.mean(),
                            'median': param_data.median(),
                            'std': param_data.std(),
                            'min': param_data.min(),
                            'max': param_data.max(),
                            'q1': param_data.quantile(0.25),
                            'q3': param_data.quantile(0.75),
                            'count': param_data.count(),
                            'missing': param_data.isna().sum()
                        }
                self.results['by_wafer'][wafer] = wafer_stats
        
        return self.results
    
    def get_results(self):
        """获取分析结果"""
        if not self.results['overall']:
            self.analyze()
        return self.results
    
    def get_summary(self, format='dataframe'):
        """
        获取统计摘要
        
        Args:
            format: 返回格式，'dataframe'或'dict'
        
        Returns:
            根据指定格式返回统计摘要
        """
        if not self.results['overall']:
            self.analyze()
        
        if format == 'dataframe':
            # 将结果转换为DataFrame
            stats_list = []
            for param, stats in self.results['overall'].items():
                stats_dict = {'Parameter': param}
                stats_dict.update(stats)
                stats_list.append(stats_dict)
            
            return pd.DataFrame(stats_list)
        else:
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