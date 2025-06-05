#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能优化配置模块
用于统一管理所有性能相关的配置参数
"""

import os
import psutil
from multiprocessing import cpu_count
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PerformanceConfig:
    """性能优化配置类"""
    
    def __init__(self):
        """初始化性能配置，自动检测硬件配置"""
        # 硬件信息检测
        self.cpu_count = cpu_count()
        self.memory_total_gb = psutil.virtual_memory().total / (1024**3)
        self.memory_available_gb = psutil.virtual_memory().available / (1024**3)
        
        # 基础性能配置
        self._init_basic_config()
        
        # 根据硬件情况自动调整配置
        self._auto_tune_config()
        
        logger.info(f"性能配置初始化完成 - CPU核心数: {self.cpu_count}, 内存: {self.memory_total_gb:.1f}GB")
    
    def _init_basic_config(self):
        """初始化基础配置"""
        # Numba优化配置
        self.ENABLE_NUMBA = True
        self.NUMBA_PARALLEL = True
        self.NUMBA_CACHE = True
        
        # 并行处理配置
        self.ENABLE_PARALLEL = True
        self.MAX_WORKERS = min(self.cpu_count, 8)  # 限制最大工作进程
        self.IO_WORKERS = min(self.cpu_count * 2, 16)  # I/O密集型任务的线程数
        
        # 内存管理配置
        self.MEMORY_LIMIT_MB = 1024  # 默认内存限制1GB
        self.CHUNK_SIZE = 5000  # 数据分块大小
        self.ENABLE_MEMORY_MONITOR = True
        self.GC_THRESHOLD = 0.8  # 内存使用率超过80%时触发垃圾回收
        
        # 缓存配置
        self.ENABLE_CACHE = True
        self.CACHE_SIZE_MB = 256  # 缓存大小限制
        self.CACHE_TTL_SECONDS = 3600  # 缓存过期时间
        
        # 散点数据优化配置
        self.SCATTER_OPTIMIZATION = True
        self.MAX_POINTS_PER_WAFER = 80
        self.MIN_POINTS_PER_WAFER = 50
        
        # 性能监控配置
        self.ENABLE_PROFILING = False  # 默认关闭详细性能分析
        self.LOG_PERFORMANCE = True
        self.PERFORMANCE_REPORT = True
    
    def _auto_tune_config(self):
        """根据硬件配置自动调整参数"""
        # 根据内存大小调整配置
        if self.memory_total_gb >= 16:
            # 高配置机器
            self.MEMORY_LIMIT_MB = 2048
            self.CHUNK_SIZE = 10000
            self.CACHE_SIZE_MB = 512
            self.MAX_POINTS_PER_WAFER = 100
        elif self.memory_total_gb >= 8:
            # 中等配置机器
            self.MEMORY_LIMIT_MB = 1024
            self.CHUNK_SIZE = 5000
            self.CACHE_SIZE_MB = 256
            self.MAX_POINTS_PER_WAFER = 80
        else:
            # 低配置机器
            self.MEMORY_LIMIT_MB = 512
            self.CHUNK_SIZE = 2000
            self.CACHE_SIZE_MB = 128
            self.MAX_POINTS_PER_WAFER = 60
            # 在低配置机器上禁用某些优化以避免内存不足
            if self.memory_total_gb < 4:
                self.ENABLE_PARALLEL = False
                self.ENABLE_CACHE = False
        
        # 根据CPU核心数调整并行配置
        if self.cpu_count <= 2:
            self.MAX_WORKERS = 2
            self.IO_WORKERS = 4
        elif self.cpu_count <= 4:
            self.MAX_WORKERS = 4
            self.IO_WORKERS = 8
        else:
            self.MAX_WORKERS = min(self.cpu_count, 8)
            self.IO_WORKERS = min(self.cpu_count * 2, 16)
        
        logger.info(f"配置已根据硬件自动调整 - 内存限制: {self.MEMORY_LIMIT_MB}MB, 最大工作进程: {self.MAX_WORKERS}")
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取所有配置作为字典"""
        return {
            # 硬件信息
            'hardware': {
                'cpu_count': self.cpu_count,
                'memory_total_gb': self.memory_total_gb,
                'memory_available_gb': self.memory_available_gb,
            },
            
            # Numba配置
            'numba': {
                'enable': self.ENABLE_NUMBA,
                'parallel': self.NUMBA_PARALLEL,
                'cache': self.NUMBA_CACHE,
            },
            
            # 并行处理配置
            'parallel': {
                'enable': self.ENABLE_PARALLEL,
                'max_workers': self.MAX_WORKERS,
                'io_workers': self.IO_WORKERS,
            },
            
            # 内存管理配置
            'memory': {
                'limit_mb': self.MEMORY_LIMIT_MB,
                'chunk_size': self.CHUNK_SIZE,
                'enable_monitor': self.ENABLE_MEMORY_MONITOR,
                'gc_threshold': self.GC_THRESHOLD,
            },
            
            # 缓存配置
            'cache': {
                'enable': self.ENABLE_CACHE,
                'size_mb': self.CACHE_SIZE_MB,
                'ttl_seconds': self.CACHE_TTL_SECONDS,
            },
            
            # 散点优化配置
            'scatter': {
                'enable': self.SCATTER_OPTIMIZATION,
                'max_points_per_wafer': self.MAX_POINTS_PER_WAFER,
                'min_points_per_wafer': self.MIN_POINTS_PER_WAFER,
            },
            
            # 性能监控配置
            'monitoring': {
                'enable_profiling': self.ENABLE_PROFILING,
                'log_performance': self.LOG_PERFORMANCE,
                'performance_report': self.PERFORMANCE_REPORT,
            }
        }
    
    def update_config(self, config_dict: Dict[str, Any]):
        """更新配置"""
        for category, settings in config_dict.items():
            if isinstance(settings, dict):
                for key, value in settings.items():
                    attr_name = f"{key.upper()}"
                    if hasattr(self, attr_name):
                        setattr(self, attr_name, value)
                        logger.info(f"配置已更新: {attr_name} = {value}")
    
    def enable_debug_mode(self):
        """启用调试模式"""
        self.ENABLE_PROFILING = True
        self.LOG_PERFORMANCE = True
        self.PERFORMANCE_REPORT = True
        logger.info("调试模式已启用")
    
    def enable_safe_mode(self):
        """启用安全模式（适用于低配置机器）"""
        self.ENABLE_PARALLEL = False
        self.ENABLE_NUMBA = False
        self.ENABLE_CACHE = False
        self.MEMORY_LIMIT_MB = min(self.MEMORY_LIMIT_MB, 512)
        self.CHUNK_SIZE = 1000
        logger.info("安全模式已启用")
    
    def print_config_summary(self):
        """打印配置摘要"""
        config = self.get_config_dict()
        print("\n" + "="*60)
        print("CP数据分析器 - 性能配置摘要")
        print("="*60)
        print(f"硬件配置: CPU {config['hardware']['cpu_count']}核, "
              f"内存 {config['hardware']['memory_total_gb']:.1f}GB")
        print(f"并行处理: {'启用' if config['parallel']['enable'] else '禁用'} "
              f"(最大进程数: {config['parallel']['max_workers']})")
        print(f"Numba加速: {'启用' if config['numba']['enable'] else '禁用'}")
        print(f"内存限制: {config['memory']['limit_mb']}MB")
        print(f"缓存: {'启用' if config['cache']['enable'] else '禁用'} "
              f"({config['cache']['size_mb']}MB)")
        print(f"散点优化: {'启用' if config['scatter']['enable'] else '禁用'} "
              f"(每wafer最多{config['scatter']['max_points_per_wafer']}点)")
        print("="*60 + "\n")


# 全局性能配置实例
perf_config = PerformanceConfig()


def get_performance_config() -> PerformanceConfig:
    """获取全局性能配置实例"""
    return perf_config


def update_performance_config(**kwargs):
    """更新性能配置的便捷函数"""
    perf_config.update_config(kwargs)


def enable_high_performance_mode():
    """启用高性能模式"""
    config = {
        'numba': {'enable': True, 'parallel': True},
        'parallel': {'enable': True},
        'cache': {'enable': True},
        'scatter': {'enable': True},
        'memory': {'enable_monitor': True}
    }
    perf_config.update_config(config)
    logger.info("高性能模式已启用")


def enable_compatibility_mode():
    """启用兼容模式（适用于旧电脑）"""
    config = {
        'numba': {'enable': False},
        'parallel': {'enable': False, 'max_workers': 1},
        'cache': {'enable': False},
        'memory': {'limit_mb': 256, 'chunk_size': 1000}
    }
    perf_config.update_config(config)
    logger.info("兼容模式已启用")


if __name__ == "__main__":
    # 测试配置模块
    config = get_performance_config()
    config.print_config_summary() 