import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from typing import Optional, Dict, Tuple, Any, Union, List
from io import BytesIO
import xlsxwriter

# 尝试相对导入
try:
    # 注意：这里的相对导入级别 .. 可能需要根据实际项目结构调整
    from ..数据类型定义 import CPWafer, CPLot, CPParameter
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
              self.params: list = [] 

    class CPParameter:
         def __init__(self, id='temp_param', group='g1', display_name='Temp', unit=None, sl=None, su=None):
             self.id = id
             self.group = group
             self.display_name = display_name
             self.unit = unit
             self.sl = sl
             self.su = su

logger = logging.getLogger(__name__)

def plot_wafer_boxplot(
    wafer: CPWafer,
    param_id: str,
    param_info: Optional[CPParameter] = None,
    ax: Optional[plt.Axes] = None
) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    为单个 Wafer 的指定参数绘制箱形图。

    Args:
        wafer (CPWafer): 包含数据的晶圆对象。
        param_id (str): 要绘制的参数的 ID ('bin' 或 chip_data 中的列名)。
        param_info (Optional[CPParameter]): 参数的元信息 (用于标题和标签)。
        ax (Optional[plt.Axes]): 要在其上绘图的 Axes。如果为 None，则创建新的。

    Returns:
        Tuple[Optional[plt.Figure], Optional[plt.Axes]]: Figure 和 Axes 对象，失败则为 (None, None)。
    """
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(3, 5)) # 箱形图通常更高
    else:
        fig = ax.figure

    # 提取数据
    try:
        if param_id.lower() == 'bin':
            data = wafer.bin
            data_label = "Bin"
            unit = ""
        elif wafer.chip_data is not None and param_id in wafer.chip_data.columns:
            data = wafer.chip_data[param_id].values
            data_label = param_info.display_name if param_info else param_id
            unit = f" ({param_info.unit})" if param_info and param_info.unit else ""
        else:
            logger.warning(f"在 Wafer '{wafer.wafer_id}' 中找不到参数数据: '{param_id}'")
            if fig and ax is None: plt.close(fig)
            return None, None

        # 确保是 NumPy 数组并处理 NaN
        data = np.asarray(data) if data is not None else np.array([])
        data_clean = data[~np.isnan(data)]

        if len(data_clean) == 0:
            logger.warning(f"Wafer '{wafer.wafer_id}' 参数 '{param_id}' 的有效数据为空。")
            # 可以选择绘制一个空图或直接返回 None
            ax.text(0.5, 0.5, 'No Valid Data', horizontalalignment='center', 
                    verticalalignment='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            # 绘制箱形图
            # patch_artist=True 填充颜色, showfliers=True 显示异常点 (默认)
            bp = ax.boxplot(data_clean, patch_artist=True, showfliers=True, widths=0.6)
            
            # 自定义外观 (可选)
            for box in bp['boxes']:
                box.set(facecolor='lightblue', alpha=0.7)
            for median in bp['medians']:
                median.set(color='red', linewidth=2)
            for whisker in bp['whiskers']:
                whisker.set(color='gray', linestyle='--')
            for cap in bp['caps']:
                cap.set(color='gray')
                
            # 移除 X 轴刻度，因为只有一个箱体
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax.set_xlabel(None)
            
            # 设置 Y 轴标签
            ax.set_ylabel(f"{data_label}{unit}")

            # 添加规格线 (如果可用)
            if param_info and param_info.sl is not None:
                ax.axhline(param_info.sl, color='orange', linestyle=':', linewidth=1.5, label=f'SL={param_info.sl}')
            if param_info and param_info.su is not None:
                ax.axhline(param_info.su, color='purple', linestyle=':', linewidth=1.5, label=f'SU={param_info.su}')
            if param_info and (param_info.sl is not None or param_info.su is not None):
                ax.legend(fontsize='small')

        # 设置标题
        ax.set_title(f"Wafer: {wafer.wafer_id}", fontsize='medium')
        
        # 调整布局 (如果 figure 是新创建的)
        if fig and ax is None:
            try:
                 fig.tight_layout()
            except ValueError:
                 pass 

    except Exception as e:
        logger.error(f"为 Wafer '{wafer.wafer_id}' 绘制参数 '{param_id}' 箱形图时出错: {e}", exc_info=True)
        if fig and ax is None: plt.close(fig)
        return None, None

    return fig, ax

def plot_parameter_boxplots_to_excel(
    cp_lot: CPLot,
    param_id: str,
    output_excel_path: str,
    cols_per_row: int = 5, # 每行排列多少个箱形图
    image_options: Optional[Dict] = None # xlsxwriter insert_image options
):
    """
    为指定参数，将 CPLot 中每个 Wafer 的箱形图插入到 Excel 文件的新 Sheet 页。

    Args:
        cp_lot (CPLot): 包含所有 Wafer 数据的 CPLot 对象。
        param_id (str): 要绘制箱形图的参数 ID ('bin' 或 chip_data 列名)。
        output_excel_path (str): 输出的 Excel 文件路径。
        cols_per_row (int): Excel 中每行排列多少个图。
        image_options (Optional[Dict]): 传递给 xlsxwriter worksheet.insert_image 的选项。
                                        例如 {'x_scale': 0.5, 'y_scale': 0.5}
    """
    if not cp_lot.wafers:
        logger.warning("CPLot 对象中没有 Wafer 数据，无法执行绘图。")
        return

    # 获取参数信息
    param_info = cp_lot.get_param_by_id(param_id)
    if param_id.lower() != 'bin' and param_info is None:
        logger.warning(f"在 CPLot 中找不到参数 ID '{param_id}' 的信息，图表标签可能不完整。")
        # 创建一个临时的，以防万一
        param_info = CPParameter(id=param_id, display_name=param_id)
    elif param_id.lower() == 'bin':
         param_info = CPParameter(id='bin', display_name='Bin') # 用于标题
         
    sheet_name = f"BoxPlot_{param_id[:25]}" # Excel sheet 名长度限制

    # -- Excel 初始化 --
    try:
        workbook = xlsxwriter.Workbook(output_excel_path)
        worksheet = workbook.add_worksheet(sheet_name)
        # 设置列宽 (可选, 估计值)
        worksheet.set_column(1, cols_per_row * 8, 10) # 估计每图占 8 列，宽度设 10
    except Exception as e:
        logger.error(f"创建 Excel 文件 '{output_excel_path}' (Sheet: {sheet_name}) 失败: {e}", exc_info=True)
        return

    # -- 图像插入位置计算 --
    row_step = 20 # 每个图大约占用的 Excel 行数 (包括标题和间距)
    col_step = 8  # 每个图大约占用的 Excel 列数
    start_row = 1 # 从第 2 行开始 (0-based index 1)
    start_col = 1 # 从 B 列开始 (0-based index 1)
    current_row_index = start_row
    current_col_index = start_col
    plot_count_in_row = 0

    # 默认图像选项
    default_img_opts = {
        'object_position': 1,
        'x_scale': 0.5, # 箱形图可能需要不同缩放
        'y_scale': 0.5
    }
    if image_options:
        default_img_opts.update(image_options)

    # -- 遍历并绘图插入 --
    logger.info(f"开始为 Lot '{cp_lot.lot_id}' 的参数 '{param_id}' 绘制箱形图并插入 Excel..."
                f" (每行 {cols_per_row} 个图)")
    
    # 添加总标题
    worksheet.write_string(0, 0, f"Parameter: {param_info.display_name if param_info else param_id} Box Plots")
    worksheet.set_row(0, 20) # 增加标题行高
    
    for i, wafer in enumerate(cp_lot.wafers):
        logger.debug(f"正在处理 Wafer {i+1}/{len(cp_lot.wafers)}: {wafer.wafer_id}")
        
        # 绘制单个 wafer 的箱形图
        fig, ax = plot_wafer_boxplot(wafer, param_id, param_info=param_info, ax=None)

        if fig is None:
            logger.warning(f"跳过 Wafer {wafer.wafer_id}，因为无法生成参数 '{param_id}' 的箱形图。")
            # 可以在 Excel 对应位置写入提示信息
            excel_cell = xlsxwriter.utility.xl_rowcol_to_cell(current_row_index, current_col_index)
            worksheet.write_string(current_row_index -1, current_col_index, f"Wafer: {wafer.wafer_id}")
            worksheet.write_string(excel_cell, "Plot Failed")
        else:
            # 保存图像到内存
            img_data = BytesIO()
            try:
                fig.savefig(img_data, format='png', bbox_inches='tight', dpi=100)
                img_data.seek(0)
            except Exception as save_e:
                logger.error(f"保存 Wafer {wafer.wafer_id} 参数 '{param_id}' 箱形图到内存时出错: {save_e}", exc_info=True)
                plt.close(fig)
                excel_cell = xlsxwriter.utility.xl_rowcol_to_cell(current_row_index, current_col_index)
                worksheet.write_string(current_row_index -1, current_col_index, f"Wafer: {wafer.wafer_id}")
                worksheet.write_string(excel_cell, "Save Failed")
                # 即使保存失败，也继续处理下一个 wafer，并更新位置
            else:
                 plt.close(fig) # 关闭 figure 释放内存
                 # 计算插入位置的 Excel 单元格名称
                 excel_cell = xlsxwriter.utility.xl_rowcol_to_cell(current_row_index, current_col_index)
                 logger.debug(f"  插入图像到单元格: {excel_cell}")
    
                 # 插入 Wafer ID (在图像上方一行，即使图像插入失败也要写)
                 try:
                    worksheet.write_string(current_row_index - 1, current_col_index, f"Wafer: {wafer.wafer_id}")
                    worksheet.set_row(current_row_index - 1, 15) # 15 points height
                 except Exception as write_e:
                     logger.warning(f"写入 Wafer ID 到 Excel 时出错: {write_e}")
    
                 # 插入图像
                 try:
                     worksheet.insert_image(excel_cell, f"{wafer.wafer_id}_{param_id}_boxplot.png",
                                            {'image_data': img_data, **default_img_opts})
                 except Exception as insert_e:
                     logger.error(f"插入 Wafer {wafer.wafer_id} 参数 '{param_id}' 箱形图到 Excel 时出错: {insert_e}", exc_info=True)
                     worksheet.write_string(excel_cell, "Insert Failed") # 在单元格写入错误信息

        # 更新下一个图像的插入位置 (无论成功与否都要移动)
        plot_count_in_row += 1
        if plot_count_in_row >= cols_per_row:
            # 换行
            current_row_index += row_step
            current_col_index = start_col
            plot_count_in_row = 0
        else:
            # 同行右移
            current_col_index += col_step

    logger.info("所有 Wafer 处理完毕。")

    # --- 保存 Excel --- 
    try:
        workbook.close() # 保存并关闭
        logger.info(f"成功将参数 '{param_id}' 的箱形图保存到 Excel 文件: '{output_excel_path}' (Sheet: {sheet_name})")
    except Exception as e:
        logger.error(f"保存 Excel 文件 '{output_excel_path}' 时失败: {e}", exc_info=True)

# --- 示例用法 --- 
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    logger.info("运行箱形图绘图模块示例...")

    # --- 创建模拟数据 (复用 wafer_map.py 的模拟数据逻辑) ---
    logger.info("创建模拟 CPLot 数据...")
    lot = CPLot(lot_id="TestLotBP01", product="TestProdBP")
    param_a_info = CPParameter(id='ParamA_BP', group='GrA', display_name='Parameter A', unit='V', sl=2.0, su=8.0)
    param_b_info = CPParameter(id='ParamB_BP', group='GrB', display_name='Parameter B', unit='mA')
    lot.params.extend([param_a_info, param_b_info])

    for i in range(1, 11): # 创建 10 个 Wafer
        wafer_id = f"BP_W{i:02d}"
        size = 100
        x_coords = np.random.randint(1, 11, size=size)
        y_coords = np.random.randint(1, 11, size=size)
        bin_values = np.random.randint(1, 5, size=size)
        param_a_values = np.random.normal(5 + i*0.2, 1.5, size=size) # Wafer 间均值有漂移
        param_b_values = np.random.gamma(2, scale=1.0 + i*0.1, size=size) # Gamma 分布
        
        # 加入 NaN
        nan_indices_a = np.random.choice(size, 5, replace=False)
        nan_indices_b = np.random.choice(size, 8, replace=False)
        param_a_values[nan_indices_a] = np.nan
        param_b_values[nan_indices_b] = np.nan
        bin_values = bin_values.astype(float)
        bin_values[np.random.choice(size, 3, replace=False)] = np.nan

        chip_data = pd.DataFrame({
            'ParamA_BP': param_a_values,
            'ParamB_BP': param_b_values
        })

        wafer = CPWafer(
            wafer_id=wafer_id,
            x=x_coords.astype(float),
            y=y_coords.astype(float),
            bin=bin_values,
            chip_data=chip_data
        )
        lot.wafers.append(wafer)

    logger.info("模拟数据创建完成。")

    # --- 测试绘制箱形图到 Excel --- 
    output_excel_a = "boxplots_ParamA_output.xlsx"
    logger.info(f"开始绘制 ParamA_BP 的箱形图并保存到 {output_excel_a}...")
    plot_parameter_boxplots_to_excel(lot, 'ParamA_BP', output_excel_a, 
                                     cols_per_row=5, 
                                     image_options={'x_scale': 0.4, 'y_scale': 0.4})
    logger.info("ParamA_BP 箱形图绘制完成。")
    
    output_excel_b = "boxplots_ParamB_output.xlsx"
    logger.info(f"开始绘制 ParamB_BP 的箱形图并保存到 {output_excel_b}...")
    plot_parameter_boxplots_to_excel(lot, 'ParamB_BP', output_excel_b, 
                                     cols_per_row=5, 
                                     image_options={'x_scale': 0.4, 'y_scale': 0.4})
    logger.info("ParamB_BP 箱形图绘制完成。")
    
    output_excel_bin = "boxplots_Bin_output.xlsx"
    logger.info(f"开始绘制 Bin 的箱形图并保存到 {output_excel_bin}...")
    plot_parameter_boxplots_to_excel(lot, 'bin', output_excel_bin, 
                                     cols_per_row=5, 
                                     image_options={'x_scale': 0.4, 'y_scale': 0.4})
    logger.info("Bin 箱形图绘制完成。")

    print(f"\n请检查生成的 Excel 文件: '{output_excel_a}', '{output_excel_b}', '{output_excel_bin}'") 