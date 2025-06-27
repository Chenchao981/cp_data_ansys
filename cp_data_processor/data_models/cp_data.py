# 定义 CP 测试数据的 Python 数据结构

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

@dataclass
class CPParameter:
    """存储单个测试参数的规格和统计信息。"""
    id: str                           # 参数 ID (名称)
    unit: Optional[str] = None        # 单位
    sl: Optional[float] = None        # 规格下限 (Lower Spec Limit)
    su: Optional[float] = None        # 规格上限 (Upper Spec Limit)
    test_cond: List[str] = field(default_factory=list) # 测试条件列表

    # 后续计算得到的统计值
    mean: Optional[float] = None      # 平均值
    std_dev: Optional[float] = None   # 标准差
    median: Optional[float] = None    # 中位数
    min_val: Optional[float] = None   # 最小值
    max_val: Optional[float] = None   # 最大值
    cp: Optional[float] = None        # 制程能力指数 Cp
    cpk: Optional[float] = None       # 制程能力指数 Cpk
    yield_rate: Optional[float] = None # 参数良率

@dataclass
class CPWafer:
    """存储单个晶圆的信息和测试数据。"""
    wafer_id: str                     # 晶圆 ID
    file_path: Optional[str] = None   # 原始数据文件路径 (可选)
    source_lot_id: Optional[str] = None  # 存储从文件R2C2提取的LotID
    chip_count: int = 0               # 晶圆上的芯片总数
    seq: Optional[np.ndarray] = None  # 每个芯片的序号 (numpy array)
    bin: Optional[np.ndarray] = None  # 每个芯片的 Bin 值 (numpy array)
    x: Optional[np.ndarray] = None    # 每个芯片的 X 坐标 (numpy array)
    y: Optional[np.ndarray] = None    # 每个芯片的 Y 坐标 (numpy array)
    # 使用 DataFrame 存储芯片数据: 行=芯片, 列=参数ID, 值=测试结果
    chip_data: Optional[pd.DataFrame] = None

    # 后续计算得到的值
    yield_rate: Optional[float] = None # 晶圆良率
    pass_chips: Optional[int] = None   # 通过的芯片数
    fail_chips: Optional[int] = None   # 失败的芯片数
    factor_level: Optional[str] = None # 实验因子水平 (如果使用)

@dataclass
class CPLot:
    """存储整个 Lot (批次) 的信息，包含多个晶圆和参数。"""
    lot_id: str = "UnknownLot"          # Lot ID (从文件名或数据中提取)
    product: Optional[str] = None       # 产品名称 (从文件名或数据中提取)
    wafer_count: int = 0                # Lot 中的晶圆数量
    wafers: List[CPWafer] = field(default_factory=list) # 包含的 CPWafer 对象列表
    param_count: int = 0                # 测试参数的数量
    params: List[CPParameter] = field(default_factory=list) # 包含的 CPParameter 对象列表
    pass_bin: Optional[int] = 1         # 定义 Pass Bin 的值 (来自配置)

    # 合并后的数据，方便分析和绘图
    # 行=芯片, 列=WaferID, Seq, Bin, X, Y, Param1, Param2, ...
    combined_data: Optional[pd.DataFrame] = None

    # 分析结果汇总
    summary_stats: Optional[pd.DataFrame] = None # 参数统计汇总表
    yield_summary: Optional[pd.DataFrame] = None # 良率汇总表

    def update_counts(self):
        """更新晶圆和参数计数。"""
        self.wafer_count = len(self.wafers)
        self.param_count = len(self.params)

    def combine_data_from_wafers(self):
        """将所有晶圆的数据合并到一个 DataFrame 中。"""
        if not self.wafers:
            self.combined_data = pd.DataFrame()
            return

        all_dfs = []
        for wafer in self.wafers:
            if wafer.chip_data is not None and not wafer.chip_data.empty:
                # 简单直接的方法：只添加LotID和WaferID
                wafer_df = wafer.chip_data.copy()
                
                # 添加LotID和WaferID列
                wafer_df.insert(0, 'LotID', wafer.source_lot_id if wafer.source_lot_id is not None else self.lot_id)
                wafer_df.insert(1, 'WaferID', wafer.wafer_id)
                
                all_dfs.append(wafer_df)

        if all_dfs:
            self.combined_data = pd.concat(all_dfs, ignore_index=True)
            
            # 去除重复列（如果存在）
            cols_to_remove = []
            for col in self.combined_data.columns:
                if col in ['Lot_ID', 'Wafer_ID'] and col != 'LotID' and col != 'WaferID':
                    cols_to_remove.append(col)
                elif '.' in col and col.split('.')[-1].isdigit():  # 去除pandas自动添加的重复列后缀
                    original_col = col.split('.')[0]  # 取第一部分作为原始列名
                    if original_col in self.combined_data.columns:
                        cols_to_remove.append(col)
            
            if cols_to_remove:
                self.combined_data = self.combined_data.drop(columns=cols_to_remove)
        else:
             self.combined_data = pd.DataFrame()

    def get_param_names(self) -> List[str]:
        """获取所有参数名称的列表。"""
        return [p.id for p in self.params] 