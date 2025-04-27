import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt

# 导入各功能模块
from .readers import create_reader
from .analysis import StatsAnalyzer, YieldAnalyzer, CapabilityAnalyzer
from .plotting import BoxPlotter, WaferMapPlotter, ScatterPlotter
from .exporters import ExcelExporter
from .processing import DataTransformer

class CPDataProcessorApp:
    """CP数据处理器应用程序"""
    
    def __init__(self, root):
        """
        初始化应用程序
        
        Args:
            root: tkinter根窗口
        """
        self.root = root
        self.root.title("CP数据处理器")
        self.root.geometry("800x600")
        
        # 设置应用程序状态变量
        self.data = None
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.test_type = tk.StringVar(value="DCP格式")
        self.wafer_type = tk.StringVar(value="普通")
        
        # 图表选项变量
        self.show_boxplot = tk.BooleanVar(value=True)
        self.include_fact_info = tk.BooleanVar(value=True)
        self.show_scatter_plot = tk.BooleanVar(value=True)
        self.show_bin_map = tk.BooleanVar(value=True)
        self.show_data_color_map = tk.BooleanVar(value=True)
        self.add_cal_data = tk.BooleanVar(value=True)
        
        # 创建UI组件
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        # 输入文件
        ttk.Label(file_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        ttk.Button(file_frame, text="浏览...", command=self._browse_input_file).grid(row=0, column=2)
        
        # 输出文件
        ttk.Label(file_frame, text="输出文件:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, padx=5, sticky=tk.W+tk.E)
        ttk.Button(file_frame, text="浏览...", command=self._browse_output_file).grid(row=1, column=2)
        
        # 数据类型选择区域
        type_frame = ttk.LabelFrame(main_frame, text="数据类型", padding="10")
        type_frame.pack(fill=tk.X, pady=5)
        
        # 测试类型
        ttk.Label(type_frame, text="测试类型:").grid(row=0, column=0, sticky=tk.W)
        ttk.Combobox(type_frame, textvariable=self.test_type, values=["DCP格式", "CW格式", "MEX格式"]).grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # 圆片类型
        ttk.Label(type_frame, text="圆片类型:").grid(row=1, column=0, sticky=tk.W)
        ttk.Combobox(type_frame, textvariable=self.wafer_type, values=["普通", "MPW"]).grid(row=1, column=1, padx=5, sticky=tk.W)
        
        # 图表选项区域
        chart_frame = ttk.LabelFrame(main_frame, text="图表选项", padding="10")
        chart_frame.pack(fill=tk.X, pady=5)
        
        # 左侧选项
        ttk.Checkbutton(chart_frame, text="箱形图(boxplot chart)", variable=self.show_boxplot).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(chart_frame, text="包含Fact信息(include Fact info)", variable=self.include_fact_info).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(chart_frame, text="散点图(scatterPlot)", variable=self.show_scatter_plot).grid(row=2, column=0, sticky=tk.W)
        
        # 右侧选项
        ttk.Checkbutton(chart_frame, text="晶圆图(bin map)", variable=self.show_bin_map).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(chart_frame, text="数据颜色图(dataColorMap)", variable=self.show_data_color_map).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(chart_frame, text="添加计算数据(addCalData)", variable=self.add_cal_data).grid(row=2, column=1, sticky=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="整理数据", command=self._process_data, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def _bind_events(self):
        """绑定事件处理器"""
        pass
    
    def _browse_input_file(self):
        """浏览输入文件"""
        filetypes = [
            ("All Files", "*.*"),
            ("Text Files", "*.txt;*.csv"),
            ("Excel Files", "*.xlsx;*.xls")
        ]
        
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.input_file.set(filename)
            
            # 根据文件扩展名推断测试类型
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.txt' or ext == '.csv':
                if 'dcp' in filename.lower():
                    self.test_type.set("DCP格式")
                else:
                    self.test_type.set("CW格式")
            elif ext == '.xlsx' or ext == '.xls':
                self.test_type.set("MEX格式")
            
            # 根据文件名推断输出文件名
            base_name = os.path.splitext(os.path.basename(filename))[0]
            output_dir = os.path.dirname(filename)
            self.output_file.set(os.path.join(output_dir, f"{base_name}_结果.xlsx"))
    
    def _browse_output_file(self):
        """浏览输出文件"""
        filetypes = [("Excel Files", "*.xlsx")]
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=filetypes)
        if filename:
            self.output_file.set(filename)
    
    def _log(self, message):
        """向日志区域添加消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # 滚动到最后
        self.root.update()
    
    def _format_to_reader_type(self, format_str):
        """将显示格式转换为读取器类型"""
        if format_str == "DCP格式":
            return "dcp"
        elif format_str == "CW格式":
            return "cw"
        elif format_str == "MEX格式":
            return "mex"
        return "dcp"  # 默认
    
    def _process_data(self):
        """处理数据"""
        # 检查输入文件
        if not self.input_file.get():
            messagebox.showerror("错误", "请选择输入文件")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("错误", "输入文件不存在")
            return
        
        # 检查输出文件
        if not self.output_file.get():
            messagebox.showerror("错误", "请指定输出文件")
            return
        
        try:
            self.status_var.set("正在处理数据...")
            self._log(f"开始处理数据: {self.input_file.get()}")
            
            # 获取读取器类型
            reader_type = self._format_to_reader_type(self.test_type.get())
            
            # 创建读取器并读取数据
            self._log(f"使用 {self.test_type.get()} 读取器读取数据...")
            reader = create_reader(reader_type)
            self.data = reader.read(self.input_file.get())
            
            if isinstance(self.data, pd.DataFrame):
                self._log(f"成功读取数据: {len(self.data)} 行, {len(self.data.columns)} 列")
            else:
                self._log(f"成功读取数据")
            
            # 应用数据转换
            if self.add_cal_data.get():
                self._log("正在添加计算数据...")
                transformer = DataTransformer(self.data)
                # 这里可以添加一些计算参数的代码
                # 例如: transformer.add_calculated_parameter('新参数', lambda df: df['参数1'] + df['参数2'])
                self.data = transformer.data
            
            # 进行数据分析
            self._log("正在进行数据分析...")
            
            # 统计分析
            stats_analyzer = StatsAnalyzer(self.data, by_wafer=True)
            stats_results = stats_analyzer.analyze()
            self._log(f"完成统计分析")
            
            # 良率分析
            yield_analyzer = YieldAnalyzer(self.data)
            yield_results = yield_analyzer.analyze()
            self._log(f"完成良率分析: 总良率 {yield_results['total_yield']:.2f}%")
            
            # 创建Excel导出器
            exporter = ExcelExporter()
            
            # 添加原始数据
            exporter.add_dataframe(self.data, "原始数据")
            
            # 添加统计分析结果
            summary_df = stats_analyzer.get_summary(format='dataframe')
            exporter.add_dataframe(summary_df, "统计分析")
            
            # 添加良率分析结果
            wafer_yield_df = pd.DataFrame({
                '晶圆': list(yield_results['wafer_yields'].keys()),
                '良率(%)': [round(y, 2) for y in yield_results['wafer_yields'].values()]
            })
            exporter.add_dataframe(wafer_yield_df, "良率分析")
            
            # 绘制图表
            if self.show_boxplot.get():
                self._log("正在生成箱形图...")
                box_plotter = BoxPlotter(self.data)
                fig_box = box_plotter.plot().fig
                exporter.add_figure(fig_box, "箱形图")
            
            if self.show_bin_map.get() and 'X' in self.data.columns and 'Y' in self.data.columns:
                self._log("正在生成晶圆Bin图...")
                wafer_plotter = WaferMapPlotter(self.data)
                fig_bin = wafer_plotter.plot().fig
                exporter.add_figure(fig_bin, "晶圆Bin图")
            
            if self.show_data_color_map.get() and 'X' in self.data.columns and 'Y' in self.data.columns:
                self._log("正在生成数据颜色图...")
                # 选择第一个参数生成颜色图
                exclude_cols = ['Wafer', 'Seq', 'Bin', 'X', 'Y']
                params = [col for col in self.data.columns if col not in exclude_cols]
                if params:
                    wafer_plotter = WaferMapPlotter(self.data)
                    fig_param = wafer_plotter.plot(parameter=params[0]).fig
                    exporter.add_figure(fig_param, f"参数{params[0]}图")
            
            if self.show_scatter_plot.get():
                self._log("正在生成散点图...")
                # 选择前两个参数生成散点图
                exclude_cols = ['Wafer', 'Seq', 'Bin', 'X', 'Y']
                params = [col for col in self.data.columns if col not in exclude_cols]
                if len(params) >= 2:
                    scatter_plotter = ScatterPlotter(self.data)
                    fig_scatter = scatter_plotter.plot(x_param=params[0], y_param=params[1]).fig
                    exporter.add_figure(fig_scatter, f"{params[0]} vs {params[1]}")
            
            # 保存结果
            self._log(f"正在保存结果到: {self.output_file.get()}")
            success = exporter.save(self.output_file.get())
            
            if success:
                self._log("数据处理完成")
                self.status_var.set("处理完成")
                messagebox.showinfo("完成", f"数据处理完成，结果已保存到:\n{self.output_file.get()}")
            else:
                self._log("保存结果失败")
                self.status_var.set("保存失败")
                messagebox.showerror("错误", "保存结果失败")
            
        except Exception as e:
            self._log(f"处理过程中出错: {str(e)}")
            self.status_var.set("处理出错")
            messagebox.showerror("错误", f"处理数据时出错: {str(e)}")


def main():
    """应用程序入口点"""
    root = tk.Tk()
    app = CPDataProcessorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 