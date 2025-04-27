"""
良率计算器模块，用于计算 CP 测试数据的各种良率指标。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter


class YieldCalculator:
    """
    良率计算器类，用于计算晶圆和参数的良率。
    
    主要功能：
    1. 计算 Bin 良率 - 基于 Pass Bin 计算晶圆和批次的良率
    2. 计算参数良率 - 基于规格限计算每个参数的良率
    3. 生成良率汇总表 - 包含所有晶圆和参数的良率信息
    """
    
    def __init__(self, cp_lot: CPLot):
        """
        初始化良率计算器
        
        Args:
            cp_lot: 要分析的 CPLot 对象
        """
        self.cp_lot = cp_lot
        self.pass_bin = cp_lot.pass_bin  # 通常为 1
    
    def calculate_bin_yield(self) -> None:
        """
        计算基于 Bin 值的良率，并更新 CPLot 和 CPWafer 对象
        """
        # 确保有合并的数据
        if self.cp_lot.combined_data is None:
            self.cp_lot.combine_data_from_wafers()
        
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            print("无法计算良率：没有可用的数据")
            return
        
        # 计算每个晶圆的良率
        wafer_yield_data = []
        
        for wafer in self.cp_lot.wafers:
            # 跳过没有数据的晶圆
            if wafer.bin is None or len(wafer.bin) == 0:
                continue
            
            # 计算通过和失败的芯片数
            pass_chips = np.sum(wafer.bin == self.pass_bin)
            fail_chips = wafer.chip_count - pass_chips
            
            # 计算良率
            yield_rate = (pass_chips / wafer.chip_count) * 100 if wafer.chip_count > 0 else 0.0
            
            # 更新晶圆对象
            wafer.yield_rate = yield_rate
            wafer.pass_chips = pass_chips
            wafer.fail_chips = fail_chips
            
            # 添加到汇总数据
            wafer_yield_data.append({
                'Wafer': wafer.wafer_id,
                'Total': wafer.chip_count,
                'Pass': pass_chips,
                'Fail': fail_chips,
                'Yield(%)': round(yield_rate, 2)
            })
        
        # 创建晶圆良率汇总表
        self.cp_lot.yield_summary = pd.DataFrame(wafer_yield_data)
        
        # 计算整个批次的良率
        if 'Pass' in self.cp_lot.yield_summary and 'Total' in self.cp_lot.yield_summary:
            total_pass = self.cp_lot.yield_summary['Pass'].sum()
            total_chips = self.cp_lot.yield_summary['Total'].sum()
            total_yield = (total_pass / total_chips) * 100 if total_chips > 0 else 0.0
            
            # 添加总计行
            self.cp_lot.yield_summary = pd.concat([
                self.cp_lot.yield_summary,
                pd.DataFrame([{
                    'Wafer': 'Total',
                    'Total': total_chips,
                    'Pass': total_pass,
                    'Fail': total_chips - total_pass,
                    'Yield(%)': round(total_yield, 2)
                }])
            ], ignore_index=True)
    
    def calculate_parameter_yield(self) -> None:
        """
        计算每个参数的良率，根据规格上下限判断
        """
        # 确保有合并的数据
        if self.cp_lot.combined_data is None:
            self.cp_lot.combine_data_from_wafers()
        
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            print("无法计算参数良率：没有可用的数据")
            return
        
        # 计算每个参数的良率
        param_yield_data = []
        
        for param in self.cp_lot.params:
            # 跳过没有规格限的参数
            if param.sl is None and param.su is None:
                continue
            
            # 如果参数不在合并数据中，跳过
            if param.id not in self.cp_lot.combined_data.columns:
                continue
            
            # 获取参数值
            param_values = self.cp_lot.combined_data[param.id].dropna()
            
            if param_values.empty:
                continue
            
            # 根据规格限判断通过/失败
            pass_count = 0
            fail_count = 0
            
            if param.sl is not None and param.su is not None:
                # 双侧规格
                pass_count = np.sum((param_values >= param.sl) & (param_values <= param.su))
            elif param.sl is not None:
                # 只有下限
                pass_count = np.sum(param_values >= param.sl)
            elif param.su is not None:
                # 只有上限
                pass_count = np.sum(param_values <= param.su)
            else:
                # 没有规格限
                pass_count = len(param_values)
            
            fail_count = len(param_values) - pass_count
            
            # 计算良率
            yield_rate = (pass_count / len(param_values)) * 100 if len(param_values) > 0 else 0.0
            
            # 更新参数对象
            param.yield_rate = yield_rate
            
            # 添加到汇总数据
            param_yield_data.append({
                'Parameter': param.id,
                'Unit': param.unit or '',
                'Lower Spec': param.sl if param.sl is not None else 'N/A',
                'Upper Spec': param.su if param.su is not None else 'N/A',
                'Min': param_values.min(),
                'Max': param_values.max(),
                'Mean': param_values.mean(),
                'StdDev': param_values.std(),
                'Total': len(param_values),
                'Pass': pass_count,
                'Fail': fail_count,
                'Yield(%)': round(yield_rate, 2)
            })
        
        # 如果有参数良率数据，创建参数良率汇总表
        if param_yield_data:
            param_yield_df = pd.DataFrame(param_yield_data)
            
            # 如果已经有了良率汇总表，合并它们
            if self.cp_lot.yield_summary is not None:
                # 假设已经计算了晶圆良率，创建一个参数良率汇总表
                # 但不替换晶圆良率汇总表
                self.cp_lot.param_yield_summary = param_yield_df
            else:
                # 如果还没有汇总表，直接使用参数良率汇总表
                self.cp_lot.yield_summary = param_yield_df
    
    def generate_yield_summary(self) -> pd.DataFrame:
        """
        生成完整的良率汇总报告
        
        Returns:
            pd.DataFrame: 包含晶圆和参数良率的汇总表
        """
        # 先计算两种良率
        self.calculate_bin_yield()
        self.calculate_parameter_yield()
        
        # 返回良率汇总表
        return self.cp_lot.yield_summary 