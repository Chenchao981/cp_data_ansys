# CP 数据处理器的配置设置

import os

# --- 文件路径 ---
# 使用主 VBA 工具的目录作为输出的基础路径
# 在实际应用中，基础路径可能会以不同方式确定（例如，脚本运行的位置）
# 目前，假设如果从项目根目录运行，相对路径结构可能有效
# 需要更好的方法来确定基础路径，也许可以根据输入文件的选择位置来确定
# BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 假设结构如 <项目根目录>/cp_data_processor/config
OUTPUT_SUBDIR = "整理后的数据文件"
# OUTPUT_PATH = os.path.join(BASE_PATH, OUTPUT_SUBDIR) # 需要完善

# --- Excel 工作表名称 ---
# 匹配 VBA 中的常量 SHEET_NAME_LIST
SHEET_NAMES = {
    "SPEC": "Spec",
    "DATA": "Data",
    "YIELD": "Yield",
    "SUMMARY": "Summary",
    "MAP": "Map",
    "BOXPLOT": "BoxPlot",
    "SCATTER": "Scatter",
    "PARAM_COLOR": "ParamColorChart"
}

# --- 处理标志 (模拟 VBA UI 工作表设置) ---
# 这些最好从配置文件或 GUI 加载
ADD_CAL_DATA_FLAG = False       # 对应 VBA 的 ADD_CAL_DATA_FLAG
BOX_PLOT_FLAG = True            # 对应 VBA 的 BOX_PLOT_FLAG
BIN_MAP_PLOT_FLAG = True        # 对应 VBA 的 BIN_MAP_PLOT_FLAG
DATA_COLOR_PLOT_FLAG = True     # 对应 VBA 的 DATA_COLOR_PLOT_FLAG
SCATTER_PLOT_FLAG = True        # 对应 VBA 的 SCATTER_PLOT_FLAG
INCLUDE_EXP_FACT_FLAG = False   # 对应 VBA 的 INCLUDE_EXP_FACT_FLAG

# --- 散点图设置 ---
# 在 VBA 中，这可能指向一个像 XY_SETUP_SHEET 这样的工作表名称
# 在 Python 中，这可以是一个单独的配置文件路径或定义的设置
SCATTER_PLOT_CONFIG_SOURCE = "config/scatter_setup.json" # 示例占位符

# --- 因子表 (如果 INCLUDE_EXP_FACT_FLAG 为 True) ---
# 类似于散点图，需要定义源
FACTOR_CONFIG_SOURCE = "config/factor_setup.csv" # 示例占位符

# --- CP 数据格式检测 ---
# 在 VBA 中，这是从 UI_SHEET.Range("c3") 和 Range("f3") 获取的
# 需要一种机制来获取此信息，可能来自用户输入或文件命名约定
DEFAULT_CP_FORMAT = "CWSW" # 示例占位符 (CW 单晶圆)

# --- 默认 Pass Bin 值 ---
# 对应 VBA 中的 TestInfo.PassBin = 1
DEFAULT_PASS_BIN = 1

# --- 输出文件名 ---
OUTPUT_FILE_SUFFIX = ".xlsx"

# --- 其他常量 ---
# 添加从 VBA 代码衍生的任何其他常量 (例如，特定的列名、阈值)


def get_output_path(base_path: str) -> str:
    """确定输出路径，如果不存在则创建。"""
    path = os.path.join(base_path, OUTPUT_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path 