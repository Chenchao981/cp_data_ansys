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
import socket
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                             QMessageBox, QStatusBar)
from PyQt5.QtCore import QSettings, Qt, pyqtSignal, QTimer

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

import logging

from gui.theme import (
    DEFAULT_THEME,
    LIGHT_THEME,
    THEME_SETTINGS_APPLICATION,
    THEME_SETTINGS_KEY,
    THEME_SETTINGS_ORGANIZATION,
    apply_application_theme,
    normalize_theme,
    opposite_theme,
    set_widget_property,
    theme_button_text,
    theme_button_tooltip,
)

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
    theme_changed = pyqtSignal(str)
    
    def __init__(self, initial_theme=None, remember_theme=True):
        super().__init__()
        self.current_company = "huahong"  # 默认选中HuaHong
        self.company_widgets = {}  # 存储公司界面组件
        self.remember_theme = remember_theme
        self.theme_settings = QSettings(
            THEME_SETTINGS_ORGANIZATION,
            THEME_SETTINGS_APPLICATION,
        )
        saved_theme = (
            self.theme_settings.value(THEME_SETTINGS_KEY, DEFAULT_THEME)
            if remember_theme
            else DEFAULT_THEME
        )
        self.current_theme = normalize_theme(initial_theme or saved_theme)
        
        # 初始化界面
        self.setup_ui()
        self.setup_connections()
        self.apply_theme(self.current_theme, remember=False)
        
        # 设置窗口属性
        self.setWindowTitle("CP数据分析工具 - 多公司版")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        logger.info("多公司GUI界面初始化完成")
    
    def setup_ui(self):
        """设置主界面UI"""
        # 创建中央widget
        central_widget = QWidget()
        central_widget.setObjectName("appRoot")
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
        nav_widget.setObjectName("navigationPanel")
        nav_widget.setFixedWidth(220)  # 宽度适应三个公司按钮
        
        layout = QVBoxLayout(nav_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 导航标题
        title_label = QLabel("公司选择")
        title_label.setObjectName("navigationHeader")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 添加一些顶部间距
        layout.addSpacing(15)
        
        # 公司选择按钮
        self.hh_button = self.create_nav_button("🏢 HuaHong", "huahong", True)
        self.jt_button = self.create_nav_button("🏭 JeTech", "jetech", False)
        self.lion_button = self.create_nav_button("🦁 Lion", "lion", False)
        self.guoyu_button = self.create_nav_button("国宇FRD", "guoyu", False)
        
        layout.addWidget(self.hh_button)
        layout.addWidget(self.jt_button)
        layout.addWidget(self.lion_button)
        layout.addWidget(self.guoyu_button)

        # 添加弹性空间
        layout.addStretch()

        self.theme_toggle_button = QPushButton()
        self.theme_toggle_button.setObjectName("themeToggleButton")
        self.theme_toggle_button.setMinimumHeight(44)
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_toggle_button)
        
        # 版本信息
        version_label = QLabel("版本: v2.0")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        return nav_widget
    
    def create_nav_button(self, text, company_id, is_selected=False):
        """创建导航按钮"""
        button = QPushButton(text)
        button.setObjectName("navButton")
        button.setFixedHeight(65)  # 增加30%：50 * 1.3 = 65
        button.setFixedWidth(200)  # 适应新的导航栏宽度
        button.company_id = company_id
        button.setCheckable(True)
        button.setChecked(is_selected)
        
        # 绑定点击事件
        button.clicked.connect(lambda: self.on_company_selected(company_id))
        
        return button
    
    def update_button_style(self, button, is_selected):
        """更新导航按钮选中状态；视觉由全局主题统一控制。"""
        button.setChecked(is_selected)
        button.update()
    
    def setup_content_area(self):
        """设置右侧内容区"""
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
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

            from gui.widgets.guoyu_widget import GuoyuWidget
            guoyu_widget = GuoyuWidget()

            for widget in (hh_widget, jt_widget, lion_widget, guoyu_widget):
                widget.cockpit_requested.connect(self.open_cp_cockpit)
            
            # 添加到堆栈
            self.content_stack.addWidget(hh_widget)
            self.content_stack.addWidget(jt_widget)
            self.content_stack.addWidget(lion_widget)
            self.content_stack.addWidget(guoyu_widget)
            
            # 存储组件引用
            self.company_widgets["huahong"] = hh_widget
            self.company_widgets["jetech"] = jt_widget
            self.company_widgets["lion"] = lion_widget
            self.company_widgets["guoyu"] = guoyu_widget
            
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
            hh_label.setProperty("role", "placeholder")
            hh_layout.addWidget(hh_label)
            
            # JeTech占位界面
            jt_placeholder = QWidget()
            jt_layout = QVBoxLayout(jt_placeholder)
            jt_label = QLabel("JeTech界面\n（组件加载失败）")
            jt_label.setAlignment(Qt.AlignCenter)
            jt_label.setProperty("role", "placeholder")
            jt_layout.addWidget(jt_label)
            
            # Lion占位界面
            lion_placeholder = QWidget()
            lion_layout = QVBoxLayout(lion_placeholder)
            lion_label = QLabel("Lion界面\n（组件加载失败）")
            lion_label.setAlignment(Qt.AlignCenter)
            lion_label.setProperty("role", "placeholder")
            lion_layout.addWidget(lion_label)

            guoyu_placeholder = QWidget()
            guoyu_layout = QVBoxLayout(guoyu_placeholder)
            guoyu_label = QLabel("国宇FRD界面\n（组件加载失败）")
            guoyu_label.setAlignment(Qt.AlignCenter)
            guoyu_label.setProperty("role", "placeholder")
            guoyu_layout.addWidget(guoyu_label)
            
            # 添加到堆栈
            self.content_stack.addWidget(hh_placeholder)
            self.content_stack.addWidget(jt_placeholder)
            self.content_stack.addWidget(lion_placeholder)
            self.content_stack.addWidget(guoyu_placeholder)
            
            # 存储组件引用
            self.company_widgets["huahong"] = hh_placeholder
            self.company_widgets["jetech"] = jt_placeholder
            self.company_widgets["lion"] = lion_placeholder
            self.company_widgets["guoyu"] = guoyu_placeholder
            
            # 默认显示HuaHong界面
            self.content_stack.setCurrentWidget(hh_placeholder)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("mainStatusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"当前公司: HuaHong", 0)
    
    def setup_connections(self):
        """设置信号连接"""
        self.company_changed.connect(self.on_company_changed)

    def apply_theme(self, theme_name, remember=True):
        """应用全局主题，并按需记住用户上次选择。"""
        app = QApplication.instance()
        self.current_theme = normalize_theme(theme_name)
        if app is not None:
            self.current_theme = apply_application_theme(app, self.current_theme)

        set_widget_property(self, "theme", self.current_theme)
        self.theme_toggle_button.setText(theme_button_text(self.current_theme))
        self.theme_toggle_button.setToolTip(theme_button_tooltip(self.current_theme))

        if remember and self.remember_theme:
            self.theme_settings.setValue(THEME_SETTINGS_KEY, self.current_theme)
            self.theme_settings.sync()

        self.theme_changed.emit(self.current_theme)
        logger.info("界面主题已切换为: %s", self.current_theme)

    def toggle_theme(self, _checked=False):
        """在暗黑主题和亮色主题之间切换。"""
        self.apply_theme(opposite_theme(self.current_theme))
        display_name = "亮色主题" if self.current_theme == LIGHT_THEME else "暗黑主题"
        self.status_bar.showMessage(f"已切换到{display_name}", 3000)
    
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
            "lion": "Lion",
            "guoyu": "国宇FRD"
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

        is_guoyu_selected = self.current_company == "guoyu"
        self.guoyu_button.setChecked(is_guoyu_selected)
        self.update_button_style(self.guoyu_button, is_guoyu_selected)
    
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

    def get_current_output_dir(self):
        """获取当前页面的输出目录，用于打开 CP Cockpit。"""
        widget = self.company_widgets.get(self.current_company)
        if widget is not None:
            output_dir = getattr(widget, "output_dir", "")
            if output_dir:
                return str(Path(output_dir).expanduser())

            output_edit = getattr(widget, "output_path_edit", None)
            if output_edit is not None:
                text = output_edit.text().strip()
                if text:
                    return text

        return str(Path.home() / "Desktop")

    def get_runtime_root(self):
        """获取源码运行或 release/app.pyz 运行时的根目录。"""
        argv0 = Path(sys.argv[0]).resolve()
        if argv0.suffix.lower() == ".pyz":
            return argv0.parent
        return Path(__file__).resolve().parents[1]

    def is_cockpit_port_open(self, port=8501):
        """检查 Streamlit 服务端口是否已启动。"""
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            return False

    def open_cp_cockpit(self):
        """启动或打开 CP Cockpit 前端。"""
        data_dir = self.get_current_output_dir()
        port = 8501
        runtime_root = self.get_runtime_root()
        project_root = Path(__file__).resolve().parents[1]
        app_candidates = [
            runtime_root / "frontend" / "yield_analyzer_app.py",
            project_root / "frontend" / "yield_analyzer_app.py",
        ]
        app_path = next((path for path in app_candidates if path.exists()), None)

        if app_path is None:
            QMessageBox.critical(
                self,
                "错误",
                "找不到 CP Cockpit 入口，已搜索:\n" + "\n".join(str(path) for path in app_candidates),
            )
            return

        if not self.is_cockpit_port_open(port):
            env = os.environ.copy()
            env["CP_COCKPIT_DATA_DIR"] = data_dir
            pyz_path = runtime_root / "app.pyz"
            if pyz_path.exists():
                env["PYTHONPATH"] = str(pyz_path) + os.pathsep + env.get("PYTHONPATH", "")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "streamlit",
                        "run",
                        str(app_path),
                        "--server.headless",
                        "true",
                        "--server.port",
                        str(port),
                        "--browser.gatherUsageStats",
                        "false",
                    ],
                    cwd=str(runtime_root if runtime_root.exists() else project_root),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                self.status_bar.showMessage("正在启动 CP Cockpit...", 3000)
            except Exception as exc:
                logger.error(f"启动 CP Cockpit 失败: {exc}", exc_info=True)
                QMessageBox.critical(self, "错误", f"启动 CP Cockpit 失败:\n{exc}")
                return

        url = f"http://127.0.0.1:{port}/?data_dir={quote(data_dir)}"
        QTimer.singleShot(1500, lambda: webbrowser.open(url))
        self.status_bar.showMessage(f"CP Cockpit 数据目录: {data_dir}", 5000)

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
