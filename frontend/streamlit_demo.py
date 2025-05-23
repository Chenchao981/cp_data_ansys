#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlit快速原型 - 1-2周完成Web界面
演示如何快速构建CP数据可视化Web应用
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.core.data_manager import DataManager
from frontend.core.chart_factory import ChartFactory

# 页面配置
st.set_page_config(
    page_title="CP数据可视化分析平台",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data_manager():
    """缓存数据管理器"""
    return DataManager(data_source="auto", cache_enabled=True, data_dir="output")

@st.cache_data
def get_available_lots():
    """获取可用的批次列表"""
    # 这里可以扫描output目录获取所有批次
    return ["FA54-5339-327A-250501@203"]

@st.cache_data
def load_lot_data(lot_id, data_type):
    """加载批次数据"""
    dm = load_data_manager()
    return dm.get_data(data_type, lot_id)

def main():
    """主应用"""
    
    # 标题和说明
    st.title("📊 CP数据可视化分析平台")
    st.markdown("---")
    
    # 侧边栏 - 数据选择
    st.sidebar.header("🔧 数据选择")
    
    # 批次选择
    lots = get_available_lots()
    selected_lot = st.sidebar.selectbox(
        "选择批次 (Lot)",
        lots,
        index=0 if lots else None
    )
    
    if not selected_lot:
        st.warning("⚠️ 未找到可用的批次数据")
        return
    
    # 图表类型选择
    chart_types = st.sidebar.multiselect(
        "选择图表类型",
        ["良率趋势", "参数分布", "散点分析", "箱线图"],
        default=["良率趋势", "参数分布"]
    )
    
    # 主界面布局
    if selected_lot:
        st.subheader(f"📈 批次分析: {selected_lot}")
        
        # 数据概览
        with st.expander("📋 数据概览", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            # 加载各类数据
            yield_data = load_lot_data(selected_lot, "yield")
            spec_data = load_lot_data(selected_lot, "spec")
            cleaned_data = load_lot_data(selected_lot, "cleaned")
            
            with col1:
                if yield_data is not None:
                    st.metric("良率数据", f"{len(yield_data)} 条记录")
                else:
                    st.metric("良率数据", "无数据")
            
            with col2:
                if spec_data is not None:
                    st.metric("规格数据", f"{len(spec_data)} 个参数")
                else:
                    st.metric("规格数据", "无数据")
            
            with col3:
                if cleaned_data is not None:
                    wafer_count = cleaned_data['Wafer_ID'].nunique() if 'Wafer_ID' in cleaned_data.columns else 0
                    st.metric("Wafer数量", f"{wafer_count} 片")
                else:
                    st.metric("Wafer数量", "无数据")
        
        # 图表展示
        if "良率趋势" in chart_types and yield_data is not None:
            st.subheader("📈 良率趋势分析")
            
            # 假设yield_data有Parameter和Yield列
            if len(yield_data.columns) >= 2:
                fig = px.line(
                    x=range(len(yield_data)), 
                    y=yield_data.iloc[:, 1],  # 第二列作为Y值
                    title="良率趋势图",
                    labels={'x': '参数序号', 'y': '数值'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("良率数据格式不支持趋势图显示")
        
        if "参数分布" in chart_types and cleaned_data is not None:
            st.subheader("📊 参数分布分析")
            
            # 选择参数列
            numeric_columns = cleaned_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if numeric_columns:
                selected_param = st.selectbox("选择参数", numeric_columns)
                
                if selected_param:
                    # 直方图
                    fig = px.histogram(
                        cleaned_data,
                        x=selected_param,
                        title=f"{selected_param} 分布图",
                        marginal="box"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("未找到数值型参数列")
        
        if "散点分析" in chart_types and cleaned_data is not None:
            st.subheader("🔍 散点分析")
            
            numeric_columns = cleaned_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if len(numeric_columns) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    x_param = st.selectbox("X轴参数", numeric_columns, key="scatter_x")
                with col2:
                    y_param = st.selectbox("Y轴参数", numeric_columns, index=1, key="scatter_y")
                
                if x_param and y_param and x_param != y_param:
                    fig = px.scatter(
                        cleaned_data,
                        x=x_param,
                        y=y_param,
                        title=f"{x_param} vs {y_param}",
                        opacity=0.6
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        if "箱线图" in chart_types and cleaned_data is not None:
            st.subheader("📦 箱线图分析")
            
            numeric_columns = cleaned_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if numeric_columns:
                selected_params = st.multiselect(
                    "选择参数（可多选）",
                    numeric_columns,
                    default=numeric_columns[:3]  # 默认选择前3个
                )
                
                if selected_params:
                    # 创建箱线图
                    fig = go.Figure()
                    for param in selected_params:
                        fig.add_trace(go.Box(
                            y=cleaned_data[param],
                            name=param,
                            boxpoints='outliers'
                        ))
                    
                    fig.update_layout(
                        title="参数箱线图对比",
                        yaxis_title="数值",
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # 数据表查看
        with st.expander("🔍 原始数据查看"):
            data_type = st.radio("选择数据类型", ["yield", "spec", "cleaned"])
            
            if data_type == "yield" and yield_data is not None:
                st.dataframe(yield_data)
            elif data_type == "spec" and spec_data is not None:
                st.dataframe(spec_data)
            elif data_type == "cleaned" and cleaned_data is not None:
                st.dataframe(cleaned_data.head(1000))  # 限制显示行数
            else:
                st.info(f"无 {data_type} 数据")

if __name__ == "__main__":
    main()


# 运行说明
"""
## 🚀 如何运行此Streamlit应用

1. 安装依赖:
   pip install streamlit plotly

2. 运行应用:
   streamlit run frontend/streamlit_demo.py

3. 浏览器访问:
   http://localhost:8501

## ⭐ 优势
- ✅ 1-2周即可完成
- ✅ 自动缓存，性能优秀
- ✅ 交互式Web界面
- ✅ 复用现有数据架构
- ✅ 支持多种图表类型
- ✅ 响应式布局

## 🔄 后续升级路径
如果后期需要企业级功能：
1. 保留核心逻辑
2. 迁移到Django+React
3. 添加Redis缓存
4. 支持多用户访问
""" 