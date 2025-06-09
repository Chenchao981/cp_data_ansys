#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
箱体图Streamlit应用 - 多参数分析工具
提供完整的BVDSS1样式箱体图+散点图，支持多批次数据分析
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from frontend.charts.boxplot_chart import BoxplotChart
    # 导入JavaScript嵌入工具 - 使用兼容的导入方式
    def get_embedded_plotly_js():
        """获取嵌入式Plotly.js内容"""
        try:
            # 尝试绝对导入
            from frontend.charts.js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
            return _get_embedded_plotly_js()
        except ImportError:
            try:
                # 尝试从当前目录导入
                current_dir = Path(__file__).parent
                if str(current_dir) not in sys.path:
                    sys.path.append(str(current_dir))
                from js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
                return _get_embedded_plotly_js()
            except ImportError:
                # 最后回退到CDN
                return 'https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js'
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.stop()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="CP数据箱体图分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """初始化session state"""
    if 'boxplot_chart' not in st.session_state:
        st.session_state.boxplot_chart = None
    if 'available_parameters' not in st.session_state:
        st.session_state.available_parameters = []
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

def setup_boxplot_chart():
    """设置箱体图管理器"""
    try:
        if st.session_state.boxplot_chart is None:
            data_dir = st.sidebar.text_input("数据目录", value="output", help="包含cleaned.csv和spec.csv的目录")
            
            if st.sidebar.button("🔄 加载数据", type="primary"):
                with st.spinner("加载数据中..."):
                    chart = BoxplotChart(data_dir=data_dir)
                    if chart.load_data():
                        st.session_state.boxplot_chart = chart
                        st.session_state.available_parameters = chart.get_available_parameters()
                        st.session_state.data_loaded = True
                        st.success(f"✅ 数据加载成功！找到 {len(st.session_state.available_parameters)} 个测试参数")
                        st.rerun()
                    else:
                        st.error("❌ 数据加载失败，请检查数据目录和文件")
        
        return st.session_state.boxplot_chart
    except Exception as e:
        st.error(f"初始化箱体图管理器失败: {e}")
        return None

def display_data_info(chart):
    """显示数据基本信息"""
    if chart and chart.cleaned_data is not None:
        st.sidebar.markdown("### 📊 数据信息")
        
        # 基本统计
        total_records = len(chart.cleaned_data)
        lot_count = chart.cleaned_data['Lot_ID'].nunique()
        wafer_count = chart.cleaned_data['Wafer_ID'].nunique()
        
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            st.metric("总记录数", f"{total_records:,}")
        with col2:
            st.metric("批次数", lot_count)
        with col3:
            st.metric("晶圆数", wafer_count)
        
        # 批次详情
        st.sidebar.markdown("#### 批次信息")
        lot_info = chart.cleaned_data.groupby('Lot_ID')['Wafer_ID'].agg(['min', 'max', 'nunique'])
        
        for lot_id, info in lot_info.iterrows():
            st.sidebar.text(f"{lot_id[:20]}...")
            st.sidebar.text(f"  晶圆: {info['min']}~{info['max']} (共{info['nunique']}片)")

def create_enhanced_boxplot(chart, parameter):
    """创建增强版箱体图，添加统计信息"""
    try:
        # 获取基础图表
        fig = chart.create_boxplot_scatter_chart(parameter)
        
        if fig is None:
            return None
        
        # 获取参数信息和数据
        param_info = chart.get_parameter_info(parameter)
        chart_data, x_labels, _, lot_positions = chart.prepare_chart_data(parameter)
        
        if chart_data.empty:
            return fig
        
        # 计算统计信息
        stats_data = []
        for lot_id in chart_data['lot_id'].unique():
            lot_data = chart_data[chart_data['lot_id'] == lot_id]
            for wafer_id in lot_data['wafer_id'].unique():
                wafer_data = lot_data[lot_data['wafer_id'] == wafer_id]
                stats_data.append({
                    'lot_id': lot_id,
                    'wafer_id': wafer_id,
                    'average': wafer_data['value'].mean(),
                    'std_dev': wafer_data['value'].std(),
                    'count': len(wafer_data)
                })
        
        stats_df = pd.DataFrame(stats_data)
        
        # 在图表底部添加统计信息表格
        if not stats_df.empty:
            # 更新图表布局，为底部统计信息留出空间
            fig.update_layout(
                height=chart.chart_config['height'] + 150,  # 增加高度
                margin=dict(b=150)  # 增加底部边距
            )
            
            # 添加统计信息注释
            y_pos = -0.25  # 位置在X轴下方
            for i, (_, row) in enumerate(stats_df.iterrows()):
                x_pos = i
                if i < len(x_labels):
                    # 添加Average
                    fig.add_annotation(
                        x=x_pos, y=y_pos,
                        text=f"{row['average']:.2f}",
                        showarrow=False,
                        xref="x", yref="paper",
                        font=dict(size=8, color="red")
                    )
                    # 添加StdDev
                    fig.add_annotation(
                        x=x_pos, y=y_pos - 0.08,
                        text=f"{row['std_dev']:.2f}",
                        showarrow=False,
                        xref="x", yref="paper",
                        font=dict(size=8, color="blue")
                    )
        
        # 添加图例说明
        fig.add_annotation(
            x=-0.1, y=y_pos,
            text="Average",
            showarrow=False,
            xref="paper", yref="paper",
            font=dict(size=10, color="red"),
            xanchor="right"
        )
        fig.add_annotation(
            x=-0.1, y=y_pos - 0.08,
            text="StdDev",
            showarrow=False,
            xref="paper", yref="paper",
            font=dict(size=10, color="blue"),
            xanchor="right"
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"创建增强箱体图失败: {e}")
        return chart.create_boxplot_scatter_chart(parameter)

def display_parameter_chart(chart, parameter):
    """显示单个参数的图表"""
    try:
        # 获取参数信息
        param_info = chart.get_parameter_info(parameter)
        
        # 显示参数信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("参数名", parameter)
        with col2:
            st.metric("单位", param_info.get('unit', 'N/A'))
        with col3:
            if param_info.get('limit_upper') is not None:
                st.metric("上限 (USL)", f"{param_info['limit_upper']}")
            else:
                st.metric("上限 (USL)", "N/A")
        with col4:
            if param_info.get('limit_lower') is not None:
                st.metric("下限 (LSL)", f"{param_info['limit_lower']}")
            else:
                st.metric("下限 (LSL)", "N/A")
        
        # 显示测试条件
        if param_info.get('test_condition'):
            st.info(f"🔧 测试条件: {param_info['test_condition']}")
        
        # 生成图表
        with st.spinner(f"生成 {parameter} 图表中..."):
            fig = create_enhanced_boxplot(chart, parameter)
            
            if fig:
                # 显示图表
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{parameter}")
                
                # 下载按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"💾 保存 {parameter} 图表", key=f"save_{parameter}"):
                        saved_path = chart.save_chart(parameter)
                        if saved_path:
                            st.success(f"✅ 图表已保存到: {saved_path}")
                        else:
                            st.error("❌ 保存失败")
                
                with col2:
                    # 获取图表HTML - 使用本地嵌入的Plotly.js
                    try:
                        html_str = fig.to_html(include_plotlyjs=get_embedded_plotly_js())
                        st.download_button(
                            label=f"📥 下载 {parameter} HTML",
                            data=html_str,
                            file_name=f"{chart.generate_chart_title(parameter)}.html",
                            mime="text/html",
                            key=f"download_{parameter}"
                        )
                    except Exception as e:
                        st.error(f"生成下载文件失败: {e}")
            else:
                st.error(f"❌ 生成 {parameter} 图表失败")
        
    except Exception as e:
        st.error(f"显示参数 {parameter} 图表失败: {e}")
        logger.error(f"显示参数图表失败: {e}")

def main():
    """主函数"""
    st.title("📊 CP数据箱体图分析系统")
    st.markdown("---")
    
    # 初始化session state
    init_session_state()
    
    # 设置箱体图管理器
    chart = setup_boxplot_chart()
    
    # 显示数据信息
    if chart:
        display_data_info(chart)
    
    # 主内容区域
    if not st.session_state.data_loaded:
        st.info("👈 请在左侧面板加载数据以开始分析")
        
        # 显示使用说明
        st.markdown("### 📖 使用说明")
        st.markdown("""
        1. **数据准备**: 确保数据目录包含以下文件：
           - `*_cleaned_*.csv`: 清洗后的测试数据
           - `*_spec_*.csv`: 参数规格文件
        
        2. **图表特性**:
           - 📊 箱体图 + 散点图组合显示
           - 🔴 红色虚线显示上下限 (USL/LSL)
           - 📏 双层X轴：上层显示Wafer_ID，下层显示Lot_ID
           - 📈 底部统计信息：Average 和 StdDev
           - 🖱️ 支持缩放和拖拽查看
        
        3. **操作指南**:
           - 每个参数单独显示在一个标签页中
           - 支持图表保存和下载
           - 可以查看详细的参数信息和测试条件
        """)
        
        return
    
    # 检查是否有可用参数
    if not st.session_state.available_parameters:
        st.warning("⚠️ 未找到可用的测试参数")
        return
    
    # 显示参数总览
    st.sidebar.markdown("### 🔬 测试参数")
    param_count = len(st.session_state.available_parameters)
    st.sidebar.success(f"共找到 {param_count} 个参数")
    
    # 批量操作
    st.sidebar.markdown("### ⚡ 批量操作")
    if st.sidebar.button("🎯 生成所有图表", type="secondary"):
        with st.spinner("批量生成图表中..."):
            charts = chart.generate_all_parameter_charts()
            st.success(f"✅ 成功生成 {len(charts)} 个图表")
    
    # 创建参数标签页
    st.markdown("### 📈 参数分析图表")
    
    # 如果参数太多，分批显示
    if param_count <= 10:
        # 少于10个参数，直接显示所有标签页
        tabs = st.tabs(st.session_state.available_parameters)
        
        for i, (tab, parameter) in enumerate(zip(tabs, st.session_state.available_parameters)):
            with tab:
                display_parameter_chart(chart, parameter)
    else:
        # 超过10个参数，使用选择框
        st.markdown("**参数数量较多，请选择要查看的参数：**")
        
        # 参数选择
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_param = st.selectbox(
                "选择参数",
                st.session_state.available_parameters,
                help="选择要分析的测试参数"
            )
        with col2:
            st.markdown("　")  # 占位
            if st.button("🔄 刷新图表"):
                st.rerun()
        
        # 显示选中参数的图表
        if selected_param:
            st.markdown(f"#### 📊 {selected_param} 分析图表")
            display_parameter_chart(chart, selected_param)
        
        # 参数列表
        with st.expander("📋 查看所有参数列表"):
            param_df = pd.DataFrame({
                '序号': range(1, len(st.session_state.available_parameters) + 1),
                '参数名': st.session_state.available_parameters
            })
            st.dataframe(param_df, use_container_width=True)

def show_footer():
    """显示页脚信息"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            CP数据箱体图分析系统 | 基于Plotly和Streamlit构建 | 
            支持多批次数据分析和BVDSS1样式图表
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    try:
        main()
        show_footer()
    except Exception as e:
        st.error(f"应用运行错误: {e}")
        logger.error(f"应用运行错误: {e}", exc_info=True) 