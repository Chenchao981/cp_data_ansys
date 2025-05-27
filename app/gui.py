#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据处理器 - 图形用户界面
提供直观的GUI界面进行数据处理
"""

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import CPDataProcessor


class CPDataProcessorGUI:
    """CP数据处理器GUI类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("CP数据处理器")
        self.root.geometry("600x500")
        
        self.input_files = []
        self.processor = CPDataProcessor()
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.file_listbox = tk.Listbox(file_frame, height=6)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        file_scroll = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=file_scroll.set)
        
        # 文件操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # 数据格式选择
        ttk.Label(main_frame, text="数据格式:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.format_var = tk.StringVar(value="dcp")
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(format_frame, text="DCP", variable=self.format_var, value="dcp").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="CW", variable=self.format_var, value="cw").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="MEX", variable=self.format_var, value="mex").pack(side=tk.LEFT, padx=10)
        
        # 图表选项
        ttk.Label(main_frame, text="图表选项:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        self.boxplot_var = tk.BooleanVar()
        self.scatter_var = tk.BooleanVar()
        self.wafer_map_var = tk.BooleanVar()
        
        chart_frame = ttk.Frame(main_frame)
        chart_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(chart_frame, text="箱形图", variable=self.boxplot_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(chart_frame, text="散点图", variable=self.scatter_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(chart_frame, text="晶圆图", variable=self.wafer_map_var).pack(side=tk.LEFT, padx=10)
        
        # 输出文件选择
        ttk.Label(main_frame, text="输出文件:").grid(row=7, column=0, sticky=tk.W, pady=5)
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览", command=self.select_output_file).pack(side=tk.RIGHT, padx=5)
        
        # 处理按钮
        ttk.Button(main_frame, text="开始处理", command=self.process_data).grid(row=9, column=0, columnspan=2, pady=20)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=11, column=0, columnspan=2, pady=5)
        
    def add_files(self):
        """添加输入文件"""
        files = filedialog.askopenfilenames(
            title="选择CP测试数据文件",
            filetypes=[
                ("所有支持格式", "*.txt *.csv *.xls *.xlsx"),
                ("DCP文件", "*.txt"),
                ("CW文件", "*.csv"),
                ("MEX文件", "*.xls *.xlsx"),
                ("所有文件", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)
                
    def clear_files(self):
        """清空文件列表"""
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
        
    def select_output_file(self):
        """选择输出文件"""
        file = filedialog.asksaveasfilename(
            title="保存结果文件",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file:
            self.output_var.set(file)
            
    def process_data(self):
        """处理数据"""
        if not self.input_files:
            messagebox.showerror("错误", "请先选择输入文件")
            return
            
        if not self.output_var.get():
            messagebox.showerror("错误", "请选择输出文件")
            return
            
        # 开始处理
        self.progress.start()
        self.status_var.set("正在处理...")
        self.root.update()
        
        try:
            success = self.processor.process_files(
                file_paths=self.input_files,
                data_format=self.format_var.get(),
                output_path=self.output_var.get(),
                enable_boxplot=self.boxplot_var.get(),
                enable_scatter=self.scatter_var.get(),
                enable_wafer_map=self.wafer_map_var.get()
            )
            
            if success:
                messagebox.showinfo("成功", "数据处理完成！")
                self.status_var.set("处理完成")
            else:
                messagebox.showerror("错误", "数据处理失败")
                self.status_var.set("处理失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"处理过程中发生错误：{e}")
            self.status_var.set("处理失败")
            
        finally:
            self.progress.stop()


def gui_main():
    """GUI主函数"""
    root = tk.Tk()
    app = CPDataProcessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    gui_main()
