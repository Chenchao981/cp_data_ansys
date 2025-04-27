"""
MAP格式化模块，用于CP测试数据的晶圆MAP图条件格式化和可视化处理。
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, List, Optional, Tuple, Union, Callable
import seaborn as sns

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter


class MapFormatter:
    """
    MAP格式化类，用于生成晶圆MAP图的颜色映射和可视化。
    
    主要功能：
    1. 创建参数数值的颜色映射方案
    2. 格式化晶圆MAP数据
    3. 生成晶圆MAP图可视化
    """
    
    def __init__(self, cp_lot: CPLot):
        """
        初始化MAP格式化器
        
        Args:
            cp_lot: 要处理的 CPLot 对象
        """
        self.cp_lot = cp_lot
        self.color_maps = {
            'default': plt.cm.viridis,
            'diverging': plt.cm.coolwarm,
            'sequential': plt.cm.plasma,
            'qualitative': plt.cm.tab10,
            'pass_fail': mcolors.ListedColormap(['red', 'green'])
        }
    
    def create_wafer_map(self, 
                         wafer_id: str, 
                         param_id: str, 
                         cmap: str = 'default',
                         title: Optional[str] = None,
                         figsize: Tuple[int, int] = (10, 8),
                         show_colorbar: bool = True,
                         vmin: Optional[float] = None,
                         vmax: Optional[float] = None) -> plt.Figure:
        """
        创建单个晶圆的参数MAP图
        
        Args:
            wafer_id: 晶圆ID
            param_id: 参数ID
            cmap: 颜色映射方案名称
            title: 图表标题
            figsize: 图表尺寸
            show_colorbar: 是否显示颜色条
            vmin: 颜色映射最小值
            vmax: 颜色映射最大值
        
        Returns:
            plt.Figure: matplotlib图表对象
        """
        # 获取晶圆对象
        wafer = None
        for w in self.cp_lot.wafers:
            if w.id == wafer_id:
                wafer = w
                break
                
        if wafer is None:
            print(f"未找到晶圆 {wafer_id}")
            return None
        
        # 获取参数对象
        param = None
        for p in self.cp_lot.params:
            if p.id == param_id:
                param = p
                break
        
        if param is None:
            print(f"未找到参数 {param_id}")
            return None
        
        # 获取晶圆数据
        if wafer.data is None or wafer.data.empty:
            print(f"晶圆 {wafer_id} 没有数据")
            return None
        
        if param_id not in wafer.data.columns:
            print(f"晶圆 {wafer_id} 中没有参数 {param_id} 的数据")
            return None
        
        # 提取坐标和参数值
        data = wafer.data.copy()
        
        # 检查是否有 X 和 Y 坐标列
        if 'X' not in data.columns or 'Y' not in data.columns:
            print("晶圆数据中缺少 X 或 Y 坐标列")
            return None
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize)
        
        # 获取颜色映射
        colormap = self.color_maps.get(cmap, self.color_maps['default'])
        
        # 确定颜色范围
        if vmin is None:
            vmin = data[param_id].min()
        if vmax is None:
            vmax = data[param_id].max()
        
        # 创建散点图
        scatter = ax.scatter(
            data['X'], 
            data['Y'], 
            c=data[param_id],
            cmap=colormap,
            s=100,  # 点大小
            alpha=0.8,
            vmin=vmin,
            vmax=vmax,
            edgecolors='k',
            linewidths=0.5
        )
        
        # 设置图表标题和标签
        if title:
            ax.set_title(title, fontsize=14)
        else:
            ax.set_title(f"晶圆 {wafer_id} - {param_id} ({param.unit if param.unit else ''})", fontsize=14)
        
        ax.set_xlabel('X 坐标', fontsize=12)
        ax.set_ylabel('Y 坐标', fontsize=12)
        
        # 反转 Y 轴使得原点在左下角
        ax.invert_yaxis()
        
        # 设置坐标轴刻度
        ax.set_xticks(sorted(data['X'].unique()))
        ax.set_yticks(sorted(data['Y'].unique()))
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 添加颜色条
        if show_colorbar:
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label(f"{param_id} ({param.unit if param.unit else ''})", fontsize=12)
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def create_lot_map(self, 
                       param_id: str, 
                       cmap: str = 'default',
                       figsize: Tuple[int, int] = (15, 10),
                       cols: int = 3,
                       show_colorbar: bool = True,
                       global_scale: bool = True) -> plt.Figure:
        """
        创建整批晶圆的参数MAP图
        
        Args:
            param_id: 参数ID
            cmap: 颜色映射方案名称
            figsize: 图表总尺寸
            cols: 每行显示的晶圆数
            show_colorbar: 是否显示颜色条
            global_scale: 是否使用全局颜色比例尺
        
        Returns:
            plt.Figure: matplotlib图表对象
        """
        # 获取有效晶圆列表
        valid_wafers = []
        for wafer in self.cp_lot.wafers:
            if wafer.data is not None and not wafer.data.empty:
                if param_id in wafer.data.columns:
                    valid_wafers.append(wafer)
        
        if not valid_wafers:
            print(f"没有包含参数 {param_id} 的有效晶圆")
            return None
        
        # 获取参数对象
        param = None
        for p in self.cp_lot.params:
            if p.id == param_id:
                param = p
                break
        
        if param is None:
            print(f"未找到参数 {param_id}")
            return None
        
        # 计算行数
        rows = (len(valid_wafers) + cols - 1) // cols
        
        # 创建图表
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        
        # 确保axes是二维数组
        if rows == 1 and cols == 1:
            axes = np.array([[axes]])
        elif rows == 1:
            axes = np.array([axes])
        elif cols == 1:
            axes = np.array([[ax] for ax in axes])
        
        # 获取颜色映射
        colormap = self.color_maps.get(cmap, self.color_maps['default'])
        
        # 如果使用全局比例尺，计算所有晶圆的值范围
        if global_scale:
            all_values = []
            for wafer in valid_wafers:
                all_values.extend(wafer.data[param_id].dropna().tolist())
            
            vmin = min(all_values)
            vmax = max(all_values)
        else:
            vmin = None
            vmax = None
        
        # 循环绘制每个晶圆
        for idx, wafer in enumerate(valid_wafers):
            row_idx = idx // cols
            col_idx = idx % cols
            
            ax = axes[row_idx, col_idx]
            
            data = wafer.data.copy()
            
            # 确定当前晶圆的颜色范围
            if not global_scale:
                vmin = data[param_id].min()
                vmax = data[param_id].max()
            
            # 创建散点图
            scatter = ax.scatter(
                data['X'], 
                data['Y'], 
                c=data[param_id],
                cmap=colormap,
                s=80,  # 点大小
                alpha=0.8,
                vmin=vmin,
                vmax=vmax,
                edgecolors='k',
                linewidths=0.5
            )
            
            # 设置图表标题
            ax.set_title(f"晶圆 {wafer.id}", fontsize=12)
            
            # 反转 Y 轴使得原点在左下角
            ax.invert_yaxis()
            
            # 设置坐标轴刻度
            ax.set_xticks(sorted(data['X'].unique()))
            ax.set_yticks(sorted(data['Y'].unique()))
            
            # 添加网格线
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # 隐藏多余的子图
        for idx in range(len(valid_wafers), rows * cols):
            row_idx = idx // cols
            col_idx = idx % cols
            axes[row_idx, col_idx].axis('off')
        
        # 添加全局颜色条
        if show_colorbar:
            # 调整布局，为颜色条腾出空间
            plt.tight_layout()
            fig.subplots_adjust(right=0.9)
            
            # 添加颜色条
            cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
            cbar = fig.colorbar(scatter, cax=cbar_ax)
            cbar.set_label(f"{param_id} ({param.unit if param.unit else ''})", fontsize=12)
        else:
            plt.tight_layout()
        
        # 设置总标题
        fig.suptitle(f"批次 {self.cp_lot.id} - {param_id} MAP图", fontsize=16)
        plt.subplots_adjust(top=0.92)
        
        return fig
    
    def create_pass_fail_map(self, 
                            wafer_id: str, 
                            param_id: str,
                            figsize: Tuple[int, int] = (10, 8),
                            lower_limit: Optional[float] = None,
                            upper_limit: Optional[float] = None) -> plt.Figure:
        """
        创建合格/不合格二值MAP图
        
        Args:
            wafer_id: 晶圆ID
            param_id: 参数ID
            figsize: 图表尺寸
            lower_limit: 下限值，默认使用参数规格
            upper_limit: 上限值，默认使用参数规格
        
        Returns:
            plt.Figure: matplotlib图表对象
        """
        # 获取晶圆对象
        wafer = None
        for w in self.cp_lot.wafers:
            if w.id == wafer_id:
                wafer = w
                break
                
        if wafer is None:
            print(f"未找到晶圆 {wafer_id}")
            return None
        
        # 获取参数对象
        param = None
        for p in self.cp_lot.params:
            if p.id == param_id:
                param = p
                break
        
        if param is None:
            print(f"未找到参数 {param_id}")
            return None
        
        # 获取晶圆数据
        if wafer.data is None or wafer.data.empty:
            print(f"晶圆 {wafer_id} 没有数据")
            return None
        
        if param_id not in wafer.data.columns:
            print(f"晶圆 {wafer_id} 中没有参数 {param_id} 的数据")
            return None
        
        # 使用参数规格如果没有提供限值
        if lower_limit is None:
            lower_limit = param.sl
        
        if upper_limit is None:
            upper_limit = param.su
        
        # 如果没有限值，无法创建合格/不合格图
        if lower_limit is None and upper_limit is None:
            print(f"参数 {param_id} 没有规格限值，无法创建合格/不合格图")
            return None
        
        # 提取坐标和参数值
        data = wafer.data.copy()
        
        # 检查是否有 X 和 Y 坐标列
        if 'X' not in data.columns or 'Y' not in data.columns:
            print("晶圆数据中缺少 X 或 Y 坐标列")
            return None
        
        # 计算合格/不合格
        is_pass = pd.Series(True, index=data.index)
        
        if lower_limit is not None:
            is_pass = is_pass & (data[param_id] >= lower_limit)
        
        if upper_limit is not None:
            is_pass = is_pass & (data[param_id] <= upper_limit)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize)
        
        # 获取颜色映射
        colormap = self.color_maps['pass_fail']
        
        # 创建散点图
        scatter = ax.scatter(
            data['X'], 
            data['Y'], 
            c=is_pass.astype(int),  # 0: 不合格, 1: 合格
            cmap=colormap,
            s=100,  # 点大小
            alpha=0.8,
            vmin=0,
            vmax=1,
            edgecolors='k',
            linewidths=0.5
        )
        
        # 设置图表标题和标签
        limit_text = ""
        if lower_limit is not None and upper_limit is not None:
            limit_text = f"[{lower_limit}, {upper_limit}]"
        elif lower_limit is not None:
            limit_text = f"≥ {lower_limit}"
        elif upper_limit is not None:
            limit_text = f"≤ {upper_limit}"
        
        ax.set_title(f"晶圆 {wafer_id} - {param_id} 合格/不合格图 {limit_text}", fontsize=14)
        ax.set_xlabel('X 坐标', fontsize=12)
        ax.set_ylabel('Y 坐标', fontsize=12)
        
        # 反转 Y 轴使得原点在左下角
        ax.invert_yaxis()
        
        # 设置坐标轴刻度
        ax.set_xticks(sorted(data['X'].unique()))
        ax.set_yticks(sorted(data['Y'].unique()))
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax, ticks=[0.25, 0.75])
        cbar.set_ticklabels(['不合格', '合格'])
        
        # 计算合格率
        pass_rate = is_pass.mean() * 100
        
        # 添加合格率文本
        ax.text(0.02, 0.02, f"合格率: {pass_rate:.2f}%", 
                transform=ax.transAxes, 
                fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def create_wafer_boxplot(self, 
                            param_id: str, 
                            figsize: Tuple[int, int] = (12, 6),
                            show_outliers: bool = True,
                            show_swarm: bool = False) -> plt.Figure:
        """
        创建晶圆箱线图，比较不同晶圆的参数分布
        
        Args:
            param_id: 参数ID
            figsize: 图表尺寸
            show_outliers: 是否显示离群点
            show_swarm: 是否显示分布点
        
        Returns:
            plt.Figure: matplotlib图表对象
        """
        # 获取参数对象
        param = None
        for p in self.cp_lot.params:
            if p.id == param_id:
                param = p
                break
        
        if param is None:
            print(f"未找到参数 {param_id}")
            return None
        
        # 收集各晶圆的参数数据
        wafer_data = {}
        for wafer in self.cp_lot.wafers:
            if wafer.data is not None and not wafer.data.empty:
                if param_id in wafer.data.columns:
                    values = wafer.data[param_id].dropna().values
                    if len(values) > 0:
                        wafer_data[wafer.id] = values
        
        if not wafer_data:
            print(f"没有包含参数 {param_id} 的有效晶圆数据")
            return None
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize)
        
        # 绘制箱线图
        boxplot = ax.boxplot(
            [wafer_data[wafer_id] for wafer_id in sorted(wafer_data.keys())],
            labels=sorted(wafer_data.keys()),
            patch_artist=True,
            showfliers=show_outliers,
            medianprops={'color': 'red', 'linewidth': 1.5},
            boxprops={'facecolor': 'lightblue', 'alpha': 0.8},
            whiskerprops={'linestyle': '--'},
        )
        
        # 如果需要显示分布点
        if show_swarm:
            for i, wafer_id in enumerate(sorted(wafer_data.keys())):
                sns.swarmplot(
                    y=wafer_data[wafer_id],
                    x=[i+1] * len(wafer_data[wafer_id]),
                    ax=ax,
                    size=4,
                    color='navy',
                    alpha=0.5
                )
        
        # 添加规格限值线
        if param.sl is not None:
            ax.axhline(param.sl, color='red', linestyle='--', alpha=0.7, label=f'下限: {param.sl}')
        
        if param.su is not None:
            ax.axhline(param.su, color='orange', linestyle='--', alpha=0.7, label=f'上限: {param.su}')
        
        # 设置图表标题和标签
        ax.set_title(f"批次 {self.cp_lot.id} - {param_id} 晶圆箱线图", fontsize=14)
        ax.set_xlabel('晶圆ID', fontsize=12)
        ax.set_ylabel(f"{param_id} ({param.unit if param.unit else ''})", fontsize=12)
        
        # 添加图例
        if param.sl is not None or param.su is not None:
            ax.legend()
        
        # 旋转 x 轴标签
        plt.xticks(rotation=45)
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def save_map_to_file(self, fig: plt.Figure, filename: str, dpi: int = 300) -> None:
        """
        保存图表到文件
        
        Args:
            fig: matplotlib图表对象
            filename: 文件名
            dpi: 分辨率
        """
        if fig is not None:
            fig.savefig(filename, dpi=dpi, bbox_inches='tight')
            print(f"图表已保存到 {filename}")
        else:
            print("无效的图表对象，无法保存") 