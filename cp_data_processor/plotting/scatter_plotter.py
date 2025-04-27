import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from .base_plotter import BasePlotter

class ScatterPlotter(BasePlotter):
    """CP数据散点图绘图器，用于绘制参数之间的关系"""
    
    def __init__(self, data=None, fig_size=(10, 8), dpi=100, style='default'):
        """
        初始化散点图绘图器
        
        Args:
            data: CP数据，可以是DataFrame、CPLot对象
            fig_size: 图表尺寸（宽, 高）
            dpi: 图像分辨率(dots per inch)
            style: matplotlib样式
        """
        super().__init__(data, fig_size, dpi, style)
    
    def plot(self, x_param, y_param, wafer_column='Wafer', bin_column='Bin', 
             hue=None, color=None, title=None, show_regression=True, 
             alpha=0.7, marker='o', size=50, **kwargs):
        """
        绘制散点图
        
        Args:
            x_param: X轴参数
            y_param: Y轴参数
            wafer_column: 晶圆列名，默认为'Wafer'
            bin_column: bin列名，默认为'Bin'
            hue: 用于对点进行分组的列名，默认为None
            color: 点的颜色，默认为None
            title: 图表标题，默认为None
            show_regression: 是否显示回归线，默认为True
            alpha: 透明度，默认为0.7
            marker: 标记符号，默认为'o'
            size: 点大小，默认为50
            **kwargs: 传递给sns.scatterplot的其他参数
        
        Returns:
            self，支持链式调用
        """
        self.validate_data()
        df = self._get_dataframe()
        
        # 确保参数列存在
        required_cols = [x_param, y_param]
        if hue:
            required_cols.append(hue)
        
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"缺少必要的列: {missing}")
        
        # 创建图表
        with plt.style.context(self.style):
            self.fig, self.ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
            
            # 绘制散点图
            sns.scatterplot(
                data=df,
                x=x_param,
                y=y_param,
                hue=hue,
                color=color,
                alpha=alpha,
                marker=marker,
                s=size,
                ax=self.ax,
                **kwargs
            )
            
            # 添加回归线
            if show_regression:
                sns.regplot(
                    data=df,
                    x=x_param,
                    y=y_param,
                    scatter=False,
                    line_kws={'color': 'red'},
                    ax=self.ax
                )
            
            # 计算相关系数
            correlation = df[[x_param, y_param]].corr().iloc[0, 1]
            
            # 设置标题
            if title:
                self.ax.set_title(title, fontsize=14)
            else:
                self.ax.set_title(f"{x_param} vs {y_param} (r = {correlation:.3f})", fontsize=14)
            
            # 设置轴标签
            self.ax.set_xlabel(x_param)
            self.ax.set_ylabel(y_param)
            
            # 添加网格线
            self.ax.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        return self
    
    def plot_matrix(self, parameters=None, wafer_column='Wafer', bin_column='Bin',
                   hue=None, diag_kind='kde', title=None, **kwargs):
        """
        绘制参数散点图矩阵
        
        Args:
            parameters: 要绘制的参数列表，默认为None表示绘制所有数值型参数
            wafer_column: 晶圆列名，默认为'Wafer'
            bin_column: bin列名，默认为'Bin'
            hue: 用于对点进行分组的列名，默认为None
            diag_kind: 对角线图形类型，'hist'或'kde'，默认为'kde'
            title: 图表标题，默认为None
            **kwargs: 传递给sns.pairplot的其他参数
        
        Returns:
            self，支持链式调用
        """
        self.validate_data()
        df = self._get_dataframe()
        
        # 确定要绘制的参数
        if parameters is None:
            # 排除非数值型列
            exclude_cols = [wafer_column, 'Seq', bin_column, 'X', 'Y']
            if hue:
                exclude_cols.append(hue)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            parameters = [col for col in numeric_cols if col not in exclude_cols]
            
            # 限制参数数量，避免图表过大
            if len(parameters) > 5:
                parameters = parameters[:5]
                print(f"参数过多，仅显示前5个: {parameters}")
        
        # 创建散点图矩阵
        with plt.style.context(self.style):
            # 使用seaborn的pairplot
            g = sns.pairplot(
                df,
                vars=parameters,
                hue=hue,
                diag_kind=diag_kind,
                height=self.fig_size[0] / len(parameters),
                **kwargs
            )
            
            # 设置标题
            if title:
                g.fig.suptitle(title, y=1.02, fontsize=16)
            else:
                g.fig.suptitle("参数相关性矩阵", y=1.02, fontsize=16)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图形对象
            self.fig = g.fig
        
        return self
    
    def plot_by_wafer(self, x_param, y_param, wafer_column='Wafer', bin_column='Bin',
                     wafers=None, max_wafers=9, color=None, show_regression=True,
                     alpha=0.7, marker='o', size=50, **kwargs):
        """
        按晶圆绘制散点图
        
        Args:
            x_param: X轴参数
            y_param: Y轴参数
            wafer_column: 晶圆列名，默认为'Wafer'
            bin_column: bin列名，默认为'Bin'
            wafers: 要绘制的晶圆ID列表，默认为None表示绘制所有晶圆
            max_wafers: 最多绘制的晶圆数，默认为9
            color: 点的颜色，默认为None
            show_regression: 是否显示回归线，默认为True
            alpha: 透明度，默认为0.7
            marker: 标记符号，默认为'o'
            size: 点大小，默认为50
            **kwargs: 传递给sns.scatterplot的其他参数
        
        Returns:
            self，支持链式调用
        """
        self.validate_data()
        df = self._get_dataframe()
        
        # 确保必要的列存在
        required_cols = [x_param, y_param, wafer_column]
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"缺少必要的列: {missing}")
        
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
            
            # 为每个晶圆绘制散点图
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
                    
                    # 绘制散点图
                    sns.scatterplot(
                        data=wafer_data,
                        x=x_param,
                        y=y_param,
                        color=color,
                        alpha=alpha,
                        marker=marker,
                        s=size,
                        ax=ax,
                        **kwargs
                    )
                    
                    # 添加回归线
                    if show_regression:
                        sns.regplot(
                            data=wafer_data,
                            x=x_param,
                            y=y_param,
                            scatter=False,
                            line_kws={'color': 'red'},
                            ax=ax
                        )
                    
                    # 计算相关系数
                    correlation = wafer_data[[x_param, y_param]].corr().iloc[0, 1]
                    
                    # 设置轴标签和标题
                    ax.set_title(f"晶圆 {wafer_id} (r = {correlation:.3f})")
                    ax.set_xlabel(x_param)
                    ax.set_ylabel(y_param)
                    
                    # 添加网格线
                    ax.grid(True, linestyle='--', alpha=0.5)
            
            # 移除多余的子图
            for i in range(n_wafers, len(axes)):
                self.fig.delaxes(axes[i])
            
            # 设置主标题
            title_text = f"{x_param} vs {y_param} 按晶圆分布"
            self.fig.suptitle(title_text, fontsize=16)
        
        plt.tight_layout()
        return self 