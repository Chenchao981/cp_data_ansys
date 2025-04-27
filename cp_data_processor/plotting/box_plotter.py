import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from .base_plotter import BasePlotter

class BoxPlotter(BasePlotter):
    """CP数据箱形图绘图器，用于绘制参数的箱形图"""
    
    def __init__(self, data=None, fig_size=(12, 8), dpi=100, style='default'):
        """
        初始化箱形图绘图器
        
        Args:
            data: CP数据，可以是DataFrame、CPLot对象
            fig_size: 图表尺寸（宽, 高）
            dpi: 图像分辨率(dots per inch)
            style: matplotlib样式
        """
        super().__init__(data, fig_size, dpi, style)
    
    def plot(self, parameters=None, by_wafer=False, wafer_column='Wafer', 
             specs=None, show_outliers=True, show_means=True, 
             notch=False, vert=True, title=None, **kwargs):
        """
        绘制箱形图
        
        Args:
            parameters: 要绘制的参数列表，默认为None，表示绘制所有数值型参数
            by_wafer: 是否按晶圆分组绘制
            wafer_column: 晶圆列名
            specs: 参数规格字典，格式为 {parameter: {'LSL': lower_limit, 'USL': upper_limit}}
            show_outliers: 是否显示离群点
            show_means: 是否显示均值
            notch: 是否使用凹口箱形图
            vert: 是否垂直绘制
            title: 图表标题
            **kwargs: 传递给plt.boxplot的其他参数
        
        Returns:
            self，支持链式调用
        """
        self.validate_data()
        df = self._get_dataframe()
        
        # 确定要绘制的参数
        if parameters is None:
            # 排除非数值型列
            exclude_cols = [wafer_column, 'Seq', 'Bin', 'X', 'Y']
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            parameters = [col for col in numeric_cols if col not in exclude_cols]
        
        # 根据by_wafer决定绘图方式
        if by_wafer and wafer_column in df.columns:
            wafers = df[wafer_column].unique()
            n_wafers = len(wafers)
            n_params = len(parameters)
            
            # 创建子图网格
            n_cols = min(3, n_params)
            n_rows = (n_params + n_cols - 1) // n_cols
            
            # 创建图表
            with plt.style.context(self.style):
                self.fig, axes = plt.subplots(n_rows, n_cols, figsize=self.fig_size, dpi=self.dpi)
                self.fig.subplots_adjust(hspace=0.4, wspace=0.4)
                
                # 将axes转换为一维数组
                if n_rows * n_cols > 1:
                    axes = axes.flatten()
                else:
                    axes = [axes]
                
                # 为每个参数绘制箱形图
                for i, param in enumerate(parameters):
                    if i < len(axes):
                        ax = axes[i]
                        
                        # 按晶圆分组数据
                        data_to_plot = [df[df[wafer_column] == wafer][param].dropna() for wafer in wafers]
                        
                        # 绘制箱形图
                        box = ax.boxplot(data_to_plot, labels=wafers, notch=notch, 
                                         vert=vert, patch_artist=True,
                                         showfliers=show_outliers, **kwargs)
                        
                        # 显示均值
                        if show_means:
                            means = [data.mean() for data in data_to_plot]
                            ax.plot(range(1, len(means) + 1), means, 'r*', markersize=8)
                        
                        # 添加规格线
                        if specs and param in specs:
                            if specs[param].get('LSL') is not None:
                                ax.axhline(y=specs[param]['LSL'], color='r', linestyle='--', 
                                           label='LSL' if i == 0 else None)
                            if specs[param].get('USL') is not None:
                                ax.axhline(y=specs[param]['USL'], color='r', linestyle='--', 
                                           label='USL' if i == 0 else None)
                        
                        # 设置轴标签和标题
                        ax.set_title(param)
                        if vert:
                            ax.set_xlabel('晶圆号')
                            ax.set_ylabel('值')
                        else:
                            ax.set_ylabel('晶圆号')
                            ax.set_xlabel('值')
                        
                        # 设置箱形图样式
                        for patch in box['boxes']:
                            patch.set_facecolor('lightblue')
                            patch.set_alpha(0.7)
                
                # 移除多余的子图
                for i in range(len(parameters), len(axes)):
                    self.fig.delaxes(axes[i])
                
                # 设置主标题
                if title:
                    self.fig.suptitle(title, fontsize=16)
                else:
                    self.fig.suptitle('参数箱形图(按晶圆分组)', fontsize=16)
                
                # 添加图例
                if specs:
                    self.fig.legend(loc='lower right')
        else:
            # 不按晶圆分组，只绘制整体参数箱形图
            with plt.style.context(self.style):
                self.fig, self.ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
                
                # 准备绘图数据
                data_to_plot = [df[param].dropna() for param in parameters]
                
                # 绘制箱形图
                box = self.ax.boxplot(data_to_plot, labels=parameters, notch=notch, 
                                     vert=vert, patch_artist=True,
                                     showfliers=show_outliers, **kwargs)
                
                # 显示均值
                if show_means:
                    means = [data.mean() for data in data_to_plot]
                    self.ax.plot(range(1, len(means) + 1), means, 'r*', markersize=8, label='均值')
                
                # 设置轴标签和标题
                if vert:
                    self.ax.set_xlabel('参数')
                    self.ax.set_ylabel('值')
                else:
                    self.ax.set_ylabel('参数')
                    self.ax.set_xlabel('值')
                
                # 设置箱形图样式
                for patch in box['boxes']:
                    patch.set_facecolor('lightblue')
                    patch.set_alpha(0.7)
                
                # 设置标题
                if title:
                    self.ax.set_title(title, fontsize=14)
                else:
                    self.ax.set_title('参数箱形图', fontsize=14)
                
                # 添加图例
                if show_means:
                    self.ax.legend()
        
        plt.tight_layout()
        return self 