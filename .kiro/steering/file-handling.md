# File Handling Patterns

## Path Management

### Use pathlib.Path Consistently
```python
from pathlib import Path

# Always use Path objects for file operations
data_dir = Path("output")
input_file = Path(input_path)
output_file = data_dir / "processed_data.csv"

# Use resolve() for logging absolute paths
logger.info(f"📂 数据目录: {data_dir.resolve()}")
logger.info(f"📊 输出目录: {output_dir.resolve()}")
```

### Directory Creation Pattern
```python
# Create directories with parents
output_dir = Path("output/charts")
output_dir.mkdir(parents=True, exist_ok=True)

# Create output directory from input directory
if output_dir is None:
    output_dir = input_dir / "processed"
    
output_dir.mkdir(parents=True, exist_ok=True)
```

### File Path Construction
```python
# Use Path division operator for joining
output_path = Path(output_dir) / output_filename
spec_file = data_dir / f"{lot_id}_spec_{timestamp}.csv"

# Extract file components
filename = Path(file_path).name
file_stem = Path(file_path).stem
file_suffix = Path(file_path).suffix
```

## File Naming Conventions

### Timestamp-Based Naming
```python
from datetime import datetime

# Standard timestamp format
timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

# File naming patterns
cleaned_file = f"{lot_id}_cleaned_{timestamp}.csv"
yield_file = f"{lot_id}_yield_{timestamp}.csv"
spec_file = f"{lot_id}_spec_{timestamp}.csv"
chart_file = f"{parameter}_boxplot_chart.html"
```

### Consistent Naming Transformations
```python
# Transform between file types while preserving timestamp
cleaned_filename = Path(cleaned_file_path).name
yield_filename = cleaned_filename.replace('_cleaned_', '_yield_')
spec_filename = cleaned_filename.replace('_cleaned_', '_spec_')

# Extract lot ID from filename
lot_id = Path(file_path).stem.split('_')[0]
```

## File Discovery Patterns

### Glob Pattern Usage
```python
# Find files by pattern
cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
dcp_files = list(input_dir.glob("*.txt"))
excel_files = list(data_dir.glob("FA*.xlsx"))

# Check for required file patterns
required_patterns = {
    'cleaned': "*_cleaned_*.csv",
    'spec': "*_spec_*.csv", 
    'yield': "*_yield_*.csv"
}

missing_types = []
for file_type, pattern in required_patterns.items():
    files = list(data_dir.glob(pattern))
    if not files:
        missing_types.append(file_type)

if missing_types:
    logger.error(f"❌ 缺少文件类型: {missing_types}")
```

### File Selection Logic
```python
# Use first available file of each type
if cleaned_files:
    cleaned_file = cleaned_files[0]
    logger.info(f"📄 使用清洗文件: {cleaned_file.name}")
else:
    logger.error("❌ 未找到清洗数据文件")
    return None
```

## CSV File Handling

### Robust CSV Reading
```python
def read_csv_robust(file_path, encodings=['utf-8', 'gbk'], separators=[',', '\t']):
    """Robustly read CSV with multiple encoding/separator attempts"""
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                logger.info(f"CSV读取成功: 编码={encoding}, 分隔符='{sep}', 行数={len(df)}")
                return df
            except Exception as e:
                logger.debug(f"读取失败: 编码={encoding}, 分隔符='{sep}', 错误={e}")
                continue
    
    logger.error(f"❌ 所有方式都无法读取CSV: {file_path}")
    return None
```

### CSV Writing with Consistent Encoding
```python
# Always use UTF-8 encoding for CSV output
df.to_csv(output_file, index=False, encoding='utf-8')
logger.info(f"✅ CSV已保存: {output_file} ({len(df)} 行)")

# Include file size in logging
file_size = output_file.stat().st_size / 1024  # KB
logger.info(f"文件大小: {file_size:.1f} KB")
```

## Excel File Handling

### Excel Reading with Sheet Validation
```python
def read_excel_with_validation(file_path, required_sheets=None):
    """Read Excel file with sheet validation"""
    try:
        # Check if file exists and is Excel format
        if not file_path.suffix.lower() in ['.xls', '.xlsx']:
            logger.error(f"❌ 不是Excel文件: {file_path}")
            return None
        
        # Get available sheets
        xl_file = pd.ExcelFile(file_path)
        available_sheets = xl_file.sheet_names
        logger.info(f"Excel工作表: {available_sheets}")
        
        # Validate required sheets
        if required_sheets:
            missing_sheets = [s for s in required_sheets if s not in available_sheets]
            if missing_sheets:
                logger.error(f"❌ 缺少工作表: {missing_sheets}")
                return None
        
        return xl_file
        
    except Exception as e:
        logger.error(f"❌ Excel文件读取失败: {e}")
        return None
```

### Excel Writing with Multiple Sheets
```python
def write_excel_multi_sheet(data_dict, output_file):
    """Write multiple DataFrames to Excel sheets"""
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info(f"工作表 '{sheet_name}': {len(df)} 行")
        
        logger.info(f"✅ Excel文件已保存: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Excel保存失败: {e}")
        return False
```

## HTML File Handling

### Plotly HTML Generation
```python
def save_plotly_chart(fig, output_file, include_plotlyjs='inline'):
    """Save Plotly chart as HTML with embedded JS"""
    try:
        fig.write_html(
            str(output_file),
            include_plotlyjs=include_plotlyjs,
            validate=False  # Skip validation for speed
        )
        logger.info(f"✅ 图表已保存: {output_file.name}")
        return output_file
        
    except Exception as e:
        logger.error(f"❌ 图表保存失败: {e}")
        return None
```

### HTML File Validation
```python
def validate_html_output(html_file):
    """Validate HTML file was created successfully"""
    if not html_file.exists():
        logger.error(f"❌ HTML文件未创建: {html_file}")
        return False
    
    file_size = html_file.stat().st_size
    if file_size < 1000:  # Less than 1KB indicates likely failure
        logger.warning(f"⚠️ HTML文件过小: {file_size} bytes")
        return False
    
    logger.info(f"✅ HTML文件验证通过: {file_size/1024:.1f} KB")
    return True
```

## File System Operations

### Safe File Operations
```python
def safe_file_copy(source, destination):
    """Safely copy file with error handling"""
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            logger.error(f"❌ 源文件不存在: {source}")
            return False
        
        # Create destination directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        import shutil
        shutil.copy2(source_path, dest_path)
        logger.info(f"✅ 文件复制成功: {dest_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件复制失败: {e}")
        return False
```

### File Cleanup Patterns
```python
def cleanup_temp_files(temp_dir, pattern="temp_*"):
    """Clean up temporary files"""
    try:
        temp_path = Path(temp_dir)
        if temp_path.exists():
            temp_files = list(temp_path.glob(pattern))
            for temp_file in temp_files:
                temp_file.unlink()
                logger.debug(f"删除临时文件: {temp_file.name}")
            
            logger.info(f"✅ 清理了 {len(temp_files)} 个临时文件")
        
    except Exception as e:
        logger.warning(f"⚠️ 临时文件清理失败: {e}")
```

## File Metadata Handling

### File Information Logging
```python
def log_file_info(file_path):
    """Log comprehensive file information"""
    try:
        path = Path(file_path)
        if path.exists():
            stat = path.stat()
            size_kb = stat.st_size / 1024
            
            logger.info(f"📄 文件信息: {path.name}")
            logger.info(f"   大小: {size_kb:.1f} KB")
            logger.info(f"   修改时间: {datetime.fromtimestamp(stat.st_mtime)}")
            
            # For CSV files, also log row count
            if path.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(path, nrows=0)  # Just get columns
                    row_count = sum(1 for _ in open(path)) - 1  # Subtract header
                    logger.info(f"   行数: {row_count}, 列数: {len(df.columns)}")
                except:
                    pass
                    
    except Exception as e:
        logger.warning(f"⚠️ 无法获取文件信息: {e}")
```

### Batch File Processing Summary
```python
def log_batch_file_summary(file_paths, operation="处理"):
    """Log summary of batch file operations"""
    logger.info(f"📁 {operation}文件列表 ({len(file_paths)} 个):")
    
    total_size = 0
    for i, file_path in enumerate(file_paths, 1):
        path = Path(file_path)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            total_size += size_kb
            logger.info(f"  {i:2d}. {path.name} ({size_kb:.1f} KB)")
        else:
            logger.warning(f"  {i:2d}. {path.name} (文件不存在)")
    
    logger.info(f"📊 总大小: {total_size:.1f} KB")
```