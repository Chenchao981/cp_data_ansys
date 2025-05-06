import pandas as pd
import matplotlib.pyplot as plt
import xlsxwriter
import io
import logging
import math
import re # For sanitizing sheet names
from typing import List, Dict, Optional, Tuple

# 尝试相对导入
try:
    from ..数据类型定义 import CPLot, CPParameter
except ImportError:
    # 处理可能的导入错误，例如直接运行此脚本时
    import sys
    import os
    # 假设脚本位于 python_cp/plotting/ 目录下
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from python_cp.数据类型定义 import CPLot, CPParameter

logger = logging.getLogger(__name__)

def _sanitize_sheet_name(name: str) -> str:
    """Sanitize a string to be a valid Excel sheet name."""
    # 移除无效字符: []\\/?*:
    name = re.sub(r'[\[\]\\/?*:]', '', name)
    # 限制长度为 31 字符
    return name[:31]

def _apply_axis_options(axis: plt.Axes, options: Dict, default_label: str):
    """Apply min, max, and title options to a matplotlib axis."""
    # axis.set_title(options.get('title', default_label)) # Use axis label instead of title here
    axis.set_label(options.get('title', default_label)) # 使用 title 作为轴标签 (Set label for legend/info, not title of axis itself)
    min_val = options.get('min')
    max_val = options.get('max')

    # 使用 set_xlabel / set_ylabel 设置轴标题
    if axis.get_yaxis() is axis: # Check if it's the Y-axis
        axis.axes.set_ylabel(options.get('title', default_label))
    else:
        axis.axes.set_xlabel(options.get('title', default_label))
        
    current_lim = axis.get_ylim() if axis.get_yaxis() is axis else axis.get_xlim()

    final_min = current_lim[0]
    final_max = current_lim[1]

    auto_min = True
    auto_max = True

    if min_val is not None:
        try:
            final_min = float(min_val)
            auto_min = False
        except (ValueError, TypeError):
            logger.warning(f"Invalid 'min' value '{min_val}' for axis '{default_label}', using auto min.")

    if max_val is not None:
        try:
            final_max = float(max_val)
            auto_max = False
        except (ValueError, TypeError):
            logger.warning(f"Invalid 'max' value '{max_val}' for axis '{default_label}', using auto max.")

    # 确保 min < max
    if not auto_min and not auto_max and final_min >= final_max:
        logger.warning(f"Manual axis limits min >= max ({final_min} >= {final_max}) for '{default_label}'. Reverting to auto scaling.")
        auto_min = True
        auto_max = True
        final_min = current_lim[0]
        final_max = current_lim[1]

    # 根据是 X 轴还是 Y 轴设置限制
    if axis.get_yaxis() is axis: # Check if it's the Y-axis
         axis.axes.set_ylim(bottom=final_min if not auto_min else None,
                       top=final_max if not auto_max else None)
    else: # Assume it's the X-axis
        axis.axes.set_xlim(left=final_min if not auto_min else None,
                      right=final_max if not auto_max else None)


def plot_scatter_charts_to_excel(
    cp_lot: CPLot,
    scatter_configs: List[Dict],
    output_excel_path: str,
    cols_per_row: int = 5,
    image_options: Optional[Dict] = None,
    marker_size: int = 5,
    figure_size: Tuple[float, float] = (6, 4) # Inches
):
    """
    为 CPLot 数据生成散点图, 并将其插入到 Excel 文件中.
    每个配置项生成一个 Sheet 页, 每个 Sheet 页包含该配置下所有 Wafer 的散点图.

    Args:
        cp_lot (CPLot): 包含已合并数据的 CPLot 对象.
        scatter_configs (List[Dict]): 散点图配置列表. 每个字典应包含:
            - 'x_param' (str): X 轴参数 ID.
            - 'y_param' (str): Y 轴参数 ID.
            - 'title' (str, optional): Sheet 页和图表标题的基础.
            - 'x_axis_options' (Dict, optional): X 轴选项 {'min': float, 'max': float, 'title': str}.
            - 'y_axis_options' (Dict, optional): Y 轴选项 {'min': float, 'max': float, 'title': str}.
        output_excel_path (str): 输出 Excel 文件的路径.
        cols_per_row (int): 每行排列多少个图表.
        image_options (Optional[Dict]): 传递给 worksheet.insert_image 的选项 (例如 {'x_scale': 0.5, 'y_scale': 0.5}).
        marker_size (int): 散点图中标记的大小.
        figure_size (Tuple[float, float]): matplotlib 图形的尺寸 (英寸).
    """
    logger.info(f"开始为 {len(scatter_configs)} 个配置生成散点图到 {output_excel_path}")
    if not cp_lot.wafers:
        logger.warning("CPLot 对象中没有 Wafer 数据, 无法生成散点图.")
        return
    if not scatter_configs:
        logger.warning("散点图配置列表为空, 不执行任何操作.")
        return

    img_opts = image_options or {}
    # 确保 combined_data 存在
    if cp_lot.combined_data is None or cp_lot.combined_data.empty:
         logger.error("CPLot.combined_data 为空, 无法生成散点图. 请确保已调用 combine_data_from_wafers()")
         return

    try:
        with xlsxwriter.Workbook(output_excel_path) as writer:
            for config_idx, config in enumerate(scatter_configs):
                x_param_id = config.get('x_param')
                y_param_id = config.get('y_param')

                if not x_param_id or not y_param_id:
                    logger.warning(f"跳过配置 {config_idx+1}: 缺少 'x_param' 或 'y_param'. 配置: {config}")
                    continue

                # 检查参数是否存在于 combined_data
                if x_param_id not in cp_lot.combined_data.columns or y_param_id not in cp_lot.combined_data.columns:
                     logger.warning(f"跳过配置 '{x_param_id}' vs '{y_param_id}': "
                                    f"一个或两个参数在 CPLot.combined_data 中不存在.")
                     continue

                # 获取参数对象以备用（例如获取单位）
                x_param_obj = cp_lot.get_param_by_id(x_param_id)
                y_param_obj = cp_lot.get_param_by_id(y_param_id)

                # 准备 Sheet 名称和图表标题
                base_title = config.get('title', f"{x_param_id}_vs_{y_param_id}")
                sheet_name = _sanitize_sheet_name(f"Scatter_{base_title}")
                worksheet = writer.add_worksheet(sheet_name)
                logger.info(f"  正在为配置 '{base_title}' 创建 Sheet 页 '{sheet_name}'...")

                row_num = 0
                col_num = 0

                # 计算图像大致高度以确定行步进 (基于默认字体和缩放)
                # 这只是一个估计, 实际可能需要调整
                # 使用 figure dpi 和 figure height in inches
                # default dpi is usually 100
                dpi = plt.rcParams.get('figure.dpi', 100)
                image_height_pixels = figure_size[1] * dpi * img_opts.get('y_scale', 1.0)
                row_step = math.ceil(image_height_pixels / 15) + 1 # 估算 Excel 行高约为 15 像素

                for wafer_idx, wafer in enumerate(cp_lot.wafers):
                    wafer_data = cp_lot.combined_data[cp_lot.combined_data['wafer_id'] == wafer.wafer_id].copy()

                    # 提取 X, Y 数据并移除 NaN 对
                    wafer_data = wafer_data[[x_param_id, y_param_id]].dropna()

                    if wafer_data.empty:
                        logger.warning(f"    跳过 Wafer '{wafer.wafer_id}': 配置 '{base_title}' 没有有效的 X/Y 数据对.")
                        continue

                    x_values = wafer_data[x_param_id]
                    y_values = wafer_data[y_param_id]

                    # --- 生成 Matplotlib 图表 ---
                    fig, ax = plt.subplots(figsize=figure_size)
                    ax.scatter(x_values, y_values, s=marker_size)

                    # 设置标题和标签
                    plot_title = f"{wafer.wafer_id} - {base_title}"
                    ax.set_title(plot_title)

                    x_label = f"{x_param_id}{f' ({x_param_obj.unit})' if x_param_obj and x_param_obj.unit else ''}"
                    y_label = f"{y_param_id}{f' ({y_param_obj.unit})' if y_param_obj and y_param_obj.unit else ''}"

                    # 应用坐标轴选项 - 注意: _apply_axis_options 修改的是 axis 对象本身
                    x_axis_opts = config.get('x_axis_options', {})
                    y_axis_opts = config.get('y_axis_options', {})
                    _apply_axis_options(ax.xaxis, x_axis_opts, x_label) # 应用到 ax.xaxis
                    _apply_axis_options(ax.yaxis, y_axis_opts, y_label) # 应用到 ax.yaxis

                    # 设置最终的坐标轴标签文本
                    ax.set_xlabel(x_axis_opts.get('title', x_label))
                    ax.set_ylabel(y_axis_opts.get('title', y_label))

                    ax.grid(True, linestyle='--', alpha=0.6)
                    fig.tight_layout()

                    # --- 将图表保存到内存并插入 Excel ---
                    img_data = io.BytesIO()
                    fig.savefig(img_data, format='png')
                    plt.close(fig) # 关闭图形, 释放内存
                    img_data.seek(0)

                    # 计算插入位置
                    insert_row = row_num
                    insert_col_char = xlsxwriter.utility.xl_col_to_name(col_num)
                    cell_location = f"{insert_col_char}{insert_row + 1}" # Excel 单元格 1-based index

                    worksheet.insert_image(cell_location, f"{plot_title}.png", {'image_data': img_data, **img_opts})
                    logger.debug(f"    已插入 Wafer '{wafer.wafer_id}' 的图表到 {sheet_name}:{cell_location}")

                    # 更新下一个图表的位置
                    col_num += 1
                    if col_num >= cols_per_row:
                        col_num = 0
                        row_num += row_step # 基于估算的行高换行

        logger.info(f"成功将散点图导出到 {output_excel_path}")

    except Exception as e:
        logger.error(f"生成散点图 Excel 文件时出错: {e}", exc_info=True)

# --- 示例用法 (可选, 用于独立测试) ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    import numpy as np # 导入 numpy

    logger.info("运行 Scatter Plot 模块示例...")

    # --- 创建模拟 CPLot 数据 ---
    logger.info("创建模拟 CPLot 数据...")
    lot = CPLot(lot_id="ScatterTest01", product="ScatterProd")
    params = [
        CPParameter(id='Vth', group='FET', unit='V', sl=0.3, su=0.7),
        CPParameter(id='Idsat', group='FET', unit='mA', sl=1.0, su=None),
        CPParameter(id='Ioff', group='FET', unit='uA', sl=None, su=0.1),
        CPParameter(id='Res', group='Passive', unit='Ohm')
    ]
    lot.params = params

    all_wafer_data = []
    wafers_list = []
    for i in range(1, 6): # 创建 5 个 Wafer
        wafer_id = f"ScatW{i:02d}"
        chip_count = 100
        seq = np.arange(1, chip_count + 1)
        x = np.random.randint(-10, 11, size=chip_count)
        y = np.random.randint(-10, 11, size=chip_count)
        bins = np.random.randint(1, 3, size=chip_count).astype(float)

        vth_data = np.random.normal(0.5 + i*0.02, 0.1, size=chip_count) # Wafer 间略有差异
        idsat_data = (np.random.normal(1.5 + i*0.05, 0.2, size=chip_count) + vth_data*0.5) * 1e-3 # Idsat 与 Vth 相关
        ioff_data = np.random.rand(chip_count) * 0.15 * 1e-6 # uA -> A
        res_data = np.random.normal(100, 10, size=chip_count)

        # Add some NaN param data
        vth_data[np.random.choice(chip_count, 5, replace=False)] = np.nan
        idsat_data[np.random.choice(chip_count, 8, replace=False)] = np.nan

        chip_df = pd.DataFrame({
            'Vth': vth_data,
            'Idsat': idsat_data,
            'Ioff': ioff_data,
            'Res': res_data
        })

        wafer = CPWafer(wafer_id=wafer_id, chip_count=chip_count, seq=seq, x=x, y=y, bin=bins, chip_data=chip_df)
        wafers_list.append(wafer)

        temp_df = chip_df.copy()
        temp_df['wafer_id'] = wafer_id
        temp_df['seq'] = seq
        temp_df['x'] = x
        temp_df['y'] = y
        temp_df['bin'] = bins
        all_wafer_data.append(temp_df)

    lot.wafers = wafers_list # 将 wafer 列表添加到 lot 对象

    # 手动合并数据
    if all_wafer_data:
        lot.combined_data = pd.concat(all_wafer_data, ignore_index=True)
        cols_to_move = ['wafer_id', 'seq', 'x', 'y', 'bin']
        remaining_cols = [col for col in lot.combined_data.columns if col not in cols_to_move]
        lot.combined_data = lot.combined_data[cols_to_move + remaining_cols]
    else:
        lot.combined_data = pd.DataFrame()

    logger.info("模拟数据创建完成.")

    # --- 定义散点图配置 ---
    scatter_configs_test = [
        {
            'x_param': 'Vth',
            'y_param': 'Idsat',
            'title': 'Vth vs Idsat',
            'x_axis_options': {'min': 0.2, 'max': 0.9, 'title': 'Threshold Voltage (V)'},
            'y_axis_options': {'title': 'Saturation Current (mA)'} # Y 轴自动范围
        },
        {
            'x_param': 'Vth',
            'y_param': 'Ioff',
            # 无 title, 将自动生成
            # 无 axis options, 将全部自动
        },
        {
             'x_param': 'Res', # 假设 Res 缺失
             'y_param': 'Vth'
        }
    ]

    # --- 测试绘图函数 ---
    output_file = "scatter_plot_output.xlsx"
    plot_options = {
        'cols_per_row': 3,
        'image_options': {'x_scale': 0.45, 'y_scale': 0.45},
        'marker_size': 8,
        'figure_size': (5, 3.5) # 调整图形大小
    }

    logger.info(f"开始生成散点图到 {output_file}...")
    plot_scatter_charts_to_excel(lot, scatter_configs_test, output_file, **plot_options)
    logger.info("散点图生成完成.")

    print(f"\n请检查生成的 Excel 文件: '{output_file}'") 