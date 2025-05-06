#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DCP格式数据采集
用于读取和处理DCP格式的半导体晶圆测试数据文件
"""

import pandas as pd
import numpy as np
import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# 定义DCP格式数据文件的列和行常量
PARAM_START_COL = 4  # 参数起始列(Python中索引从0开始)
STD_ITEM_ROW = 6     # 标准项目行
USER_ITEM_ROW = 6    # 用户项目行
UPPER_ROW = 7        # 上限行
LOWER_ROW = 8        # 下限行
COND_START_ROW = 9   # 测试条件开始行
COND_END_ROW = 14    # 测试条件结束行
DATA_START_ROW = 15  # 数据开始行
SEQ_COL = 0          # 序号列
X_COL = 1            # X坐标列
Y_COL = 2            # Y坐标列
BIN_COL = 3          # Bin列


@dataclass
class TestItem:
    """测试参数类，存储测试参数的定义信息"""
    id: str = ""                 # 参数ID(唯一标识)
    display_name: str = ""       # 显示名称
    group: str = ""              # 参数组
    unit: str = ""               # 单位
    sl: float = 0.0              # 规格下限
    su: float = 0.0              # 规格上限
    test_cond: List[str] = field(default_factory=list)  # 测试条件列表


@dataclass
class WaferInfo:
    """晶圆信息类，存储单片晶圆的所有测试数据"""
    wafer_id: str = ""           # 晶圆ID
    seq: np.ndarray = None       # 序号数组
    bin: np.ndarray = None       # Bin值数组
    x: np.ndarray = None         # X坐标数组
    y: np.ndarray = None         # Y坐标数组
    width: int = 0               # 晶圆宽度
    chip_datas: Dict[int, np.ndarray] = field(default_factory=dict)  # 各参数的芯片数据
    param_count: int = 0         # 参数数量
    chip_count: int = 0          # 芯片数量


@dataclass
class LotInfo:
    """晶圆批次类，存储整批晶圆的信息与数据"""
    product: str = ""            # 产品名称
    params: List[TestItem] = field(default_factory=list)  # 参数列表
    wafers: List[WaferInfo] = field(default_factory=list)  # 晶圆列表
    param_count: int = 0         # 参数数量
    wafer_count: int = 0         # 晶圆数量
    pass_bin: int = 1            # 通过Bin值(默认为1)


class DCPDataParser:
    """DCP格式数据解析器，用于读取和处理DCP格式的晶圆测试数据"""
    
    def __init__(self):
        """初始化解析器"""
        self.lot_info = LotInfo()
        self._param_pos = {}      # 参数位置映射
        self._test_name_dic = {}  # 测试名称字典，用于确保名称唯一性
    
    def parse_file(self, file_path):
        """解析DCP文件并返回LotInfo对象"""
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取Excel文件
        wafer_data = pd.read_excel(file_path, header=None)
        
        # 确保文件格式正确
        self._check_format(wafer_data)
        
        # 检查第6行是否为空行，如果不是则插入
        self._check_sixth_row(wafer_data)
        
        # 解析数据
        if self.lot_info.param_count == 0:
            # 首次导入，需要添加参数信息
            self._add_param_info(wafer_data)
        
        # 添加晶圆信息
        wafer_info = WaferInfo()
        self._add_wafer_info(wafer_info, wafer_data)
        
        # 将晶圆添加到批次中
        self.lot_info.wafers.append(wafer_info)
        self.lot_info.wafer_count += 1
        
        return self.lot_info
    
    def _check_sixth_row(self, data):
        """检查第6行是否为空行，如果不是则插入空行"""
        if data.shape[0] >= 6 and not pd.isna(data.iloc[5, 0]) and str(data.iloc[5, 0]) != "":
            # 在第6行插入空行
            data_before = data.iloc[:5, :]
            data_after = data.iloc[5:, :]
            
            # 创建一个空行(与data同列数的空行)
            empty_row = pd.DataFrame([[np.nan] * data.shape[1]], index=[5])
            
            # 合并数据
            data_updated = pd.concat([data_before, empty_row, data_after])
            
            # 更新数据
            data = data_updated
    
    def _check_format(self, data):
        """检查文件格式是否符合DCP标准"""
        # 基本格式检查
        if data.shape[0] < DATA_START_ROW + 1:
            raise ValueError("文件格式不正确: 行数不足")
        if data.shape[1] < PARAM_START_COL + 1:
            raise ValueError("文件格式不正确: 列数不足")
    
    def _add_param_info(self, data):
        """添加参数信息"""
        param_index = 0
        params = []
        param_pos = {}
        
        # 遍历所有参数列
        for col_index in range(PARAM_START_COL, data.shape[1]):
            # 获取参数名称
            param_name = data.iloc[USER_ITEM_ROW, col_index]
            
            # 跳过"Discharge Time"
            if param_name == "Discharge Time":
                continue
            
            # 创建新参数
            param_index += 1
            param_pos[col_index] = param_index
            
            # 提取参数信息
            param = TestItem()
            param.display_name = param_name
            param.group = param_name
            param.id = self._change_to_unique_name(param.group)
            param.unit = self._split_unit(data.iloc[LOWER_ROW, col_index])
            param.sl = self._change_val(data.iloc[LOWER_ROW, col_index])
            param.su = self._change_val(data.iloc[UPPER_ROW, col_index])
            
            # 提取测试条件
            test_cond = []
            for i in range(COND_START_ROW, COND_END_ROW + 1):
                cond = data.iloc[i, col_index]
                test_cond.append(str(cond) if not pd.isna(cond) else "")
            param.test_cond = test_cond
            
            params.append(param)
        
        # 更新批次参数信息
        self._param_pos = param_pos
        self.lot_info.params = params
        self.lot_info.param_count = param_index
        
        # 获取产品名称
        product = data.iloc[0, 1]
        self.lot_info.product = product.replace(".dcp", "") if isinstance(product, str) else ""
    
    def _add_wafer_info(self, wafer_info, data):
        """添加晶圆信息"""
        # 计算数据点数量
        data_count = data.shape[0] - DATA_START_ROW
        
        # 设置晶圆ID
        wafer_info.wafer_id = data.iloc[2, 1]
        
        # 提取基本数据列
        wafer_info.seq = np.array(data.iloc[DATA_START_ROW:DATA_START_ROW+data_count, SEQ_COL])
        wafer_info.bin = np.array(data.iloc[DATA_START_ROW:DATA_START_ROW+data_count, BIN_COL])
        wafer_info.x = np.array(data.iloc[DATA_START_ROW:DATA_START_ROW+data_count, X_COL])
        wafer_info.y = np.array(data.iloc[DATA_START_ROW:DATA_START_ROW+data_count, Y_COL])
        
        # 计算晶圆宽度
        wafer_info.width = int(np.max(wafer_info.x) - np.min(wafer_info.x) + 2)
        
        # 提取各参数数据
        chip_datas = {}
        for col, param_idx in self._param_pos.items():
            if param_idx > 0:
                chip_datas[param_idx] = np.array(data.iloc[DATA_START_ROW:DATA_START_ROW+data_count, col])
        
        wafer_info.chip_datas = chip_datas
        wafer_info.param_count = self.lot_info.param_count
        wafer_info.chip_count = data_count
    
    def _change_to_unique_name(self, name):
        """转换为唯一名称，防止参数名称重复"""
        if name in self._test_name_dic:
            self._test_name_dic[name] += 1
            return f"{name}_{self._test_name_dic[name]}"
        else:
            self._test_name_dic[name] = 0
            return name
    
    def _split_unit(self, spec):
        """从规格字符串中提取单位"""
        if pd.isna(spec):
            return ""
        
        spec_str = str(spec)
        match = re.search(r'\d+(\.\d+)?[munpfk]?(V|A|OHM)', spec_str)
        if match:
            return match.group(2)
        return ""
    
    def _change_val(self, spec):
        """根据单位转换值"""
        if pd.isna(spec):
            return 0.0
        
        spec_str = str(spec)
        match = re.search(r'(\d+(?:\.\d+)?)([munpfk]?)(?:V|A|OHM)', spec_str)
        if not match:
            return 0.0
        
        value = float(match.group(1))
        unit_prefix = match.group(2).lower()
        
        # 计算单位换算率
        rate = self._cal_rate(unit_prefix)
        return value * rate
    
    def _cal_rate(self, rate_str):
        """计算单位换算率"""
        rates = {
            'm': 0.001,          # 毫 (milli)
            'u': 0.000001,       # 微 (micro)
            'n': 0.000000001,    # 纳 (nano)
            'p': 0.000000000001, # 皮 (pico)
            'f': 0.000000000000001, # 飞 (femto)
            'k': 1000,           # 千 (kilo)
        }
        return rates.get(rate_str, 1.0)  # 默认为1


def main():
    """主函数示例"""
    # 创建解析器
    parser = DCPDataParser()
    
    # 假设有一个示例文件路径
    file_path = "example.xlsx"
    
    # 检查文件是否存在，如果不存在则显示消息
    if not os.path.exists(file_path):
        print(f"示例文件 {file_path} 不存在。请提供一个有效的DCP格式数据文件路径。")
        return
    
    try:
        # 解析文件
        lot_info = parser.parse_file(file_path)
        print(f"产品名称: {lot_info.product}")
        print(f"晶圆数量: {lot_info.wafer_count}")
        print(f"参数数量: {lot_info.param_count}")
        
        # 打印第一片晶圆的信息
        if lot_info.wafer_count > 0:
            wafer = lot_info.wafers[0]
            print(f"\n晶圆ID: {wafer.wafer_id}")
            print(f"芯片数量: {wafer.chip_count}")
            
            # 计算良率示例
            pass_count = np.sum(wafer.bin == 1)  # 假设Bin=1为通过
            yield_rate = pass_count / wafer.chip_count if wafer.chip_count > 0 else 0
            print(f"良率: {yield_rate:.2%}")
            
    except Exception as e:
        print(f"处理文件时出错: {e}")


if __name__ == "__main__":
    main() 