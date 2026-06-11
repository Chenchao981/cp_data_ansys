# 🏭 新增公司数据分析功能指南

## 📋 概述

本文档以new公司为例，详细说明如何在现有模块化架构中新增一个公司的数据分析功能。得益于模块化设计，新增公司只需要实现数据清洗适配器，其他功能（图表生成、GUI、打包）将自动复用。

## 🎯 预期目标

- **开发时间**: 3-5天（相比之前的2-3周）
- **代码复用率**: 80%以上
- **新增代码量**: 约300-500行（主要是适配器逻辑）
- **测试覆盖**: 完整的单元测试和集成测试

## 📝 Todo List

### 阶段1: 需求分析和配置 (1天)

- [ ] **分析new公司数据格式**
  - [ ] 获取new公司的样本数据文件
  - [ ] 分析文件格式（Excel、CSV、TXT等）
  - [ ] 识别字段结构和命名规则
  - [ ] 确定数据类型和单位信息
  - [ ] 记录特殊处理需求

- [ ] **设计字段映射规则**
  - [ ] 创建new字段到标准字段的映射表
  - [ ] 确定需要的单位转换规则
  - [ ] 设计文件识别模式（路径、文件名、扩展名）
  - [ ] 定义数据验证规则

- [ ] **更新公司配置**
  - [ ] 在`company_config.py`中添加new公司配置
  - [ ] 配置字段映射和单位转换
  - [ ] 设置文件识别模式
  - [ ] 定义数据质量验证规则

### 阶段2: 适配器开发 (2天)

- [ ] **创建new适配器类**
  - [ ] 创建`new_adapter.py`文件
  - [ ] 继承`BaseCompanyAdapter`基类
  - [ ] 实现`transform_to_standard_format`方法
  - [ ] 实现`can_process_file`方法
  - [ ] 实现`get_field_mapping`方法

- [ ] **处理new特定数据转换**
  - [ ] 实现字段重命名逻辑
  - [ ] 实现单位转换逻辑
  - [ ] 实现数据类型标准化
  - [ ] 处理缺失数据和异常值
  - [ ] 添加new特定的数据验证

- [ ] **创建new数据读取器（如需要）**
  - [ ] 评估是否需要专用读取器
  - [ ] 如需要，创建`new_reader.py`
  - [ ] 实现new格式的文件解析逻辑
  - [ ] 集成到`reader_factory.py`中

### 阶段3: 测试和验证 (1天)

- [ ] **单元测试**
  - [ ] 创建测试用例文件
  - [ ] 测试适配器的各个方法
  - [ ] 测试字段映射和单位转换
  - [ ] 测试异常处理逻辑

- [ ] **集成测试**
  - [ ] 测试完整的数据处理流程
  - [ ] 验证标准CSV文件生成
  - [ ] 测试与现有图表生成的兼容性
  - [ ] 验证GUI集成功能

- [ ] **性能测试**
  - [ ] 测试大数据文件处理性能
  - [ ] 对比处理时间和内存使用
  - [ ] 优化性能瓶颈

### 阶段4: GUI集成 (1天)

- [ ] **创建new公司GUI组件**
  - [ ] 创建`new_widget.py`文件
  - [ ] 继承`BaseCompanyWidget`
  - [ ] 实现new特定的界面元素
  - [ ] 添加new特定的参数配置

- [ ] **更新主界面**
  - [ ] 在`multi_company_gui.py`中注册new组件
  - [ ] 测试GUI界面显示和功能
  - [ ] 更新帮助文档和用户手册

### 阶段5: 文档和发布 (0.5天)

- [ ] **更新项目文档**
  - [ ] 更新README.md
  - [ ] 更新用户手册
  - [ ] 添加new公司使用示例

- [ ] **版本发布**
  - [ ] 更新版本号
  - [ ] 创建发布包
  - [ ] 部署到生产环境

## 💻 代码实现任务

### 任务1: 添加new公司配置

**文件**: `cp_data_processor/readers/company_adapters/company_config.py`

```python
# 在COMPANY_CONFIGS字典中添加new配置
'new': {
    'name': 'new半导体公司',
    'description': 'new公司CSV格式CP测试数据',
    'supported_formats': ['new_CSV', 'new_EXCEL'],
    'default_format': 'new_CSV',
    'version': '1.0.0',
    
    # new字段到标准字段的映射
    'field_mapping': {
        'LOT_NO': 'Lot_ID',
        'WAFER_NO': 'Wafer_ID',
        'SITE_X': 'X',
        'SITE_Y': 'Y',
        'CHIP_ID': 'Seq',
        'BIN_NO': 'Bin',
        # 添加更多字段映射...
    },
    
    # 单位转换配置
    'unit_conversion': {
        'VTH_VOLTAGE': {'factor': 0.001, 'offset': 0.0},  # mV to V
        'CURRENT_UA': {'factor': 1e-6, 'offset': 0.0},    # μA to A
        # 添加更多单位转换...
    },
    
    # 文件识别特征
    'file_patterns': {
        'path_patterns': ['/new_data/', '/new/', '_new_'],
        'filename_patterns': ['*_new_*', 'new_*', '*_new_*'],
        'content_signatures': ['new_FORMAT', 'new_VERSION'],
        'file_extensions': ['.csv', '.xlsx', '.xls']
    },
    
    # 数据质量配置
    'data_validation': {
        'required_fields': ['LOT_NO', 'WAFER_NO', 'SITE_X', 'SITE_Y', 'CHIP_ID', 'BIN_NO'],
        'optional_fields': ['CONTACT', 'TEST_TIME'],
        'bin_values': {
            'pass_bins': [1, 11],
            'fail_bins': [2, 3, 4, 5, 6, 7, 8, 9, 10]
        }
    }
}
```

### 任务2: 创建new适配器

**文件**: `cp_data_processor/readers/company_adapters/new_adapter.py`

```python
"""
new公司适配器

将new公司的数据格式转换为标准HH格式。
"""

from typing import Dict, Any
import pandas as pd
import logging
from pathlib import Path

from .base_company_adapter import BaseCompanyAdapter
from cp_data_processor.data_models.cp_data import CPLot

logger = logging.getLogger(__name__)


class newAdapter(BaseCompanyAdapter):
    """
    new公司数据适配器
    
    负责将new公司的数据格式转换为标准HH格式。
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('new', config)
        self.logger = logging.getLogger(f"{__name__}.new")
    
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """将new格式转换为标准HH格式"""
        self.logger.info(f"开始处理new格式数据，批次: {lot.lot_id}")
        
        # 1. 验证输入数据
        if not self.validate_data_format(lot):
            raise ValueError("new格式数据验证失败")
        
        # 2. 处理每个晶圆的数据
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                # 应用new特定的数据处理
                wafer.chip_data = self._process_new_data(wafer.chip_data)
                
                # 应用字段映射
                wafer.chip_data = self.apply_field_mapping(wafer.chip_data)
                
                # 应用单位转换
                wafer.chip_data = self.convert_units(wafer.chip_data)
                
                # 标准化数据类型
                wafer.chip_data = self._standardize_data_types(wafer.chip_data)
        
        # 3. 更新参数信息
        self._update_lot_parameters(lot)
        
        # 4. 重新计算统计数据
        lot.combine_data_from_wafers()
        
        self.logger.info(f"new格式数据处理完成，晶圆数: {len(lot.wafers)}")
        return lot
    
    def can_process_file(self, file_path: str) -> bool:
        """检查是否能处理指定文件"""
        file_path_obj = Path(file_path)
        
        # 检查文件扩展名
        file_ext = file_path_obj.suffix.lower()
        supported_extensions = self.config.get('file_patterns', {}).get('file_extensions', [])
        
        if file_ext not in supported_extensions:
            return False
        
        # 检查文件名模式
        filename = file_path_obj.name
        filename_patterns = self.config.get('file_patterns', {}).get('filename_patterns', [])
        
        for pattern in filename_patterns:
            pattern_clean = pattern.replace('*', '')
            if pattern_clean.lower() in filename.lower():
                return True
        
        return False
    
    def get_field_mapping(self) -> Dict[str, str]:
        """获取new字段映射配置"""
        return self.field_mapping
    
    def _process_new_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """处理new特定的数据格式"""
        processed_data = data.copy()
        
        # new特定的数据处理逻辑
        # 例如：处理特殊的编码格式、数据清洗等
        
        return processed_data
    
    def _standardize_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据类型"""
        # 实现数据类型标准化逻辑
        return data
    
    def _update_lot_parameters(self, lot: CPLot):
        """更新批次参数信息"""
        # 实现参数更新逻辑
        pass
```

### 任务3: 创建new数据读取器（如需要）

**文件**: `cp_data_processor/readers/new_reader.py`

```python
"""
new公司数据读取器

专门用于读取new公司的数据文件格式。
"""

import pandas as pd
from typing import List, Optional
import logging

from .base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter

logger = logging.getLogger(__name__)


class newReader(BaseReader):
    """
    new公司数据读取器
    
    支持读取new公司的CSV和Excel格式数据文件。
    """
    
    def __init__(self, file_paths: List[str], pass_bin: int = 1):
        super().__init__(file_paths, pass_bin)
        self.logger = logging.getLogger(__name__)
    
    def read_file(self, file_path: str) -> CPLot:
        """读取单个new数据文件"""
        self.logger.info(f"开始读取new数据文件: {file_path}")
        
        # 根据文件扩展名选择读取方法
        if file_path.endswith('.csv'):
            return self._read_csv_file(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            return self._read_excel_file(file_path)
        else:
            raise ValueError(f"不支持的new文件格式: {file_path}")
    
    def _read_csv_file(self, file_path: str) -> CPLot:
        """读取new CSV格式文件"""
        # 实现CSV文件读取逻辑
        pass
    
    def _read_excel_file(self, file_path: str) -> CPLot:
        """读取new Excel格式文件"""
        # 实现Excel文件读取逻辑
        pass
```

### 任务4: 创建new GUI组件

**文件**: `gui/widgets/new_widget.py`

```python
"""
new公司GUI组件

提供new公司特定的数据分析界面。
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .base_company_widget import BaseCompanyWidget


class newWidget(BaseCompanyWidget):
    """
    new公司数据分析界面组件
    """
    
    def __init__(self, parent=None):
        super().__init__('new', parent)
        self.company_name = "new半导体公司"
        self.init_ui()
    
    def init_ui(self):
        """初始化new特定的用户界面"""
        layout = QVBoxLayout()
        
        # 公司标题
        title_label = QLabel(f"📊 {self.company_name}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        layout.addWidget(title_label)
        
        # new特定的配置选项
        config_group = QGroupBox("new数据配置")
        config_layout = QFormLayout()
        
        # 数据格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["new_CSV", "new_EXCEL"])
        config_layout.addRow("数据格式:", self.format_combo)
        
        # new特定参数
        self.new_param_input = QLineEdit()
        self.new_param_input.setPlaceholderText("输入new特定参数...")
        config_layout.addRow("特定参数:", self.new_param_input)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 添加通用的文件选择和处理按钮
        self.add_common_widgets(layout)
        
        self.setLayout(layout)
    
    def get_company_specific_config(self) -> dict:
        """获取new公司特定的配置"""
        return {
            'format': self.format_combo.currentText(),
            'new_param': self.new_param_input.text(),
            'company': 'new'
        }
    
    def process_files(self):
        """处理new数据文件"""
        config = self.get_company_specific_config()
        
        # 调用new特定的数据处理逻辑
        self.process_company_data(config)
```

### 任务5: 更新注册管理器

**文件**: `cp_data_processor/readers/company_adapters/company_registry.py`

在`_auto_load_adapters`方法中添加new适配器的加载：

```python
def _auto_load_adapters(self):
    """自动加载已知的适配器"""
    # 现有的HH和JT适配器加载...
    
    # 加载new适配器
    try:
        from .new_adapter import newAdapter
        self.register_company('new', newAdapter)
    except ImportError as e:
        self.logger.warning(f"无法加载new适配器: {e}")
```

### 任务6: 更新模块导入

**文件**: `cp_data_processor/readers/company_adapters/__init__.py`

```python
from .new_adapter import newAdapter

__all__ = [
    'BaseCompanyAdapter',
    'COMPANY_CONFIGS', 
    'get_company_config',
    'CompanyRegistry',
    'get_company_registry',
    'get_adapter_for_file',
    'HHAdapter',
    'JTAdapter',
    'newAdapter'  # 新增
]
```

### 任务7: 创建测试用例

**文件**: `tests/test_new_adapter.py`

```python
"""
new适配器测试用例
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch

from cp_data_processor.readers.company_adapters.new_adapter import newAdapter
from cp_data_processor.readers.company_adapters.company_config import get_company_config
from cp_data_processor.data_models.cp_data import CPLot, CPWafer


class TestnewAdapter(unittest.TestCase):
    """new适配器测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = get_company_config('new')
        self.adapter = newAdapter(self.config)
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertEqual(self.adapter.company_name, 'new')
        self.assertIsNotNone(self.adapter.field_mapping)
        self.assertIsNotNone(self.adapter.unit_conversion)
    
    def test_can_process_file(self):
        """测试文件处理能力"""
        # 测试支持的文件格式
        self.assertTrue(self.adapter.can_process_file('/data/new_test.csv'))
        self.assertTrue(self.adapter.can_process_file('/data/new_batch.xlsx'))
        
        # 测试不支持的文件格式
        self.assertFalse(self.adapter.can_process_file('/data/test.txt'))
    
    def test_field_mapping(self):
        """测试字段映射"""
        test_data = pd.DataFrame({
            'LOT_NO': ['new001'],
            'WAFER_NO': [1],
            'SITE_X': [1],
            'SITE_Y': [1],
            'CHIP_ID': [1],
            'BIN_NO': [1]
        })
        
        mapped_data = self.adapter.apply_field_mapping(test_data)
        
        # 验证字段映射是否正确
        self.assertIn('Lot_ID', mapped_data.columns)
        self.assertIn('Wafer_ID', mapped_data.columns)
        self.assertIn('X', mapped_data.columns)
        self.assertIn('Y', mapped_data.columns)
    
    def test_unit_conversion(self):
        """测试单位转换"""
        test_data = pd.DataFrame({
            'VTH_VOLTAGE': [1000.0],  # mV
            'CURRENT_UA': [1000000.0]  # μA
        })
        
        converted_data = self.adapter.convert_units(test_data)
        
        # 验证单位转换是否正确
        self.assertAlmostEqual(converted_data['VTH_VOLTAGE'].iloc[0], 1.0)  # 转换为V
        self.assertAlmostEqual(converted_data['CURRENT_UA'].iloc[0], 1.0)   # 转换为A


if __name__ == '__main__':
    unittest.main()
```

## 🔧 开发流程

### 1. 环境准备

```bash
# 确保项目环境正确
cd /path/to/cp_data_ansys
pip install -r requirements.txt

# 运行现有测试确保基础架构正常
python test_modular_architecture.py
```

### 2. 获取和分析样本数据

```bash
# 创建new数据目录
mkdir -p data/new_samples

# 获取new公司提供的样本数据文件
# 分析文件结构和内容
```

### 3. 增量开发和测试

```bash
# 每完成一个任务，立即进行测试
python -m pytest tests/test_new_adapter.py -v

# 集成测试
python test_modular_architecture.py
```

### 4. 端到端验证

```bash
# 使用实际new数据文件进行完整流程测试
python cp_data_processor_cli.py new_sample.csv output.xlsx --format new_CSV
```

## 📊 质量保证

### 代码质量检查

```bash
# 代码风格检查
flake8 cp_data_processor/readers/company_adapters/new_adapter.py

# 类型检查
mypy cp_data_processor/readers/company_adapters/new_adapter.py
```

### 测试覆盖率

```bash
# 生成测试覆盖率报告
pytest --cov=cp_data_processor tests/test_new_adapter.py --cov-report=html
```

### 性能基准测试

```bash
# 性能测试
python -m pytest tests/test_new_performance.py -v
```

## 🚀 部署检查清单

- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 代码覆盖率达到80%以上
- [ ] 性能测试符合要求
- [ ] 文档更新完成
- [ ] GUI集成测试通过
- [ ] 与现有公司数据兼容性验证

## 📈 成功标准

1. **功能完整性**
   - new数据能够正确读取和解析
   - 字段映射和单位转换准确
   - 生成的标准CSV文件格式正确

2. **性能要求**
   - 处理速度与现有公司相当
   - 内存使用合理
   - 大文件处理稳定

3. **用户体验**
   - GUI界面友好直观
   - 错误提示清晰
   - 处理过程有进度显示

4. **代码质量**
   - 代码结构清晰
   - 注释完整
   - 测试覆盖率高
   - 遵循项目编码规范

## 🎯 预期收益

通过模块化架构，新增new公司功能预期将获得：

- **开发效率提升**: 70%的代码可直接复用
- **维护成本降低**: 统一的数据处理流程
- **用户体验一致**: 相同的界面和操作逻辑
- **质量保证**: 经过验证的基础架构

---

**版本**: v1.0  
**创建时间**: 2025-01-26  
**适用范围**: 基于模块化架构的CP数据分析平台  
**负责人**: 开发团队