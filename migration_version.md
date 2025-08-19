# Anaconda 迁移至 Miniconda 环境指南

## 1. 背景

本项目最初使用完整的 Anaconda 发行版作为开发环境。为了实现一个更轻量、启动更快且更易于管理的开发环境，我们决定迁移至 **Miniconda**。

Miniconda 是一个轻量级的 Conda 安装程序，它仅包含 Conda 包管理器、Python 以及少量核心包。这使我们能够按需构建一个干净、最小化的项目环境，同时继续利用 Conda 强大的包管理和环境隔离功能。本文档将指导您完成这一迁移过程，并以 `conda-forge` 作为主要的包渠道。

## 2. 迁移步骤

### 2.1. 安装 Miniconda

1.  **卸载 Anaconda**：为避免路径冲突，建议首先从您的系统中卸载现有的 Anaconda 发行版。
2.  **下载 Miniconda**：访问 [Miniconda 文档](https://docs.conda.io/en/latest/miniconda.html) 并下载适用于您操作系统（Windows x86_64）的最新 Python 3.12 安装程序。
3.  **安装**：运行安装程序。在安装过程中，建议遵循默认选项。安装程序可能会询问是否将 Miniconda添加到您的 PATH 环境变量中，通常建议让安装程序为您完成此操作。

### 2.2. 配置 Conda-Forge

`conda-forge` 是一个由社区维护的 Conda 包仓库，提供了大量最新、最全的软件包。我们将其设置为主要渠道，以确保依赖的可用性和版本更新。

打开命令行工具（Anaconda Prompt, CMD, 或 PowerShell），并运行以下命令：

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```
这会告诉 Conda 优先从 `conda-forge` 渠道搜索和安装包。

### 2.3. 创建项目环境

我们将使用一个 `environment.yml` 文件来定义和复现项目环境。这是 Conda 管理环境的推荐方式。

1.  **创建 `environment.yml` 文件**：
    在您的项目根目录下，创建一个名为 `environment.yml` 的文件，并将以下内容复制进去。这个文件取代了 `requirements.txt` 的作用。

    ```yaml
    name: cp-data-env
    channels:
      - conda-forge
      - defaults
    dependencies:
      # Core Python
      - python=3.12
    
      # GUI Framework
      - pyqt>=5.15
    
      # Data Processing and Numerics
      - pandas>=1.3
      - numpy>=1.21
      - openpyxl>=3.0
    
      # Plotting and Visualization
      - matplotlib>=3.0
      - seaborn>=0.10
      - plotly>=5.0
    
      # Web Frontend (Optional)
      - streamlit
    
      # Pip for any packages not on Conda
      - pip
    ```

2.  **创建并激活环境**：
    在项目根目录下打开命令行，并运行以下命令来创建环境：

    ```bash
    conda env create -f environment.yml
    ```
    Conda 会自动创建一个名为 `cp-data-env` 的新环境，并安装 `environment.yml` 文件中列出的所有依赖项。

3.  **激活环境**：
    创建成功后，使用以下命令激活新环境：
    
    ```bash
    conda activate cp-data-env
    ```
    激活后，您的命令行提示符前会显示 `(cp-data-env)`。

## 3. 验证安装

安装完成后，您可以通过运行项目的主要功能来验证新环境是否配置正确。

-   **运行命令行工具**：
    ```bash
    python cp_data_processor_cli.py --help
    ```
-   **启动 GUI 应用**：
    ```bash
    python cp_data_processor_gui.py
    ```
-   **启动 Web 应用 (如果需要)**：
    ```bash
    streamlit run frontend/yield_analyzer_app.py
    ```

如果所有命令都能正常执行，没有出现 `ModuleNotFoundError` 等导入错误，则说明迁移成功。

## 4. 注意事项

-   **Conda vs. Pip**：在 Conda 环境中，应优先使用 `conda install` 命令安装依赖。只有当某个包在 Conda 渠道（特别是 `conda-forge`）中不可用时，才在 `environment.yml` 文件的 `pip:` 部分下使用 `pip` 进行安装。这有助于确保环境的稳定性和一致性。
-   **关于 `pathlib2`**：之前的 `requirements.txt` 中包含了 `pathlib2`。这是一个在旧版本 Python 中提供 `pathlib` 功能的库。由于本项目已迁移至 Python 3.12，`pathlib` 已成为标准库的一部分，因此不再需要 `pathlib2`。
-   **编辑器/IDE 配置**：迁移后，请确保您的代码编辑器（如 VS Code）或 IDE（如 PyCharm）已将其 Python 解释器指向新创建的 `cp-data-env` Conda 环境，以获得正确的代码提示和调试支持。
