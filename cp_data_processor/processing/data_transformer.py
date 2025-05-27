"""
数据转换器模块，用于对 CP 测试数据进行各种转换和增强。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Callable

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter


class DataTransformer:
    """
    数据转换器类，用于对 CP 测试数据进行清洗、转换和增强。
    
    主要功能：
    1. 添加计算列 - 根据现有参数计算新的参数
    2. 数据清洗 - 处理异常值、缺失值等
    3. 数据转换 - 单位转换、归一化等
    4. 分类和分组 - 根据条件对数据进行分类
    """
    
    def __init__(self, cp_lot: CPLot):
        """
        初始化数据转换器
        
        Args:
            cp_lot: 要处理的 CPLot 对象
        """
        self.cp_lot = cp_lot
        self.calculated_params = {}  # 记录已计算的参数 {参数名: 参数对象}
    
    @property
    def data(self):
        """
        获取处理后的数据
        
        Returns:
            pd.DataFrame 或 CPLot: 根据输入类型返回处理后的数据
        """
        return self.cp_lot
    
    def add_calculated_parameter(self, 
                                 param_id: str, 
                                 formula: Union[str, Callable],
                                 unit: Optional[str] = None,
                                 sl: Optional[float] = None,
                                 su: Optional[float] = None) -> None:
        """
        添加一个计算参数到 CPLot 对象
        
        Args:
            param_id: 新参数的 ID
            formula: 计算公式，可以是字符串表达式或函数
            unit: 新参数的单位
            sl: 规格下限
            su: 规格上限
        """
        # 检查参数是否已存在
        if param_id in [p.id for p in self.cp_lot.params]:
            print(f"参数 '{param_id}' 已存在，跳过添加")
            return
        
        # 计算新参数的值
        if self.cp_lot.combined_data is None:
            self.cp_lot.combine_data_from_wafers()
        
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            print("无法添加计算参数：没有可用的数据")
            return
        
        # 应用公式计算新参数
        try:
            if isinstance(formula, str):
                # 将字符串表达式作为 Python 代码计算
                # 注意：这种方法有安全风险，应在可信环境中使用
                param_values = self.cp_lot.combined_data.eval(formula)
            else:
                # 使用函数进行计算
                param_values = formula(self.cp_lot.combined_data)
            
            # 更新 combined_data 以包含新参数
            self.cp_lot.combined_data[param_id] = param_values
        except Exception as e:
            print(f"计算参数 '{param_id}' 时出错: {e}")
            return
        
        # 创建新的参数对象
        new_param = CPParameter(
            id=param_id,
            unit=unit,
            sl=sl,
            su=su,
            test_cond=[]
        )
        
        # 计算参数的基本统计值
        valid_values = pd.Series(param_values).dropna()
        if not valid_values.empty:
            new_param.mean = float(valid_values.mean())
            new_param.std_dev = float(valid_values.std())
            new_param.median = float(valid_values.median())
            new_param.min_val = float(valid_values.min())
            new_param.max_val = float(valid_values.max())
        
        # 添加到 CPLot 和 calculated_params
        self.cp_lot.params.append(new_param)
        self.cp_lot.param_count += 1
        self.calculated_params[param_id] = new_param
        
        # 更新每个晶圆的 chip_data
        self._update_wafer_chip_data(param_id)
    
    def _update_wafer_chip_data(self, param_id: str) -> None:
        """
        将新计算的参数添加到每个晶圆的 chip_data 中
        
        Args:
            param_id: 参数 ID
        """
        if self.cp_lot.combined_data is None or param_id not in self.cp_lot.combined_data.columns:
            return
        
        for wafer in self.cp_lot.wafers:
            # 跳过没有数据的晶圆
            if wafer.chip_data is None:
                continue
            
            # 从 combined_data 中提取对应晶圆的参数值
            wafer_data = self.cp_lot.combined_data[
                self.cp_lot.combined_data['Wafer_ID'] == wafer.wafer_id
            ]
            
            if not wafer_data.empty:
                # 将参数值添加到晶圆的 chip_data 中
                wafer.chip_data[param_id] = wafer_data[param_id].values
    
    def add_standard_calculated_parameters(self) -> None:
        """
        添加一组标准的计算参数
        """
        # 示例：添加最大值和最小值的差值
        try:
            # 获取所有数值参数的列表
            numeric_params = []
            for param in self.cp_lot.params:
                if param.id in self.cp_lot.combined_data.columns:
                    if np.issubdtype(self.cp_lot.combined_data[param.id].dtype, np.number):
                        numeric_params.append(param.id)
            
            # 对每个参数计算差值
            for param_id in numeric_params:
                delta_id = f"{param_id}_Delta"
                
                # 定义计算函数
                def calc_delta(df):
                    # 按晶圆分组计算最大值和最小值的差
                    result = df.groupby('Wafer_ID')[param_id].transform(
                        lambda x: x.max() - x.min()
                    )
                    return result
                
                # 添加计算参数
                self.add_calculated_parameter(
                    param_id=delta_id,
                    formula=calc_delta,
                    unit=self.cp_lot.params[self.cp_lot.get_param_names().index(param_id)].unit
                )
        except Exception as e:
            print(f"添加标准计算参数时出错: {e}")
    
    def clean_data(self, outlier_method: str = 'std_dev', std_dev_threshold: float = 3.0) -> None:
        """
        清理数据中的异常值
        
        Args:
            outlier_method: 检测异常值的方法，可选 'std_dev'（标准差法）、'iqr'（四分位法）
            std_dev_threshold: 使用标准差法时，超过均值多少个标准差视为异常值
        """
        print(f"开始数据清洗（{outlier_method}方法处理异常值）...")
        
        # 确保combined_data存在并有数据
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            # 如果没有，尝试合并数据
            print("合并晶圆数据...")
            self.cp_lot.combine_data_from_wafers()
            
            # 再次检查合并后的数据
            if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
                print("没有可用的数据，无法进行清洗")
                return
        
        # 获取所有数值参数的列表
        numeric_params = []
        for param in self.cp_lot.params:
            try:
                if param.id in self.cp_lot.combined_data.columns:
                    # 安全检查列的数据类型
                    param_series = self.cp_lot.combined_data[param.id]
                    if pd.api.types.is_numeric_dtype(param_series) and not param_series.empty:
                        numeric_params.append(param.id)
            except Exception as e:
                print(f"检查参数 {param.id} 时出错: {e}")
                continue
        
        print(f"找到 {len(numeric_params)} 个数值参数进行清洗")
        
        # 对每个参数处理异常值
        for param_id in numeric_params:
            try:
                if outlier_method == 'std_dev':
                    # 标准差法
                    param_values = self.cp_lot.combined_data[param_id]
                    valid_values = param_values.dropna()
                    
                    if not valid_values.empty:
                        mean = valid_values.mean()
                        std_dev = valid_values.std()
                        
                        # 将异常值替换为 NaN
                        lower_bound = mean - std_dev_threshold * std_dev
                        upper_bound = mean + std_dev_threshold * std_dev
                        
                        # 标记异常值
                        outliers = (param_values < lower_bound) | (param_values > upper_bound)
                        outlier_count = outliers.sum()
                        
                        # 替换异常值
                        self.cp_lot.combined_data.loc[outliers, param_id] = np.nan
                        print(f"参数 {param_id}: 检测到 {outlier_count} 个异常值 (超出均值±{std_dev_threshold}倍标准差)")
                
                elif outlier_method == 'iqr':
                    # 四分位法
                    param_values = self.cp_lot.combined_data[param_id]
                    valid_values = param_values.dropna()
                    
                    if not valid_values.empty:
                        q1 = valid_values.quantile(0.25)
                        q3 = valid_values.quantile(0.75)
                        iqr = q3 - q1
                        
                        # 将异常值替换为 NaN
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        
                        # 标记异常值
                        outliers = (param_values < lower_bound) | (param_values > upper_bound)
                        outlier_count = outliers.sum()
                        
                        # 替换异常值
                        self.cp_lot.combined_data.loc[outliers, param_id] = np.nan
                        print(f"参数 {param_id}: 检测到 {outlier_count} 个异常值 (IQR方法)")
            except Exception as e:
                print(f"处理参数 {param_id} 时出错: {e}")
                continue
        
        # 更新晶圆的 chip_data
        for param_id in numeric_params:
            try:
                self._update_wafer_chip_data(param_id)
            except Exception as e:
                print(f"更新晶圆数据 {param_id} 时出错: {e}")
        
        print("数据清洗完成")
    
    def normalize_parameters(self, method: str = 'min_max') -> None:
        """
        对所有数值参数进行归一化处理
        
        Args:
            method: 归一化方法，可选 'min_max'（最小-最大归一化）、'z_score'（Z-分数标准化）
        """
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            return
        
        # 获取所有数值参数的列表
        numeric_params = []
        for param in self.cp_lot.params:
            if param.id in self.cp_lot.combined_data.columns:
                if np.issubdtype(self.cp_lot.combined_data[param.id].dtype, np.number):
                    numeric_params.append(param.id)
        
        # 对每个参数进行归一化
        for param_id in numeric_params:
            norm_id = f"{param_id}_norm"
            
            param_values = self.cp_lot.combined_data[param_id]
            valid_values = param_values.dropna()
            
            if not valid_values.empty:
                if method == 'min_max':
                    # 最小-最大归一化
                    min_val = valid_values.min()
                    max_val = valid_values.max()
                    
                    if min_val != max_val:  # 避免除以零
                        # 定义归一化函数
                        def normalize_min_max(df):
                            return (df[param_id] - min_val) / (max_val - min_val)
                        
                        # 添加归一化参数
                        self.add_calculated_parameter(
                            param_id=norm_id,
                            formula=normalize_min_max,
                            unit='归一化'
                        )
                
                elif method == 'z_score':
                    # Z-分数标准化
                    mean = valid_values.mean()
                    std_dev = valid_values.std()
                    
                    if std_dev != 0:  # 避免除以零
                        # 定义标准化函数
                        def normalize_z_score(df):
                            return (df[param_id] - mean) / std_dev
                        
                        # 添加标准化参数
                        self.add_calculated_parameter(
                            param_id=norm_id,
                            formula=normalize_z_score,
                            unit='标准差'
                        ) 