# Redis + Django 架构详细规划

## 🏗️ 架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  数据清洗模块    │───▶│  Redis数据库     │───▶│  Django后端     │───▶│  Web前端        │
│  clean_dcp_data │    │  内存存储       │    │  REST API      │    │  图表展示       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 第1阶段：Redis数据层 (1-2周)

### 数据结构设计
```python
# Redis Key设计
LOT:{lot_id}:cleaned     # 清洗后数据
LOT:{lot_id}:yield       # 良率数据  
LOT:{lot_id}:spec        # 规格数据
LOT:{lot_id}:meta        # 元数据信息

# 示例
LOT:FA54-5339:cleaned
LOT:FA54-5339:yield
LOT:FA54-5339:spec
```

### 工作内容
1. **Redis连接管理**
   ```python
   # redis_client.py
   import redis
   import pandas as pd
   import json
   import pickle
   
   class RedisDataManager:
       def __init__(self):
           self.client = redis.Redis(host='localhost', port=6379, db=0)
       
       def store_dataframe(self, key, df):
           # 序列化DataFrame
           serialized = pickle.dumps(df)
           self.client.set(key, serialized)
       
       def get_dataframe(self, key):
           # 反序列化DataFrame
           data = self.client.get(key)
           return pickle.loads(data) if data else None
   ```

2. **数据序列化优化**
   - DataFrame → Pickle/Parquet格式
   - 压缩算法选择
   - 过期策略设计

3. **clean_dcp_data.py集成**
   ```python
   # 在现有清洗脚本中添加
   def save_to_redis(cleaned_data, yield_data, spec_data, lot_id):
       redis_client = RedisDataManager()
       redis_client.store_dataframe(f"LOT:{lot_id}:cleaned", cleaned_data)
       redis_client.store_dataframe(f"LOT:{lot_id}:yield", yield_data)
       redis_client.store_dataframe(f"LOT:{lot_id}:spec", spec_data)
   ```

## 🌐 第2阶段：Django后端 (2-3周)

### Django项目结构
```
cp_visualization_backend/
├── cp_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/
│   ├── models.py          # 数据模型
│   ├── serializers.py     # API序列化
│   ├── views.py           # API视图
│   └── urls.py            # API路由
├── charts/
│   ├── generators.py      # 图表生成逻辑
│   └── utils.py           # 工具函数
└── requirements.txt
```

### API接口设计
```python
# API端点
GET /api/lots/                           # 获取所有批次列表
GET /api/lots/{lot_id}/                  # 获取特定批次信息
GET /api/lots/{lot_id}/data/{data_type}/ # 获取数据(cleaned/yield/spec)
GET /api/lots/{lot_id}/charts/{chart_type}/ # 获取图表数据
POST /api/charts/generate/               # 生成图表
```

### 工作内容
1. **Django模型设计**
   ```python
   # models.py
   class Lot(models.Model):
       lot_id = models.CharField(max_length=100, unique=True)
       created_at = models.DateTimeField(auto_now_add=True)
       wafer_count = models.IntegerField()
       status = models.CharField(max_length=20)
   
   class WaferData(models.Model):
       lot = models.ForeignKey(Lot, on_delete=models.CASCADE)
       wafer_id = models.CharField(max_length=50)
       # 其他字段...
   ```

2. **Redis集成到Django**
   ```python
   # services.py
   class DataService:
       def __init__(self):
           self.redis_client = RedisDataManager()
       
       def get_lot_data(self, lot_id, data_type):
           key = f"LOT:{lot_id}:{data_type}"
           return self.redis_client.get_dataframe(key)
   ```

3. **REST API实现**
   ```python
   # views.py
   from rest_framework.decorators import api_view
   from rest_framework.response import Response
   
   @api_view(['GET'])
   def get_lot_data(request, lot_id, data_type):
       service = DataService()
       data = service.get_lot_data(lot_id, data_type)
       if data is not None:
           return Response(data.to_dict('records'))
       return Response({'error': 'Data not found'}, status=404)
   ```

## 🎨 第3阶段：前端开发 (2-4周)

### 选项A: Django模板 (2周)
```html
<!-- dashboard.html -->
<div class="dashboard">
    <div class="lot-selector">
        <select id="lot-select">
            {% for lot in lots %}
            <option value="{{ lot.lot_id }}">{{ lot.lot_id }}</option>
            {% endfor %}
        </select>
    </div>
    
    <div class="charts-container">
        <div id="yield-chart"></div>
        <div id="scatter-chart"></div>
        <div id="box-chart"></div>
    </div>
</div>

<script>
// 使用Plotly.js生成图表
function loadCharts(lotId) {
    fetch(`/api/lots/${lotId}/charts/yield/`)
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('yield-chart', data.traces, data.layout);
        });
}
</script>
```

### 选项B: React前端 (4周)
```jsx
// LotDashboard.jsx
import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

function LotDashboard() {
    const [lots, setLots] = useState([]);
    const [selectedLot, setSelectedLot] = useState('');
    const [chartData, setChartData] = useState({});
    
    useEffect(() => {
        fetchLots();
    }, []);
    
    const fetchLots = async () => {
        const response = await fetch('/api/lots/');
        const data = await response.json();
        setLots(data);
    };
    
    return (
        <div className="dashboard">
            <LotSelector lots={lots} onSelect={setSelectedLot} />
            <ChartsContainer lotId={selectedLot} />
        </div>
    );
}
```

## 📊 第4阶段：图表生成服务 (1-2周)

### 图表服务设计
```python
# charts/generators.py
class ChartGenerator:
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def generate_yield_chart(self, lot_id):
        data = self.redis_client.get_dataframe(f"LOT:{lot_id}:yield")
        
        traces = [{
            'x': data['Parameter'].tolist(),
            'y': data['Yield'].tolist(),
            'type': 'scatter',
            'mode': 'lines+markers',
            'name': 'Yield Trend'
        }]
        
        layout = {
            'title': f'Yield Analysis - {lot_id}',
            'xaxis': {'title': 'Parameters'},
            'yaxis': {'title': 'Yield (%)'}
        }
        
        return {'traces': traces, 'layout': layout}
```

## 🚀 第5阶段：部署配置 (1周)

### Docker配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  django:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - django
```

## ⏱️ 开发时间估算

### 🔥 快速版本 (6-8周)
- Redis集成: 1-2周
- Django基础API: 2-3周  
- Django模板前端: 2周
- 部署配置: 1周

### 🚀 完整版本 (10-12周)
- Redis高级优化: 2周
- Django完整API: 3-4周
- React前端: 4周
- 测试+优化: 2-3周
- 生产部署: 1周

## 💰 成本效益分析

### 优势
✅ **真正的内存共享** - 多用户并发访问
✅ **Web界面友好** - 更好的用户体验
✅ **数据实时性** - Redis内存存储
✅ **可扩展性强** - 支持集群部署
✅ **API标准化** - RESTful接口

### 劣势
❌ **开发工作量大** - 6-12周开发周期
❌ **技术复杂度高** - 需要Redis、Django知识
❌ **运维成本增加** - 需要维护Redis服务
❌ **资源消耗** - 内存占用较大

## 🎯 推荐方案

### 场景1: 个人使用/小团队
**推荐**: 保持当前文件+缓存架构
- 开发周期: 0-1周
- 性能: 已经足够
- 维护: 简单

### 场景2: 多用户/企业级
**推荐**: Redis + Django架构
- 开发周期: 8-12周
- 适合多人协作
- 长期价值高

### 场景3: 快速验证
**推荐**: 混合方案
- 先用Streamlit快速搭建Web界面 (1-2周)
- 后期升级到Django (如需要)

## 🔄 迁移策略

如果选择Redis+Django方案，建议：

1. **第1步**: 保留现有架构，并行开发Redis集成
2. **第2步**: 开发Django API，复用现有图表逻辑  
3. **第3步**: 逐步迁移前端到Web界面
4. **第4步**: 性能优化和生产部署

这样可以确保业务连续性，降低迁移风险。 