# 散点图功能说明

## 📊 功能概述

散点图模块是CP数据分析工具的核心功能之一，专门用于**参数关联分析**。通过可视化两个参数之间的关系，帮助工程师快速识别参数相关性、发现异常模式，并结合规格限制进行合格性分析。

## 🎯 主要功能

### 1. 参数关联分析
- **双参数散点图**：展示X轴和Y轴参数的分布关系
- **相关性计算**：自动计算并显示Pearson相关系数
- **趋势线拟合**：基于线性回归的趋势线和R²值

### 2. 规格限制可视化
- **规格区域显示**：基于spec.csv的LSL/USL绘制合格区域
- **状态标色**：合格点（绿色）vs 不合格点（红色）
- **规格合规检查**：自动判断每个数据点的合格性状态

### 3. 交互式图表
- **参数选择**：支持动态选择X/Y轴参数
- **批次筛选**：支持单批次或多批次分析
- **图表配置**：点大小、透明度、显示选项等可调节

## 📁 文件结构

```
frontend/charts/
├── scatter_chart.py          # 核心散点图类
├── scatter_chart_app.py      # Streamlit Web应用
├── scatter_chart.md          # 功能说明文档（本文件）
└── scatter_chart_plan.md     # 开发计划文档
```

## 🔧 技术架构

### 继承关系
```python
BaseChart (基类)
├── LineChart (折线图)
└── ScatterChart (散点图) ← 新实现
```

### 核心类：ScatterChart

#### 主要方法
- `__init__(data_manager, lot_id, x_param, y_param, **params)`: 初始化
- `load_required_data()`: 加载cleaned.csv和spec.csv数据
- `generate()`: 生成散点图
- `get_available_parameters()`: 获取可用参数列表
- `get_correlation_matrix()`: 计算相关性矩阵
- `update_parameters(x_param, y_param)`: 更新参数选择

#### 配置参数
```python
ScatterChart(
    data_manager=dm,
    lot_id="FA54-5339@203",
    x_param="Parameter1",
    y_param="Parameter2",
    point_size=30,           # 点大小
    point_alpha=0.7,         # 透明度
    show_spec_limits=True,   # 显示规格限制
    show_trend_line=True,    # 显示趋势线
    show_correlation=True    # 显示相关性信息
)
```

## 📊 数据要求

### 输入数据格式

#### cleaned.csv（必需）
```csv
LotID,WaferID,DieX,DieY,Parameter1,Parameter2,Parameter3,...
FA54-5339@203,W01,1,1,12.5,8.3,156.7,...
FA54-5339@203,W01,1,2,12.8,8.1,158.2,...
```

#### spec.csv（可选）
```csv
Parameter,LSL,USL,Target,Unit
Parameter1,10.0,15.0,12.5,mA
Parameter2,7.0,9.0,8.0,V
Parameter3,150.0,170.0,160.0,Ohm
```

### 数据验证
- **数值类型检查**：自动过滤非数值列
- **缺失值处理**：自动移除包含NaN的数据点
- **规格匹配**：自动匹配参数名称与规格定义

## 🎨 图表元素

### 散点可视化
- **合格点**：绿色（#2E8B57），在规格范围内
- **不合格点**：红色（#DC143C），超出规格范围
- **未知状态**：蓝色，无规格信息时的默认色

### 规格限制区域
- **颜色**：天蓝色（#87CEEB）
- **透明度**：20%
- **边框**：2px实线
- **显示条件**：仅当X和Y参数都有规格定义时显示

### 趋势线
- **颜色**：番茄色（#FF6347）
- **样式**：2px虚线
- **算法**：线性回归（scipy.stats.linregress）
- **显示信息**：R²决定系数

### 相关性信息
- **位置**：图表左上角
- **内容**：Pearson相关系数
- **背景**：白色半透明框

## 💻 使用方法

### 1. 编程接口使用

```python
from frontend.charts.scatter_chart import ScatterChart
from frontend.core.data_manager import DataManager

# 创建数据管理器
dm = DataManager(data_source="csv", data_dir="output")

# 创建散点图
chart = ScatterChart(
    data_manager=dm,
    lot_id="FA54-5339@203",
    x_param="Parameter1",
    y_param="Parameter2"
)

# 生成图表
if chart.generate():
    # 保存图表
    chart.save("./output", "scatter_param1_param2.png")
    
    # 获取相关性矩阵
    corr_matrix = chart.get_correlation_matrix()
    print(corr_matrix)
    
    # 关闭图表
    chart.close()
```

### 2. Web应用使用

```bash
# 启动Streamlit应用
streamlit run frontend/charts/scatter_chart_app.py
```

#### 操作步骤
1. **数据初始化**：设置数据目录，点击"初始化数据管理器"
2. **批次选择**：从下拉列表选择要分析的批次
3. **参数配置**：选择X轴和Y轴参数
4. **图表选项**：配置显示选项（规格限制、趋势线等）
5. **生成图表**：点击"生成散点图"按钮
6. **交互分析**：缩放、平移、悬停查看数据点详情
7. **导出保存**：设置输出路径和文件名，保存图表

## 📈 分析解读

### 相关性强度判断
- **|r| > 0.7**：强相关，参数间存在明显线性关系
- **0.3 < |r| < 0.7**：中等相关，参数间有一定关联
- **|r| < 0.3**：弱相关，参数间关联性较弱

### 趋势分析
- **R² > 0.5**：线性模型解释度较好
- **R² < 0.3**：线性关系不明显，可能存在非线性关系

### 异常点识别
- **离群点**：远离主要数据簇的点，可能是测试异常
- **规格外点**：超出规格限制的红色点，需要关注的问题点
- **边界点**：接近规格边界的点，存在风险

## 🔍 高级功能

### 1. 多参数相关性矩阵
```python
# 获取所有参数的相关性矩阵
corr_matrix = chart.get_correlation_matrix()

# 热图可视化（在Streamlit应用中自动提供）
```

### 2. 动态参数更新
```python
# 更新分析的参数对
chart.update_parameters("Parameter3", "Parameter4")
chart.generate()  # 重新生成图表
```

### 3. 批量分析
```python
# 分析多个参数组合
param_pairs = [
    ("Parameter1", "Parameter2"),
    ("Parameter1", "Parameter3"),
    ("Parameter2", "Parameter3")
]

for x_param, y_param in param_pairs:
    chart = ScatterChart(dm, lot_id, x_param, y_param)
    chart.generate()
    chart.save("./output", f"scatter_{x_param}_{y_param}.png")
    chart.close()
```

## ⚡ 性能优化

### 数据量处理
- **推荐数据量**：< 10,000 数据点
- **大数据量优化**：自动采样或分批处理
- **内存管理**：及时调用`close()`方法释放内存

### 渲染优化
- **Matplotlib后端**：生成静态图片时使用'Agg'后端
- **点密度控制**：大数据量时自动调整点大小和透明度
- **缓存机制**：相同参数组合的结果可缓存复用

## 🐛 常见问题

### 1. 数据加载失败
**问题**：`无法加载cleaned数据`
**解决**：
- 检查数据目录路径是否正确
- 确认cleaned.csv文件存在且格式正确
- 检查文件权限

### 2. 参数不可用
**问题**：`X轴参数不存在于数据中`
**解决**：
- 使用`get_available_parameters()`查看可用参数
- 检查参数名称拼写是否正确
- 确认参数为数值类型

### 3. 规格限制不显示
**问题**：规格区域未显示
**解决**：
- 检查spec.csv文件是否存在
- 确认参数名称在spec.csv中有对应定义
- 检查LSL/USL列是否有有效数值

### 4. 内存使用过高
**问题**：处理大数据量时内存不足
**解决**：
- 分批处理数据
- 及时关闭图表对象
- 降低点密度或使用数据采样

## 🔄 与其他模块的集成

### 数据流
```
CSV文件 → DataManager → ScatterChart → 图表输出
```

### 依赖模块
- **基础架构**：`BaseChart`提供统一接口
- **数据管理**：`DataManager`负责数据加载
- **文件工具**：`file_utils`处理文件操作
- **数据验证**：`data_validator`确保数据质量

### 扩展性
- **新图表类型**：可基于相同架构实现箱体图、正态分布图
- **数据源扩展**：支持数据库、API等其他数据源
- **导出格式**：可扩展支持PDF等格式

## 📝 更新日志

### v1.0.0 (2025-01-23)
- ✅ 实现基础散点图功能
- ✅ 集成规格限制可视化
- ✅ 添加趋势线和相关性分析
- ✅ 创建Streamlit Web应用
- ✅ 完善文档和测试

### 计划功能
- 🔄 3D散点图支持
- 🔄 动画时序分析
- 🔄 聚类分析集成
- 🔄 异常检测算法

## 🧪 **手动测试指南**

### 1. 核心功能测试

#### 测试散点图类基础功能
```bash
# 进入项目根目录
cd D:\cp_data_ansys

# 运行核心类测试
cd frontend\charts
python scatter_chart.py
```

**预期结果**：
- ✅ 输出："散点图生成成功！"
- ✅ 生成测试图片：`scatter_chart_test.png`
- ✅ 显示可用参数列表
- ✅ 输出相关性矩阵

### 2. Streamlit Web应用测试

#### 启动命令
```bash
# 返回项目根目录
cd D:\cp_data_ansys

# 1. 先启动良率分析应用
streamlit run frontend/yield_analyzer_app.py --server.port 8504

# 2. 再启动散点图应用 
streamlit run frontend/charts/scatter_chart_app.py --server.port 8505
```

#### 首次启动设置
如果是首次使用Streamlit，会看到邮箱设置提示：
```
Welcome to Streamlit!
Email: 
```
**解决方法**：直接按 `Enter` 键跳过，或输入任意邮箱

#### 访问应用
应用启动成功后，会显示：
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8505
Network URL: http://192.168.x.x:8505
```

在浏览器打开：`http://localhost:8505`

### 3. Web应用测试步骤

#### 第一步：数据初始化
1. 在侧边栏设置数据目录（默认：`output`）
2. 点击 **"初始化数据管理器"** 按钮
3. 确认显示："数据管理器初始化成功！"

#### 第二步：批次和参数选择
1. **选择批次**：从下拉菜单选择要分析的批次
   - 示例批次：`FA54-5339@203`、`FA54-5340@203`
2. **选择参数**：
   - **X轴参数**：选择第一个分析参数
   - **Y轴参数**：选择第二个分析参数
   - 确保X轴和Y轴参数不同

#### 第三步：图表配置
在侧边栏 **"图表选项"** 中设置：
- ✅ **显示规格限制**：显示spec.csv定义的合格区域
- ✅ **显示趋势线**：显示线性回归趋势线
- ✅ **显示相关性信息**：显示Pearson相关系数
- 调整 **点大小**：10-100（推荐30）
- 调整 **透明度**：0.1-1.0（推荐0.7）

#### 第四步：生成和分析
1. 点击 **"🚀 生成散点图"** 按钮
2. 等待处理，确认显示："散点图生成成功！"
3. 查看生成的交互式散点图

#### 第五步：结果验证
**图表检查**：
- 🟢 **绿色点**：合格数据点（在规格范围内）
- 🔴 **红色点**：不合格数据点（超出规格范围）
- 🔵 **蓝色区域**：规格限制范围（如果启用）
- 📈 **虚线**：线性趋势线（如果启用）

**数据统计**：
- 数据点总数
- 合格数量
- 不合格数量
- 相关系数值

**相关性矩阵**：
- 查看参数相关性热图
- 点击 **"查看相关性数值表"** 展开详细数据

#### 第六步：导出测试
1. 设置 **输出目录**：`./charts_output`
2. 设置 **文件名**：`scatter_参数1_参数2.png`
3. 点击 **"💾 保存图表"**
4. 确认显示保存成功信息

### 4. 故障排除

#### 端口冲突问题

**1. 查看Streamlit进程**
```bash
# 查看所有streamlit进程
tasklist | findstr streamlit

# 查看端口占用情况  
netstat -ano | findstr ":850"
```

**2. 清理僵尸进程**
```bash
# 强制终止所有streamlit进程
taskkill /F /IM streamlit.exe

# 或终止特定PID的进程
taskkill /F /PID <进程ID>
```

**3. 重新启动应用**
```bash
# 重启良率分析应用（8504端口）
streamlit run frontend/yield_analyzer_app.py --server.port 8504

# 启动散点图应用（8505端口）  
streamlit run frontend/charts/scatter_chart_app.py --server.port 8505
```

**4. 如果8505端口冲突，使用其他端口**：
```bash
streamlit run frontend/charts/scatter_chart_app.py --server.port 8506
streamlit run frontend/charts/scatter_chart_app.py --server.port 8507
```

#### 数据加载失败
- 检查数据目录是否包含 `cleaned.csv` 文件
- 确认文件格式正确（包含数值型参数列）
- 检查文件权限

#### 参数不可用
- 确认数据中包含数值型列
- 检查参数名称不包含坐标列（DieX、DieY等）

#### 中文字体警告
Windows系统可能显示中文字体警告，不影响功能：
```
UserWarning: Glyph xxx missing from font(s) Arial
```
**解决**：忽略此警告，或安装中文字体支持

### 5. 性能测试

#### 大数据量测试
测试不同数据规模的响应时间：
- **< 1K 数据点**：瞬时响应
- **1K-10K 数据点**：< 3秒
- **> 10K 数据点**：可能需要优化

#### 内存使用测试
```bash
# 监控内存使用
tasklist | findstr python
```

### 6. 测试检查清单

#### 功能测试 ✅
- [ ] 核心类测试通过
- [ ] Web应用启动成功
- [ ] 数据管理器初始化正常
- [ ] 参数选择功能正常
- [ ] 散点图生成成功
- [ ] 规格限制显示正确
- [ ] 趋势线计算正确
- [ ] 相关性矩阵显示正常
- [ ] 图表导出成功

#### 交互测试 ✅
- [ ] 参数切换响应正常
- [ ] 图表缩放平移正常
- [ ] 悬停信息显示正确
- [ ] 配置选项生效

#### 异常测试 ✅
- [ ] 相同参数选择提示错误
- [ ] 无效数据处理正常
- [ ] 缺失文件容错处理

---
**作者**: CP数据分析工具开发团队  
**创建日期**: 2025-01-23  
**更新日期**: 2025-01-23  
**版本**: v1.0.0  
**测试指南添加**: 2025-01-23 