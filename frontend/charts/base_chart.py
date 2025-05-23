#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表基类 - 定义统一的图表接口
所有具体图表类都应继承此基类
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseChart(ABC):
    """图表基类 - 定义统一接口"""
    
    def __init__(self, data_manager, lot_id: Optional[str] = None, **params):
        """
        初始化图表
        
        Args:
            data_manager: 数据管理器实例
            lot_id (str): 批次ID
            **params: 图表参数
        """
        self.data_manager = data_manager
        self.lot_id = lot_id
        self.params = params
        self.figure = None
        self.axes = None
        
        # 图表数据
        self.data = {}
        
        # 默认图表设置
        self.default_figsize = (12, 8)
        self.default_dpi = 300
        self.default_style = 'whitegrid'
        
        # 设置图表样式
        self._setup_style()
        
        logger.info(f"{self.__class__.__name__} 初始化 - 批次: {lot_id}")
    
    def _setup_style(self):
        """设置图表样式"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置seaborn样式
        sns.set_style(self.default_style)
        sns.set_palette("husl")
    
    @abstractmethod
    def load_required_data(self) -> bool:
        """
        加载图表所需数据 - 子类必须实现
        
        Returns:
            bool: 是否成功加载数据
        """
        pass
    
    @abstractmethod
    def generate(self) -> bool:
        """
        生成图表 - 子类必须实现
        
        Returns:
            bool: 是否成功生成图表
        """
        pass
    
    def save(self, output_dir: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        保存图表
        
        Args:
            output_dir (str): 输出目录
            filename (str): 文件名（可选）
            
        Returns:
            Path: 保存路径，失败返回None
        """
        try:
            # 确保图表已生成
            if self.figure is None:
                logger.info("图表未生成，开始生成...")
                if not self.generate():
                    logger.error("图表生成失败")
                    return None
            
            # 生成文件名
            if filename is None:
                filename = self._generate_filename()
            
            # 确保输出目录存在
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 完整文件路径
            file_path = output_path / filename
            
            # 保存图表
            self.figure.savefig(
                file_path, 
                dpi=self.default_dpi, 
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            
            logger.info(f"图表已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存图表失败: {str(e)}")
            return None
    
    def _generate_filename(self) -> str:
        """生成文件名"""
        chart_name = self.__class__.__name__.replace('Chart', '').lower()
        if self.lot_id:
            return f"{chart_name}_{self.lot_id}.png"
        else:
            return f"{chart_name}.png"
    
    def show(self):
        """显示图表"""
        if self.figure is None:
            logger.info("图表未生成，开始生成...")
            if not self.generate():
                logger.error("图表生成失败")
                return
        
        plt.show()
    
    def close(self):
        """关闭图表，释放内存"""
        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None
            self.axes = None
            logger.debug(f"{self.__class__.__name__} 图表已关闭")
    
    def get_data_info(self) -> Dict[str, Any]:
        """获取数据信息"""
        info = {
            "chart_type": self.__class__.__name__,
            "lot_id": self.lot_id,
            "params": self.params,
            "data_loaded": len(self.data) > 0,
            "figure_created": self.figure is not None
        }
        
        # 添加数据详情
        if self.data:
            info["data_info"] = {}
            for key, df in self.data.items():
                if isinstance(df, pd.DataFrame):
                    info["data_info"][key] = {
                        "shape": df.shape,
                        "columns": list(df.columns)
                    }
        
        return info
    
    def _create_figure(self, figsize: Optional[Tuple[float, float]] = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        创建图表画布
        
        Args:
            figsize: 图表大小
            
        Returns:
            Tuple[Figure, Axes]: 图表对象和坐标轴
        """
        if figsize is None:
            figsize = self.default_figsize
        
        fig, ax = plt.subplots(figsize=figsize)
        self.figure = fig
        self.axes = ax
        
        return fig, ax
    
    def _add_title_and_labels(self, title: str, xlabel: str = "", ylabel: str = ""):
        """添加标题和标签"""
        if self.axes is None:
            logger.warning("坐标轴未初始化，无法添加标题和标签")
            return
        
        if title:
            self.axes.set_title(title, fontsize=14, fontweight='bold', pad=20)
        if xlabel:
            self.axes.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            self.axes.set_ylabel(ylabel, fontsize=12)
    
    def _add_grid(self, alpha: float = 0.3):
        """添加网格"""
        if self.axes is None:
            logger.warning("坐标轴未初始化，无法添加网格")
            return
        
        self.axes.grid(True, alpha=alpha)
    
    def _add_legend(self, loc: str = 'best'):
        """添加图例"""
        if self.axes is None:
            logger.warning("坐标轴未初始化，无法添加图例")
            return
        
        self.axes.legend(loc=loc)
    
    def _format_axes(self):
        """格式化坐标轴"""
        if self.axes is None:
            return
        
        # 设置坐标轴样式
        self.axes.tick_params(axis='both', which='major', labelsize=10)
        
        # 紧凑布局
        if self.figure is not None:
            self.figure.tight_layout()


class TestChart(BaseChart):
    """测试图表类 - 用于验证基类功能"""
    
    def load_required_data(self) -> bool:
        """加载测试数据"""
        try:
            # 创建测试数据
            test_data = pd.DataFrame({
                'x': range(10),
                'y': [i**2 for i in range(10)],
                'category': ['A', 'B'] * 5
            })
            self.data['test'] = test_data
            logger.info(f"测试数据加载成功: {test_data.shape}")
            return True
        except Exception as e:
            logger.error(f"加载测试数据失败: {str(e)}")
            return False
    
    def generate(self) -> bool:
        """生成测试图表"""
        try:
            # 加载数据
            if not self.load_required_data():
                return False
            
            # 创建图表
            fig, ax = self._create_figure()
            
            # 绘制测试图表
            test_data = self.data['test']
            ax.plot(test_data['x'], test_data['y'], 'o-', label='测试数据')
            
            # 添加标题和标签
            self._add_title_and_labels(
                title="测试图表 - BaseChart验证",
                xlabel="X值",
                ylabel="Y值"
            )
            
            # 添加网格和图例
            self._add_grid()
            self._add_legend()
            
            # 格式化坐标轴
            self._format_axes()
            
            logger.info("测试图表生成成功")
            return True
            
        except Exception as e:
            logger.error(f"生成测试图表失败: {str(e)}")
            return False


def main():
    """测试图表基类"""
    print("=== BaseChart 测试 ===")
    
    # 模拟数据管理器
    class MockDataManager:
        def get_data(self, data_type, lot_id=None, **kwargs):
            return pd.DataFrame({'test': [1, 2, 3]})
    
    # 创建测试图表
    print("\n1. 创建测试图表")
    data_manager = MockDataManager()
    chart = TestChart(data_manager, lot_id="TEST_LOT")
    
    # 显示图表信息
    print("\n2. 图表信息:")
    info = chart.get_data_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # 生成图表
    print("\n3. 生成图表:")
    success = chart.generate()
    print(f"   生成结果: {'成功' if success else '失败'}")
    
    # 显示更新后的信息
    if success:
        print("\n4. 生成后图表信息:")
        info = chart.get_data_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
    
    # 保存图表
    print("\n5. 保存图表:")
    output_dir = "./test_charts"
    saved_path = chart.save(output_dir)
    if saved_path:
        print(f"   保存成功: {saved_path}")
    else:
        print("   保存失败")
    
    # 关闭图表
    print("\n6. 关闭图表")
    chart.close()
    
    print("\n=== BaseChart 测试完成 ===")


if __name__ == "__main__":
    main() 