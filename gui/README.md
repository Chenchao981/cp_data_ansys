# 🔬 CP数据分析工具 - GUI版本

## 📋 简介

这是CP数据分析工具的图形用户界面版本，提供简洁易用的操作界面，让用户通过三个简单步骤完成从原始数据到交互式图表的全流程分析。

## 🎯 设计理念

- **高度自动化**：最少的用户配置，智能默认设置
- **操作简洁**：三步完成分析流程
- **流程清晰**：直观的界面引导用户操作

## 🚀 快速开始

### 📦 环境要求

```bash
pip install PyQt5 pandas numpy plotly openpyxl
```

### 🏃‍♂️ 启动GUI

```bash
cd gui
python cp_data_gui.py
```

## 📖 使用指南

### 🔄 操作流程

#### 第一步：选择路径
1. **数据文件夹**：选择包含DCP数据文件(.txt或.dcp)的文件夹
2. **输出文件夹**：选择图表输出位置（默认与输入文件夹相同）

#### 第二步：清洗数据
1. 点击 **"🧹 开始清洗数据"** 按钮
2. 系统自动执行：
   - 扫描DCP数据文件
   - 数据清洗和格式化
   - 提取规格信息
   - 生成中间数据文件

#### 第三步：生成图表
1. 点击 **"📊 生成图表"** 按钮
2. 系统自动生成：
   - 📈 良率分析图表
   - 📦 箱体统计图表
   - 🌈 参数散点图表
   - 所有图表均为HTML交互式格式

### 🎨 界面说明

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 CP数据分析工具                                            │
├─────────────────────────────────────────────────────────────┤
│  📁 数据文件夹: [路径输入框]           [选择文件夹...]        │
│  📁 输出文件夹: [路径输入框]           [选择文件夹...]        │
│                                                             │
│           [🧹 开始清洗数据]    [📊 生成图表]                 │
│                                                             │
│  📋 处理状态:                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 实时显示处理进度和状态信息...                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 功能特性

#### ✨ 自动化特性
- **参数选择**：所有测试参数默认全选，无需手动配置
- **图表类型**：所有图表类型默认生成，无需选择
- **输出格式**：默认HTML交互式图表，无需配置
- **路径设置**：输出路径默认与输入路径相同

#### 🛡️ 用户体验
- **实时反馈**：处理过程实时显示进度和状态
- **错误处理**：友好的错误提示和解决建议
- **后台处理**：使用多线程，界面不会卡顿
- **智能引导**：按钮状态智能控制，引导正确操作流程

#### 📊 输出结果
- **良率图表**：Wafer良率趋势、批次对比、参数折线图
- **箱体图表**：参数分布统计、异常值检测
- **交互功能**：缩放、平移、悬停提示、数据点选择
- **自动打开**：完成后可选择自动打开输出文件夹

## 📁 文件结构

```
gui/
├── cp_data_gui.py          # GUI主程序
├── README.md               # 使用说明文档
└── requirements.txt        # 依赖包列表
```

## 🔧 技术实现

### 🏗️ 架构设计

```python
CPDataGUI (主窗口)
├── DataProcessingThread (后台处理线程)
│   ├── _clean_data()      # 数据清洗
│   └── _generate_charts() # 图表生成
├── UI组件
│   ├── 路径选择器
│   ├── 操作按钮
│   ├── 进度条
│   └── 状态显示区
└── 事件处理
    ├── 文件夹选择
    ├── 数据处理
    └── 状态更新
```

### 🔗 依赖模块

- **PyQt5**：GUI框架
- **clean_dcp_data**：数据清洗模块
- **dcp_spec_extractor**：规格提取模块
- **YieldChart**：良率图表生成
- **BoxplotChart**：箱体图表生成

## 🐛 故障排除

### 常见问题

#### 1. 启动失败
**问题**：运行时提示模块导入错误
**解决**：
```bash
# 确保在项目根目录运行
cd /path/to/cp_data_ansys
python gui/cp_data_gui.py

# 或者安装缺失的依赖
pip install PyQt5 pandas numpy plotly openpyxl
```

#### 2. 数据清洗失败
**问题**：未找到DCP数据文件
**解决**：
- 确保选择的文件夹包含 `.txt` 或 `.dcp` 格式的数据文件
- 检查文件权限，确保程序可以读取文件

#### 3. 图表生成失败
**问题**：缺少清洗后的数据文件
**解决**：
- 确保先完成数据清洗步骤
- 检查输出文件夹是否包含 `*_cleaned_*.csv` 和 `*_spec_*.csv` 文件

#### 4. 界面卡顿
**问题**：处理大文件时界面无响应
**解决**：
- 这是正常现象，处理在后台进行
- 观察状态显示区的进度信息
- 避免在处理过程中关闭程序

## 📈 性能优化

### 🚀 处理速度
- **多线程处理**：数据处理在后台线程执行，不阻塞界面
- **批量操作**：支持同时处理多个DCP文件
- **内存优化**：分批处理大数据文件，避免内存溢出

### 💾 存储优化
- **智能路径**：输出路径默认与输入路径相同，减少磁盘占用
- **格式优化**：生成压缩的HTML文件，减少存储空间

## 🔄 版本更新

### v1.0 (当前版本)
- ✅ 基础GUI界面
- ✅ 三步式操作流程
- ✅ 自动化数据处理
- ✅ 实时进度反馈
- ✅ 错误处理机制

### 🚧 计划功能
- 📊 图表预览功能
- ⚙️ 高级设置选项
- 📱 响应式界面设计
- 🌐 多语言支持

## 📞 技术支持

如果遇到问题或有改进建议，请：

1. 检查本文档的故障排除部分
2. 查看状态显示区的错误信息
3. 检查项目根目录的日志文件
4. 联系技术支持团队

---

> 💡 **提示**：建议在使用前先用小批量数据测试，确认流程正常后再处理大批量数据。 