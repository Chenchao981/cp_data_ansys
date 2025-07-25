# Logging Standards

## Logging Configuration

### Standard Setup Pattern
```python
import logging

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
```

### Module-Specific Logger Setup
```python
# For modules requiring detailed debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
```

## Logging Message Patterns

### Use Emoji Icons for Visual Clarity
- ✅ Success: `logger.info("✅ 数据加载成功")`
- ❌ Error: `logger.error("❌ 数据加载失败")`
- ⚠️ Warning: `logger.warning("⚠️ 未找到可用的测试参数")`
- 📂 Directory/File: `logger.info(f"📂 数据目录: {data_dir.resolve()}")`
- 📊 Chart/Analysis: `logger.info("📊 开始生成图表...")`
- 🔄 Processing: `logger.info("🔄 标准化CSV列名")`
- 📈 Progress: `logger.info("📈 开始生成良率图表...")`

### Progress Reporting
```python
# For batch processing
logger.info(f"✅ 良率图表已保存 ({len(saved_charts)}个):")
for i, chart_path in enumerate(saved_charts, 1):
    logger.info(f"  {i}. {chart_path.name}")

# For parameter processing
logger.info(f"🎯 找到 {len(available_params)} 个测试参数: {available_params}")
logger.info(f"  ✅ [{i}/{len(plot_params)}] 箱体图: {filename}")
```

### Error Context
```python
# Include context in error messages
logger.error(f"❌ 列名标准化失败: {e}")
logger.error(f"❌ 生成参数 {param} 箱体图失败: {e}")
logger.error(f"处理批次 {batch_id} 失败", exc_info=True)
```

## Exception Handling with Logging

### Standard Exception Pattern
```python
try:
    # Processing code
    result = process_data()
    logger.info("✅ 处理完成")
except Exception as e:
    logger.error(f"❌ 处理失败: {e}")
    # Optional: include stack trace for debugging
    logger.exception(f"详细错误信息: {e}")
```

### File Processing Exception Pattern
```python
try:
    # File operations
    data = load_file(file_path)
except Exception as e:
    logger.error(f"❌ 文件加载失败 {file_path}: {e}")
    return None
```

### Batch Processing Exception Pattern
```python
failed_items = []
for item in items:
    try:
        process_item(item)
        logger.info(f"    ✓ 成功: {item}")
    except Exception as e:
        failed_items.append((item, str(e)))
        logger.error(f"    ❌ 失败: {e}")

if failed_items:
    logger.warning(f"⚠️ {len(failed_items)} 个项目处理失败")
```

## Logging Levels Usage

### INFO Level
- Process start/completion status
- File paths and directory information
- Progress updates and counts
- Successful operations

### WARNING Level
- Missing optional data
- Fallback operations
- Non-critical issues that don't stop processing

### ERROR Level
- File not found or access errors
- Data processing failures
- Critical errors that prevent completion

### DEBUG Level
- Detailed processing steps
- Variable values during debugging
- Internal state information

## File and Path Logging

### Always Use Resolved Paths for Clarity
```python
logger.info(f"📂 数据目录: {data_dir.resolve()}")
logger.info(f"📊 图表输出目录: {output_dir.resolve()}")
```

### Log File Operations
```python
# File discovery
logger.info(f"✅ 找到JT数据文件:")
logger.info(f"   - 清洗数据: {cleaned_files[0].name}")
logger.info(f"   - 规格数据: {spec_files[0].name}")

# File processing
logger.info(f"📄 加载清洗数据: {cleaned_file.name}")
logger.info(f"✅ 标准化完成: {cleaned_file.name}")
```

## Console Output Coordination

### Coordinate with Print Statements
- Use `logger.info()` for structured logging
- Use `print()` for immediate user feedback
- Ensure both provide consistent information

```python
print(f"    ✓ 成功")
logger.info(f"处理成功: {item}")

print(f"    ❌ 失败: {e}")
logger.error(f"处理失败 {item}: {e}")
```