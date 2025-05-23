# CP数据可视化前端模块 - 混合式架构规划

## 🎯 项目目标
基于已清洗的CP数据文件，生成多种类型的数据可视化图表，用于分析半导体晶圆片的特性分析。

## 🏗️ 架构设计：混合式架构（方案1）

### 核心理念
- **🚀 开发期**：快速基于现有文件验证功能
- **🏗️ 扩展期**：支持内存数据处理，提升性能  
- **🌐 B/S架构**：天然支持Web部署，数据可缓存

### 架构优势
1. **渐进式发展**：从文件处理平滑升级到内存处理
2. **多数据源支持**：文件、内存、缓存三种数据源
3. **统一接口**：DataManager提供一致的数据访问API
4. **工厂模式**：ChartFactory统一管理图表创建
5. **向下兼容**：保持现有文件处理流程不变

## 📂 项目结构（混合式架构版）

```
frontend/
├── core/                    # 🎯 核心架构层
│   ├── data_manager.py      # 数据管理器（支持文件/内存/缓存）
│   ├── chart_factory.py     # 图表工厂（统一创建接口）
│   └── config.py            # 配置管理
├── data_sources/            # 📡 数据源适配器层
│   ├── file_adapter.py      # 文件数据适配器（兼容现有CSV）
│   ├── memory_adapter.py    # 内存数据适配器（DataFrame处理）
│   └── cache_adapter.py     # 缓存数据适配器（性能优化）
├── charts/                  # 📊 图表生成层
│   ├── base_chart.py        # 图表基类（定义统一接口）
│   ├── line_chart.py        # 折线图（良率趋势）
│   ├── scatter_chart.py     # 散点图（参数关联）
│   ├── box_chart.py         # 箱体图（参数分布）
│   └── normal_dist.py       # 正态分布图（单参数分析）
├── utils/                   # 🛠️ 工具层
│   ├── data_loader.py       # 数据加载器（升级版）
│   └── validators.py        # 数据验证工具
└── main.py                  # 🚀 快速测试入口（升级版）
```

## 🗂️ 数据源说明
- **数据目录**: `../data/` (真实测试数据，无需测试文件夹)
- **输出目录**: `../output/` (处理后的CSV文件)

### 数据文件类型：
1. **spec.csv** - 参数规格文件
   - 包含参数名称、单位、上下限值
   - 用途：提供图表中的单位信息和参考限值

2. **yield.csv** - 良率统计文件  
   - 包含各参数的良率统计数据
   - 用途：生成折线图，展示良率趋势

3. **cleaned.csv** - 清洗后的测试数据
   - 包含所有芯片的测试结果
   - 用途：生成散点图、箱体图、正态分布图

## 🚀 开发计划（分阶段实施）

### 🏗️ 第1阶段：基础架构搭建（1-2天）
**目标**：建立混合式架构的基础框架
- [ ] `core/data_manager.py` - 数据管理器核心类
- [ ] `data_sources/file_adapter.py` - 文件适配器（兼容现有CSV）
- [ ] `charts/base_chart.py` - 图表基类
- [ ] `core/chart_factory.py` - 图表工厂
- [ ] 验证基础架构可用性

### 📊 第2阶段：第一个图表实现（1天）
**目标**：实现折线图，验证整个架构
- [ ] `charts/line_chart.py` - 折线图实现
- [ ] 基于yield.csv数据源
- [ ] 验证DataManager → FileAdapter → LineChart完整流程
- [ ] 确保图表基类设计合理

### 📈 第3阶段：完善图表模块（2-3天）
**目标**：实现其余三种图表类型
- [ ] `charts/scatter_chart.py` - 散点图（参数关联分析）
- [ ] `charts/box_chart.py` - 箱体图（参数分布）
- [ ] `charts/normal_dist.py` - 正态分布图（单参数分析）
- [ ] 验证所有图表类型正常工作

### 🧠 第4阶段：内存处理能力（1天）
**目标**：添加内存数据处理，提升性能
- [ ] `data_sources/memory_adapter.py` - 内存适配器
- [ ] `data_sources/cache_adapter.py` - 缓存适配器
- [ ] 验证内存处理性能提升
- [ ] 完善DataManager的auto模式

### 🌐 第5阶段：B/S架构准备（1天）
**目标**：为后期Web部署做准备
- [ ] 添加Web API接口设计
- [ ] 优化图表输出格式（支持Web显示）
- [ ] 性能测试和优化
- [ ] 文档完善

## 📋 核心类设计

### DataManager（数据管理器）
```python
class DataManager:
    """混合式数据管理器 - 支持文件/内存/缓存多种数据源"""
    
    def __init__(self, data_source="auto", cache_enabled=True):
        """
        初始化数据管理器
        Args:
            data_source: "file", "memory", "cache", "auto"
            cache_enabled: 是否启用缓存
        """
        pass
    
    def get_data(self, data_type, lot_id=None, **kwargs):
        """
        统一数据获取接口
        Args:
            data_type: "cleaned", "yield", "spec"
            lot_id: 批次ID
        Returns:
            pandas.DataFrame: 数据
        """
        pass
    
    def _auto_load_data(self, data_type, lot_id, **kwargs):
        """智能数据源选择（优先内存，fallback到文件）"""
        pass
```

### ChartFactory（图表工厂）
```python
class ChartFactory:
    """图表工厂 - 统一图表创建接口"""
    
    def __init__(self, data_manager):
        """初始化图表工厂"""
        pass
    
    def create_chart(self, chart_type, **params):
        """
        创建指定类型图表
        Args:
            chart_type: "line", "scatter", "box", "normal"
            **params: 图表参数
        Returns:
            BaseChart: 图表对象
        """
        pass
    
    def generate_all_charts(self, lot_id, output_dir="./charts_output"):
        """
        一键生成所有图表
        Args:
            lot_id: 批次ID
            output_dir: 输出目录
        Returns:
            List[BaseChart]: 图表列表
        """
        pass
```

### BaseChart（图表基类）
```python
class BaseChart:
    """图表基类 - 定义统一接口"""
    
    def __init__(self, data_manager, lot_id=None, **params):
        """初始化图表"""
        pass
    
    def load_required_data(self):
        """加载图表所需数据 - 子类实现"""
        raise NotImplementedError
    
    def generate(self):
        """生成图表 - 子类实现"""
        raise NotImplementedError
    
    def save(self, output_dir, filename=None):
        """
        保存图表
        Args:
            output_dir: 输出目录
            filename: 文件名（可选）
        Returns:
            Path: 保存路径
        """
        pass
```

### FileAdapter（文件适配器）
```python
class FileAdapter:
    """文件数据适配器 - 兼容现有文件结构"""
    
    def __init__(self, data_dir="../output"):
        """初始化文件适配器"""
        pass
    
    def load_data(self, data_type, lot_id=None, **kwargs):
        """
        从CSV文件加载数据
        Args:
            data_type: "cleaned", "yield", "spec"
            lot_id: 批次ID
        Returns:
            pandas.DataFrame: 数据
        """
        pass
    
    def _load_cleaned_data(self, lot_id):
        """加载清洗后的测试数据"""
        pass
    
    def _load_yield_data(self, lot_id):
        """加载良率统计数据"""
        pass
    
    def _load_spec_data(self, lot_id):
        """加载参数规格数据"""
        pass
```

### MemoryAdapter（内存适配器）
```python
class MemoryAdapter:
    """内存数据适配器 - 支持直接处理DataFrame"""
    
    def __init__(self):
        """初始化内存适配器"""
        pass
    
    def load_data(self, data_type, lot_id=None, **kwargs):
        """从内存获取数据"""
        pass
    
    def store_data(self, data_type, data, lot_id=None):
        """存储数据到内存"""
        pass
    
    def clear_cache(self):
        """清空内存缓存"""
        pass
```

## 💻 使用示例

### 基础使用（基于文件）
```python
from frontend.core.data_manager import DataManager
from frontend.core.chart_factory import ChartFactory

# 创建数据管理器和图表工厂
data_manager = DataManager(data_source="file")
chart_factory = ChartFactory(data_manager)

# 生成单个图表
line_chart = chart_factory.create_chart('line', lot_id='FA54-5339-327A-250501@203')
line_chart.save('./output')

# 生成所有图表
charts = chart_factory.generate_all_charts(lot_id='FA54-5339-327A-250501@203')
```

### 高级使用（混合模式）
```python
# 启用缓存和自动数据源选择
data_manager = DataManager(data_source="auto", cache_enabled=True)
chart_factory = ChartFactory(data_manager)

# 批量处理多个批次（第一次从文件，后续从缓存）
lot_ids = ['FA54-5339-327A-250501@203', 'FA54-5340-325A-250502@203', 'FA54-5341-327A-250430@203']
for lot_id in lot_ids:
    charts = chart_factory.generate_all_charts(lot_id=lot_id)
    print(f"批次 {lot_id} 图表生成完成")
```

### 内存处理模式
```python
# 直接处理内存中的DataFrame
from frontend.data_sources.memory_adapter import MemoryAdapter

memory_adapter = MemoryAdapter()
# 假设已有DataFrame数据
memory_adapter.store_data("cleaned", cleaned_df, lot_id="TEST_LOT")

data_manager = DataManager(data_source="memory")
chart_factory = ChartFactory(data_manager)
charts = chart_factory.generate_all_charts(lot_id="TEST_LOT")
```

## 🛠️ 技术栈
- **Python**: 核心编程语言
- **Pandas**: 数据处理和分析
- **Matplotlib/Seaborn**: 图表绘制
- **Pathlib**: 文件路径处理
- **设计模式**: 工厂模式、适配器模式、策略模式

## 📝 开发规范

### 代码规范
1. **模块化设计**：每个模块职责单一，接口清晰
2. **统一数据接口**：通过DataManager统一访问数据
3. **工厂模式**：通过ChartFactory统一创建图表
4. **向下兼容**：保持对现有文件结构的支持
5. **异常处理**：完善的错误处理和日志记录

### 文件命名规范
- **类文件**: 使用小写+下划线，如 `data_manager.py`
- **类名**: 使用驼峰命名，如 `DataManager`
- **方法名**: 使用小写+下划线，如 `load_data()`
- **常量**: 使用大写+下划线，如 `DEFAULT_DATA_DIR`

### 测试规范
- **每个模块包含测试代码**: `if __name__ == "__main__"`
- **独立可运行**: 每个文件都可以单独测试
- **数据验证**: 输入输出数据格式验证
- **异常测试**: 异常情况的处理测试

## 🧪 测试方法

### 单元测试
```bash
# 测试数据管理器
python -m frontend.core.data_manager

# 测试文件适配器
python -m frontend.data_sources.file_adapter

# 测试图表模块
python -m frontend.charts.line_chart

# 测试图表工厂
python -m frontend.core.chart_factory
```

### 集成测试
```bash
# 运行主程序（完整流程测试）
python frontend/main.py

# 批量测试所有图表
python -c "
from frontend.core.data_manager import DataManager
from frontend.core.chart_factory import ChartFactory

dm = DataManager(data_source='file')
cf = ChartFactory(dm)
charts = cf.generate_all_charts('FA54-5339-327A-250501@203')
print(f'生成了 {len(charts)} 个图表')
"
```

### 性能测试
```python
import time
from frontend.core.data_manager import DataManager

# 测试文件vs内存性能
start_time = time.time()
dm_file = DataManager(data_source="file")
data1 = dm_file.get_data("cleaned", "FA54-5339-327A-250501@203")
file_time = time.time() - start_time

start_time = time.time()
dm_cache = DataManager(data_source="auto", cache_enabled=True)
data2 = dm_cache.get_data("cleaned", "FA54-5339-327A-250501@203")  # 第二次访问
cache_time = time.time() - start_time

print(f"文件加载耗时: {file_time:.3f}s")
print(f"缓存加载耗时: {cache_time:.3f}s")
print(f"性能提升: {file_time/cache_time:.1f}x")
```

## 📈 开发状态

### ✅ 已完成
- [x] 项目结构设计
- [x] 架构方案确定
- [x] 核心类设计
- [x] 开发计划制定
- [x] 技术栈选择
- [x] 开发规范制定

### 🚧 进行中
- [ ] 基础架构搭建
- [ ] 数据管理器实现
- [ ] 文件适配器实现

### 📋 待开始  
- [ ] 图表基类实现
- [ ] 图表工厂实现
- [ ] 折线图模块开发
- [ ] 散点图模块开发
- [ ] 箱体图模块开发
- [ ] 正态分布图模块开发
- [ ] 内存适配器实现
- [ ] 缓存适配器实现
- [ ] B/S架构适配
- [ ] 性能优化
- [ ] 文档完善

## 🎯 里程碑时间线

| 阶段 | 目标 | 预计完成时间 | 关键交付物 |
|------|------|-------------|-----------|
| 第1阶段 | 基础架构 | 2天 | DataManager, FileAdapter, BaseChart |
| 第2阶段 | 折线图验证 | +1天 | LineChart, 完整流程验证 |
| 第3阶段 | 图表模块 | +3天 | 4种图表类型完整实现 |
| 第4阶段 | 内存处理 | +1天 | MemoryAdapter, CacheAdapter |
| 第5阶段 | B/S准备 | +1天 | Web接口设计, 性能优化 |
| **总计** | **完整系统** | **8天** | **生产可用的图表生成系统** |

## 🔄 后期扩展规划

### B/S架构扩展
```python
# Flask Web接口示例
from flask import Flask, jsonify, request
from frontend.core.data_manager import DataManager
from frontend.core.chart_factory import ChartFactory

app = Flask(__name__)

@app.route('/api/charts/<chart_type>/<lot_id>')
def generate_chart_api(chart_type, lot_id):
    """Web API接口 - 生成指定图表"""
    try:
        data_manager = DataManager(data_source="auto", cache_enabled=True)
        chart_factory = ChartFactory(data_manager)
        
        chart = chart_factory.create_chart(chart_type, lot_id=lot_id)
        chart_path = chart.save('./web_output')
        
        return jsonify({
            'status': 'success',
            'chart_url': f'/static/charts/{chart_path.name}',
            'chart_type': chart_type,
            'lot_id': lot_id
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/charts/batch/<lot_id>')
def generate_all_charts_api(lot_id):
    """Web API接口 - 生成所有图表"""
    try:
        data_manager = DataManager(data_source="auto", cache_enabled=True)
        chart_factory = ChartFactory(data_manager)
        
        charts = chart_factory.generate_all_charts(lot_id=lot_id, output_dir='./web_output')
        
        chart_urls = []
        for chart in charts:
            chart_urls.append({
                'type': chart.__class__.__name__,
                'url': f'/static/charts/{chart.filename}'
            })
        
        return jsonify({
            'status': 'success',
            'lot_id': lot_id,
            'charts': chart_urls,
            'total': len(charts)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

### 多用户支持
```python
# 用户隔离的数据管理
class MultiUserDataManager(DataManager):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.user_cache_prefix = f"user_{user_id}_"
    
    def get_data(self, data_type, lot_id=None, **kwargs):
        # 添加用户前缀到缓存键
        cache_key = f"{self.user_cache_prefix}{data_type}_{lot_id}_{hash(str(kwargs))}"
        # ... 其余逻辑
```

### 分布式处理
```python
# 任务队列支持（Celery）
from celery import Celery

app = Celery('chart_generator')

@app.task
def generate_chart_async(chart_type, lot_id, user_id):
    """异步图表生成任务"""
    data_manager = MultiUserDataManager(user_id, data_source="auto")
    chart_factory = ChartFactory(data_manager)
    
    chart = chart_factory.create_chart(chart_type, lot_id=lot_id)
    chart_path = chart.save(f'./user_output/{user_id}')
    
    return {
        'chart_path': str(chart_path),
        'status': 'completed'
    }
```

## 🚀 下一步行动

### 立即开始：第1阶段基础架构搭建
1. **创建目录结构**
   ```bash
   mkdir -p frontend/{core,data_sources,charts}
   touch frontend/core/{__init__.py,data_manager.py,chart_factory.py,config.py}
   touch frontend/data_sources/{__init__.py,file_adapter.py,memory_adapter.py,cache_adapter.py}
   touch frontend/charts/{__init__.py,base_chart.py}
   ```

2. **实现核心类**
   - 从 `DataManager` 开始
   - 然后实现 `FileAdapter`
   - 接着实现 `BaseChart`
   - 最后实现 `ChartFactory`

3. **验证架构**
   - 创建简单的测试用例
   - 验证数据流: FileAdapter → DataManager → BaseChart
   - 确保设计合理可扩展

### 成功标准
- [ ] 能够通过DataManager加载现有CSV文件
- [ ] 能够通过ChartFactory创建图表对象
- [ ] 基础架构代码清晰易懂
- [ ] 为后续图表实现打好基础

---

**文档创建时间**: 2025-01-23  
**架构版本**: v1.0 混合式架构  
**规划状态**: 完成，准备实施  
**预计完成时间**: 8个工作日  
**负责人**: 开发团队  
**审核状态**: 待审核 