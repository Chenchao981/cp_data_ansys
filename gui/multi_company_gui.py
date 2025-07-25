#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 多公司支持版GUI界面
支持HuaHong和JeTech两家公司的数据处理流程

功能特性:
- 左侧导航栏: 公司选择，选中高亮效果
- 右侧内容区: 动态切换不同公司的专用界面
- 默认界面: 启动时显示HuaHong界面
- 状态保持: 切换公司后保持各自的设置
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                             QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiCompanyCPDataGUI(QMainWindow):
    """
    多公司CP数据分析工具主界面
    
    架构设计:
    - 左侧导航栏: 200px固定宽度，公司选择按钮
    - 右侧内容区: 自适应宽度，动态切换公司界面
    - 默认状态: 启动时显示HuaHong界面
    """
    
    # 信号定义
    company_changed = pyqtSignal(str)  # 公司切换信号
    
    def __init__(self):
        super().__init__()
        self.current_company = "huahong"  # 默认选中HuaHong
        self.company_widgets = {}  # 存储公司界面组件
        
        # 初始化界面
        self.setup_ui()
        self.setup_connections()
        
        # 设置窗口属性
        self.setWindowTitle("CP数据分析工具 - 多公司版")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        logger.info("多公司GUI界面初始化完成")
    
    def setup_ui(self):
        """设置主界面UI"""
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        self.setup_main_layout(central_widget)
        
        # 创建导航栏
        self.setup_navigation_bar()
        
        # 创建内容区
        self.setup_content_area()
        
        # 创建状态栏
        self.setup_status_bar()
    
    def setup_main_layout(self, central_widget):
        """设置主布局：左侧导航 + 右侧内容"""
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
    
    def setup_navigation_bar(self):
        """设置左侧导航栏"""
        self.navigation_widget = self.create_navigation_widget()
        self.main_layout.addWidget(self.navigation_widget)
    
    def create_navigation_widget(self):
        """创建导航栏组件"""
        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)  # 宽度适应三个公司按钮
        nav_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f0f0f0);
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(nav_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 导航标题
        title_label = QLabel("公司选择")
        title_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 27px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                color: #2c3e50;
                padding: 25px 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #d5dbdb);
                border-bottom: 2px solid #bdc3c7;
                letter-spacing: 0.8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 添加一些顶部间距
        layout.addSpacing(15)
        
        # 公司选择按钮
        self.hh_button = self.create_nav_button("🏢 HuaHong", "huahong", True)
        self.jt_button = self.create_nav_button("🏭 JeTech", "jetech", False)
        self.lion_button = self.create_nav_button("🦁 Lion", "lion", False)
        
        layout.addWidget(self.hh_button)
        layout.addWidget(self.jt_button)
        layout.addWidget(self.lion_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 版本信息
        version_label = QLabel("版本: v2.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 11px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                padding: 15px;
                background-color: rgba(189, 195, 199, 0.1);
                border-top: 1px solid #ecf0f1;
            }
        """)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        return nav_widget
    
    def create_nav_button(self, text, company_id, is_selected=False):
        """创建导航按钮"""
        button = QPushButton(text)
        button.setFixedHeight(65)  # 增加30%：50 * 1.3 = 65
        button.setFixedWidth(200)  # 适应新的导航栏宽度
        button.company_id = company_id
        button.setCheckable(True)
        button.setChecked(is_selected)
        
        # 设置按钮样式
        self.update_button_style(button, is_selected)
        
        # 绑定点击事件
        button.clicked.connect(lambda: self.on_company_selected(company_id))
        
        return button
    
    def update_button_style(self, button, is_selected):
        """更新按钮样式 - 现代商务风格"""
        if is_selected:
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #64B5F6, stop:1 #1976D2);
                    color: white;
                    border: none;
                    border-left: 5px solid #0D47A1;
                    text-align: left;
                    font-size: 21px;
                    font-weight: 600;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    margin: 8px 10px;
                    border-radius: 12px;
                    padding-left: 18px;
                    padding-right: 12px;
                    min-height: 60px;
                    box-shadow: 0 3px 10px rgba(25, 118, 210, 0.25);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #42A5F5, stop:1 #1565C0);
                    box-shadow: 0 5px 15px rgba(25, 118, 210, 0.35);
                    border-left: 5px solid #0D47A1;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1565C0, stop:1 #0D47A1);
                    box-shadow: 0 2px 6px rgba(25, 118, 210, 0.2);
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    color: #495057;
                    border: 1px solid #dee2e6;
                    text-align: left;
                    font-size: 21px;
                    font-weight: 500;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    margin: 8px 10px;
                    border-radius: 12px;
                    padding-left: 18px;
                    padding-right: 12px;
                    min-height: 60px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #e9ecef);
                    color: #212529;
                    border: 1px solid #adb5bd;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
                    border-left: 4px solid #6c757d;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    border: 1px solid #6c757d;
                    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
                }
            """)
    
    def setup_content_area(self):
        """设置右侧内容区"""
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border: none;
            }
        """)
        self.main_layout.addWidget(self.content_stack)
        
        # 创建占位界面
        self.create_placeholder_widgets()
    
    def create_placeholder_widgets(self):
        """创建实际的公司界面组件"""
        try:
            # 导入HuaHong界面组件
            from gui.widgets.huahong_widget import HuaHongWidget
            hh_widget = HuaHongWidget()
            
            # 导入JeTech界面组件
            from gui.widgets.jetech_widget import JeTechWidget
            jt_widget = JeTechWidget()
            
            # 导入Lion界面组件
            from gui.widgets.lion_widget import LionWidget
            lion_widget = LionWidget()
            
            # 添加到堆栈
            self.content_stack.addWidget(hh_widget)
            self.content_stack.addWidget(jt_widget)
            self.content_stack.addWidget(lion_widget)
            
            # 存储组件引用
            self.company_widgets["huahong"] = hh_widget
            self.company_widgets["jetech"] = jt_widget
            self.company_widgets["lion"] = lion_widget
            
            # 默认显示HuaHong界面
            self.content_stack.setCurrentWidget(hh_widget)
            
            logger.info("公司界面组件创建成功")
            
        except ImportError as e:
            logger.warning(f"导入公司界面组件失败，使用占位界面: {e}")
            
            # 使用占位界面作为备用方案
            # HuaHong占位界面
            hh_placeholder = QWidget()
            hh_layout = QVBoxLayout(hh_placeholder)
            hh_label = QLabel("HuaHong界面\n（组件加载失败）")
            hh_label.setAlignment(Qt.AlignCenter)
            hh_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    color: #666;
                    padding: 50px;
                }
            """)
            hh_layout.addWidget(hh_label)
            
            # JeTech占位界面
            jt_placeholder = QWidget()
            jt_layout = QVBoxLayout(jt_placeholder)
            jt_label = QLabel("JeTech界面\n（组件加载失败）")
            jt_label.setAlignment(Qt.AlignCenter)
            jt_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    color: #666;
                    padding: 50px;
                }
            """)
            jt_layout.addWidget(jt_label)
            
            # Lion占位界面
            lion_placeholder = QWidget()
            lion_layout = QVBoxLayout(lion_placeholder)
            lion_label = QLabel("Lion界面\n（组件加载失败）")
            lion_label.setAlignment(Qt.AlignCenter)
            lion_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    color: #666;
                    padding: 50px;
                }
            """)
            lion_layout.addWidget(lion_label)
            
            # 添加到堆栈
            self.content_stack.addWidget(hh_placeholder)
            self.content_stack.addWidget(jt_placeholder)
            self.content_stack.addWidget(lion_placeholder)
            
            # 存储组件引用
            self.company_widgets["huahong"] = hh_placeholder
            self.company_widgets["jetech"] = jt_placeholder
            self.company_widgets["lion"] = lion_placeholder
            
            # 默认显示HuaHong界面
            self.content_stack.setCurrentWidget(hh_placeholder)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"当前公司: HuaHong", 0)
    
    def setup_connections(self):
        """设置信号连接"""
        self.company_changed.connect(self.on_company_changed)
    
    def on_company_selected(self, company_id):
        """处理公司选择事件"""
        if company_id == self.current_company:
            return  # 避免重复切换
        
        logger.info(f"切换公司: {self.current_company} -> {company_id}")
        
        # 更新当前公司
        old_company = self.current_company
        self.current_company = company_id
        
        # 更新导航按钮样式
        self.update_navigation_styles()
        
        # 切换内容区
        self.switch_content_area(company_id)
        
        # 更新状态栏
        company_name_map = {
            "huahong": "HuaHong",
            "jetech": "JeTech", 
            "lion": "Lion"
        }
        company_name = company_name_map.get(company_id, company_id)
        self.status_bar.showMessage(f"当前公司: {company_name}", 0)
        
        # 发送公司切换信号
        self.company_changed.emit(company_id)
        
        logger.info(f"公司切换完成: {company_name}")
    
    def update_navigation_styles(self):
        """更新导航按钮样式"""
        # 更新HH按钮样式
        is_hh_selected = self.current_company == "huahong"
        self.hh_button.setChecked(is_hh_selected)
        self.update_button_style(self.hh_button, is_hh_selected)
        
        # 更新JT按钮样式
        is_jt_selected = self.current_company == "jetech"
        self.jt_button.setChecked(is_jt_selected)
        self.update_button_style(self.jt_button, is_jt_selected)
        
        # 更新Lion按钮样式
        is_lion_selected = self.current_company == "lion"
        self.lion_button.setChecked(is_lion_selected)
        self.update_button_style(self.lion_button, is_lion_selected)
    
    def switch_content_area(self, company_id):
        """切换内容区域"""
        if company_id in self.company_widgets:
            widget = self.company_widgets[company_id]
            self.content_stack.setCurrentWidget(widget)
            logger.debug(f"切换到 {company_id} 界面")
        else:
            logger.warning(f"找不到公司 {company_id} 的界面组件")
    
    def on_company_changed(self, company_id):
        """公司切换事件处理"""
        logger.info(f"公司切换事件: {company_id}")
        # 这里可以添加额外的公司切换逻辑
        # 例如：保存当前状态、加载新公司配置等
    
    def add_company_widget(self, company_id, widget):
        """添加公司界面组件"""
        if company_id in self.company_widgets:
            # 移除旧的组件
            old_widget = self.company_widgets[company_id]
            self.content_stack.removeWidget(old_widget)
            old_widget.deleteLater()
        
        # 添加新组件
        self.content_stack.addWidget(widget)
        self.company_widgets[company_id] = widget
        
        logger.info(f"添加公司界面组件: {company_id}")
    
    def get_current_company(self):
        """获取当前选中的公司"""
        return self.current_company
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(self, '确认退出', 
                                   '确定要退出CP数据分析工具吗？',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            logger.info("用户确认退出应用")
            event.accept()
        else:
            event.ignore()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("CP数据分析工具")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("CP Data Analysis Team")
    
    # 创建主窗口
    window = MultiCompanyCPDataGUI()
    window.show()
    
    logger.info("多公司GUI应用启动完成")
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 