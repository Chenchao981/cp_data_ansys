#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT公司目录结构检测器

基于HH公司的目录检测逻辑，专门适配JT公司的Excel文件格式。
支持与HH公司完全一致的目录处理逻辑：
- 单批次：浏览到 .\data\jetech\FA44-4149\ 自动处理该批次
- 多批次：浏览到 .\data\jetech\ 自动处理所有子批次

作者: CP Data Analysis Team
版本: 1.0.0
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Union

# 设置日志
logger = logging.getLogger(__name__)


class JTDirectoryDetector:
    """
    JT公司目录结构检测器
    
    完全复制HH公司的目录检测逻辑，但适配JT的Excel文件格式。
    
    功能：
    - 自动检测单层/双层目录结构
    - 文件夹递归处理（最多2层）
    - 批次识别和文件收集
    """
    
    def __init__(self):
        """初始化目录检测器"""
        self.logger = logging.getLogger(f"{__name__}.JTDirectoryDetector")
        self.supported_extensions = ['.xls', '.xlsx']
        
    def detect_directory_structure(self, directory_path: str) -> Tuple[str, Union[str, List[str]]]:
        """
        检测目录结构类型（完全复制HH公司逻辑）
        
        Args:
            directory_path: 输入目录路径
            
        Returns:
            tuple: (structure_type, batch_info)
            - structure_type: 'single', 'double', 或 'none'
            - batch_info: 单层时为目录名，双层时为子目录列表
        """
        directory_path = os.path.abspath(directory_path)
        
        # 检查当前目录是否直接包含JT Excel文件
        has_excel_files_in_current = False
        has_subdirs_with_excel = False
        subdirs_with_excel = []
        
        self.logger.info(f"检测目录结构: {directory_path}")
        
        # 检查当前目录中的直接文件
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and self._is_jt_excel_file(file):
                has_excel_files_in_current = True
                self.logger.debug(f"在当前目录找到JT Excel文件: {file}")
                break
        
        # 如果当前目录没有Excel文件，检查子目录
        if not has_excel_files_in_current:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    # 检查子目录中是否有JT Excel文件
                    subdir_has_excel = False
                    try:
                        for file in os.listdir(item_path):
                            if self._is_jt_excel_file(file):
                                subdir_has_excel = True
                                self.logger.debug(f"在子目录 {item} 找到JT Excel文件: {file}")
                                break
                    except PermissionError:
                        self.logger.warning(f"无法访问子目录: {item_path}")
                        continue
                    
                    if subdir_has_excel:
                        has_subdirs_with_excel = True
                        subdirs_with_excel.append(item)
        
        # 根据检测结果返回结构类型
        if has_excel_files_in_current:
            # 单层结构：当前目录直接包含JT Excel文件
            dir_name = os.path.basename(directory_path)
            self.logger.info(f"✅ 检测到单层结构，批次文件夹: {dir_name}")
            return 'single', dir_name
        elif has_subdirs_with_excel:
            # 双层结构：子目录包含JT Excel文件
            self.logger.info(f"✅ 检测到双层结构，{len(subdirs_with_excel)}个批次: {subdirs_with_excel}")
            return 'double', subdirs_with_excel
        else:
            # 没有找到JT Excel文件
            self.logger.warning(f"❌ 未找到JT Excel文件")
            return 'none', None
    
    def _is_jt_excel_file(self, filename: str) -> bool:
        """
        检查文件是否为JT格式的Excel文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否为JT Excel文件
        """
        # 检查文件扩展名
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_extensions:
            return False
        
        # 可以添加更多的JT文件特征检查（如文件名模式）
        # 当前简化为只检查扩展名
        return True
    
    def collect_excel_files(self, directory_path: str) -> List[str]:
        """
        收集指定目录下的所有JT Excel文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            List[str]: Excel文件路径列表
        """
        excel_files = []
        
        try:
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path) and self._is_jt_excel_file(file):
                    excel_files.append(file_path)
                    self.logger.debug(f"收集到Excel文件: {file}")
        except Exception as e:
            self.logger.error(f"收集Excel文件失败: {e}")
        
        self.logger.info(f"在 {directory_path} 中收集到 {len(excel_files)} 个Excel文件")
        return excel_files
    
    def extract_lot_id_from_folder_name(self, folder_name: str) -> Tuple[str, str]:
        """
        从文件夹名称中提取产品名和批次ID
        
        JT格式示例：FA44-4149
        - product_name: FA44-4149 （简化：直接使用文件夹名）
        - lot_id: FA44-4149
        
        Args:
            folder_name: 文件夹名称
            
        Returns:
            tuple: (product_name, lot_id)
        """
        try:
            # JT公司简化规则：文件夹名即为批次ID
            lot_id = folder_name
            product_name = folder_name  # 简化处理，产品名=批次ID
            
            self.logger.info(f"JT批次识别: 文件夹={folder_name} → 产品名={product_name}, 批次ID={lot_id}")
            return product_name, lot_id
            
        except Exception as e:
            self.logger.error(f"提取批次ID失败: {e}")
            return folder_name, folder_name
    
    def scan_and_process_directory(self, input_path: str) -> List[dict]:
        """
        扫描目录并准备处理信息（主要接口）
        
        完全复制HH公司的处理逻辑：
        - 单批次：返回该批次的处理信息
        - 多批次：返回所有子批次的处理信息列表
        
        Args:
            input_path: 输入路径（可以是文件夹或文件）
            
        Returns:
            List[dict]: 处理信息列表，每个dict包含：
                - batch_name: 批次名称
                - lot_id: 批次ID
                - product_name: 产品名称
                - excel_files: Excel文件路径列表
                - source_directory: 源目录路径
        """
        processing_info = []
        
        # 如果输入是文件，直接处理
        if os.path.isfile(input_path):
            self.logger.info(f"输入为文件，直接处理: {input_path}")
            folder_name = os.path.basename(os.path.dirname(input_path))
            product_name, lot_id = self.extract_lot_id_from_folder_name(folder_name)
            
            processing_info.append({
                'batch_name': folder_name,
                'lot_id': lot_id,
                'product_name': product_name,
                'excel_files': [input_path],
                'source_directory': os.path.dirname(input_path)
            })
            return processing_info
        
        # 如果输入是目录，检测结构
        if not os.path.isdir(input_path):
            raise ValueError(f"输入路径不存在或无效: {input_path}")
        
        structure_type, batch_info = self.detect_directory_structure(input_path)
        
        if structure_type == 'single':
            # 单层结构：浏览到具体批次文件夹
            batch_name = batch_info
            product_name, lot_id = self.extract_lot_id_from_folder_name(batch_name)
            excel_files = self.collect_excel_files(input_path)
            
            if excel_files:
                processing_info.append({
                    'batch_name': batch_name,
                    'lot_id': lot_id,
                    'product_name': product_name,
                    'excel_files': excel_files,
                    'source_directory': input_path
                })
                self.logger.info(f"✅ 单批次处理准备完成: {batch_name}, {len(excel_files)}个文件")
            else:
                self.logger.warning(f"❌ 批次 {batch_name} 中未找到Excel文件")
        
        elif structure_type == 'double':
            # 双层结构：浏览到上级目录，处理所有子批次
            subdirs = batch_info
            
            for subdir in subdirs:
                subdir_path = os.path.join(input_path, subdir)
                product_name, lot_id = self.extract_lot_id_from_folder_name(subdir)
                excel_files = self.collect_excel_files(subdir_path)
                
                if excel_files:
                    processing_info.append({
                        'batch_name': subdir,
                        'lot_id': lot_id,
                        'product_name': product_name,
                        'excel_files': excel_files,
                        'source_directory': subdir_path
                    })
                    self.logger.info(f"✅ 子批次处理准备完成: {subdir}, {len(excel_files)}个文件")
                else:
                    self.logger.warning(f"❌ 子批次 {subdir} 中未找到Excel文件")
        
        elif structure_type == 'none':
            self.logger.error(f"❌ 在 {input_path} 中未找到JT Excel文件")
            raise ValueError(f"未找到JT Excel文件: {input_path}")
        
        self.logger.info(f"🎯 目录扫描完成，准备处理 {len(processing_info)} 个批次")
        return processing_info


def scan_jt_directory(input_path: str) -> List[dict]:
    """
    JT目录扫描的便捷函数
    
    Args:
        input_path: 输入路径
        
    Returns:
        List[dict]: 处理信息列表
    """
    detector = JTDirectoryDetector()
    return detector.scan_and_process_directory(input_path)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        print(f"测试JT目录检测: {test_path}")
        
        try:
            detector = JTDirectoryDetector()
            result = detector.scan_and_process_directory(test_path)
            
            print(f"检测结果: {len(result)} 个批次")
            for info in result:
                print(f"  批次: {info['batch_name']}")
                print(f"  Lot ID: {info['lot_id']}")
                print(f"  文件数: {len(info['excel_files'])}")
                print(f"  源目录: {info['source_directory']}")
                print()
        except Exception as e:
            print(f"检测失败: {e}")
    else:
        print("用法: python jt_directory_detector.py <directory_path>")