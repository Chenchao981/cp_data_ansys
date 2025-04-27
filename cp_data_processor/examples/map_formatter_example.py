"""
MAP格式化器示例脚本

该脚本展示如何使用MAP格式化模块生成和可视化晶圆MAP图。
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.analysis.map_formatter import MapFormatter


def create_test_cp_lot():
    """
    创建测试用的CP批次数据
    """
    # 创建CP批次
    cp_lot = CPLot(id="LOT12345")
    
    # 创建参数
    param1 = CPParameter(id="VTH", unit="V", target=1.0, sl=0.8, su=1.2)
    param2 = CPParameter(id="IOFF", unit="nA", target=0.5, sl=None, su=1.0)
    param3 = CPParameter(id="IDSat", unit="mA", target=10.0, sl=8.0, su=12.0)
    
    cp_lot.params = [param1, param2, param3]
    
    # 创建晶圆
    for wafer_id in range(1, 6):  # 5个晶圆
        wafer = CPWafer(id=f"W{wafer_id}")
        
        # 创建模拟数据
        rows, cols = 5, 5  # 5x5的晶圆
        n_dies = rows * cols
        
        # 创建坐标
        x_coords = []
        y_coords = []
        for r in range(rows):
            for c in range(cols):
                x_coords.append(c)
                y_coords.append(r)
        
        # 创建模拟测试数据
        data_dict = {
            'X': x_coords,
            'Y': y_coords,
            'DIE_ID': [f"D{i+1}" for i in range(n_dies)],
        }
        
        # 为每个参数生成随机数据，但保持某种模式
        # VTH - 中心高，边缘低的模式
        center_x, center_y = (cols-1)/2, (rows-1)/2
        vth_data = []
        
        for x, y in zip(x_coords, y_coords):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            
            # 中心值高，远离中心值低
            base_value = 1.0  # 目标值
            variation = -0.3 * (dist / max_dist)  # -0.3到0的变化
            noise = np.random.normal(0, 0.05)  # 添加一些随机噪声
            
            value = base_value + variation + noise
            vth_data.append(value)
        
        data_dict['VTH'] = vth_data
        
        # IOFF - 随机但有一些异常值
        ioff_data = np.random.lognormal(-1, 0.5, n_dies)
        
        # 添加一些异常值
        outlier_indices = np.random.choice(n_dies, size=int(n_dies * 0.1), replace=False)
        for idx in outlier_indices:
            ioff_data[idx] *= 2.5
            
        data_dict['IOFF'] = ioff_data
        
        # IDSat - 水平梯度模式
        idsat_data = []
        for x in x_coords:
            base_value = 10.0  # 目标值
            gradient = 0.4 * (x / (cols-1))  # 0到0.4的变化
            noise = np.random.normal(0, 0.2)  # 添加一些随机噪声
            
            value = base_value + gradient + noise
            idsat_data.append(value)
        
        data_dict['IDSat'] = idsat_data
        
        # 创建DataFrame
        wafer.data = pd.DataFrame(data_dict)
        
        # 添加到批次
        cp_lot.wafers.append(wafer)
    
    return cp_lot


def main():
    """
    主函数，展示MAP格式化器的使用
    """
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建测试数据
    cp_lot = create_test_cp_lot()
    print(f"创建测试批次: {cp_lot.id} 包含 {len(cp_lot.wafers)} 个晶圆")
    
    # 创建MAP格式化器
    map_formatter = MapFormatter(cp_lot)
    
    # 示例1: 创建单个晶圆的参数MAP图
    print("\n示例1: 创建单个晶圆的参数MAP图")
    wafer_id = "W1"
    param_id = "VTH"
    
    fig = map_formatter.create_wafer_map(wafer_id, param_id)
    map_formatter.save_map_to_file(fig, os.path.join(output_dir, f"{wafer_id}_{param_id}_map.png"))
    plt.close(fig)
    
    # 示例2: 使用不同的颜色映射方案
    print("\n示例2: 使用不同的颜色映射方案")
    param_id = "IDSat"
    
    fig = map_formatter.create_wafer_map(wafer_id, param_id, cmap="diverging")
    map_formatter.save_map_to_file(fig, os.path.join(output_dir, f"{wafer_id}_{param_id}_diverging_map.png"))
    plt.close(fig)
    
    # 示例3: 创建合格/不合格MAP图
    print("\n示例3: 创建合格/不合格MAP图")
    param_id = "VTH"
    
    fig = map_formatter.create_pass_fail_map(wafer_id, param_id)
    map_formatter.save_map_to_file(fig, os.path.join(output_dir, f"{wafer_id}_{param_id}_pass_fail_map.png"))
    plt.close(fig)
    
    # 示例4: 创建整批晶圆的参数MAP图
    print("\n示例4: 创建整批晶圆的参数MAP图")
    param_id = "VTH"
    
    fig = map_formatter.create_lot_map(param_id, cmap="sequential")
    map_formatter.save_map_to_file(fig, os.path.join(output_dir, f"lot_{param_id}_map.png"))
    plt.close(fig)
    
    # 示例5: 创建晶圆箱线图
    print("\n示例5: 创建晶圆箱线图")
    param_id = "IDSat"
    
    fig = map_formatter.create_wafer_boxplot(param_id, show_outliers=True)
    map_formatter.save_map_to_file(fig, os.path.join(output_dir, f"lot_{param_id}_boxplot.png"))
    plt.close(fig)
    
    # 示例6: 创建晶圆箱线图并显示分布点
    print("\n示例6: 创建晶圆箱线图并显示分布点")
    param_id = "IOFF"
    
    fig = map_formatter.create_wafer_boxplot(param_id, show_outliers=True, show_swarm=True)
    map_formatter.save_map_to_file(fig, os.path.join(output_dir, f"lot_{param_id}_boxplot_with_swarm.png"))
    plt.close(fig)
    
    print(f"\n所有示例图表已保存到: {output_dir}")


if __name__ == "__main__":
    main() 