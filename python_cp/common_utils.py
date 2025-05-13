import numpy as np
from typing import Any, List, Union, Sequence, Dict, Optional
import logging
import sys
import re
import pandas as pd

def is_valid_list(lst: Any) -> bool:
    """检查输入是否为非空列表或 NumPy 数组。"""
    # 检查是否是列表或NumPy数组，并且长度大于0
    return isinstance(lst, (list, np.ndarray)) and len(lst) > 0

def check_list(input_var: Union[str, Sequence, Any]) -> List[Any]:
    """
    检查输入变量，将其规范化为列表。
    - 如果是列表或元组，直接返回列表。
    - 如果是 NumPy 数组，转换为列表。
    - 如果是字符串，按逗号分割并去除空白后返回列表。
    - 如果是 None 或空字符串，返回空列表。
    - 其他类型，放入单元素列表返回。
    对应 VBA CheckList 函数。
    """
    if input_var is None:
        return []
    if isinstance(input_var, (list, tuple)):
        return list(input_var)
    if isinstance(input_var, np.ndarray):
        return input_var.tolist() # 将 NumPy 数组转换为 Python 列表
    if isinstance(input_var, str):
        stripped_input = input_var.strip()
        if not stripped_input: # 处理空字符串或仅包含空白的字符串
            return []
        # 按逗号分割，并去除每个元素前后的空白字符
        return [item.strip() for item in stripped_input.split(',')]
    # 其他类型，放入单元素列表
    return [input_var]

def safe_get_element(lst: Sequence, index: int) -> Any:
    """
    安全地获取序列中指定索引的元素，支持负索引。
    索引越界或类型错误返回 None。
    部分对应 VBA nth 函数。
    """
    # 检查 lst 是否是序列类型且不为空
    if not isinstance(lst, Sequence) or len(lst) == 0:
        return None
    try:
        # 尝试访问元素
        return lst[index]
    except (IndexError, TypeError):
        # 捕捉索引越界或类型错误（例如对非序列类型使用索引）
        return None

def ensure_list(item_or_list: Any) -> List[Any]:
    """
    确保输入被包装成列表。
    如果输入是列表或元组，返回列表形式。
    否则，将输入项放入新的单元素列表。
    """
    if isinstance(item_or_list, list):
        return item_or_list
    if isinstance(item_or_list, tuple):
        return list(item_or_list)
    # 对于 None 或其他非序列类型，放入列表中
    return [item_or_list]

# --- 未转换的 VBA 函数说明 ---
# Push, cons, Append, cdr, car: Python 中使用 list.append(), list.insert(), +, list slicing
# ExpandBlank2List, ExpandValue2List, ExpandList2List: Python 中使用 list.append(), list.extend(), +
# GetDimension, DimensionLength: Python 中使用 len(), numpy.ndim, numpy.shape
# IsArrayEmpty: Python 中使用 len(arr) == 0
# ArrayValueCopy: Python 中使用 =, copy.copy(), copy.deepcopy()
# BigArrayTranspose: Python 中使用 numpy.transpose() 或 ndarray.T 

# 配置日志记录器
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO) # 默认记录 INFO 及以上级别
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ShowInfo:
    """
    模拟 VBA clsShowInfo 的功能，用于显示信息和错误。
    使用 Python logging 模块进行输出，并限制重复信息的输出。
    """
    def __init__(self, repeat_count_max: int = 10):
        """
        初始化 ShowInfo 实例。
        Args:
            repeat_count_max: 同一信息允许重复显示的最大次数。
        """
        self._show_info_dic = {}
        self._repeat_count_max = repeat_count_max

    def _get_info_repeat_times(self, message: str) -> int:
        """获取并更新消息的显示次数"""
        count = self._show_info_dic.get(message, 0) + 1
        self._show_info_dic[message] = count
        return count

    def info(self, message: Any, title: str = "提示") -> None:
        """
        记录提示信息 (INFO 级别)，限制重复输出。
        对应 VBA PromptInfo。
        Args:
            message: 要显示的信息内容。
            title: (未使用，仅为保持接口相似性) 标题。
        """
        s_message = str(message)
        if self._get_info_repeat_times(s_message) <= self._repeat_count_max:
            logger.info(f"[{title}] {s_message}")

    def alarm(self, error_info: Any, title: str = "警告", ocap: Any = None) -> None:
        """
        记录警告信息 (WARNING 级别)。
        对应 VBA ErrAlarm。
        Args:
            error_info: 错误或警告信息。
            title: (未使用，仅为保持接口相似性) 标题。
            ocap: (未使用，仅为保持接口相似性) 可选的解决方案信息。
        """
        s_error = str(error_info)
        s_ocap = f"\n  推荐解决方案: {str(ocap)}" if ocap else ""
        logger.warning(f"[{title}] {s_error}{s_ocap}")

    def stop(self, error_info: Any, title: str = "异常终止", ocap: Any = None) -> None:
        """
        记录严重错误信息 (CRITICAL 级别) 并退出程序。
        对应 VBA ErrStop。
        Args:
            error_info: 错误信息。
            title: (未使用，仅为保持接口相似性) 标题。
            ocap: (未使用，仅为保持接口相似性) 可选的解决方案信息。
        """
        s_error = str(error_info)
        s_ocap = f"\n  推荐解决方案: {str(ocap)}" if ocap else ""
        logger.critical(f"[{title}] {s_error}{s_ocap}")
        sys.exit(1) # 退出程序，表示有错误发生

# --- 实例化 ShowInfo --- (可选, 供全局使用)
# g_show = ShowInfo()

# 示例用法:
# if __name__ == '__main__':
#     g_show = ShowInfo(repeat_count_max=2)
#     g_show.info("这是一条普通提示")
#     g_show.info("这条提示会出现")
#     g_show.info("这条提示也会出现")
#     g_show.info("这条提示因为超过次数，将不再显示")
#     g_show.alarm("这是一个警告信息")
#     g_show.alarm("硬盘空间不足", ocap="请清理临时文件")
#     try:
#         x = 1 / 0
#     except ZeroDivisionError as e:
#         g_show.stop(f"计算错误: {e}", ocap="检查除数是否为零")
#     print("这一行不会执行，因为程序已退出")

# === Functions moved from 通用代码.py ===

# 命名和字符串处理相关函数
def change_to_unique_name(to_check_name: str, name_dic: Dict[str, int]) -> str:
    """
    确保名称唯一性。如果to_check_name在name_dic中已存在，则在末尾添加数字后缀(2, 3, ...)直到唯一。
    
    Args:
        to_check_name: 要检查的名称。
        name_dic: 用于存储已使用名称及其出现次数的字典 (会被修改)。
        
    Returns:
        确保唯一的名称。
    """
    ret = to_check_name
    k = name_dic.get(to_check_name, 0) # 获取当前名称的计数
    
    if k == 0: # 第一次出现
        name_dic[ret] = 1
        return ret
    else: # 已存在，需要加后缀
        while True:
            k += 1
            ret = f"{to_check_name}{k}"
            if ret not in name_dic: # 找到唯一的后缀
                name_dic[to_check_name] = k # 更新基础名称的计数器
                name_dic[ret] = 1 # 添加新名称
                return ret
            # 如果带后缀的名称也存在，理论上不应发生，除非字典被外部修改，但循环会继续寻找

# 从字符串中提取由一对特定字符包围的内容
def split_content_in_pair_char(to_split_info: str, pair_char: str = "[]") -> str:
    """
    从字符串中提取由一对特定字符包围的内容。优先提取最外层匹配。
    
    Args:
        to_split_info: 要处理的字符串。
        pair_char: 包围内容的一对字符，默认为"[]"。
        
    Returns:
        提取的内容（不包含包围字符），如果未找到则返回空字符串。
    """
    if not isinstance(to_split_info, str) or len(pair_char) < 2:
        return ""
    
    left_char = pair_char[0]
    right_char = pair_char[-1]
    
    # 正则表达式查找最外层匹配
    # 需要转义特殊字符
    left_escaped = re.escape(left_char)
    right_escaped = re.escape(right_char)
    
    # 非贪婪匹配 .*? 查找最短内容，但可能不是最外层
    # 贪婪匹配 .* 查找最长内容，但可能跨越多个右括号
    # 使用查找第一个左括号和最后一个右括号的方式更接近VBA行为
    pos_left = to_split_info.find(left_char)
    pos_right = to_split_info.rfind(right_char)
    
    if pos_left != -1 and pos_right > pos_left:
        return to_split_info[pos_left + 1:pos_right].strip() # 返回去除前后空格的内容
    
    return ""

# 单位转换相关函数
def get_unit_order_change_rate(unit: str) -> float:
    """
    获取单位对应的数量级转换率 (相对于基本单位，如 V, A, Ohm)
    
    Args:
        unit: 单位字符串 (e.g., "mV", "uA", "kOhm", "GOhm")
        
    Returns:
        转换率 (float), 例如 "mV" 返回 1e-3。如果单位未知或无前缀，返回 1.0。
    """
    unit_lower = str(unit).lower() if unit else ""
    
    if unit_lower.startswith("f"): return 1e-15
    if unit_lower.startswith("p"): return 1e-12
    if unit_lower.startswith("n"): return 1e-9
    if unit_lower.startswith("u") or unit_lower.startswith("μ"): return 1e-6
    if unit_lower.startswith("m"): return 1e-3
    if unit_lower.startswith("k"): return 1e3
    if unit_lower.startswith("meg"): return 1e6 # 支持 "Meg" 或 "meg"
    if unit_lower.startswith("g"): return 1e9
    if unit_lower.startswith("t"): return 1e12
        
    return 1.0 # 默认为 1 (无前缀或未知单位)

def get_unit_change_rate(new_unit: str, old_unit: str) -> float:
    """
    计算从旧单位转换到新单位所需的乘法因子。
    
    Args:
        new_unit: 目标单位。
        old_unit: 原始单位。
        
    Returns:
        转换因子 (float)。例如从 "mV" 到 "V" 返回 1e-3。
    """
    # 例如: value_in_new_unit = value_in_old_unit * get_unit_change_rate(new_unit, old_unit)
    # 从 old 转换为 base: multiplier = get_unit_order_change_rate(old_unit)
    # 从 base 转换为 new: divider = get_unit_order_change_rate(new_unit)
    # 总因子 = multiplier / divider
    
    old_rate = get_unit_order_change_rate(old_unit)
    new_rate = get_unit_order_change_rate(new_unit)
    
    if new_rate == 0: # 防止除以零
        return 0.0 
    return old_rate / new_rate

def change_with_unit(value_with_std_unit: Any, target_unit: str) -> Optional[float]:
    """
    将带有标准单位的值转换为目标单位的值。
    假定 value_with_std_unit 已经是基本单位 (如 V, A, Ohm)。
    
    Args:
        value_with_std_unit: 带有标准单位的值 (应为数值类型)。
        target_unit: 目标单位字符串。
        
    Returns:
        转换到目标单位后的值 (float)，如果输入无效则返回 None。
    """
    try:
        value_float = float(value_with_std_unit)
    except (ValueError, TypeError):
        return None # 输入值无法转换为浮点数

    # 转换率是从目标单位转换到标准单位的比率
    # 例如 target_unit="mV", rate = 1e-3 (1mV = 1e-3 V)
    # value_in_target_unit = value_in_std_unit / rate
    rate = get_unit_order_change_rate(target_unit)
    if rate == 0:
        return None # 目标单位的转换率为0，无法计算
        
    return value_float / rate

def change_range_unit(unit_rate_series: pd.Series, data_series: pd.Series) -> pd.Series:
    """
    (此函数在VBA中的用途似乎是将一个已经包含转换率的Series应用到数据Series上，
     在Python中通常直接计算更方便，但保留其结构以备不时之需)
    根据提供的单位转换率序列，调整数据序列的值。
    
    Args:
        unit_rate_series: 包含每个对应数据点所需转换率的 Series。
        data_series: 原始数据 Series。
        
    Returns:
        调整单位后的数据 Series。
    """
    if len(unit_rate_series) != len(data_series):
        raise ValueError("单位转换率序列和数据序列的长度必须一致。")
        
    # 直接用数据除以转换率 (假设转换率是从目标单位到标准单位的)
    # 确保两个Series对齐索引进行计算
    aligned_rates, aligned_data = unit_rate_series.align(data_series, join='left')
    
    # 处理可能的除零错误和非数值类型
    # 使用 numpy 来处理向量化操作和 nan/inf
    rates_np = aligned_rates.to_numpy(dtype=float)
    data_np = aligned_data.to_numpy(dtype=float)
    
    # 避免除以0
    rates_np[rates_np == 0] = np.nan 
    
    result_np = data_np / rates_np
    
    return pd.Series(result_np, index=data_series.index) 