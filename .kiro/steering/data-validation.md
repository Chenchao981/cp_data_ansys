# Data Validation Patterns

## File and Path Validation

### Path Existence Checks
```python
from pathlib import Path

# Directory validation
data_dir = Path(data_directory)
if not data_dir.exists():
    logger.error(f"❌ 数据目录不存在: {data_dir}")
    return False

# File validation
dcp_file = Path(dcp_file_path)
if not dcp_file.exists() or not dcp_file.is_file():
    logger.error(f"DCP文件未找到或不是一个文件: {dcp_file_path}")
    return None
```

### Required File Pattern Validation
```python
# Check for required CSV files (JT company pattern)
cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
spec_files = list(data_dir.glob("*_spec_*.csv"))
yield_files = list(data_dir.glob("*_yield_*.csv"))

if not (cleaned_files and spec_files and yield_files):
    logger.error("❌ 缺少必要的CSV文件，请确保存在：")
    logger.error("   - *_cleaned_*.csv (清洗数据)")
    logger.error("   - *_spec_*.csv (规格数据)")
    logger.error("   - *_yield_*.csv (良率数据)")
    return False
```

## DataFrame Validation

### Empty DataFrame Checks
```python
# Check for empty DataFrame
if df.empty:
    logger.warning("DataFrame为空，不进行保存")
    return None

# Check for sufficient data
if len(df) < minimum_required_rows:
    logger.warning(f"数据行数不足: {len(df)} < {minimum_required_rows}")
    return None
```

### Column Validation
```python
# Check for required columns
required_columns = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Bin']
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    logger.error(f"❌ 缺少必要列: {missing_columns}")
    return None

# Check for numeric columns
numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
if len(numeric_columns) == 0:
    logger.warning("⚠️ 未找到数值类型的列")
    return None
```

### Data Type Validation
```python
# Validate specific column types
def validate_column_types(df, column_specs):
    """
    Validate DataFrame column types
    
    Args:
        df: DataFrame to validate
        column_specs: dict of {column_name: expected_type}
    """
    for col_name, expected_type in column_specs.items():
        if col_name in df.columns:
            if not df[col_name].dtype == expected_type:
                logger.warning(f"列 {col_name} 类型不匹配: 期望 {expected_type}, 实际 {df[col_name].dtype}")

# Usage
column_specs = {
    'X': 'int64',
    'Y': 'int64',
    'Bin': 'int64'
}
validate_column_types(df, column_specs)
```

## Object Attribute Validation

### Safe Attribute Access
```python
# Check for object attributes before access
if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
    process_chip_data(wafer.chip_data)

# Multiple attribute checks
if (hasattr(wafer, 'seq') and wafer.seq is not None and
    hasattr(wafer, 'x') and wafer.x is not None):
    df['Seq'] = wafer.seq
    df['X'] = wafer.x
```

### Nested Attribute Validation
```python
# Check nested object structure
if (hasattr(lot, 'wafers') and lot.wafers and
    len(lot.wafers) > 0 and
    hasattr(lot.wafers[0], 'chip_data') and
    lot.wafers[0].chip_data is not None):
    sample_wafer = lot.wafers[0]
    chip_count = len(sample_wafer.chip_data)
```

## Data Content Validation

### Value Range Validation
```python
def validate_coordinate_ranges(df):
    """Validate X,Y coordinates are within reasonable ranges"""
    if 'X' in df.columns and 'Y' in df.columns:
        x_range = df['X'].max() - df['X'].min()
        y_range = df['Y'].max() - df['Y'].min()
        
        if x_range > 1000 or y_range > 1000:
            logger.warning(f"坐标范围异常: X范围={x_range}, Y范围={y_range}")
        
        if df['X'].min() < 0 or df['Y'].min() < 0:
            logger.warning("发现负坐标值")
```

### Missing Value Validation
```python
def check_missing_values(df, critical_columns):
    """Check for missing values in critical columns"""
    for col in critical_columns:
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(df)) * 100
                logger.warning(f"列 {col} 有 {missing_count} 个缺失值 ({missing_pct:.1f}%)")
                
                if missing_pct > 50:
                    logger.error(f"❌ 列 {col} 缺失值过多: {missing_pct:.1f}%")
                    return False
    return True
```

### Data Consistency Validation
```python
def validate_lot_consistency(df):
    """Validate data consistency within lot"""
    if 'Lot_ID' in df.columns:
        unique_lots = df['Lot_ID'].nunique()
        if unique_lots > 1:
            logger.warning(f"数据包含多个批次: {df['Lot_ID'].unique()}")
        
        # Check wafer count consistency
        if 'Wafer_ID' in df.columns:
            wafer_counts = df.groupby('Lot_ID')['Wafer_ID'].nunique()
            if wafer_counts.var() > 0:
                logger.info(f"各批次晶圆数量: {wafer_counts.to_dict()}")
```

## File Format Validation

### CSV File Validation
```python
def validate_csv_format(file_path):
    """Validate CSV file format and encoding"""
    try:
        # Try different encodings
        encodings = ['utf-8', 'gbk', 'latin1']
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                logger.info(f"CSV文件编码: {encoding}")
                return True
            except UnicodeDecodeError:
                continue
        
        logger.error(f"❌ 无法确定CSV文件编码: {file_path}")
        return False
        
    except Exception as e:
        logger.error(f"❌ CSV文件格式验证失败: {e}")
        return False
```

### Excel File Validation
```python
def validate_excel_format(file_path, required_sheets=None):
    """Validate Excel file format and required sheets"""
    try:
        # Check file extension
        if not file_path.lower().endswith(('.xls', '.xlsx')):
            logger.error(f"❌ 不是Excel文件: {file_path}")
            return False
        
        # Check required sheets
        if required_sheets:
            xl_file = pd.ExcelFile(file_path)
            missing_sheets = [sheet for sheet in required_sheets 
                            if sheet not in xl_file.sheet_names]
            
            if missing_sheets:
                logger.error(f"❌ 缺少必要工作表: {missing_sheets}")
                logger.info(f"可用工作表: {xl_file.sheet_names}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Excel文件验证失败: {e}")
        return False
```

## Parameter Validation

### Numeric Parameter Validation
```python
def validate_numeric_parameters(df, param_columns):
    """Validate numeric parameters for analysis"""
    valid_params = []
    
    for param in param_columns:
        if param not in df.columns:
            logger.warning(f"参数列不存在: {param}")
            continue
        
        # Check if column is numeric
        if not pd.api.types.is_numeric_dtype(df[param]):
            logger.warning(f"参数 {param} 不是数值类型: {df[param].dtype}")
            continue
        
        # Check for sufficient non-null values
        valid_count = df[param].count()
        if valid_count < 10:  # Minimum threshold
            logger.warning(f"参数 {param} 有效值不足: {valid_count}")
            continue
        
        # Check for variance (avoid constant values)
        if df[param].var() == 0:
            logger.warning(f"参数 {param} 值恒定，无法分析")
            continue
        
        valid_params.append(param)
    
    logger.info(f"✅ 验证通过的参数: {valid_params}")
    return valid_params
```

## Validation Helper Functions

### Generic Validation Wrapper
```python
def validate_and_process(data, validation_func, process_func, error_msg="验证失败"):
    """Generic validation and processing wrapper"""
    try:
        if not validation_func(data):
            logger.error(f"❌ {error_msg}")
            return None
        
        result = process_func(data)
        logger.info("✅ 验证和处理完成")
        return result
        
    except Exception as e:
        logger.error(f"❌ {error_msg}: {e}")
        return None
```

### Validation Result Reporting
```python
def report_validation_results(validation_results):
    """Report comprehensive validation results"""
    total_checks = len(validation_results)
    passed_checks = sum(validation_results.values())
    
    logger.info(f"📊 验证结果: {passed_checks}/{total_checks} 项通过")
    
    for check_name, result in validation_results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {check_name}")
    
    return passed_checks == total_checks
```