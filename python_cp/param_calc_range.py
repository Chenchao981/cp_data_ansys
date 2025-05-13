import pandas as pd
import logging
from typing import Optional, Dict, Tuple, Any

# 配置日志记录器
logger = logging.getLogger(__name__)

def _to_float_or_none(value: Any) -> Optional[float]:
    """尝试将值转换为 float，如果失败或值无效则返回 None。"""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def load_scope_limits_from_excel(
        file_path: str,
        sheet_name: str,
        product_name: str
    ) -> Optional[Dict[str, Tuple[Optional[float], Optional[float]]]]:
    """
    从 Excel 文件加载特定产品的参数计算范围。

    模拟 VBA 脚本 `vbas/参数计算范围定义.bas` 中 `GetProductScopeDefine` 的行为。

    Args:
        file_path (str): Excel 文件的路径。
        sheet_name (str): 包含范围定义的工作表名称。
        product_name (str): 要查找的产品名称。

    Returns:
        Optional[Dict[str, Tuple[Optional[float], Optional[float]]]]:
            如果成功找到产品并提取范围，返回一个字典 {参数ID: (下限, 上限)}。
            下限或上限可以是 float 或 None (表示无限制)。
            如果找不到产品或发生错误，返回 None。
            如果找到产品但无法提取任何有效范围，返回空字典 {}。
    """
    try:
        # 读取 Excel 文件，不将第一行作为 header，以便按索引访问
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        logger.info(f"成功读取 Excel 文件 '{file_path}' 的工作表 '{sheet_name}'。")

        # 查找产品名称所在的行 (从第二行开始，即索引 1)
        product_row_index = -1
        # 清理目标产品名称
        clean_product_name = product_name.strip().lower()
        # 检查第一列是否存在且为 object 类型
        if 0 in df.columns and pd.api.types.is_object_dtype(df[0]):
             # 使用矢量化操作查找匹配项
             matches = df.iloc[1:, 0].astype(str).str.strip().str.lower() == clean_product_name
             found_indices = matches[matches].index
             if not found_indices.empty:
                 product_row_index = found_indices[0] # 取第一个匹配项的索引
                 logger.info(f"找到产品 '{product_name}' 在行索引 {product_row_index}。")
        
        # 如果没有找到或者通过比较找到
        if product_row_index == -1:
             # 尝试迭代查找（作为备用方案，处理可能的类型问题）
             for i in range(1, len(df)):
                 cell_value = df.iloc[i, 0]
                 if pd.notna(cell_value):
                     current_name = str(cell_value).strip().lower()
                     if current_name == clean_product_name:
                         product_row_index = i
                         logger.info(f"通过迭代找到产品 '{product_name}' 在行索引 {product_row_index}。")
                         break # 找到即停止

        if product_row_index == -1:
            logger.warning(f"在工作表 '{sheet_name}' 的第一列未找到产品名称 '{product_name}'。")
            return None # 未找到产品

        # 确定参数、下限、上限行的索引
        param_row_index = product_row_index - 1
        lower_limit_row_index = product_row_index + 1
        upper_limit_row_index = product_row_index + 2

        # 检查所需行是否存在
        if not (0 <= param_row_index < len(df) and
                0 <= lower_limit_row_index < len(df) and
                0 <= upper_limit_row_index < len(df)):
            logger.error(f"产品 '{product_name}' 周围的行索引无效或超出范围。需要行: "
                         f"{param_row_index}, {lower_limit_row_index}, {upper_limit_row_index}。"
                         f"工作表总行数: {len(df)}")
            return None

        # 提取参数行、下限行、上限行数据
        param_row = df.iloc[param_row_index]
        lower_limit_row = df.iloc[lower_limit_row_index]
        upper_limit_row = df.iloc[upper_limit_row_index]

        scope_limits: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
        
        # 从第二列开始遍历参数行 (列索引从 1 开始)
        for col_index in range(1, len(param_row)):
            param_id_raw = param_row.iloc[col_index]
            
            # 检查参数 ID 是否有效 (非空且为字符串)
            if pd.notna(param_id_raw) and isinstance(param_id_raw, str) and param_id_raw.strip():
                param_id = param_id_raw.strip()
                
                # 提取下限和上限，使用辅助函数处理转换和 None 值
                lower = _to_float_or_none(lower_limit_row.iloc[col_index] if col_index < len(lower_limit_row) else None)
                upper = _to_float_or_none(upper_limit_row.iloc[col_index] if col_index < len(upper_limit_row) else None)
                
                # 仅当下限或上限至少有一个有效时才添加到字典
                if lower is not None or upper is not None:
                    scope_limits[param_id] = (lower, upper)
                    logger.debug(f"为参数 '{param_id}' 添加范围: ({lower}, {upper})")
                else:
                     logger.debug(f"参数 '{param_id}' 的上下限均无效，已忽略。")

        if not scope_limits:
             logger.warning(f"为产品 '{product_name}' 提取到 0 个有效的参数范围。")
             # 根据需求，可以返回 None 或空字典。返回空字典表示找到了产品但没有范围数据。
             # 与 VBA 返回 Nothing 的行为对应，可能返回 None 更合适？
             # 但调用方可能期望知道产品存在但无范围。返回空字典。
             # return None 
             return {}

        logger.info(f"成功为产品 '{product_name}' 加载了 {len(scope_limits)} 个参数的计算范围。")
        return scope_limits

    except FileNotFoundError:
        logger.error(f"错误：Excel 文件未找到 '{file_path}'。")
        return None
    except Exception as e:
        logger.error(f"从 Excel 加载范围时发生错误: {e}", exc_info=True)
        return None

# 示例用法 (需要一个名为 'scope_definitions.xlsx' 的文件和 'ScopeSheet' 工作表)
if __name__ == '__main__':
    # 配置基本日志记录
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 创建一个示例 Excel 文件用于测试
    try:
        example_data = {
            0: [None, 'ProductA', None, None, 'ProductB', None, None, 'ProductC', None, None],
            1: ['Param1', None, 0.1, 0.5, None, 1.0, 5.0, 'ParamX', None, 10],
            2: ['Param2', None, 10, 100, None, None, 200, 'ParamY', 'abc', '100'], # 加入非数字测试
            3: ['Param3', None, None, 50, None, None, 99, 'ParamZ', 20, None] # 加入纯 None 测试
        }
        example_df = pd.DataFrame(example_data)
        with pd.ExcelWriter('scope_definitions.xlsx', engine='openpyxl') as writer:
             example_df.to_excel(writer, sheet_name='ScopeSheet', index=False, header=False)
        logger.info("创建了示例 Excel 文件 'scope_definitions.xlsx'")

        file = 'scope_definitions.xlsx'
        sheet = 'ScopeSheet'
        
        # 测试找到产品 A
        product_a_scopes = load_scope_limits_from_excel(file, sheet, ' ProductA ') # 测试带空格和大小写
        if product_a_scopes is not None:
            print("\n--- ProductA Scopes ---")
            for param, (low, high) in product_a_scopes.items():
                print(f"  {param}: ({low}, {high})")
        
        # 测试找到产品 B
        product_b_scopes = load_scope_limits_from_excel(file, sheet, 'ProductB')
        if product_b_scopes is not None:
            print("\n--- ProductB Scopes ---")
            for param, (low, high) in product_b_scopes.items():
                print(f"  {param}: ({low}, {high})")

        # 测试找到产品 C (包含无效数据)
        product_c_scopes = load_scope_limits_from_excel(file, sheet, 'ProductC')
        if product_c_scopes is not None:
            print("\n--- ProductC Scopes ---")
            for param, (low, high) in product_c_scopes.items():
                print(f"  {param}: ({low}, {high})")
        
        # 测试未找到的产品
        product_d_scopes = load_scope_limits_from_excel(file, sheet, 'ProductD')
        if product_d_scopes is None:
            print("\n--- ProductD Scopes ---")
            print("  未找到 ProductD (预期结果)")
            
        # 测试文件不存在
        # load_scope_limits_from_excel('non_existent.xlsx', sheet, 'ProductA')
        
    except Exception as main_e:
        print(f"运行示例时出错: {main_e}") 