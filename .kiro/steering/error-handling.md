# Error Handling Patterns

## Standard Exception Handling

### Basic Exception Pattern
```python
try:
    # Main processing logic
    result = process_data()
    return result
except Exception as e:
    logger.error(f"❌ 处理失败: {e}")
    return None  # or appropriate default value
```

### File Operation Exception Pattern
```python
try:
    dcp_file = Path(dcp_file_path)
    if not dcp_file.exists() or not dcp_file.is_file():
        logger.error(f"DCP文件未找到或不是一个文件: {dcp_file_path}")
        return None
    
    # File processing logic
    data = process_file(dcp_file)
    return data
except Exception as e:
    logger.exception(f"生成规格文件 {dcp_file_path} 时发生意外错误: {e}")
    return None
```

## Data Validation Patterns

### Null/None Checks
```python
# Check for None values
if value is None:
    logger.warning("值为None，跳过处理")
    return None

# Check for empty DataFrames
if df.empty:
    logger.warning("DataFrame为空，不进行保存")
    return None

# Check for missing attributes
if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
    # Process chip data
    process_chip_data(wafer.chip_data)
```

### File Existence Validation
```python
# Directory validation
if not data_dir.exists():
    logger.error(f"❌ 数据目录不存在: {data_dir}")
    return False

# File validation
if not dcp_file.exists() or not dcp_file.is_file():
    logger.error(f"DCP文件未找到或不是一个文件: {dcp_file_path}")
    return None
```

### Data Content Validation
```python
# Check for sufficient data
if len(header_lines) < 15:
    logger.warning(f"文件 {dcp_file_path} 的行数少于15行。规格数据可能不完整或缺失。")

# Check for empty data after processing
if final_df is None or final_df.empty:
    logger.error("经过转换后，没有有效的芯片数据可供分析。")
    return
```

## Batch Processing Error Handling

### Collect and Report Failures
```python
failed_files = []
success_count = 0

for file_path in file_paths:
    try:
        result = process_file(file_path)
        success_count += 1
        logger.info(f"    ✓ 成功")
    except Exception as e:
        failed_files.append((file_path, str(e)))
        logger.error(f"    ❌ 失败: {e}")

# Report summary
if failed_files:
    logger.warning(f"⚠️ {len(failed_files)} 个文件处理失败")
    for file_path, error in failed_files:
        logger.error(f"  - {Path(file_path).name}: {error}")
```

### Continue Processing Despite Failures
```python
results = {}
for batch_id in batch_ids:
    try:
        result = process_batch(batch_id)
        results[batch_id] = result
        success_count += 1
    except Exception as e:
        logger.error(f"   ❌ 批次 {batch_id} 处理失败: {e}")
        logger.error(f"处理批次 {batch_id} 失败", exc_info=True)
        results[batch_id] = False
        failed_batches.append(batch_id)

return results
```

## Graceful Degradation

### Fallback Mechanisms
```python
try:
    # Try primary method
    df = pd.read_csv(input_file, delimiter='\t', encoding='utf-8')
    logger.info(f"使用制表符分隔符读取CSV文件，读取了 {len(df)} 行数据")
except Exception as e:
    logger.warning(f"使用制表符分隔符读取失败: {e}, 尝试其他分隔符")
    try:
        # Fallback method
        df = pd.read_csv(input_file, delimiter=',', encoding='utf-8')
        logger.info(f"使用逗号分隔符读取CSV文件，读取了 {len(df)} 行数据")
    except Exception as e2:
        logger.error(f"使用逗号分隔符读取也失败: {e2}")
        return False
```

### Optional Feature Handling
```python
# Handle optional features gracefully
try:
    # Optional yield report generation
    generate_yield_report(data, yield_report_filepath)
    logger.info(f"✅ 良率报告已生成: {yield_report_filepath}")
except Exception as e_yield:
    logger.error(f"生成良率报告时发生意外错误: {e_yield}")
    logger.warning("警告: 良率报告生成失败，但主要处理继续")
```

## User Interruption Handling

### KeyboardInterrupt Pattern
```python
try:
    main_processing_loop()
except KeyboardInterrupt:
    logger.info("用户中断处理")
    print("\n\n⚠️  用户中断处理")
    sys.exit(130)  # Standard exit code for SIGINT
except Exception as e:
    logger.error("程序异常", exc_info=True)
    print(f"\n❌ 程序异常: {e}")
    sys.exit(1)
```

## Error Recovery Strategies

### Retry with Different Parameters
```python
def robust_file_read(file_path, encodings=['utf-8', 'gbk', 'latin1']):
    """Try multiple encodings for file reading"""
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            logger.warning(f"编码 {encoding} 读取失败，尝试下一个")
            continue
    
    logger.error(f"所有编码都失败，无法读取文件: {file_path}")
    return None
```

### Default Value Provision
```python
def safe_get_value(obj, attr, default=None):
    """Safely get attribute value with default"""
    if hasattr(obj, attr) and getattr(obj, attr) is not None:
        return getattr(obj, attr)
    return default

# Usage
wafer_id = safe_get_value(wafer, 'wafer_id', 'Unknown')
```

## Error Context Preservation

### Include Relevant Context in Errors
```python
try:
    process_parameter(param_name, param_data)
except Exception as e:
    logger.error(f"❌ 生成参数 {param_name} 箱体图失败: {e}")
    # Include parameter context for debugging
    logger.debug(f"参数数据形状: {param_data.shape if param_data is not None else 'None'}")
```

### Stack Trace for Critical Errors
```python
try:
    critical_operation()
except Exception as e:
    logger.exception(f"关键操作失败: {e}")  # Includes full stack trace
    # or explicitly:
    logger.error("关键操作失败", exc_info=True)
```

## Return Value Conventions

### Consistent Return Values
- **Success**: Return processed data or `True`
- **Failure**: Return `None` or `False`
- **Partial Success**: Return results dict with success/failure indicators

```python
def process_batch(batch_data):
    """
    Returns:
        dict: Processing results with success indicators
        None: Complete failure
    """
    try:
        results = {'success': True, 'data': processed_data, 'errors': []}
        return results
    except Exception as e:
        logger.error(f"批次处理失败: {e}")
        return None
```