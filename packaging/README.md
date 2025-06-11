# CP数据分析工具 - 开发者打包指南

本文档说明如何打包CP数据分析工具，包括离线依赖包的准备。

> **注意**: 这是开发者文档。最终用户请查看 `dist/用户安装使用说明.md`

## 🚀 快速打包

### 自动打包（推荐）

运行打包脚本，它会自动完成所有步骤：

```bash
cd packaging
python build.py
```

这个脚本会：

1. ✅ 打包源代码为 `app.pyz`
2. ✅ 下载所有依赖包到 `wheels/` 文件夹
3. ✅ 创建离线安装脚本 `install_offline.bat`
4. ✅ 准备完整的分发包

### 手动下载依赖（可选）

如果需要单独下载依赖包：

```bash
cd packaging
python download_dependencies.py
```

## 📁 打包后的文件结构

```
packaging/dist/
├── 📄 requirements.txt      # 依赖清单
├── 🚀 start.bat             # 启动脚本
├── 💾 install_offline.bat   # 离线安装脚本
├── 📦 app.pyz               # 核心程序包
├── 📁 wheels/               # 离线依赖包
│   ├── pandas-xxx.whl
│   ├── numpy-xxx.whl
│   ├── matplotlib-xxx.whl
│   └── ...
└── 📖 用户安装使用说明.md       # 用户说明文档
```

## 🎯 用户安装方式

用户收到分发包后，有两种安装方式：

### 方式一：在线安装

```bash
pip install -r requirements.txt
```

### 方式二：离线安装

双击 `install_offline.bat` 即可

## 🔧 技术细节

### 依赖下载原理

使用 `pip download` 命令将PyPI上的包下载到本地：

```bash
pip download -r requirements.txt -d wheels/
```

### 离线安装原理

使用 `pip install` 的本地查找功能：

```bash
pip install --find-links wheels --no-index --requirement requirements.txt
```

参数说明：

- `--find-links wheels`: 在wheels文件夹中查找包
- `--no-index`: 不使用PyPI索引，只使用本地包
- `--requirement requirements.txt`: 按照requirements.txt安装

## 🛠️ 故障排除

### 依赖下载失败

- **原因**: 网络连接问题或PyPI访问受限
- **解决**:
  1. 检查网络连接
  2. 使用国内镜像源：`pip download -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt -d wheels/`

### 离线安装失败

- **原因**: wheels文件夹缺失或损坏
- **解决**: 重新运行 `python download_dependencies.py`

### 包版本冲突

- **原因**: 不同平台的包不兼容
- **解决**: 在目标平台上重新下载依赖包

## 📝 注意事项

1. **平台兼容性**: 下载的wheel包可能包含平台特定的二进制文件，建议在目标平台上下载
2. **版本管理**: requirements.txt中建议指定具体版本号，避免版本冲突
3. **包大小**: 离线包会增加分发包的体积，根据需要选择是否包含
4. **更新维护**: 定期更新依赖包，确保安全性和兼容性

## 🎉 优势

- ✅ **无网络依赖**: 用户无需联网即可安装依赖
- ✅ **安装快速**: 本地安装比在线下载更快
- ✅ **稳定可靠**: 避免网络问题导致的安装失败
- ✅ **版本锁定**: 确保所有用户使用相同版本的依赖包
