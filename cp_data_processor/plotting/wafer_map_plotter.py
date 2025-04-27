import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from .base_plotter import BasePlotter

class WaferMapPlotter(BasePlotter):
    """CP数据晶圆图绘图器，用于绘制晶圆图"""
    
    def __init__(self, data=None, fig_size=(10, 10), dpi=100, style='default'):
        """
        初始化晶圆图绘图器
        
        Args:
            data: CP数据，可以是DataFrame、CPLot对象
            fig_size: 图表尺寸（宽, 高）
            dpi: 图像分辨率(dots per inch)
            style: matplotlib样式
        """
        super().__init__(data, fig_size, dpi, style)
        # 定义默认的颜色映射
        self.default_cmap = LinearSegmentedColormap.from_list('custom_cmap', 
                                                            ['navy', 'blue', 'cyan', 'lime', 'yellow', 'red', 'maroon'])
    
    def plot(self, parameter=None, bin_column='Bin', x_column='X', y_column='Y', 
             wafer_column='Wafer', wafer_id=None, colormap=None, 
             show_colorbar=True, title=None, show_values=False,
             value_format='.2f', marker_size=100, annotate_size=8, **kwargs):
        """
        绘制晶圆图
        
        Args:
            parameter: 要绘制的参数名，如果为None则绘制bin图
            bin_column: bin列名，默认为'Bin'
            x_column: X坐标列名，默认为'X'
            y_column: Y坐标列名，默认为'Y'
            wafer_column: 晶圆列名，默认为'Wafer'
            wafer_id: 要绘制的晶圆ID，默认为None表示绘制第一个晶圆
            colormap: 自定义颜色映射，默认为None使用内置颜色映射
            show_colorbar: 是否显示颜色条，默认为True
            title: 图表标题，默认为None
            show_values: 是否在每个点上显示数值，默认为False
            value_format: 数值格式化字符串，默认为'.2f'
            marker_size: 标记点大小，默认为100
            annotate_size: 标注文字大小，默认为8
            **kwargs: 传递给plt.scatter的其他参数
        
        Returns:
            self，支持链式调用
        """
        self.validate_data()
        df = self._get_dataframe()
        
        # 确保必要的列存在
        required_cols = [x_column, y_column]
        if parameter is None:
            required_cols.append(bin_column)
        else:
            required_cols.append(parameter)
        
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"缺少必要的列: {missing}")
        
        # 过滤特定晶圆的数据
        if wafer_column in df.columns:
            if wafer_id is None:
                wafer_id = df[wafer_column].iloc[0]
            wafer_data = df[df[wafer_column] == wafer_id]
        else:
            wafer_data = df
        
        if len(wafer_data) == 0:
            raise ValueError(f"找不到晶圆ID为{wafer_id}的数据")
        
        # 创建图表
        with plt.style.context(self.style):
            self.fig, self.ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
            
            # 获取用于着色的值
            if parameter is None:
                values = wafer_data[bin_column]
                color_title = 'Bin'
            else:
                values = pd.to_numeric(wafer_data[parameter], errors='coerce')
                color_title = parameter
            
            # 设置颜色映射
            cmap = colormap if colormap else self.default_cmap
            
            # 绘制散点图
            scatter = self.ax.scatter(wafer_data[x_column], wafer_data[y_column], 
                                     c=values, cmap=cmap, s=marker_size, **kwargs)
            
            # 添加颜色条
            if show_colorbar:
                colorbar = self.fig.colorbar(scatter, ax=self.ax)
                colorbar.set_label(color_title)
            
            # 显示数值
            if show_values:
                for i, row in wafer_data.iterrows():
                    x = row[x_column]
                    y = row[y_column]
                    if parameter is None:
                        value = row[bin_column]
                        value_str = str(int(value))
                    else:
                        value = row[parameter]
                        value_str = f"{value:{value_format}}"
                    
                    self.ax.annotate(value_str, (x, y), ha='center', va='center', 
                                    fontsize=annotate_size, color='black')
            
            # 设置轴标签
            self.ax.set_xlabel(x_column)
            self.ax.set_ylabel(y_column)
            
            # 设置标题
            if title:
                self.ax.set_title(title, fontsize=14)
            else:
                if parameter is None:
                    title_text = f"晶圆 {wafer_id} - Bin图"
                else:
                    title_text = f"晶圆 {wafer_id} - {parameter}参数图"
                self.ax.set_title(title_text, fontsize=14)
            
            # 设置坐标轴等比例
            self.ax.set_aspect('equal')
            
            # 反转Y轴以匹配常规晶圆图方向
            self.ax.invert_yaxis()
            
            # 添加网格线
            self.ax.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        return self
    
    def plot_multi_wafers(self, parameter=None, wafers=None, max_wafers=9, 
                         bin_column='Bin', x_column='X', y_column='Y', 
                         wafer_column='Wafer', colormap=None, 
                         show_colorbar=True, title=None, **kwargs):
        """
        绘制多个晶圆的晶圆图
        
        Args:
            parameter: 要绘制的参数名，如果为None则绘制bin图
            wafers: 要绘制的晶圆ID列表，默认为None表示绘制所有晶圆
            max_wafers: 最多绘制的晶圆数，默认为9
            bin_column: bin列名，默认为'Bin'
            x_column: X坐标列名，默认为'X'
            y_column: Y坐标列名，默认为'Y'
            wafer_column: 晶圆列名，默认为'Wafer'
            colormap: 自定义颜色映射，默认为None使用内置颜色映射
            show_colorbar: 是否显示颜色条，默认为True
            title: 图表主标题，默认为None
            **kwargs: 传递给plt.scatter的其他参数
        
        Returns:
            self，支持链式调用
        """
        self.validate_data()
        df = self._get_dataframe()
        
        # 确保晶圆列存在
        if wafer_column not in df.columns:
            raise ValueError(f"找不到晶圆列: {wafer_column}")
        
        # 确定要绘制的晶圆
        all_wafers = df[wafer_column].unique()
        if wafers is None:
            wafers = all_wafers[:max_wafers]
        else:
            # 过滤不存在的晶圆
            wafers = [w for w in wafers if w in all_wafers]
            if len(wafers) == 0:
                raise ValueError("没有找到指定的晶圆")
            # 限制晶圆数量
            wafers = wafers[:max_wafers]
        
        # 创建子图网格
        n_wafers = len(wafers)
        n_cols = min(3, n_wafers)
        n_rows = (n_wafers + n_cols - 1) // n_cols
        
        # 创建图表
        with plt.style.context(self.style):
            self.fig, axes = plt.subplots(n_rows, n_cols, figsize=self.fig_size, dpi=self.dpi)
            self.fig.subplots_adjust(hspace=0.4, wspace=0.4)
            
            # 将axes转换为一维数组
            if n_rows * n_cols > 1:
                axes = axes.flatten()
            else:
                axes = [axes]
            
            # 设置颜色映射
            cmap = colormap if colormap else self.default_cmap
            
            # 确定用于着色的值范围
            if parameter is None:
                all_values = df[bin_column]
                vmin, vmax = all_values.min(), all_values.max()
                color_title = 'Bin'
            else:
                all_values = pd.to_numeric(df[parameter], errors='coerce')
                vmin, vmax = all_values.min(), all_values.max()
                color_title = parameter
            
            # 为每个晶圆绘制晶圆图
            for i, wafer_id in enumerate(wafers):
                if i < len(axes):
                    ax = axes[i]
                    
                    # 获取该晶圆数据
                    wafer_data = df[df[wafer_column] == wafer_id]
                    
                    if len(wafer_data) == 0:
                        ax.text(0.5, 0.5, f"晶圆 {wafer_id}\n无数据", 
                               ha='center', va='center', fontsize=12)
                        ax.axis('off')
                        continue
                    
                    # 获取用于着色的值
                    if parameter is None:
                        values = wafer_data[bin_column]
                    else:
                        values = pd.to_numeric(wafer_data[parameter], errors='coerce')
                    
                    # 绘制散点图
                    scatter = ax.scatter(wafer_data[x_column], wafer_data[y_column], 
                                        c=values, cmap=cmap, vmin=vmin, vmax=vmax, **kwargs)
                    
                    # 设置轴标签和标题
                    ax.set_title(f"晶圆 {wafer_id}")
                    
                    # 设置坐标轴等比例
                    ax.set_aspect('equal')
                    
                    # 反转Y轴以匹配常规晶圆图方向
                    ax.invert_yaxis()
                    
                    # 添加网格线
                    ax.grid(True, linestyle='--', alpha=0.5)
            
            # 移除多余的子图
            for i in range(n_wafers, len(axes)):
                self.fig.delaxes(axes[i])
            
            # 添加颜色条
            if show_colorbar:
                cbar_ax = self.fig.add_axes([0.92, 0.15, 0.02, 0.7])
                colorbar = self.fig.colorbar(scatter, cax=cbar_ax)
                colorbar.set_label(color_title)
            
            # 设置主标题
            if title:
                self.fig.suptitle(title, fontsize=16)
            else:
                if parameter is None:
                    title_text = "晶圆Bin图"
                else:
                    title_text = f"晶圆{parameter}参数图"
                self.fig.suptitle(title_text, fontsize=16)
        
        plt.tight_layout()
        if show_colorbar:
            plt.subplots_adjust(right=0.9)
        
        return self 