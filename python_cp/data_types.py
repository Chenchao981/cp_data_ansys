import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple, Dict

@dataclass
class CPParameter:
    """
    表示单个 CP 测试参数的信息。
    对应 VBA 中的 TestItem 类型。
    """
    id: str                     # 内部唯一标识符 (通常是参数名，可能包含后缀以保证唯一性)
    group: str                  # 参数的组别或原始名称 (通常与 id 相同或为其基础)
    display_name: str           # 用于在报告或图表中显示的名称
    unit: Optional[str] = None  # 参数的物理单位 (例如: 'V', 'A', 'Ohm')
    sl: Optional[float] = None  # 规格下限 (Specification Lower Limit)
    su: Optional[float] = None  # 规格上限 (Specification Upper Limit)
    test_cond: List[Any] = field(default_factory=list) # 测试条件列表 (具体内容格式取决于数据源)

@dataclass
class CPWafer:
    """
    表示单个晶圆 (Wafer) 的测试数据。
    对应 VBA 中的 CPWafer 类型。
    """
    wafer_id: str                     # 晶圆编号 (例如: "Wafer01", "Slot3")
    source_lot_id: Optional[str] = None # 从文件原始R2C2提取的LotID (Python新增字段)
    file_path: Optional[str] = None   # 读取该晶圆数据的源文件路径 (Python新增字段)
    chip_count: int = 0               # 该晶圆上测试的芯片 (Die/Site) 总数
    seq: Optional[np.ndarray] = None  # 芯片测试序号 (1D NumPy 数组, int/float)
    x: Optional[np.ndarray] = None    # 芯片的 X 坐标 (1D NumPy 数组, int/float)
    y: Optional[np.ndarray] = None    # 芯片的 Y 坐标 (1D NumPy 数组, int/float)
    bin: Optional[np.ndarray] = None  # 芯片的 Bin 值 (1D NumPy 数组, int/float)
    chip_data: Optional[pd.DataFrame] = None # 存储参数测试数据的 Pandas DataFrame。
                                            # 行对应芯片 (Die/Site), 列对应参数 (`CPParameter.id`)。

    @property
    def width(self) -> int:
        """计算晶圆宽度"""
        if self.x is not None and len(self.x) > 0:
            # VBA 中 DCP 格式计算为 Max - Min + 2, 其他格式可能不同，暂用 + 1
            # 注意：需要根据实际坐标含义调整 +1 或 +2
            try:
                return int(np.nanmax(self.x) - np.nanmin(self.x) + 1)
            except ValueError:
                return 0 # 如果 x 全是 NaN
        return 0

    @property
    def height(self) -> int:
        """计算晶圆高度"""
        if self.y is not None and len(self.y) > 0:
            try:
                return int(np.nanmax(self.y) - np.nanmin(self.y) + 1)
            except ValueError:
                return 0 # 如果 y 全是 NaN
        return 0

    @property
    def param_count(self) -> int:
        """返回参数数量"""
        if self.chip_data is not None:
            return self.chip_data.shape[1]
        return 0

@dataclass
class CPLot:
    """
    表示整个 CP 测试批次 (Lot) 的数据。
    对应 VBA 中的 CPLot 类型。
    """
    lot_id: str                             # Lot 编号 (例如: "LOT12345")
    product: Optional[str] = None           # 产品名称
    pass_bin: int = 1                       # 定义 Pass Bin 的值 (默认值为 1)
    wafers: List[CPWafer] = field(default_factory=list) # 包含该 Lot 中所有 `CPWafer` 对象的列表
    params: List[CPParameter] = field(default_factory=list) # 包含该 Lot 所有参数 (`CPParameter` 对象) 的列表
    combined_data: Optional[pd.DataFrame] = None # (Python 新增) 合并所有 Wafer 数据的 Pandas DataFrame

    @property
    def wafer_count(self) -> int:
        """返回批次中的晶圆数量"""
        return len(self.wafers)

    @property
    def param_count(self) -> int:
        """返回批次中的参数数量"""
        return len(self.params)

    def get_param_by_id(self, param_id: str) -> Optional[CPParameter]:
        """根据参数 ID 查找参数对象"""
        for param in self.params:
            if param.id == param_id:
                return param
        return None

    def get_wafer_by_id(self, wafer_id: str) -> Optional[CPWafer]:
        """根据晶圆 ID 查找晶圆对象"""
        for wafer in self.wafers:
            if wafer.wafer_id == wafer_id:
                return wafer
        return None

    def combine_data_from_wafers(self) -> None:
        """
        将所有晶圆的 `chip_data` 合并到 `combined_data` DataFrame 中。
        会添加 'LotID' (来自 wafer.source_lot_id), 'WaferID' (原wafer_id), 'Seq' (原seq), 'Bin' (原bin), 'X' (原x), 'Y' (原y) 列。
        """
        if not self.wafers:
            self.combined_data = pd.DataFrame()
            return

        all_wafer_data = []
        for wafer in self.wafers:
            if wafer.chip_data is not None and not wafer.chip_data.empty:
                # 创建一个临时 DataFrame 以便合并
                temp_df = wafer.chip_data.copy()
                temp_df['LotID'] = wafer.source_lot_id # 使用source_lot_id作为LotID列
                temp_df['WaferID'] = wafer.wafer_id    # 重命名为WaferID
                if wafer.seq is not None:
                    temp_df['Seq'] = wafer.seq         # 重命名为Seq
                if wafer.x is not None:
                    temp_df['X'] = wafer.x             # 重命名为X
                if wafer.y is not None:
                    temp_df['Y'] = wafer.y             # 重命名为Y
                if wafer.bin is not None:
                    temp_df['Bin'] = wafer.bin         # 重命名为Bin
                all_wafer_data.append(temp_df)

        if all_wafer_data:
            self.combined_data = pd.concat(all_wafer_data, ignore_index=True)
            # 按要求排列列的顺序：LotID, WaferID, Seq, Bin, X, Y, CONT, ...
            cols_to_move = ['LotID', 'WaferID', 'Seq', 'Bin', 'X', 'Y'] 
            
            # 将'CONT'列提前到指定位置(如果存在)
            if 'CONT' in self.combined_data.columns:
                cols_to_move.append('CONT')
            
            # 过滤掉实际不存在的列，保留指定顺序
            cols_to_move = [col for col in cols_to_move if col in self.combined_data.columns]
            
            # 其他参数列按字母顺序排序
            remaining_cols = [col for col in self.combined_data.columns if col not in cols_to_move]
            remaining_cols.sort()  # 字母顺序排序
            
            # 重新组合所有列
            self.combined_data = self.combined_data[cols_to_move + remaining_cols]
        else:
            self.combined_data = pd.DataFrame()

    def update_counts(self) -> None:
        """
        (示例方法) 更新批次级别的计数，例如 wafer_count 和 param_count。
        由于使用了 @property，这些计数是动态的，此方法可能不需要，
        但可以保留用于未来可能的其他批次级别计算。
        """
        # wafer_count 和 param_count 是 @property, 自动更新
        pass

    # 可以根据需要添加更多 Lot 级别的方法，例如：
    # - 计算 Lot 级别的良率 (如果需要直接存储)
    # - 过滤数据等 