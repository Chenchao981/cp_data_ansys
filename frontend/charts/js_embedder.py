#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JavaScript嵌入工具模块
用于将本地JavaScript库文件嵌入到HTML中，避免CDN加载失败问题
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class JSEmbedder:
    """JavaScript嵌入器类"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化JavaScript嵌入器
        
        Args:
            project_root: 项目根目录，如果为None则自动检测
        """
        if project_root is None:
            # 自动检测项目根目录
            current_file = Path(__file__)
            # 从frontend/charts/js_embedder.py向上找到项目根目录
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)
            
        self.plotly_js_path = self.project_root / "plotly.min.js"
        self._plotly_js_content = None
        
    def get_plotly_js_content(self) -> Optional[str]:
        """
        获取Plotly.js的内容
        
        Returns:
            str: Plotly.js的完整内容，如果文件不存在则返回None
        """
        if self._plotly_js_content is not None:
            return self._plotly_js_content
            
        try:
            if not self.plotly_js_path.exists():
                logger.error(f"Plotly.js文件不存在: {self.plotly_js_path}")
                return None
                
            with open(self.plotly_js_path, 'r', encoding='utf-8') as f:
                self._plotly_js_content = f.read()
                
            logger.info(f"成功加载Plotly.js文件，大小: {len(self._plotly_js_content)} 字符")
            return self._plotly_js_content
            
        except Exception as e:
            logger.error(f"读取Plotly.js文件失败: {e}")
            return None
    
    def get_embedded_plotly_js(self) -> str:
        """
        获取用于include_plotlyjs参数的内嵌JavaScript内容
        
        Returns:
            str: 可直接用于fig.write_html()的include_plotlyjs参数值
                 如果加载失败则返回True（使用默认CDN）
        """
        js_content = self.get_plotly_js_content()
        if js_content is None:
            logger.warning("无法加载本地Plotly.js，将使用默认CDN")
            return True
            
        # 返回完整的JavaScript内容，Plotly会将其嵌入到HTML中
        return js_content
    
    def is_plotly_js_available(self) -> bool:
        """
        检查Plotly.js文件是否可用
        
        Returns:
            bool: True如果文件存在且可读取
        """
        return self.plotly_js_path.exists() and self.plotly_js_path.is_file()

# 创建全局实例
_js_embedder = JSEmbedder()

def get_embedded_plotly_js() -> str:
    """
    便捷函数：获取嵌入式Plotly.js内容
    
    Returns:
        str: 可直接用于fig.write_html()的include_plotlyjs参数值
    """
    return _js_embedder.get_embedded_plotly_js()

def is_plotly_js_available() -> bool:
    """
    便捷函数：检查Plotly.js是否可用
    
    Returns:
        bool: True如果本地Plotly.js可用
    """
    return _js_embedder.is_plotly_js_available() 