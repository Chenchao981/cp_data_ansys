# JavaScript嵌入改进说明

## 问题描述

之前的版本中，所有生成的HTML图表文件都依赖于unpkg CDN来加载Plotly.js库：
```
include_plotlyjs='https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js'
```

这种方式存在以下问题：
- **网络依赖**：用户需要能够访问unpkg.com网站
- **加载失败**：在网络受限或CDN不可用时，图表无法正常显示
- **稳定性问题**：依赖外部服务的可用性

## 解决方案

### 1. 新增JavaScript嵌入工具模块

创建了 `frontend/charts/js_embedder.py` 模块，提供以下功能：
- 自动检测项目根目录中的 `plotly.min.js` 文件
- 将JavaScript内容完整嵌入到HTML文件中
- 支持缓存机制，避免重复读取文件
- 优雅降级：如果本地文件不可用，自动回退到默认CDN

### 2. 核心功能

```python
from frontend.charts.js_embedder import get_embedded_plotly_js

# 替换原来的CDN链接
fig.write_html(
    str(file_path),
    include_plotlyjs=get_embedded_plotly_js(),  # 本地嵌入
    validate=False
)
```

### 3. 涉及的文件修改

以下文件已完成CDN到本地嵌入的迁移：

1. **frontend/charts/boxplot_chart.py**
   - `save_chart()` 方法
   - `save_all_charts()` 方法

2. **frontend/charts/summary_chart/summary_chart.py**
   - `save_summary_chart()` 方法

3. **frontend/charts/yield_chart.py**
   - `save_chart()` 方法
   - `save_all_charts()` 方法

4. **chart_generator.py**
   - 箱体图生成部分
   - 散点图生成部分

5. **frontend/charts/boxplot_chart_app.py**
   - Streamlit下载功能

## 使用方法

### 1. 下载Plotly.js文件

项目根目录已包含 `plotly.min.js` 文件（版本2.26.0），无需手动下载。

如需更新版本，可执行：
```bash
curl -o plotly.min.js https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js
```

### 2. 验证功能

运行测试脚本验证功能是否正常：
```bash
python test_js_embedder.py
```

### 3. 生成图表

使用任何现有的图表生成工具，生成的HTML文件将自动包含完整的Plotly.js代码，无需网络连接即可查看。

## 优势

### ✅ 改进后的优势
- **完全离线**：生成的HTML文件可以在无网络环境下正常查看
- **加载稳定**：不依赖外部CDN服务的可用性
- **一致性**：所有用户看到的图表完全一致，不受网络环境影响
- **向后兼容**：如果本地文件不可用，自动回退到CDN模式

### 📊 文件大小对比
- **CDN版本**：HTML文件很小（~50KB），但需要网络加载JS（~3.6MB）
- **嵌入版本**：HTML文件较大（~3.7MB），但完全自包含

## 注意事项

1. **文件大小**：嵌入版本的HTML文件会增大约3.6MB，但换来了完全的独立性
2. **版本管理**：更新Plotly.js版本需要重新下载文件到项目根目录
3. **备份机制**：如果检测不到本地文件，系统会自动使用CDN作为备份

## 技术细节

### 自动路径检测
```python
# 从frontend/charts/js_embedder.py向上找到项目根目录
current_file = Path(__file__)
self.project_root = current_file.parent.parent.parent
self.plotly_js_path = self.project_root / "plotly.min.js"
```

### 缓存机制
```python
if self._plotly_js_content is not None:
    return self._plotly_js_content  # 使用缓存，避免重复读取
```

### 错误处理
```python
js_content = self.get_plotly_js_content()
if js_content is None:
    logger.warning("无法加载本地Plotly.js，将使用默认CDN")
    return True  # 回退到Plotly默认CDN
```

## 总结

这次改进成功解决了CDN依赖问题，让生成的图表文件具备了完全的离线查看能力，大大提升了用户体验和系统稳定性。用户不再需要担心网络问题导致的图表显示异常。 