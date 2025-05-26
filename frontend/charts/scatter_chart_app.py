#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
散点图Streamlit应用 - 参数关联分析工具
提供交互式的参数选择和图表展示功能
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
    from frontend.charts.scatter_chart import ScatterChart
    from frontend.core.data_manager import DataManager
    from frontend.utils.file_utils import ensure_directory
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.stop()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="CP数据散点图分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """初始化session state"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = None
    if 'available_lots' not in st.session_state:
        st.session_state.available_lots = []
    if 'available_parameters' not in st.session_state:
        st.session_state.available_parameters = []
    if 'current_chart' not in st.session_state:
        st.session_state.current_chart = None

def setup_data_manager():
    """设置数据管理器"""
    try:
        if st.session_state.data_manager is None:
            data_dir = st.sidebar.text_input("数据目录", value="output", help="包含cleaned.csv和spec.csv的目录")
            
            if st.sidebar.button("初始化数据管理器"):
                with st.spinner("初始化数据管理器..."):
                    dm = DataManager(
                        data_source="auto",
                        cache_enabled=True,
                        data_dir=data_dir
                    )
                    st.session_state.data_manager = dm
                    st.success("数据管理器初始化成功！")
                    st.rerun()
        
        return st.session_state.data_manager
    except Exception as e:
        st.error(f"初始化数据管理器失败: {e}")
        return None

def load_available_data(data_manager):
    """加载可用的数据信息"""
    try:
        # 这里需要根据实际的data_manager接口来获取可用批次
        # 暂时使用示例数据
        if not st.session_state.available_lots:
            # 根据实际数据文件定义可用批次列表
            lots = [
                "FA54-5339-327A-250501@203",
                "FA54-5340-325A-250502@203", 
                "FA54-5341-327A-250430@203",
                "FA54-5341-327A-250501@203",
                "FA54-5342-325A-250501@203"
            ]
            st.session_state.available_lots = lots
        
        return st.session_state.available_lots
    except Exception as e:
        st.error(f"加载可用数据失败: {e}")
        return []

def create_plotly_scatter(scatter_chart, plot_data):
    """使用Plotly创建交互式散点图"""
    try:
        fig = go.Figure()
        
        # 添加散点
        if 'status' in plot_data.columns:
            # 按状态分组
            pass_data = plot_data[plot_data['status'] == 'pass']
            fail_data = plot_data[plot_data['status'] == 'fail']
            
            if len(pass_data) > 0:
                fig.add_trace(go.Scatter(
                    x=pass_data['x'],
                    y=pass_data['y'],
                    mode='markers',
                    name='合格',
                    marker=dict(
                        color='#2E8B57',
                        size=8,
                        opacity=0.7,
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate=f'{scatter_chart.x_param}: %{{x}}<br>{scatter_chart.y_param}: %{{y}}<br>状态: 合格<extra></extra>'
                ))
            
            if len(fail_data) > 0:
                fig.add_trace(go.Scatter(
                    x=fail_data['x'],
                    y=fail_data['y'],
                    mode='markers',
                    name='不合格',
                    marker=dict(
                        color='#DC143C',
                        size=8,
                        opacity=0.7,
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate=f'{scatter_chart.x_param}: %{{x}}<br>{scatter_chart.y_param}: %{{y}}<br>状态: 不合格<extra></extra>'
                ))
        else:
            fig.add_trace(go.Scatter(
                x=plot_data['x'],
                y=plot_data['y'],
                mode='markers',
                name='数据点',
                marker=dict(
                    color='#2E8B57',
                    size=8,
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                hovertemplate=f'{scatter_chart.x_param}: %{{x}}<br>{scatter_chart.y_param}: %{{y}}<extra></extra>'
            ))
        
        # 添加规格限制区域
        if scatter_chart.show_spec_limits and 'spec' in scatter_chart.data:
            spec_data = scatter_chart.data['spec']
            x_spec = spec_data[spec_data['Parameter'] == scatter_chart.x_param]
            y_spec = spec_data[spec_data['Parameter'] == scatter_chart.y_param]
            
            if len(x_spec) > 0 and len(y_spec) > 0:
                x_lsl = x_spec['LSL'].iloc[0] if 'LSL' in x_spec.columns else None
                x_usl = x_spec['USL'].iloc[0] if 'USL' in x_spec.columns else None
                y_lsl = y_spec['LSL'].iloc[0] if 'LSL' in y_spec.columns else None
                y_usl = y_spec['USL'].iloc[0] if 'USL' in y_spec.columns else None
                
                if all(v is not None for v in [x_lsl, x_usl, y_lsl, y_usl]):
                    fig.add_shape(
                        type="rect",
                        x0=x_lsl, y0=y_lsl,
                        x1=x_usl, y1=y_usl,
                        line=dict(color="#87CEEB", width=2),
                        fillcolor="#87CEEB",
                        opacity=0.2,
                        layer="below"
                    )
        
        # 添加趋势线
        if scatter_chart.show_trend_line and len(plot_data) >= 2:
            try:
                from scipy import stats
                x_data = plot_data['x'].values
                y_data = plot_data['y'].values
                slope, intercept, r_value, _, _ = stats.linregress(x_data, y_data)
                
                x_range = [plot_data['x'].min(), plot_data['x'].max()]
                y_trend = [slope * x + intercept for x in x_range]
                
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=y_trend,
                    mode='lines',
                    name=f'趋势线 (R²={r_value**2:.3f})',
                    line=dict(color='#FF6347', width=2, dash='dash'),
                    hovertemplate=f'趋势线<br>R² = {r_value**2:.3f}<extra></extra>'
                ))
            except Exception as e:
                logger.warning(f"添加趋势线失败: {e}")
        
        # 更新布局
        fig.update_layout(
            title=f'参数关联分析: {scatter_chart.x_param} vs {scatter_chart.y_param}',
            xaxis_title=scatter_chart.x_param,
            yaxis_title=scatter_chart.y_param,
            hovermode='closest',
            showlegend=True,
            width=800,
            height=600,
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        st.error(f"创建Plotly图表失败: {e}")
        return None

def show_correlation_matrix(scatter_chart):
    """显示相关性矩阵"""
    try:
        corr_matrix = scatter_chart.get_correlation_matrix()
        if corr_matrix is not None:
            st.subheader("📈 参数相关性矩阵")
            
            # 使用Plotly创建热图
            fig = px.imshow(
                corr_matrix,
                labels=dict(x="参数", y="参数", color="相关系数"),
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                color_continuous_scale='RdBu_r',
                aspect="auto",
                title="参数相关性热图"
            )
            
            # 添加数值标注
            fig.update_traces(
                texttemplate="%{z:.2f}",
                textfont={"size": 10}
            )
            
            fig.update_layout(
                width=600,
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示数值表格
            with st.expander("查看相关性数值表"):
                st.dataframe(corr_matrix.round(3))
        else:
            st.warning("无法计算相关性矩阵")
    except Exception as e:
        st.error(f"显示相关性矩阵失败: {e}")

def main():
    """主函数"""
    st.title("📊 CP数据散点图分析")
    st.markdown("---")
    
    # 初始化session state
    init_session_state()
    
    # 侧边栏 - 数据设置
    st.sidebar.header("🔧 数据设置")
    data_manager = setup_data_manager()
    
    if data_manager is None:
        st.warning("请先初始化数据管理器")
        return
    
    # 加载可用数据
    available_lots = load_available_data(data_manager)
    
    if not available_lots:
        st.warning("未找到可用的批次数据")
        return
    
    # 侧边栏 - 参数选择
    st.sidebar.header("📊 图表设置")
    
    # 批次选择
    selected_lot = st.sidebar.selectbox(
        "选择批次",
        options=available_lots,
        help="选择要分析的批次"
    )
    
    # 创建临时图表以获取可用参数
    if selected_lot:
        try:
            temp_chart = ScatterChart(data_manager, selected_lot)
            if temp_chart.load_required_data():
                available_params = temp_chart.get_available_parameters()
                st.session_state.available_parameters = available_params
                temp_chart.close()
            else:
                st.error("无法加载数据")
                return
        except Exception as e:
            st.error(f"获取参数列表失败: {e}")
            return
    
    if not st.session_state.available_parameters:
        st.warning("未找到可用的参数")
        return
    
    # 参数选择
    col1, col2 = st.sidebar.columns(2)
    with col1:
        x_param = st.selectbox(
            "X轴参数",
            options=st.session_state.available_parameters,
            help="选择X轴显示的参数"
        )
    with col2:
        y_param = st.selectbox(
            "Y轴参数", 
            options=st.session_state.available_parameters,
            index=1 if len(st.session_state.available_parameters) > 1 else 0,
            help="选择Y轴显示的参数"
        )
    
    # 图表选项
    st.sidebar.subheader("🎨 图表选项")
    show_spec_limits = st.sidebar.checkbox("显示规格限制", value=True)
    show_trend_line = st.sidebar.checkbox("显示趋势线", value=True)
    show_correlation = st.sidebar.checkbox("显示相关性信息", value=True)
    point_size = st.sidebar.slider("点大小", min_value=10, max_value=100, value=30)
    point_alpha = st.sidebar.slider("透明度", min_value=0.1, max_value=1.0, value=0.7)
    
    # 生成图表按钮
    if st.sidebar.button("🚀 生成散点图", type="primary"):
        if x_param == y_param:
            st.error("X轴和Y轴参数不能相同")
            return
        
        try:
            with st.spinner("正在生成散点图..."):
                # 创建散点图
                scatter_chart = ScatterChart(
                    data_manager=data_manager,
                    lot_id=selected_lot,
                    x_param=x_param,
                    y_param=y_param,
                    point_size=point_size,
                    point_alpha=point_alpha,
                    show_spec_limits=show_spec_limits,
                    show_trend_line=show_trend_line,
                    show_correlation=show_correlation
                )
                
                # 生成图表
                if scatter_chart.generate():
                    st.session_state.current_chart = scatter_chart
                    st.success("散点图生成成功！")
                else:
                    st.error("散点图生成失败")
                    return
        except Exception as e:
            st.error(f"生成散点图时出错: {e}")
            return
    
    # 显示图表
    if st.session_state.current_chart is not None:
        chart = st.session_state.current_chart
        
        # 主要内容区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 散点图")
            
            # 准备绘图数据
            plot_data = chart._prepare_plot_data()
            if plot_data is not None:
                # 创建Plotly交互图表
                fig = create_plotly_scatter(chart, plot_data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # 数据统计
                st.subheader("📊 数据统计")
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                
                with stats_col1:
                    st.metric("数据点总数", len(plot_data))
                
                with stats_col2:
                    if 'status' in plot_data.columns:
                        pass_count = len(plot_data[plot_data['status'] == 'pass'])
                        st.metric("合格数量", pass_count)
                
                with stats_col3:
                    if 'status' in plot_data.columns:
                        fail_count = len(plot_data[plot_data['status'] == 'fail'])
                        st.metric("不合格数量", fail_count)
                
                # 计算相关性
                if len(plot_data) >= 2:
                    correlation = np.corrcoef(plot_data['x'], plot_data['y'])[0, 1]
                    st.metric("相关系数", f"{correlation:.3f}")
            else:
                st.error("无法准备绘图数据")
        
        with col2:
            st.subheader("ℹ️ 图表信息")
            
            # 显示图表信息
            info = chart.get_data_info()
            st.json(info)
            
            # 导出功能
            st.subheader("💾 导出功能")
            
            output_dir = st.text_input("输出目录", value="./charts_output")
            filename = st.text_input("文件名", value=f"scatter_{x_param}_{y_param}.png")
            
            if st.button("💾 保存图表"):
                try:
                    ensure_directory(output_dir)
                    save_path = chart.save(output_dir, filename)
                    if save_path:
                        st.success(f"图表已保存: {save_path}")
                    else:
                        st.error("保存失败")
                except Exception as e:
                    st.error(f"保存失败: {e}")
        
        # 相关性矩阵（全宽显示）
        st.markdown("---")
        show_correlation_matrix(chart)
    
    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 功能说明
        1. **数据加载**: 初始化数据管理器，自动加载cleaned.csv和spec.csv文件
        2. **参数选择**: 选择X轴和Y轴要分析的参数
        3. **图表生成**: 生成交互式散点图，支持缩放、平移、悬停信息
        4. **规格限制**: 显示参数的规格范围（如果有spec.csv）
        5. **趋势分析**: 显示线性趋势线和相关系数
        6. **数据导出**: 保存图表为PNG文件
        
        ### 图表说明
        - **绿色点**: 合格数据点（在规格范围内）
        - **红色点**: 不合格数据点（超出规格范围）
        - **蓝色区域**: 规格限制范围
        - **虚线**: 线性趋势线
        
        ### 相关性分析
        - **|r| > 0.7**: 强相关
        - **0.3 < |r| < 0.7**: 中等相关  
        - **|r| < 0.3**: 弱相关
        """)

if __name__ == "__main__":
    main() 