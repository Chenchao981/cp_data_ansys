import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer
from ..data_models.cp_data import CPParameter, CPWafer, CPLot

class CapabilityAnalyzer(BaseAnalyzer):
    """CP数据工艺能力分析器，用于计算Cp、Cpk等工艺能力指标"""
    
    def __init__(self, data=None, parameters=None, specs=None, by_wafer=False):
        """
        初始化工艺能力分析器
        
        Args:
            data: CP数据，可以是DataFrame、CPLot对象
            parameters: 需要分析的参数列表，默认为None表示分析所有有规格的参数
            specs: 参数规格字典，格式为 {parameter: {'LSL': lower_limit, 'USL': upper_limit}}
            by_wafer: 是否按晶圆分组计算能力指标，默认为False
        """
        super().__init__(data)
        self.parameters = parameters
        self.specs = specs or {}
        self.by_wafer = by_wafer
        self.results = {
            'overall': {},
            'by_wafer': {}
        }
    
    def analyze(self):
        """执行工艺能力分析"""
        self.validate_data()
        
        # 处理不同类型的输入数据
        df = self._get_dataframe()
        
        # 确定要分析的参数列表
        if self.parameters is None:
            # 如果没有指定参数，使用有规格的参数
            self.parameters = list(self.specs.keys())
        
        # 计算整体工艺能力指标
        param_capability = {}
        for param in self.parameters:
            if param in df.columns and param in self.specs:
                param_data = pd.to_numeric(df[param], errors='coerce')
                param_capability[param] = self._calculate_capability(
                    param_data, 
                    self.specs[param].get('LSL'), 
                    self.specs[param].get('USL')
                )
        
        self.results['overall'] = param_capability
        
        # 按晶圆分组计算工艺能力指标
        if self.by_wafer and 'Wafer' in df.columns:
            wafer_groups = df.groupby('Wafer')
            for wafer, group in wafer_groups:
                wafer_capability = {}
                for param in self.parameters:
                    if param in group.columns and param in self.specs:
                        param_data = pd.to_numeric(group[param], errors='coerce')
                        wafer_capability[param] = self._calculate_capability(
                            param_data, 
                            self.specs[param].get('LSL'), 
                            self.specs[param].get('USL')
                        )
                self.results['by_wafer'][wafer] = wafer_capability
        
        return self.results
    
    def get_results(self):
        """获取分析结果"""
        if not self.results['overall']:
            self.analyze()
        return self.results
    
    def get_summary(self, format='dataframe'):
        """
        获取工艺能力摘要
        
        Args:
            format: 返回格式，'dataframe'或'dict'
        
        Returns:
            根据指定格式返回工艺能力摘要
        """
        if not self.results['overall']:
            self.analyze()
        
        if format == 'dataframe':
            # 将结果转换为DataFrame
            capability_list = []
            for param, capability in self.results['overall'].items():
                capability_dict = {'Parameter': param}
                capability_dict.update(capability)
                capability_list.append(capability_dict)
            
            return pd.DataFrame(capability_list)
        else:
            return self.results
    
    def _calculate_capability(self, data, lsl=None, usl=None):
        """
        计算能力指标
        
        Args:
            data: 参数数据
            lsl: 下限
            usl: 上限
        
        Returns:
            包含Cp、Cpk等指标的字典
        """
        # 剔除缺失值
        data = data.dropna()
        
        # 计算基本统计量
        mean = data.mean()
        std = data.std()
        
        # 初始化结果
        result = {
            'mean': mean,
            'std': std,
            'Cp': None,
            'Cpk': None,
            'Cpl': None,
            'Cpu': None,
            'within_spec_percent': None
        }
        
        # 检查是否有足够的数据点和非零标准差
        if len(data) < 30 or std == 0:
            return result
        
        # 计算在规格内的百分比
        if lsl is not None and usl is not None:
            within_spec = ((data >= lsl) & (data <= usl)).sum()
            result['within_spec_percent'] = (within_spec / len(data)) * 100
        
        # 计算Cp (Process Capability)
        if lsl is not None and usl is not None:
            result['Cp'] = (usl - lsl) / (6 * std)
            
            # 计算Cpl (Lower Process Capability)
            result['Cpl'] = (mean - lsl) / (3 * std)
            
            # 计算Cpu (Upper Process Capability)
            result['Cpu'] = (usl - mean) / (3 * std)
            
            # 计算Cpk (Minimum Process Capability)
            result['Cpk'] = min(result['Cpl'], result['Cpu'])
        elif lsl is not None:
            # 只有下限
            result['Cpl'] = (mean - lsl) / (3 * std)
            result['Cpk'] = result['Cpl']
        elif usl is not None:
            # 只有上限
            result['Cpu'] = (usl - mean) / (3 * std)
            result['Cpk'] = result['Cpu']
        
        return result
    
    def _get_dataframe(self):
        """根据输入数据类型获取DataFrame"""
        if isinstance(self.data, pd.DataFrame):
            return self.data
        elif isinstance(self.data, CPLot):
            # 假设CPLot对象有to_dataframe方法
            return self.data.to_dataframe()
        else:
            raise TypeError("不支持的数据类型，请提供DataFrame或CPLot对象")
            
    def load_specs_from_file(self, file_path):
        """从文件加载参数规格"""
        # 后续实现从CSV、Excel等文件加载规格
        pass 