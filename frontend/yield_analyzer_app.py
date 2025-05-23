#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专门的Yield分析Web应用 - 基于Streamlit
针对半导体CP测试良率数据优化的专业分析工具
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.core.data_manager import DataManager

# 页面配置
st.set_page_config(
    page_title="🏭 Yield分析专家",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data_manager():
    """缓存数据管理器"""
    return DataManager(data_source="auto", cache_enabled=True, data_dir="output")

@st.cache_data
def load_yield_data(lot_id):
    """加载yield数据并预处理"""
    dm = load_data_manager()
    yield_data = dm.get_data('yield', lot_id)
    
    if yield_data is not None:
        # 数据预处理
        df = yield_data.copy()
        
        # 过滤掉汇总行
        df_wafers = df[df['Lot_ID'] != 'ALL'].copy()
        
        # 转换yield为数值
        if 'Yield' in df_wafers.columns:
            df_wafers['Yield_Numeric'] = df_wafers['Yield'].str.rstrip('%').astype(float)
        
        # 提取批次简称
        df_wafers['Lot_Short'] = df_wafers['Lot_ID'].str.extract(r'(FA54-\d+)')
        
        # 计算失效总数
        failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
        df_wafers['Total_Failures'] = df_wafers[failure_columns].sum(axis=1)
        
        return df_wafers, df[df['Lot_ID'] == 'ALL']
    
    return None, None

def create_wafer_trend_chart(df_wafers):
    """创建wafer良率趋势图"""
    fig = go.Figure()
    
    lots = df_wafers['Lot_Short'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, lot in enumerate(lots):
        lot_data = df_wafers[df_wafers['Lot_Short'] == lot].sort_values('Wafer_ID')
        
        fig.add_trace(go.Scatter(
            x=lot_data['Wafer_ID'],
            y=lot_data['Yield_Numeric'],
            mode='lines+markers',
            name=lot,
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=8, symbol='circle'),
            hovertemplate=f'<b>{lot}</b><br>Wafer: %{{x}}<br>良率: %{{y:.2f}}%<extra></extra>'
        ))
    
    # 添加平均线
    overall_mean = df_wafers['Yield_Numeric'].mean()
    fig.add_hline(y=overall_mean, line_dash="dash", line_color="red",
                  annotation_text=f"平均良率: {overall_mean:.2f}%")
    
    fig.update_layout(
        title="📈 Wafer良率趋势分析",
        xaxis_title="Wafer编号",
        yaxis_title="良率 (%)",
        yaxis=dict(range=[95, 101]),
        hovermode='x unified',
        height=500
    )
    
    return fig

def create_lot_comparison_chart(df_wafers):
    """创建批次对比图"""
    lot_stats = df_wafers.groupby('Lot_Short')['Yield_Numeric'].agg([
        'mean', 'std', 'min', 'max', 'count'
    ]).reset_index()
    
    fig = go.Figure()
    
    # 柱状图
    fig.add_trace(go.Bar(
        x=lot_stats['Lot_Short'],
        y=lot_stats['mean'],
        error_y=dict(type='data', array=lot_stats['std']),
        name='平均良率',
        marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(lot_stats)],
        hovertemplate='<b>%{x}</b><br>平均良率: %{y:.2f}%<br>标准差: %{error_y.array:.2f}%<extra></extra>'
    ))
    
    # 添加数据标签
    for i, row in lot_stats.iterrows():
        fig.add_annotation(
            x=row['Lot_Short'],
            y=row['mean'] + row['std'] + 0.2,
            text=f"{row['mean']:.2f}%<br>({int(row['count'])} wafers)",
            showarrow=False,
            font=dict(size=12)
        )
    
    fig.update_layout(
        title="📊 批次良率对比",
        xaxis_title="批次",
        yaxis_title="平均良率 (%)",
        yaxis=dict(range=[96, 100]),
        height=500
    )
    
    return fig

def create_failure_analysis_chart(df_wafers):
    """创建失效类型分析图"""
    failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
    failure_totals = df_wafers[failure_columns].sum()
    
    # 过滤掉为0的bin
    failure_totals = failure_totals[failure_totals > 0]
    
    if len(failure_totals) == 0:
        return None
    
    fig = go.Figure(data=[go.Pie(
        labels=failure_totals.index,
        values=failure_totals.values,
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="🔍 失效类型分布",
        height=500,
        annotations=[dict(text='失效分析', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    return fig

def create_yield_distribution_chart(df_wafers):
    """创建良率分布图"""
    fig = go.Figure()
    
    # 直方图
    fig.add_trace(go.Histogram(
        x=df_wafers['Yield_Numeric'],
        nbinsx=20,
        name='良率分布',
        marker_color='skyblue',
        opacity=0.7
    ))
    
    # 添加统计线
    mean_yield = df_wafers['Yield_Numeric'].mean()
    std_yield = df_wafers['Yield_Numeric'].std()
    
    fig.add_vline(x=mean_yield, line_dash="dash", line_color="red",
                  annotation_text=f"平均: {mean_yield:.2f}%")
    fig.add_vline(x=mean_yield + std_yield, line_dash="dot", line_color="orange",
                  annotation_text=f"+1σ: {mean_yield + std_yield:.2f}%")
    fig.add_vline(x=mean_yield - std_yield, line_dash="dot", line_color="orange",
                  annotation_text=f"-1σ: {mean_yield - std_yield:.2f}%")
    
    fig.update_layout(
        title="📊 良率分布直方图",
        xaxis_title="良率 (%)",
        yaxis_title="Wafer数量",
        height=500
    )
    
    return fig

def main():
    """主应用"""
    
    # 应用标题
    st.title("🏭 Yield分析专家")
    st.markdown("### 半导体CP测试良率专业分析工具")
    st.markdown("---")
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 分析配置")
    
    # 批次选择（目前固定，可以扩展为自动扫描）
    lot_id = st.sidebar.selectbox(
        "📦 选择批次",
        ["FA54-5339-327A-250501@203"],
        help="选择要分析的批次数据"
    )
    
    # 分析视图选择
    analysis_views = st.sidebar.multiselect(
        "📊 选择分析视图",
        ["Wafer趋势", "批次对比", "失效分析", "良率分布"],
        default=["Wafer趋势", "批次对比"],
        help="选择要显示的分析图表"
    )
    
    # 加载数据
    with st.spinner("🔄 加载yield数据..."):
        df_wafers, df_summary = load_yield_data(lot_id)
    
    if df_wafers is None:
        st.error("❌ 无法加载yield数据，请检查数据文件")
        return
    
    # 数据概览
    st.subheader("📋 数据概览")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总Wafer数", len(df_wafers))
    
    with col2:
        avg_yield = df_wafers['Yield_Numeric'].mean()
        st.metric("平均良率", f"{avg_yield:.2f}%")
    
    with col3:
        total_chips = df_wafers['Total'].sum()
        st.metric("总芯片数", f"{total_chips:,}")
    
    with col4:
        total_pass = df_wafers['Pass'].sum()
        st.metric("通过芯片数", f"{total_pass:,}")
    
    st.markdown("---")
    
    # 分析图表展示
    if "Wafer趋势" in analysis_views:
        st.subheader("📈 Wafer良率趋势")
        fig_trend = create_wafer_trend_chart(df_wafers)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    if "批次对比" in analysis_views:
        st.subheader("📊 批次良率对比")
        fig_comparison = create_lot_comparison_chart(df_wafers)
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        if "失效分析" in analysis_views:
            st.subheader("🔍 失效类型分析")
            fig_failure = create_failure_analysis_chart(df_wafers)
            if fig_failure:
                st.plotly_chart(fig_failure, use_container_width=True)
            else:
                st.info("📝 当前数据无失效芯片")
    
    with col_right:
        if "良率分布" in analysis_views:
            st.subheader("📊 良率分布")
            fig_distribution = create_yield_distribution_chart(df_wafers)
            st.plotly_chart(fig_distribution, use_container_width=True)
    
    # 详细数据表
    with st.expander("🔍 详细数据查看"):
        st.subheader("Wafer级别数据")
        
        # 数据筛选
        col1, col2 = st.columns(2)
        with col1:
            selected_lots = st.multiselect(
                "筛选批次",
                df_wafers['Lot_Short'].unique(),
                default=df_wafers['Lot_Short'].unique()
            )
        
        with col2:
            yield_range = st.slider(
                "良率范围 (%)",
                float(df_wafers['Yield_Numeric'].min()),
                float(df_wafers['Yield_Numeric'].max()),
                (float(df_wafers['Yield_Numeric'].min()), float(df_wafers['Yield_Numeric'].max()))
            )
        
        # 筛选数据
        filtered_data = df_wafers[
            (df_wafers['Lot_Short'].isin(selected_lots)) &
            (df_wafers['Yield_Numeric'] >= yield_range[0]) &
            (df_wafers['Yield_Numeric'] <= yield_range[1])
        ]
        
        st.dataframe(
            filtered_data[['Lot_ID', 'Wafer_ID', 'Yield', 'Total', 'Pass', 'Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']],
            use_container_width=True
        )
    
    # 汇总信息
    if df_summary is not None and len(df_summary) > 0:
        st.markdown("---")
        st.subheader("📈 批次汇总")
        st.dataframe(df_summary, use_container_width=True)

if __name__ == "__main__":
    main() 