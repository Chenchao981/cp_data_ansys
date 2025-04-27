from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from ..data_models.cp_data import CPParameter, CPWafer, CPLot

class BasePlotter(ABC):
    """基础绘图器抽象类，定义所有CP数据绘图器的通用接口"""
    
    def __init__(self, data=None, fig_size=(10, 6), dpi=100, style='default'):
        """
        初始化绘图器
        
        Args:
            data: 可以是DataFrame、CPLot或其他数据对象
            fig_size: 图表尺寸（宽, 高）
            dpi: 图像分辨率(dots per inch)
            style: matplotlib样式
        """
        self.data = data
        self.fig_size = fig_size
        self.dpi = dpi
        self.style = style
        self.fig = None
        self.ax = None
    
    @abstractmethod
    def plot(self, **kwargs):
        """绘制图表，必须由子类实现"""
        pass
    
    def save_figure(self, file_path, **kwargs):
        """
        保存图表到文件
        
        Args:
            file_path: 保存路径
            **kwargs: 传递给plt.savefig的其他参数
        
        Returns:
            保存是否成功的布尔值
        """
        if self.fig is None:
            raise ValueError("没有图表可以保存，请先调用plot方法")
        
        try:
            self.fig.savefig(file_path, dpi=self.dpi, **kwargs)
            return True
        except Exception as e:
            print(f"保存图表失败: {e}")
            return False
    
    def show(self):
        """显示图表"""
        if self.fig is None:
            raise ValueError("没有图表可以显示，请先调用plot方法")
        
        plt.show()
    
    def close(self):
        """关闭图表"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
    
    def validate_data(self):
        """验证输入数据的有效性"""
        if self.data is None:
            raise ValueError("没有提供数据进行绘图")
        return True
    
    def _get_dataframe(self):
        """根据输入数据类型获取DataFrame"""
        if isinstance(self.data, pd.DataFrame):
            return self.data
        elif isinstance(self.data, CPLot):
            # 假设CPLot对象有to_dataframe方法
            return self.data.to_dataframe()
        else:
            raise TypeError("不支持的数据类型，请提供DataFrame或CPLot对象") 