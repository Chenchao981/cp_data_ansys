"""
统计分析模块，用于计算 CP 测试数据的统计指标和过程能力。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter


class SummaryStats:
    """
    统计分析类，用于计算 CP 测试数据的各种统计指标。
    
    主要功能：
    1. 计算基本统计量 - 均值、标准差、中位数等
    2. 计算过程能力指数 - Cp, Cpk, Cpm 等
    3. 生成统计汇总表 - 包含所有参数的统计分析结果
    """
    
    def __init__(self, cp_lot: CPLot):
        """
        初始化统计分析器
        
        Args:
            cp_lot: 要分析的 CPLot 对象
        """
        self.cp_lot = cp_lot
    
    def calculate_basic_stats(self) -> None:
        """
        计算所有参数的基本统计量，并更新 CPParameter 对象
        """
        # 确保有合并的数据
        if self.cp_lot.combined_data is None:
            self.cp_lot.combine_data_from_wafers()
        
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            print("无法计算统计量：没有可用的数据")
            return
        
        # 初始化统计汇总数据
        stats_data = []
        
        # 计算每个参数的统计量
        for param in self.cp_lot.params:
            # 如果参数不在合并数据中，跳过
            if param.id not in self.cp_lot.combined_data.columns:
                continue
            
            # 获取参数值
            param_values = self.cp_lot.combined_data[param.id].dropna()
            
            if param_values.empty:
                continue
            
            # 计算基本统计量
            mean = param_values.mean()
            std_dev = param_values.std()
            median = param_values.median()
            min_val = param_values.min()
            max_val = param_values.max()
            range_val = max_val - min_val
            
            # 计算四分位数
            q1 = param_values.quantile(0.25)
            q3 = param_values.quantile(0.75)
            iqr = q3 - q1
            
            # 异常值上下限（IQR 方法）
            lower_outlier = q1 - 1.5 * iqr
            upper_outlier = q3 + 1.5 * iqr
            
            # 更新参数对象
            param.mean = mean
            param.std_dev = std_dev
            param.median = median
            param.min_val = min_val
            param.max_val = max_val
            
            # 创建统计数据字典
            stats_dict = {
                'Parameter': param.id,
                'Unit': param.unit or '',
                'Count': len(param_values),
                'Mean': mean,
                'StdDev': std_dev,
                'CV(%)': (std_dev / abs(mean)) * 100 if mean != 0 else np.nan,
                'Min': min_val,
                'Q1': q1,
                'Median': median,
                'Q3': q3,
                'Max': max_val,
                'Range': range_val,
                'IQR': iqr
            }
            
            # 添加过程能力指数
            if param.sl is not None or param.su is not None:
                cp, cpk, cpm = self.calculate_capability_indices(param_values, param.sl, param.su)
                stats_dict.update({
                    'Cp': cp,
                    'Cpk': cpk,
                    'Cpm': cpm,
                    'Lower Spec': param.sl if param.sl is not None else 'N/A',
                    'Upper Spec': param.su if param.su is not None else 'N/A'
                })
            
            # 添加到汇总数据
            stats_data.append(stats_dict)
        
        # 创建统计汇总表
        if stats_data:
            self.cp_lot.summary_stats = pd.DataFrame(stats_data)
    
    def calculate_capability_indices(self, 
                                     values: pd.Series, 
                                     lower_spec: Optional[float] = None,
                                     upper_spec: Optional[float] = None) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        计算过程能力指数 Cp, Cpk, Cpm
        
        Args:
            values: 参数值序列
            lower_spec: 规格下限
            upper_spec: 规格上限
        
        Returns:
            (Cp, Cpk, Cpm): 过程能力指数元组，如果无法计算则返回 None
        """
        # 如果没有规格限或数据点太少，返回 None
        if (lower_spec is None and upper_spec is None) or len(values) < 30:
            return None, None, None
        
        # 计算基本统计量
        mean = values.mean()
        std_dev = values.std()
        
        # 如果标准差为 0，无法计算能力指数
        if std_dev == 0:
            return None, None, None
        
        # 计算过程能力指数
        cp = None
        cpk = None
        cpm = None
        
        if lower_spec is not None and upper_spec is not None:
            # 双侧规格
            cp = (upper_spec - lower_spec) / (6 * std_dev)
            cpu = (upper_spec - mean) / (3 * std_dev)
            cpl = (mean - lower_spec) / (3 * std_dev)
            cpk = min(cpu, cpl)
            
            # 计算 Cpm (考虑目标值，假设目标值为规格中点)
            target = (upper_spec + lower_spec) / 2
            cpm = cp / np.sqrt(1 + ((mean - target) / std_dev) ** 2)
        
        elif lower_spec is not None:
            # 只有下限
            cpl = (mean - lower_spec) / (3 * std_dev)
            cpk = cpl
        
        elif upper_spec is not None:
            # 只有上限
            cpu = (upper_spec - mean) / (3 * std_dev)
            cpk = cpu
        
        return cp, cpk, cpm
    
    def test_normality(self, significance_level: float = 0.05) -> pd.DataFrame:
        """
        对所有参数进行正态性检验
        
        Args:
            significance_level: 显著性水平，默认 0.05
        
        Returns:
            pd.DataFrame: 包含正态性检验结果的 DataFrame
        """
        # 确保有合并的数据
        if self.cp_lot.combined_data is None:
            self.cp_lot.combine_data_from_wafers()
        
        if self.cp_lot.combined_data is None or self.cp_lot.combined_data.empty:
            print("无法进行正态性检验：没有可用的数据")
            return pd.DataFrame()
        
        # 初始化结果数据
        normality_data = []
        
        # 对每个参数进行正态性检验
        for param in self.cp_lot.params:
            # 如果参数不在合并数据中，跳过
            if param.id not in self.cp_lot.combined_data.columns:
                continue
            
            # 获取参数值
            param_values = self.cp_lot.combined_data[param.id].dropna()
            
            if param_values.empty or len(param_values) < 8:  # 最小样本量要求
                continue
            
            # 进行 Shapiro-Wilk 检验
            shapiro_stat, shapiro_pval = stats.shapiro(param_values)
            
            # 进行 Anderson-Darling 检验
            ad_result = stats.anderson(param_values, dist='norm')
            ad_stat = ad_result.statistic
            ad_crit_vals = ad_result.critical_values
            ad_sig_level = ad_result.significance_level
            
            # 判断是否服从正态分布
            is_normal_shapiro = shapiro_pval > significance_level
            
            # 查找 Anderson-Darling 检验对应显著性水平的临界值
            ad_idx = np.where(ad_sig_level == significance_level * 100)[0]
            ad_crit_val = ad_crit_vals[ad_idx[0]] if len(ad_idx) > 0 else ad_crit_vals[-1]
            is_normal_ad = ad_stat < ad_crit_val
            
            # 添加到结果数据
            normality_data.append({
                'Parameter': param.id,
                'Sample Size': len(param_values),
                'Shapiro-Wilk Statistic': shapiro_stat,
                'Shapiro-Wilk p-value': shapiro_pval,
                'Anderson-Darling Statistic': ad_stat,
                'Anderson-Darling Critical Value': ad_crit_val,
                'Is Normal (Shapiro-Wilk)': is_normal_shapiro,
                'Is Normal (Anderson-Darling)': is_normal_ad,
                'Is Normal (Combined)': is_normal_shapiro and is_normal_ad
            })
        
        # 创建正态性检验结果表
        return pd.DataFrame(normality_data)
    
    def generate_summary_statistics(self) -> pd.DataFrame:
        """
        生成完整的统计汇总报告
        
        Returns:
            pd.DataFrame: 包含所有参数统计分析的汇总表
        """
        # 计算基本统计量
        self.calculate_basic_stats()
        
        # 返回统计汇总表
        return self.cp_lot.summary_stats 