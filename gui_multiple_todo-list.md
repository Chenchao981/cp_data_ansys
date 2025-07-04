# 🏭 GUI多公司支持开发任务清单 - 完善版

**项目目标**: 在现有CP数据分析工具GUI中添加多公司支持，实现HuaHong(HH)和JeTech(JT)两家公司的独立数据处理界面

**开发日期**: 2025-01-06
**预期完成**: 2025-01-10
**负责人**: 开发团队

---

## 📋 项目概览

### 🎯 核心需求 (基于UI原型图)

- **左侧导航栏**: 添加公司选择功能（HuaHong、JeTech）
- **右侧内容区**: 根据公司选择动态切换界面内容
- **功能分离**: 不同公司使用各自的数据处理流程
- **界面一致性**: 保持现有GUI设计风格和布局
- **默认界面**: 启动时默认显示HuaHong界面
- **选中效果**: 侧边栏选中项显示底色高亮效果

### 🏗️ 技术架构设计

```
多公司GUI架构
├── 🧭 左侧导航栏 (Side Navigation) - 200px宽
│   ├── HuaHong公司选项 (默认选中)
│   ├── JeTech公司选项
│   └── 选中状态视觉反馈
├── 📱 右侧内容区 (Content Area) - 自适应宽度
│   ├── HuaHong界面 (复用现有gui/cp_data_gui.py)
│   └── JeTech界面 (新增JT专用界面)
└── ⚙️ 后端处理逻辑
    ├── HuaHong数据处理流程 (现有)
    └── JeTech数据处理流程 (jt_data_processor + jt_chart_generator)
```

---

## 📝 详细任务分解

### 阶段一: 主界面架构搭建 (0.5天)

#### ✅ 任务1.1: 创建多公司GUI主文件

- [ ] **创建主文件**: `gui/multi_company_gui.py`
  ```python
  class MultiCompanyCPDataGUI(QMainWindow):
      def __init__(self):
          super().__init__()
          self.setWindowTitle("CP数据分析工具 - 多公司版")
          self.setGeometry(100, 100, 1200, 800)
          self.current_company = "HuaHong"  # 默认选中HH
          self.setup_ui()
          
      def setup_ui(self):
          self.setup_main_layout()
          self.setup_navigation_bar()
          self.setup_content_area()
          self.setup_connections()
  ```

#### ✅ 任务1.2: 设计主布局结构

- [ ] **实现主布局**:
  ```python
  def setup_main_layout(self):
      central_widget = QWidget()
      self.setCentralWidget(central_widget)
      
      # 水平布局：左侧导航 + 右侧内容
      main_layout = QHBoxLayout(central_widget)
      main_layout.setContentsMargins(0, 0, 0, 0)
      main_layout.setSpacing(0)
      
      # 左侧导航栏 (固定宽度200px)
      self.navigation_widget = self.create_navigation_widget()
      main_layout.addWidget(self.navigation_widget)
      
      # 右侧内容区 (自适应)
      self.content_stack = QStackedWidget()
      main_layout.addWidget(self.content_stack)
  ```

#### ✅ 任务1.3: 创建导航栏组件

- [ ] **导航栏UI设计**:
  ```python
  def create_navigation_widget(self):
      nav_widget = QWidget()
      nav_widget.setFixedWidth(200)
      nav_widget.setStyleSheet("""
          QWidget {
              background-color: #f5f5f5;
              border-right: 1px solid #ddd;
          }
      """)
      
      layout = QVBoxLayout(nav_widget)
      
      # 导航标题
      title_label = QLabel("公司选择")
      title_label.setStyleSheet("font-weight: bold; padding: 10px;")
      layout.addWidget(title_label)
      
      # 公司选择按钮
      self.hh_button = self.create_nav_button("HuaHong", "huahong", True)
      self.jt_button = self.create_nav_button("JeTech", "jetech", False)
      
      layout.addWidget(self.hh_button)
      layout.addWidget(self.jt_button)
      layout.addStretch()
      
      return nav_widget
  ```

- [ ] **导航按钮样式**:
  ```python
  def create_nav_button(self, text, company_id, is_selected=False):
      button = QPushButton(text)
      button.setFixedHeight(50)
      button.company_id = company_id
      
      # 设置选中/未选中样式
      self.update_button_style(button, is_selected)
      
      # 绑定点击事件
      button.clicked.connect(lambda: self.on_company_selected(company_id))
      
      return button
  
  def update_button_style(self, button, is_selected):
      if is_selected:
          button.setStyleSheet("""
              QPushButton {
                  background-color: #2196F3;
                  color: white;
                  border: none;
                  text-align: left;
                  padding-left: 20px;
                  font-size: 14px;
              }
          """)
      else:
          button.setStyleSheet("""
              QPushButton {
                  background-color: transparent;
                  color: #333;
                  border: none;
                  text-align: left;
                  padding-left: 20px;
                  font-size: 14px;
              }
              QPushButton:hover {
                  background-color: #e3f2fd;
              }
          """)
  ```

### 阶段二: HuaHong界面迁移 (0.5天)

#### ✅ 任务2.1: 创建HuaHong界面组件

- [ ] **创建HH界面类**: `gui/widgets/huahong_widget.py`
  ```python
  class HuaHongWidget(QWidget):
      def __init__(self):
          super().__init__()
          self.processing_thread = None
          self.setup_ui()
          
      def setup_ui(self):
          # 直接复用现有cp_data_gui.py的UI布局
          self.init_ui_from_original()
          
      def init_ui_from_original(self):
          # 从原始GUI复制所有UI组件
          # 文件夹选择、按钮、状态显示等
          pass
  ```

#### ✅ 任务2.2: 复用现有HH数据处理逻辑

- [ ] **迁移DataProcessingThread**:
  ```python
  from gui.cp_data_gui import DataProcessingThread
  
  class HHDataProcessingThread(DataProcessingThread):
      """HH数据处理线程 - 复用现有逻辑"""
      pass
  ```

- [ ] **复用现有事件处理**:
  - 文件夹选择事件 (`browse_input_dir`, `browse_output_dir`)
  - 数据清洗启动 (`start_cleaning`)
  - 图表生成启动 (`start_generating`)
  - 进度更新处理 (`on_cleaning_finished`, `on_generating_finished`)

### 阶段三: JeTech界面开发 (1天)

#### ✅ 任务3.1: 创建JeTech界面组件

- [ ] **创建JT界面类**: `gui/widgets/jetech_widget.py`
  ```python
  class JeTechWidget(QWidget):
      def __init__(self):
          super().__init__()
          self.jt_processing_thread = None
          self.setup_ui()
          
      def setup_ui(self):
          # 参考HH界面布局，但调整为JT专用
          self.create_jt_ui_layout()
          
      def create_jt_ui_layout(self):
          layout = QVBoxLayout(self)
          
          # JT数据文件夹选择 (支持Excel文件)
          self.setup_jt_input_section(layout)
          
          # 输出文件夹选择
          self.setup_output_section(layout)
          
          # JT专用处理按钮
          self.setup_jt_action_buttons(layout)
          
          # 处理状态显示
          self.setup_status_section(layout)
  ```

#### ✅ 任务3.2: JT数据处理集成

- [ ] **创建JT数据处理线程**: `gui/threads/jt_processing_thread.py`
  ```python
  class JTDataProcessingThread(QThread):
      progress_updated = pyqtSignal(str)
      finished = pyqtSignal(bool, str)
      
      def __init__(self, input_dir, output_dir, operation_type):
          super().__init__()
          self.input_dir = input_dir
          self.output_dir = output_dir
          self.operation_type = operation_type
          
      def run(self):
          if self.operation_type == "clean":
              self._process_jt_data()
          elif self.operation_type == "generate":
              self._generate_jt_charts()
              
      def _process_jt_data(self):
          from jt_data_processor.jt_main_processor import process_jt_files
          try:
              result = process_jt_files(self.input_dir, self.output_dir)
              self.finished.emit(True, "JT数据处理完成")
          except Exception as e:
              self.finished.emit(False, f"JT数据处理失败: {e}")
              
      def _generate_jt_charts(self):
          from jt_chart_generator import main as generate_jt_charts
          try:
              generate_jt_charts()
              self.finished.emit(True, "JT图表生成完成")
          except Exception as e:
              self.finished.emit(False, f"JT图表生成失败: {e}")
  ```

#### ✅ 任务3.3: JT界面UI细节

- [ ] **JT输入区域设计**:
  ```python
  def setup_jt_input_section(self, layout):
      # JT数据文件夹选择
      input_group = QGroupBox("JT数据文件夹")
      input_layout = QVBoxLayout(input_group)
      
      # 文件夹路径显示
      self.jt_input_path_edit = QLineEdit()
      self.jt_input_path_edit.setPlaceholderText("请选择包含JT Excel文件的文件夹...")
      
      # 浏览按钮
      browse_button = QPushButton("浏览文件夹")
      browse_button.clicked.connect(self.browse_jt_input_dir)
      
      input_layout.addWidget(self.jt_input_path_edit)
      input_layout.addWidget(browse_button)
      layout.addWidget(input_group)
  ```

- [ ] **JT处理按钮设计**:
  ```python
  def setup_jt_action_buttons(self, layout):
      button_layout = QHBoxLayout()
      
      # JT数据处理按钮
      self.jt_clean_button = QPushButton("开始处理JT数据")
      self.jt_clean_button.setStyleSheet("""
          QPushButton {
              background-color: #4CAF50;
              color: white;
              border: none;
              padding: 10px 20px;
              font-size: 14px;
              border-radius: 5px;
          }
          QPushButton:hover {
              background-color: #45a049;
          }
      """)
      self.jt_clean_button.clicked.connect(self.start_jt_processing)
      
      # JT图表生成按钮
      self.jt_chart_button = QPushButton("生成JT图表")
      self.jt_chart_button.setStyleSheet("""
          QPushButton {
              background-color: #2196F3;
              color: white;
              border: none;
              padding: 10px 20px;
              font-size: 14px;
              border-radius: 5px;
          }
          QPushButton:hover {
              background-color: #1976D2;
          }
      """)
      self.jt_chart_button.clicked.connect(self.start_jt_chart_generation)
      
      button_layout.addWidget(self.jt_clean_button)
      button_layout.addWidget(self.jt_chart_button)
      button_layout.addStretch()
      
      layout.addLayout(button_layout)
  ```

### 阶段四: 界面交互和样式优化 (0.5天)

#### ✅ 任务4.1: 公司切换逻辑

- [ ] **实现公司切换功能**:
  ```python
  def on_company_selected(self, company_id):
      if company_id == self.current_company:
          return  # 避免重复切换
          
      # 更新当前公司
      self.current_company = company_id
      
      # 更新导航按钮样式
      self.update_navigation_styles()
      
      # 切换内容区
      self.switch_content_area(company_id)
      
      # 状态栏提示
      self.show_switch_message(company_id)
      
  def update_navigation_styles(self):
      # 更新HH按钮样式
      is_hh_selected = self.current_company == "huahong"
      self.update_button_style(self.hh_button, is_hh_selected)
      
      # 更新JT按钮样式
      is_jt_selected = self.current_company == "jetech"
      self.update_button_style(self.jt_button, is_jt_selected)
      
  def switch_content_area(self, company_id):
      if company_id == "huahong":
          self.content_stack.setCurrentWidget(self.hh_widget)
      elif company_id == "jetech":
          self.content_stack.setCurrentWidget(self.jt_widget)
  ```

#### ✅ 任务4.2: 状态保持功能

- [ ] **实现界面状态保持**:
  ```python
  def save_widget_state(self, widget, company_id):
      """保存界面状态到配置"""
      # 保存输入路径、输出路径等状态
      pass
      
  def restore_widget_state(self, widget, company_id):
      """恢复界面状态"""
      # 恢复之前保存的状态
      pass
  ```

### 阶段五: 完整集成和测试 (0.5天)

#### ✅ 任务5.1: 创建主启动文件

- [ ] **创建启动文件**: `gui/multi_company_main.py`
  ```python
  import sys
  from PyQt5.QtWidgets import QApplication
  from multi_company_gui import MultiCompanyCPDataGUI
  
  def main():
      app = QApplication(sys.argv)
      
      # 创建主窗口
      window = MultiCompanyCPDataGUI()
      window.show()
      
      # 运行应用
      sys.exit(app.exec_())
  
  if __name__ == "__main__":
      main()
  ```

#### ✅ 任务5.2: 功能验证测试

- [ ] **HuaHong功能测试**:
  - [ ] 界面加载正常
  - [ ] 数据处理流程正常
  - [ ] 图表生成功能正常
  - [ ] 与原GUI功能完全一致

- [ ] **JeTech功能测试**:
  - [ ] JT Excel文件选择正常
  - [ ] JT数据处理流程正常
  - [ ] JT图表生成功能正常
  - [ ] 输出CSV格式正确

- [ ] **界面交互测试**:
  - [ ] 公司切换流畅
  - [ ] 导航栏样式正确
  - [ ] 状态保持功能正常
  - [ ] 界面响应速度正常

#### ✅ 任务5.3: 启动脚本更新

- [ ] **更新启动脚本**: `gui/start_gui.bat`
  ```bat
  @echo off
  cd /d "%~dp0"
  python multi_company_main.py
  pause
  ```

---

## 🔧 技术实现细节

### 📁 文件结构 (完善版)

```
gui/
├── cp_data_gui.py                    # 原有GUI（保留备份）
├── multi_company_gui.py              # 新的多公司GUI主文件
├── multi_company_main.py             # 启动入口
├── widgets/
│   ├── __init__.py
│   ├── huahong_widget.py            # HuaHong界面
│   └── jetech_widget.py             # JeTech界面
├── threads/
│   ├── __init__.py
│   ├── hh_processing_thread.py       # HH数据处理线程
│   └── jt_processing_thread.py       # JT数据处理线程
├── styles/
│   ├── navigation_style.css          # 导航栏样式
│   └── widget_styles.css             # 组件样式
├── resources/
│   ├── huahong_logo.png             # HH公司Logo (可选)
│   └── jetech_logo.png              # JT公司Logo (可选)
├── start_gui.bat                    # 启动脚本
└── README.md                        # 使用说明
```

### 🎨 界面设计细节

#### 导航栏设计规范
- **宽度**: 200px (固定)
- **背景色**: #f5f5f5
- **选中背景**: #2196F3 (Material Design蓝)
- **选中文字**: 白色
- **未选中文字**: #333
- **悬停效果**: #e3f2fd (浅蓝色)
- **字体**: 微软雅黑 14px

#### 内容区设计规范
- **背景色**: 白色
- **边距**: 与原GUI保持一致
- **按钮样式**: 保持HH和JT界面按钮风格统一
- **状态显示**: 使用相同的样式和布局

### 🔗 模块集成策略

#### HuaHong模块集成
```python
# 复用现有完整处理流程
from gui.cp_data_gui import DataProcessingThread
from clean_dcp_data import process_directory
from frontend.charts.yield_chart import YieldChart
from frontend.charts.boxplot_chart import BoxplotChart
```

#### JeTech模块集成
```python
# 集成JT专用处理流程
from jt_data_processor.jt_main_processor import process_jt_files
from jt_chart_generator import main as generate_jt_charts
```

---

## 📊 开发进度跟踪

### 里程碑计划
- **Day 1前半天**: 完成主界面架构搭建
- **Day 1后半天**: 完成HuaHong界面迁移
- **Day 2**: 完成JeTech界面开发
- **Day 3前半天**: 完成界面交互和样式优化
- **Day 3后半天**: 完成集成测试和验证

### 开发优先级
1. **P0 (最高)**: 主界面架构 + 导航栏
2. **P1 (高)**: HuaHong界面迁移 (复用现有)
3. **P2 (中)**: JeTech界面开发 (新增)
4. **P3 (低)**: 样式优化 + 高级功能

---

## 🚨 风险控制

### 技术风险
1. **现有HH功能破坏**: 
   - 保留原GUI完整备份
   - 采用组件化设计，最小化影响
   
2. **JT模块集成问题**:
   - 先独立验证JT处理流程
   - 逐步集成，分步测试

3. **界面性能问题**:
   - 延迟加载非当前页面
   - 使用QStackedWidget优化内存

### 回退策略
- 保持原`cp_data_gui.py`完整性
- 新功能作为独立模块开发
- 支持快速回退到单公司模式

---

## ✅ 验收标准

### 功能验收
- [ ] 启动默认显示HuaHong界面
- [ ] 左侧导航栏正常显示两个公司选项
- [ ] 点击导航能正确切换界面，有选中高亮效果
- [ ] HuaHong界面功能与原GUI 100%一致
- [ ] JeTech界面能处理Excel文件，生成图表
- [ ] 界面切换状态保持正常

### 界面验收
- [ ] 导航栏选中效果符合UI原型图
- [ ] 两个公司界面布局风格统一
- [ ] 界面切换流畅，响应时间<1秒
- [ ] 不同分辨率下显示正常

### 性能验收
- [ ] 程序启动时间≤5秒
- [ ] 界面切换响应时间≤1秒
- [ ] 数据处理性能与原GUI一致
- [ ] 内存使用合理，无泄漏

---

**创建日期**: 2025-01-06
**最后更新**: 2025-01-06
**文档版本**: v2.0 - 完善版
**状态**: 准备开发 🚀
