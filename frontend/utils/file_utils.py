#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件工具模块
提供文件操作、路径处理等工具功能
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict
import logging
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)

class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(dir_path: str) -> Path:
        """
        确保目录存在，不存在则创建
        
        Args:
            dir_path (str): 目录路径
            
        Returns:
            Path: 目录路径对象
        """
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"确保目录存在: {path}")
        return path
    
    @staticmethod  
    def ensure_directory(dir_path: str) -> Path:
        """
        确保目录存在，不存在则创建（ensure_dir的别名）
        
        Args:
            dir_path (str): 目录路径
            
        Returns:
            Path: 目录路径对象
        """
        return FileUtils.ensure_dir(dir_path)
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        列出目录中匹配模式的文件
        
        Args:
            directory (str): 目录路径
            pattern (str): 文件模式，默认"*"
            recursive (bool): 是否递归搜索，默认False
            
        Returns:
            List[Path]: 匹配的文件列表
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"目录不存在: {directory}")
                return []
            
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            # 只返回文件，不返回目录
            files = [f for f in files if f.is_file()]
            
            logger.debug(f"在 {directory} 中找到 {len(files)} 个匹配文件")
            return files
            
        except Exception as e:
            logger.error(f"列出文件时出错: {str(e)}")
            return []
    
    @staticmethod
    def copy_file(src: str, dst: str, create_dirs: bool = True) -> bool:
        """
        复制文件
        
        Args:
            src (str): 源文件路径
            dst (str): 目标文件路径
            create_dirs (bool): 是否创建目标目录，默认True
            
        Returns:
            bool: 是否成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                logger.error(f"源文件不存在: {src}")
                return False
            
            if create_dirs:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, dst_path)
            logger.info(f"文件复制成功: {src} -> {dst}")
            return True
            
        except Exception as e:
            logger.error(f"复制文件时出错: {str(e)}")
            return False
    
    @staticmethod
    def move_file(src: str, dst: str, create_dirs: bool = True) -> bool:
        """
        移动文件
        
        Args:
            src (str): 源文件路径
            dst (str): 目标文件路径
            create_dirs (bool): 是否创建目标目录，默认True
            
        Returns:
            bool: 是否成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                logger.error(f"源文件不存在: {src}")
                return False
            
            if create_dirs:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            logger.info(f"文件移动成功: {src} -> {dst}")
            return True
            
        except Exception as e:
            logger.error(f"移动文件时出错: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str, safe_mode: bool = True) -> bool:
        """
        删除文件
        
        Args:
            file_path (str): 文件路径
            safe_mode (bool): 安全模式，默认True（不删除系统文件）
            
        Returns:
            bool: 是否成功
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return True  # 文件不存在视为删除成功
            
            if safe_mode:
                # 安全检查：不删除系统重要文件
                if path.is_absolute() and len(path.parts) < 3:
                    logger.error(f"拒绝删除系统路径下的文件: {file_path}")
                    return False
            
            path.unlink()
            logger.info(f"文件删除成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"删除文件时出错: {str(e)}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict]:
        """
        获取文件信息
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Dict: 文件信息字典，失败返回None
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return None
            
            stat = path.stat()
            
            info = {
                'name': path.name,
                'stem': path.stem,
                'suffix': path.suffix,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'absolute_path': str(path.absolute())
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取文件信息时出错: {str(e)}")
            return None
    
    @staticmethod
    def generate_unique_filename(base_path: str, extension: str = None) -> str:
        """
        生成唯一的文件名（如果文件已存在，添加数字后缀）
        
        Args:
            base_path (str): 基础路径
            extension (str): 文件扩展名，可选
            
        Returns:
            str: 唯一的文件路径
        """
        try:
            path = Path(base_path)
            
            if extension:
                path = path.with_suffix(extension)
            
            if not path.exists():
                return str(path)
            
            # 文件已存在，生成唯一名称
            stem = path.stem
            suffix = path.suffix
            parent = path.parent
            
            counter = 1
            while True:
                new_name = f"{stem}_{counter:03d}{suffix}"
                new_path = parent / new_name
                if not new_path.exists():
                    logger.debug(f"生成唯一文件名: {new_path}")
                    return str(new_path)
                counter += 1
                
                # 防止无限循环
                if counter > 999:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_name = f"{stem}_{timestamp}{suffix}"
                    new_path = parent / new_name
                    return str(new_path)
            
        except Exception as e:
            logger.error(f"生成唯一文件名时出错: {str(e)}")
            # 返回带时间戳的文件名作为fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_path = Path(base_path).with_name(f"{Path(base_path).stem}_{timestamp}")
            if extension:
                fallback_path = fallback_path.with_suffix(extension)
            return str(fallback_path)
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename (str): 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # Windows文件名非法字符
        illegal_chars = '<>:"|?*'
        
        # 替换非法字符
        clean_name = filename
        for char in illegal_chars:
            clean_name = clean_name.replace(char, '_')
        
        # 替换路径分隔符
        clean_name = clean_name.replace('/', '_').replace('\\', '_')
        
        # 移除前后空格
        clean_name = clean_name.strip()
        
        # 确保不为空
        if not clean_name:
            clean_name = "unnamed_file"
        
        logger.debug(f"文件名清理: '{filename}' -> '{clean_name}'")
        return clean_name
    
    @staticmethod
    def get_directory_size(directory: str) -> Dict:
        """
        获取目录大小信息
        
        Args:
            directory (str): 目录路径
            
        Returns:
            Dict: 目录大小信息
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists() or not dir_path.is_dir():
                return {'total_size': 0, 'file_count': 0, 'error': '目录不存在或不是有效目录'}
            
            total_size = 0
            file_count = 0
            
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'directory': str(dir_path.absolute())
            }
            
        except Exception as e:
            logger.error(f"获取目录大小时出错: {str(e)}")
            return {'total_size': 0, 'file_count': 0, 'error': str(e)}


def main():
    """测试文件工具"""
    print("=== 文件工具测试 ===")
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 测试目录确保
    test_dir = "./test_output"
    FileUtils.ensure_dir(test_dir)
    print(f"创建测试目录: {test_dir}")
    
    # 测试文件列表
    output_files = FileUtils.list_files("../output", "*.csv")
    print(f"Output目录中的CSV文件: {len(output_files)}个")
    for f in output_files[:3]:  # 只显示前3个
        print(f"  {f.name}")
    
    # 测试文件信息
    if output_files:
        file_info = FileUtils.get_file_info(str(output_files[0]))
        if file_info:
            print(f"\n文件信息示例:")
            print(f"  名称: {file_info['name']}")
            print(f"  大小: {file_info['size_mb']} MB")
            print(f"  修改时间: {file_info['modified']}")
    
    # 测试目录大小
    dir_size = FileUtils.get_directory_size("../output")
    print(f"\nOutput目录大小: {dir_size['total_size_mb']} MB, {dir_size['file_count']} 个文件")
    
    # 测试文件名清理
    test_names = ["FA54-5339@203", "test<file>name", "normal_file"]
    print(f"\n文件名清理测试:")
    for name in test_names:
        clean = FileUtils.clean_filename(name)
        print(f"  '{name}' -> '{clean}'")


# 便捷的模块级别函数
def ensure_directory(dir_path: str) -> Path:
    """
    确保目录存在，不存在则创建（模块级别便捷函数）
    
    Args:
        dir_path (str): 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    return FileUtils.ensure_directory(dir_path)


if __name__ == "__main__":
    main() 