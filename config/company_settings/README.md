# 🔧 厂商配置目录

## 📋 概述

本目录用于存储不同厂商的外部配置文件，支持运行时配置热加载和用户自定义配置。

## 📁 目录结构

```
company_settings/
├── README.md           # 本说明文档
├── hh_config.json      # HH公司配置文件（可选）
├── jt_config.json      # JT公司配置文件（可选）
└── custom_mapping.json # 用户自定义字段映射
```

## 🎯 使用场景

1. **生产环境配置** - 独立的配置文件便于部署管理
2. **用户自定义** - 允许用户修改字段映射而不改动代码
3. **A/B测试** - 支持不同配置版本的对比测试
4. **配置备份** - 重要配置的版本化管理

## 📄 配置文件格式

### 基本格式 (JSON)

```json
{
    "company_name": "HH",
    "display_name": "HH公司",
    "version": "1.0.0",
    "field_mapping": {
        "source_field": "target_field"
    },
    "unit_conversion": {
        "parameter_name": {
            "factor": 1.0,
            "offset": 0.0,
            "description": "转换说明"
        }
    },
    "file_patterns": {
        "path_patterns": ["/HH_data/"],
        "filename_patterns": ["*_HH_*"]
    }
}
```

## 🚀 加载优先级

1. **外部配置文件** (此目录)
2. **代码内置配置** (`company_config.py`)
3. **默认配置**

## 📝 示例配置

### HH公司配置示例

```json
{
    "company_name": "HH",
    "display_name": "HH公司",
    "supported_formats": ["DCP", "CW", "MEX"],
    "field_mapping": {
        "Lot_ID": "Lot_ID",
        "Wafer_ID": "Wafer_ID",
        "Seq": "Seq",
        "Bin": "Bin",
        "X": "X",
        "Y": "Y",
        "CONT": "CONT"
    },
    "data_validation": {
        "required_fields": ["Lot_ID", "Wafer_ID", "Seq", "Bin"],
        "bin_values": {
            "pass_bins": [1],
            "fail_bins": [2, 3, 4, 5]
        }
    }
}
```

## 🔄 热加载支持

配置文件修改后自动生效，无需重启程序：

```python
from cp_data_processor.readers.company_adapters.company_config import reload_config

# 重新加载指定厂商配置
reload_config('HH')

# 重新加载所有配置
reload_config()
```

## ⚙️ 环境变量

支持通过环境变量指定配置目录：

```bash
export CP_COMPANY_CONFIG_DIR="/path/to/config"
```

---

**注意**: 配置文件为可选项，如不存在将使用代码内置的默认配置。 