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
                # 创建包含基础信息的 DataFrame
                info_df = pd.DataFrame({
                    'LotID': wafer.source_lot_id if wafer.source_lot_id is not None else self.lot_id,
                    'WaferID': wafer.wafer_id,
                    'Seq': wafer.seq if wafer.seq is not None else np.nan,
                    'Bin': wafer.bin if wafer.bin is not None else np.nan,
                    'X': wafer.x if wafer.x is not None else np.nan,
                    'Y': wafer.y if wafer.y is not None else np.nan,
                    'CONT': np.ones(len(wafer.chip_data)) * 1  # 添加CONT列，默认值为1
                })
                # 确保索引与 chip_data 对齐，如果 chip_data 有索引的话
                if wafer.chip_data.index.name or wafer.chip_data.index.equals(pd.RangeIndex(start=0, stop=len(wafer.chip_data), step=1)):
                     info_df.index = wafer.chip_data.index
                else: # 如果 chip_data 索引无效，尝试重置
                     info_df.index = pd.RangeIndex(start=0, stop=len(info_df), step=1)
                     wafer.chip_data.index = pd.RangeIndex(start=0, stop=len(wafer.chip_data), step=1)

                # 合并基础信息和参数数据
                # 假设 chip_data 的列名是参数 ID
                combined_wafer_df = pd.concat([info_df, wafer.chip_data], axis=1)
                all_dfs.append(combined_wafer_df)

        if all_dfs:
            self.combined_data = pd.concat(all_dfs, ignore_index=True)
            # 确保列顺序符合预期 (LotID, WaferID, Seq, Bin, X, Y, CONT, Params...)
            param_cols = sorted([p.id for p in self.params])
            ordered_cols = ['LotID', 'WaferID', 'Seq', 'Bin', 'X', 'Y', 'CONT'] + param_cols
            # 处理可能在 combined_data 中但不在 ordered_cols 中的列 (例如索引)
            final_cols = [col for col in ordered_cols if col in self.combined_data.columns]
            self.combined_data = self.combined_data[final_cols]
        else:
             self.combined_data = pd.DataFrame()

    def get_param_names(self) -> List[str]:
        """获取所有参数名称的列表。"""
        return [p.id for p in self.params]
