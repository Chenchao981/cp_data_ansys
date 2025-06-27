# 🏭 厂商适配器模块

## 📋 概述

厂商适配器模块提供多厂商CP数据格式的统一适配功能，将不同厂商的数据格式转换为标准HH格式，实现数据清洗的模块化和可扩展性。

## 🎯 设计原则

- **统一输出**：所有厂商数据最终转换为HH标准CSV格式
- **最小侵入**：后端图表生成模块保持不变
- **可扩展性**：支持未来新增更多厂商格式
- **配置驱动**：通过配置文件管理厂商差异
- **向后兼容**：保持现有HH格式功能不变

## 🏗️ 架构设计

```
原始数据 → 厂商识别 → 专用读取器 → 厂商适配器 → 统一CPLot → 标准CSV → 图表生成
```

### 核心组件

1. **BaseCompanyAdapter** - 厂商适配器基类
2. **CompanyConfig** - 厂商配置管理
3. **HHAdapter** - HH公司适配器（标准格式）
4. **JTAdapter** - JT公司适配器（待开发）

## 📁 目录结构

```
company_adapters/
├── __init__.py                 # 模块初始化
├── README.md                   # 本文档
├── base_company_adapter.py     # 适配器基类
├── company_config.py           # 厂商配置管理
├── hh_adapter.py              # HH公司适配器
└── jt_adapter.py              # JT公司适配器（待开发）
```

## 🚀 使用方法

### 基本用法

```python
from cp_data_processor.readers.company_adapters import (
    get_company_config, 
    BaseCompanyAdapter
)
from cp_data_processor.readers.company_adapters.hh_adapter import HHAdapter

# 获取HH公司配置
config = get_company_config('HH')

# 创建HH适配器
adapter = HHAdapter(config)

# 转换数据格式
standardized_lot = adapter.transform_to_standard_format(original_lot)
```

### 厂商自动识别

```python
from cp_data_processor.readers.company_adapters.company_config import (
    detect_company_from_path,
    detect_company_from_filename
)

# 从文件路径识别厂商
company = detect_company_from_path('/data/HH_data/test.txt')  # 返回: 'HH'

# 从文件名识别厂商
company = detect_company_from_filename('JT_batch_001.csv')   # 返回: 'JT'
```

## ⚙️ 配置说明

### 厂商配置结构

```python
COMPANY_CONFIGS = {
    'HH': {
        'name': 'HH公司',
        'supported_formats': ['DCP', 'CW', 'MEX'],
        'field_mapping': {
            'Lot_ID': 'Lot_ID',    # HH -> HH (恒等映射)
            'Wafer_ID': 'Wafer_ID',
            # ... 其他字段
        },
        'unit_conversion': {},      # HH格式不需要单位转换
        'file_patterns': {
            'path_patterns': ['/HH_data/', '/hh/'],
            'filename_patterns': ['*_HH_*', 'HH_*']
        }
    },
    'JT': {
        'name': 'JT公司', 
        'supported_formats': ['JT'],
        'field_mapping': {
            'jt_lot_id': 'Lot_ID',     # JT -> HH 字段映射
            'jt_wafer_id': 'Wafer_ID',
            # ... 其他字段映射
        },
        'unit_conversion': {
            'VTH': {
                'factor': 0.001,       # mV -> V 单位转换
                'offset': 0.0
            }
        }
    }
}
```

## 🔧 开发新适配器

### 步骤1：添加厂商配置

在 `company_config.py` 中添加新厂商的配置：

```python
COMPANY_CONFIGS['NEW_COMPANY'] = {
    'name': '新公司',
    'supported_formats': ['NEW_FORMAT'],
    'field_mapping': {
        'new_lot_id': 'Lot_ID',
        # ... 字段映射
    },
    'unit_conversion': {
        # ... 单位转换配置
    }
}
```

### 步骤2：创建适配器类

```python
# new_company_adapter.py
from .base_company_adapter import BaseCompanyAdapter

class NewCompanyAdapter(BaseCompanyAdapter):
    def __init__(self, config):
        super().__init__('NEW_COMPANY', config)
    
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        # 实现具体的转换逻辑
        pass
    
    def get_field_mapping(self) -> Dict[str, str]:
        return self.field_mapping
```

### 步骤3：添加测试

在 `tests/company_adapters/` 中创建对应的测试文件。

## 🧪 测试

### 运行所有测试

```bash
python -m pytest tests/company_adapters/
```

### 运行特定测试

```bash
python -m pytest tests/company_adapters/test_hh_adapter.py
```

## 📊 支持的厂商

| 厂商代码 | 厂商名称 | 支持格式 | 状态 |
|---------|---------|---------|------|
| HH      | HH公司   | DCP, CW, MEX | ✅ 已完成 |
| JT      | JT公司   | JT      | 🚧 开发中 |

## 🔄 数据转换流程

1. **厂商识别** - 从文件路径/名称/内容识别厂商
2. **读取数据** - 使用对应的数据读取器
3. **格式适配** - 应用厂商适配器转换
4. **字段映射** - 将厂商字段映射为标准字段
5. **单位转换** - 执行必要的单位转换
6. **数据验证** - 验证转换后数据的完整性
7. **输出标准** - 生成标准HH格式的CSV

## 📈 扩展计划

- [ ] 完成JT公司适配器开发
- [ ] 添加第三方厂商支持
- [ ] 实现配置文件热加载
- [ ] 添加数据转换性能监控
- [ ] 支持自定义字段映射规则

## 🐛 故障排除

### 常见问题

1. **厂商识别失败**
   - 检查文件路径是否包含厂商标识
   - 确认厂商配置中的识别模式

2. **字段映射错误**  
   - 验证源数据字段名称
   - 检查配置文件中的字段映射

3. **单位转换异常**
   - 确认转换因子配置正确
   - 检查源数据的数值类型

### 日志调试

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 适配器会输出详细的调试信息
adapter.transform_to_standard_format(lot)
```

---

**版本**: v1.0.0  
**最后更新**: 2025-01-06 