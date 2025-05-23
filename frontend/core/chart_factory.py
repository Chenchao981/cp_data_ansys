#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表工厂 - 统一图表创建接口
使用工厂模式管理各种图表类型的创建
"""

from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ChartFactory:
    """图表工厂 - 统一图表创建接口"""
    
    def __init__(self, data_manager):
        """
        初始化图表工厂
        
        Args:
            data_manager: 数据管理器实例
        """
        self.data_manager = data_manager
        self.chart_classes = {}
        
        # 注册可用的图表类型
        self._register_chart_types()
        
        logger.info(f"ChartFactory 初始化完成 - 支持图表类型: {list(self.chart_classes.keys())}")
    
    def _register_chart_types(self):
        """注册图表类型"""
        try:
            # 注册基础图表（用于测试）
            from ..charts.base_chart import TestChart
            self.chart_classes['test'] = TestChart
            
        except Exception as e:
            logger.error(f"注册图表类型失败: {str(e)}")
    
    def get_available_chart_types(self) -> List[str]:
        """获取可用的图表类型"""
        return list(self.chart_classes.keys())
    
    def create_chart(self, chart_type: str, **params):
        """
        创建指定类型的图表
        
        Args:
            chart_type (str): 图表类型
            **params: 图表参数
            
        Returns:
            BaseChart: 图表对象
        """
        if chart_type not in self.chart_classes:
            available_types = ", ".join(self.chart_classes.keys())
            raise ValueError(f"不支持的图表类型: {chart_type}. 可用类型: {available_types}")
        
        try:
            chart_class = self.chart_classes[chart_type]
            chart = chart_class(self.data_manager, **params)
            
            logger.info(f"创建图表成功: {chart_type}, 参数: {params}")
            return chart
            
        except Exception as e:
            logger.error(f"创建图表失败: {chart_type}, 错误: {str(e)}")
            raise


def main():
    """测试图表工厂"""
    print("=== ChartFactory 测试 ===")
    
    # 模拟数据管理器
    class MockDataManager:
        def get_data(self, data_type, lot_id=None, **kwargs):
            import pandas as pd
            return pd.DataFrame({'test': [1, 2, 3, 4, 5]})
    
    # 创建图表工厂
    data_manager = MockDataManager()
    factory = ChartFactory(data_manager)
    
    # 显示可用图表类型
    print(f"可用图表类型: {factory.get_available_chart_types()}")
    
    # 测试创建图表
    try:
        test_chart = factory.create_chart('test', lot_id='TEST_LOT')
        print(f"创建成功: {test_chart.__class__.__name__}")
        test_chart.close()
    except Exception as e:
        print(f"创建失败: {str(e)}")
    
    print("=== ChartFactory 测试完成 ===")


if __name__ == "__main__":
    main() 