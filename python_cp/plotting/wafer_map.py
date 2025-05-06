import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import pandas as pd
import logging
from typing import Optional, Dict, Tuple, Any, Union
from io import BytesIO
import xlsxwriter

# 尝试相对导入
try:
    # 注意：这里的相对导入级别 .. 可能需要根据实际项目结构调整
    from ..数据类型定义 import CPWafer, CPLot
except ImportError:
    # 如果直接运行脚本或包结构不同，则给出警告并定义占位符
    logger = logging.getLogger(__name__)
    logger.warning("无法执行相对导入 '..数据类型定义'。请确保脚本从正确的包结构运行，" 
                   "或调整导入路径。将使用占位符类。")
    # 定义临时的 Placeholder 类，以便脚本至少可以加载和解析
    class CPWafer:
        def __init__(self, wafer_id='temp', x=None, y=None, bin=None, chip_data=None):
            self.wafer_id = wafer_id
            self.x = x if x is not None else np.array([])
            self.y = y if y is not None else np.array([])
            self.bin = bin if bin is not None else np.array([])
            self.chip_data = chip_data if chip_data is not None else pd.DataFrame()

    class CPLot:
         def __init__(self, lot_id='temp_lot', product='temp_prod'):
              self.lot_id = lot_id
              self.product = product
              self.wafers: list[CPWafer] = []
              self.params: list = [] # 简化，实际需要 CPParameter

    # 临时添加 CPParameter 占位符，如果示例用法需要
    class CPParameter:
         def __init__(self, id='temp_param', group='g1', display_name='Temp'):
             self.id = id
             self.group = group
             self.display_name = display_name

logger = logging.getLogger(__name__)

# --- 默认 Bin 颜色配置 (可以后续从文件加载) ---
# 颜色名称参考: https://matplotlib.org/stable/gallery/color/named_colors.html
DEFAULT_BIN_COLOR_MAP = {
    1: 'lime',      # Pass Bin (例如: 绿色)
    2: 'yellow',    # Bin 2
    3: 'orange',    # Bin 3
    4: 'red',       # Bin 4 (例如: Fail)
    5: 'fuchsia',   # Bin 5
    6: 'aqua',      # Bin 6
    7: 'blue',      # Bin 7
    8: 'darkviolet',
    9: 'saddlebrown',
    # 可以添加更多 Bin 值和颜色
    np.nan: 'lightgrey', # NaN 值颜色
    'default': 'grey'    # 未在字典中定义的其他 Bin 值的颜色
}

def _prepare_discrete_cmap(value_map: Dict[Any, str], default_color: str = 'grey') -> Tuple[Optional[colors.ListedColormap], Optional[colors.BoundaryNorm]]:
    """根据值到颜色的字典创建 ListedColormap 和 BoundaryNorm。"""
    if not value_map:
        return None, None

    # 提取有效的数值键和颜色 (过滤掉 NaN 和 'default' 键)
    valid_values = sorted([k for k in value_map.keys() if pd.notna(k) and k != 'default'])
    if not valid_values:
        logger.warning("颜色映射字典中没有找到有效的非 NaN、非 'default' 数值键。")
        return None, None

    color_list = [value_map.get(v, default_color) for v in valid_values]

    # 检查是否有 NaN 的颜色定义
    nan_color = value_map.get(np.nan)

    try:
        cmap = colors.ListedColormap(color_list)
        if nan_color:
             cmap.set_bad(color=nan_color) # NaN 值通常被 imshow 视为 'bad'

        # 创建边界，使每个颜色对应一个整数 Bin 值
        # 边界需要在每个 bin 值的两侧，例如 bin 1 对应 0.5 到 1.5
        bounds = [v - 0.5 for v in valid_values] + [valid_values[-1] + 0.5]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        return cmap, norm
    except Exception as e:
        logger.error(f"创建离散颜色映射时出错: {e}", exc_info=True)
        return None, None

def plot_wafer_map(
    wafer: CPWafer,
    value_col: str = 'bin',
    cmap: Union[Dict[Any, str], colors.Colormap, None] = None,
    ax: Optional[plt.Axes] = None,
    title: Optional[str] = None,
    show_missing_dies: bool = True, # 是否显示没有数据的 Die (用 NaN 颜色)
    invert_xaxis: bool = True # 是否反转 X 轴以匹配 VBA d(y, MaxX-x) 逻辑
) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    绘制单个 Wafer 的 Map 图。

    Args:
        wafer (CPWafer): 包含要绘制数据的 CPWafer 对象。
        value_col (str): 要映射到颜色的列名 ('bin' 或参数 ID)。
        cmap (Union[Dict, Colormap, None]): 颜色映射。
            如果是字典 (用于离散值如 Bin)，键是值，值是颜色字符串。
            如果是 Colormap (用于连续值)。
            如果是 None，将使用 DEFAULT_BIN_COLOR_MAP 或 matplotlib 默认。
        ax (Optional[plt.Axes]): 要在其上绘图的 Axes。None则创建新的。
        title (Optional[str]): 图表标题。None则用 wafer.wafer_id。
        show_missing_dies (bool): 如果 True，坐标范围内但数据中缺失的点将用 NaN 颜色显示。
                                  如果 False，这些点将不被绘制（可能显示背景色）。
        invert_xaxis (bool): 如果为 True，将反转 X 轴（水平翻转数据矩阵）以模拟
                             VBA 中 d(y, MaxX - x) 的填充方式。

    Returns:
        Tuple[Optional[plt.Figure], Optional[plt.Axes]]: Figure 和 Axes 对象，失败则为 (None, None)。
    """
    fig = None
    if ax is None:
        # 创建新的 Figure 和 Axes
        fig, ax = plt.subplots(figsize=(5, 5)) # 可调整大小
    else:
        # 使用传入的 Axes，获取其 Figure
        fig = ax.figure

    # 提取数据
    try:
        x = wafer.x
        y = wafer.y
        # 尝试获取数据，优先从 chip_data 获取，然后尝试作为 wafer 属性
        if wafer.chip_data is not None and value_col in wafer.chip_data.columns:
            values = wafer.chip_data[value_col].values
        elif hasattr(wafer, value_col):
            values = getattr(wafer, value_col)
        else:
            logger.error(f"在 Wafer '{wafer.wafer_id}' 中找不到要绘制的数据列/属性: '{value_col}'")
            if fig and ax is None: plt.close(fig) # 只有当 figure 是新创建的时才关闭
            return None, None

        # 确保都是 NumPy 数组
        x = np.asarray(x) if x is not None else np.array([])
        y = np.asarray(y) if y is not None else np.array([])
        values = np.asarray(values) if values is not None else np.array([])

        if not (len(x) == len(y) == len(values)) or len(x) == 0:
            logger.warning(f"Wafer '{wafer.wafer_id}' 的 X, Y, 和 '{value_col}' 数据长度不匹配或为空。无法绘制 Map。")
            if fig and ax is None: plt.close(fig)
            return None, None

    except Exception as e:
        logger.error(f"从 Wafer '{wafer.wafer_id}' 提取数据时出错: {e}", exc_info=True)
        if fig and ax is None: plt.close(fig)
        return None, None

    # 计算范围 (忽略 NaN)
    try:
        # 过滤掉 NaN 值再计算范围
        x_finite = x[np.isfinite(x)]
        y_finite = y[np.isfinite(y)]
        if len(x_finite) == 0 or len(y_finite) == 0:
             raise ValueError("坐标数据全是 NaN 或无效")
        min_x, max_x = int(np.min(x_finite)), int(np.max(x_finite))
        min_y, max_y = int(np.min(y_finite)), int(np.max(y_finite))
    except ValueError as ve:
        logger.warning(f"Wafer '{wafer.wafer_id}' 无法计算坐标范围: {ve}")
        if fig and ax is None: plt.close(fig)
        return None, None

    grid_height = max_y - min_y + 1
    grid_width = max_x - min_x + 1

    if grid_height <= 0 or grid_width <= 0:
        logger.warning(f"Wafer '{wafer.wafer_id}' 计算得到的网格尺寸无效 ({grid_height}x{grid_width})。")
        if fig and ax is None: plt.close(fig)
        return None, None

    # 创建数据矩阵 (初始化为 NaN)
    # 使用 float 类型以容纳 NaN
    data_matrix = np.full((grid_height, grid_width), np.nan, dtype=float)

    # 填充矩阵
    # 仅处理 x, y, value 都有有效值的点
    valid_indices = np.isfinite(x) & np.isfinite(y) & np.isfinite(values)
    x_valid, y_valid, values_valid = x[valid_indices], y[valid_indices], values[valid_indices]

    # 转换为整数索引
    rows = (y_valid - min_y).astype(int)
    cols = (x_valid - min_x).astype(int)

    # 检查索引是否在范围内 (冗余检查，但更安全)
    valid_grid_indices = (rows >= 0) & (rows < grid_height) & (cols >= 0) & (cols < grid_width)
    rows = rows[valid_grid_indices]
    cols = cols[valid_grid_indices]
    values_valid = values_valid[valid_grid_indices]

    # 填充数据
    data_matrix[rows, cols] = values_valid

    # --- 颜色映射处理 ---
    final_cmap = None
    norm = None
    nan_color = 'lightgrey' # 默认 NaN 颜色
    is_discrete = False

    if isinstance(cmap, dict):
        is_discrete = True
        default_color = cmap.get('default', 'grey')
        nan_color = cmap.get(np.nan, nan_color)
        final_cmap, norm = _prepare_discrete_cmap(cmap, default_color)
        if final_cmap is None:
             logger.warning(f"无法为 Wafer '{wafer.wafer_id}' 创建离散颜色映射，将使用默认连续映射。")
             final_cmap = plt.cm.viridis # 后备方案
             norm = None
             is_discrete = False
        else:
            final_cmap.set_bad(color=nan_color)

    elif isinstance(cmap, colors.Colormap):
        final_cmap = cmap
        # 尝试从 cmap 获取 bad color
        try:
             nan_color_from_cmap = final_cmap.get_bad()
             nan_color = nan_color_from_cmap
        except AttributeError:
             pass # Colormap 可能没有 get_bad 方法
        final_cmap.set_bad(color=nan_color) # 确保设置了 NaN 颜色
        norm = None # 使用默认的线性归一化
    else: # cmap is None or other type
        # 自动判断是离散 (bin) 还是连续 (参数)
        non_nan_values = data_matrix[~np.isnan(data_matrix)]
        has_data = non_nan_values.size > 0
        is_integer_data = False
        unique_value_count = 0
        if has_data:
             # 检查是否所有非 NaN 值都接近整数
             is_integer_data = np.all(np.isclose(non_nan_values, np.round(non_nan_values)))
             unique_value_count = len(np.unique(non_nan_values.round().astype(int))) # 统计近似整数的唯一值

        # 启发式方法：value_col 是 'bin' 或数据是整数且唯一值不多 (<20)
        if value_col.lower() == 'bin' or (has_data and is_integer_data and unique_value_count < 20):
             is_discrete = True
             logger.debug(f"Wafer '{wafer.wafer_id}', value '{value_col}' 被视为离散数据，使用默认 Bin Map。")
             default_color = DEFAULT_BIN_COLOR_MAP.get('default', 'grey')
             nan_color = DEFAULT_BIN_COLOR_MAP.get(np.nan, nan_color)
             final_cmap, norm = _prepare_discrete_cmap(DEFAULT_BIN_COLOR_MAP, default_color)
             if final_cmap is None:
                  logger.warning(f"无法为 Wafer '{wafer.wafer_id}' 创建默认 Bin Map，将使用 viridis。")
                  final_cmap = plt.cm.viridis
                  norm = None
                  is_discrete = False
             else:
                 final_cmap.set_bad(color=nan_color)
        else:
            is_discrete = False
            logger.debug(f"Wafer '{wafer.wafer_id}', value '{value_col}' 被视为连续数据，使用 viridis colormap。")
            final_cmap = plt.cm.viridis
            try:
                nan_color_from_cmap = final_cmap.get_bad()
                nan_color = nan_color_from_cmap
            except AttributeError:
                pass
            final_cmap.set_bad(color=nan_color) # 确保设置了 NaN 颜色
            norm = None

    # --- 绘图 --- 
    # 根据 invert_xaxis 决定是否翻转数据矩阵以匹配 VBA 逻辑 d(y, MaxX-x)
    # np.fliplr 水平翻转 (左右)
    matrix_to_plot = np.fliplr(data_matrix) if invert_xaxis else data_matrix

    # 使用 imshow 绘制
    # origin='lower' 使 (0,0) 在左下角 (y=min_y)，匹配常见 Wafer Map 习惯
    im = ax.imshow(matrix_to_plot, cmap=final_cmap, norm=norm,
                   interpolation='none', origin='lower',
                   aspect='equal') # aspect='equal' 使像素为方形

    # 设置轴和标题
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title if title is not None else f"Wafer: {wafer.wafer_id}")

    # --- (可选) 添加图例或颜色条 ---
    if is_discrete and final_cmap is not None and norm is not None:
        # 创建离散图例
        try:
            handles = []
            labels = []
            # 使用传入的 cmap (如果是 dict) 或默认 map 来构建图例
            legend_source_map = cmap if isinstance(cmap, dict) else DEFAULT_BIN_COLOR_MAP

            # 获取颜色映射中实际定义的值和颜色
            defined_bins = sorted([k for k in legend_source_map if pd.notna(k) and k != 'default'])

            for bin_val in defined_bins:
                 color = legend_source_map.get(bin_val)
                 if color:
                     handles.append(plt.Rectangle((0, 0), 1, 1, fc=color))
                     labels.append(f"Bin {bin_val}")

            # 添加 NaN 图例
            nan_legend_color = legend_source_map.get(np.nan)
            if nan_legend_color:
                 handles.append(plt.Rectangle((0, 0), 1, 1, fc=nan_legend_color))
                 labels.append("NaN/Skip")

            # 添加 Default 图例 (如果数据中有未明确定义的 bin)
            default_legend_color = legend_source_map.get('default')
            if default_legend_color and default_legend_color != nan_legend_color:
                 all_map_vals_set = set(data_matrix[~np.isnan(data_matrix)].astype(int))
                 defined_bin_vals_set = set(defined_bins)
                 if not all_map_vals_set.issubset(defined_bin_vals_set):
                    handles.append(plt.Rectangle((0, 0), 1, 1, fc=default_legend_color))
                    labels.append("Other")

            if handles:
                # 将图例放在图像右侧外部
                legend = ax.legend(handles, labels, title=value_col, loc='center left',
                                 bbox_to_anchor=(1.02, 0.5), borderaxespad=0.)
                # 尝试自动调整布局，如果 figure 是新创建的
                if fig and ax is None:
                    try:
                        fig.tight_layout(rect=[0, 0, 0.85, 1]) # rect 留出右侧空间给图例
                    except ValueError: # tight_layout 可能因某些情况失败
                        pass

        except Exception as legend_e:
            logger.warning(f"为 Wafer '{wafer.wafer_id}' 创建离散图例时出错: {legend_e}", exc_info=True)

    elif not is_discrete: # 连续数据，添加颜色条
        try:
             cbar = fig.colorbar(im, ax=ax, shrink=0.8, aspect=20)
             cbar.set_label(value_col)
             # 尝试自动调整布局
             if fig and ax is None:
                  try:
                       fig.tight_layout()
                  except ValueError:
                       pass
        except Exception as cbar_e:
             logger.warning(f"为 Wafer '{wafer.wafer_id}' 添加颜色条时出错: {cbar_e}", exc_info=True)

    return fig, ax

def plot_all_wafers_to_excel(
    cp_lot: CPLot,
    output_excel_path: str,
    value_col: str = 'bin',
    color_map: Union[Dict[Any, str], colors.Colormap, None] = None,
    invert_xaxis: bool = True,
    cols_per_row: int = 4, # 每行排列多少个 Wafer Map
    image_options: Optional[Dict] = None # xlsxwriter insert_image options
):
    """
    将 CPLot 中所有 Wafer 的指定 Map 图插入到 Excel 文件的 "Map" Sheet 页。

    Args:
        cp_lot (CPLot): 包含所有 Wafer 数据的 CPLot 对象。
        output_excel_path (str): 输出的 Excel 文件路径。
        value_col (str): 要绘制的 Map 类型 ('bin' 或参数 ID)。
        color_map (Union[Dict, Colormap, None]): 颜色映射。
            如果是字典 (用于离散值如 Bin)。
            如果是 Colormap (用于连续值)。
            如果是 None，将使用模块默认。
        invert_xaxis (bool): 是否反转 X 轴以匹配 VBA。
        cols_per_row (int): Excel 中每行排列多少个图。
        image_options (Optional[Dict]): 传递给 xlsxwriter worksheet.insert_image 的选项。
                                        例如 {'x_scale': 0.5, 'y_scale': 0.5}
    """
    if not cp_lot.wafers:
        logger.warning("CPLot 对象中没有 Wafer 数据，无法执行绘图。")
        return

    # -- Excel 初始化 --
    try:
        workbook = xlsxwriter.Workbook(output_excel_path)
        worksheet = workbook.add_worksheet("Map")
        # 设置默认列宽 (可选)
        worksheet.set_column(1, cols_per_row * 10, 15) # 假设每图占 10 列，宽度设 15
    except Exception as e:
        logger.error(f"创建 Excel 文件 '{output_excel_path}' 失败: {e}", exc_info=True)
        return

    # -- 图像插入位置计算 --
    # 估计的行/列步长 (需要根据实际图像大小和缩放调整)
    row_step = 25 # 每个图大约占用的 Excel 行数 (包括标题和间距)
    col_step = 10 # 每个图大约占用的 Excel 列数
    start_row = 1 # 从第 2 行开始 (0-based index 1)
    start_col = 1 # 从 B 列开始 (0-based index 1)
    current_row_index = start_row
    current_col_index = start_col
    wafer_count_in_row = 0

    # 默认图像选项 (可以被 image_options 覆盖)
    default_img_opts = {
        'object_position': 1, # 移动和调整单元格大小
        'x_scale': 0.5,       # 默认缩放比例 (可调)
        'y_scale': 0.5
    }
    if image_options:
        default_img_opts.update(image_options)

    # -- 遍历并绘图插入 --
    logger.info(f"开始为 Lot '{cp_lot.lot_id}' 的 {len(cp_lot.wafers)} 个 Wafer 绘制 '{value_col}' Map 并插入 Excel..."
                f" (每行 {cols_per_row} 个图)")
    for i, wafer in enumerate(cp_lot.wafers):
        logger.debug(f"正在处理 Wafer {i+1}/{len(cp_lot.wafers)}: {wafer.wafer_id}")
        # 为每个 wafer 创建独立的 figure
        fig, ax = plot_wafer_map(wafer, value_col=value_col, cmap=color_map, invert_xaxis=invert_xaxis, ax=None)

        if fig is None:
            logger.warning(f"跳过 Wafer {wafer.wafer_id}，因为无法生成 Map 图。")
            continue

        # 保存图像到内存
        img_data = BytesIO()
        try:
            # 保存时移除图例/颜色条以获得更干净的图像插入Excel?
            # 或者保存完整图像？先保存完整图像。
            fig.savefig(img_data, format='png', bbox_inches='tight', dpi=150) # dpi 可调
            img_data.seek(0)
        except Exception as save_e:
            logger.error(f"保存 Wafer {wafer.wafer_id} 图像到内存时出错: {save_e}", exc_info=True)
            plt.close(fig)
            continue

        plt.close(fig) # 关闭 figure 释放内存

        # 计算插入位置的 Excel 单元格名称
        excel_cell = xlsxwriter.utility.xl_rowcol_to_cell(current_row_index, current_col_index)
        logger.debug(f"  插入图像到单元格: {excel_cell}")

        # 插入 Wafer ID (在图像上方一行)
        try:
            worksheet.write_string(current_row_index - 1, current_col_index, f"Wafer: {wafer.wafer_id}")
            # 可以设置行高以容纳标题
            worksheet.set_row(current_row_index - 1, 15) # 15 points height
        except Exception as write_e:
             logger.warning(f"写入 Wafer ID 到 Excel 时出错: {write_e}")

        # 插入图像
        try:
            # insert_image 使用左上角单元格定位
            worksheet.insert_image(excel_cell, f"{wafer.wafer_id}_{value_col}.png", # 提供文件名用于 Excel 内部引用
                                   {'image_data': img_data, **default_img_opts})
        except Exception as insert_e:
            logger.error(f"插入 Wafer {wafer.wafer_id} 图像到 Excel 时出错: {insert_e}", exc_info=True)
            # 即使插入失败，也继续处理下一个 wafer

        # 更新下一个图像的插入位置
        wafer_count_in_row += 1
        if wafer_count_in_row >= cols_per_row:
            # 换行
            current_row_index += row_step
            current_col_index = start_col
            wafer_count_in_row = 0
        else:
            # 同行右移
            current_col_index += col_step

    # --- (TODO) 添加全局图例到 Excel --- 
    # 可以创建一个只包含图例的 matplotlib 图，保存到 BytesIO，然后插入
    # 或者，如果颜色配置来自 Excel，可以将该配置表复制或链接过来
    logger.info("所有 Wafer 处理完毕。")

    # --- 保存 Excel --- 
    try:
        workbook.close() # 保存并关闭
        logger.info(f"成功将 Wafer Maps 保存到 Excel 文件: '{output_excel_path}'")
    except Exception as e:
        logger.error(f"保存 Excel 文件 '{output_excel_path}' 时失败: {e}", exc_info=True)

# --- 示例用法 --- 
if __name__ == '__main__':
    # 配置日志级别为 DEBUG 以查看详细信息
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # 设置 matplotlib 日志级别为 WARNING，避免过多内部信息
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    logger.info("运行 Wafer Map 绘图模块示例...")

    # --- 创建模拟数据 --- 
    logger.info("创建模拟 CPLot 数据...")
    # 确保占位符类已定义（如果相对导入失败）
    lot = CPLot(lot_id="TestLot001", product="TestProd")
    lot.params.append(CPParameter(id='ParamA', group='Gr1', display_name='Param A'))

    for i in range(1, 7): # 创建 6 个 Wafer
        wafer_id = f"W{i:02d}"
        # 随机生成一些坐标和 bin 值 (模拟 10x10 grid)
        size = 80
        x_coords = np.random.randint(-4, 5, size=size) # X 范围 -4 到 4
        y_coords = np.random.randint(-4, 5, size=size) # Y 范围 -4 到 4
        # 确保至少包含 min/max 坐标以定义完整范围
        x_coords = np.concatenate([x_coords, [-4, 4]])
        y_coords = np.concatenate([y_coords, [-4, 4]])
        current_size = len(x_coords)
        
        bin_values = np.random.randint(1, 6, size=current_size) # Bins 1-5
        param_a_values = np.random.normal(5, 2, size=current_size) # 正态分布参数值
        
        # 加入一些 NaN (模拟 skip die 或无效数据)
        nan_indices = np.random.choice(current_size, int(current_size * 0.1), replace=False)
        x_coords = x_coords.astype(float)
        y_coords = y_coords.astype(float)
        bin_values = bin_values.astype(float)
        param_a_values = param_a_values.astype(float)
        
        x_coords[nan_indices[:len(nan_indices)//3]] = np.nan
        y_coords[nan_indices[len(nan_indices)//3 : 2*len(nan_indices)//3]] = np.nan
        bin_values[nan_indices[1*len(nan_indices)//3:]] = np.nan
        param_a_values[nan_indices[2*len(nan_indices)//3:]] = np.nan

        chip_data = pd.DataFrame({'ParamA': param_a_values})

        wafer = CPWafer(
            wafer_id=wafer_id,
            x=x_coords,
            y=y_coords,
            bin=bin_values,
            chip_data=chip_data
        )
        lot.wafers.append(wafer)

    logger.info("模拟数据创建完成。")

    # --- 测试绘制 Bin Map 到 Excel --- 
    output_file = "wafer_maps_output.xlsx"
    logger.info(f"开始绘制 Bin Maps 并保存到 {output_file}... (invert_xaxis=True)")
    # 使用默认颜色映射 (DEFAULT_BIN_COLOR_MAP)
    plot_all_wafers_to_excel(lot, output_file, value_col='bin', 
                             cols_per_row=3, invert_xaxis=True, 
                             image_options={'x_scale': 0.35, 'y_scale': 0.35}) # 调整缩放
    logger.info("Bin Map 绘制完成。")

    # --- 测试绘制参数 Map 到 Excel --- 
    output_param_file = "paramA_maps_output.xlsx"
    logger.info(f"开始绘制 ParamA Maps 并保存到 {output_param_file}... (invert_xaxis=True)")
    # 使用指定的连续颜色映射 (coolwarm)
    plot_all_wafers_to_excel(lot, output_param_file, value_col='ParamA', 
                             cols_per_row=3, invert_xaxis=True,
                             color_map=plt.cm.coolwarm, 
                             image_options={'x_scale': 0.35, 'y_scale': 0.35})
    logger.info("ParamA Map 绘制完成。")

    print(f"\n请检查生成的 Excel 文件: '{output_file}' 和 '{output_param_file}'")
 