"""
JT公司特定格式的CP数据读取器。
"""
from typing import List, Union
import pandas as pd

from .base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer

class JTReader(BaseReader):
    """
    用于读取和解析JT公司特定Excel格式的CP数据。
    """

    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        super().__init__(file_paths, pass_bin)

    def read(self) -> CPLot:
        """
        读取所有指定的JT Excel文件，并将它们合并到一个CPLot对象中。

        Returns:
            CPLot: 包含所有读取和解析后的数据的CPLot对象。
        """
        # 假设所有文件属于同一个Lot，从第一个文件中提取Lot ID
        lot_id = self._extract_lot_id_from_summary(self.file_paths[0])
        self.lot = CPLot(lot_id=lot_id)

        for file_path in self.file_paths:
            self._extract_from_file(file_path, self.lot)

        return self.lot

    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        """
        从单个JT Excel文件中提取数据并填充到CPLot对象中。

        Args:
            file_path: 要读取的单个Excel文件的路径。
            lot: 要填充数据的CPLot对象。
        """
        try:
            xls = pd.ExcelFile(file_path)
            
            # 1. 读取元数据
            try:
                summary_df = pd.read_excel(xls, sheet_name='Summary information', header=None)
                # 查找包含'WAFER_ID:'的行
                for idx, row in summary_df.iterrows():
                    if 'WAFER_ID:' in str(row.iloc[0]):
                        wafer_id_text = str(row.iloc[0])
                        import re
                        match = re.search(r':(\d+)', wafer_id_text)
                        wafer_id_str = match.group(1) if match else "01"
                        break
                else:
                    wafer_id_str = "01"  # 默认值
                print(f"提取到Wafer ID: {wafer_id_str}")
            except Exception as e:
                print(f"提取Wafer ID失败: {e}")
                wafer_id_str = "01"  # 默认值

            # 2. 读取测试数据
            # 跳过元信息行，并将第一行作为表头
            data_df = pd.read_excel(xls, sheet_name='DUT_DATA', header=0, skiprows=[1, 2, 3, 4])
            
            # 3. 直接应用字段映射，创建完整的chip_data
            # 简单直接的方法：应用映射后包含所有列在chip_data中
            field_mapping = {
                'DUT_NO': 'Seq',
                'SOFT_BIN': 'Bin', 
                'X_COORD': 'X',
                'Y_COORD': 'Y',
                'TEST_NUM': 'CONT'
            }
            
            # 应用字段映射
            chip_data = data_df.copy()
            for old_name, new_name in field_mapping.items():
                if old_name in chip_data.columns:
                    chip_data = chip_data.rename(columns={old_name: new_name})
            
            # 移除不需要的列（包括可能重复的列）
            cols_to_remove = ['SITE_NUM', 'PART_ID', 'PASSFG']
            # 如果存在Lot_ID和Wafer_ID列，也移除它们，避免与后续添加的LotID和WaferID重复
            if 'Lot_ID' in chip_data.columns:
                cols_to_remove.append('Lot_ID')
            if 'Wafer_ID' in chip_data.columns:
                cols_to_remove.append('Wafer_ID')
            chip_data = chip_data.drop(columns=[col for col in cols_to_remove if col in chip_data.columns])

            # 4. 创建并添加CPWafer对象 - chip_data包含所有数据
            wafer = CPWafer(
                wafer_id=str(wafer_id_str),
                file_path=file_path,
                source_lot_id=lot.lot_id,
                chip_count=len(data_df),
                x=None,  # 数据已在chip_data中
                y=None,  # 数据已在chip_data中
                bin=None,  # 数据已在chip_data中
                seq=None,  # 数据已在chip_data中
                chip_data=chip_data
            )
            lot.wafers.append(wafer)
            lot.update_counts()

        except FileNotFoundError:
            print(f"错误: 文件未找到 '{file_path}'")
        except KeyError as e:
            print(f"处理 '{file_path}' 时发生列名错误: {e}。请检查Excel文件中的列名是否与代码预期一致。")
        except Exception as e:
            print(f"处理 '{file_path}' 时发生未知错误: {e}")

    def _extract_lot_id_from_summary(self, file_path: str) -> str:
        """
        从文件夹路径提取Lot ID（按照用户要求）。

        Args:
            file_path: Excel文件的路径。

        Returns:
            从文件夹路径提取的Lot ID字符串。
        """
        try:
            # 从文件夹路径提取Lot ID
            from pathlib import Path
            folder_path = Path(file_path).parent
            lot_id = folder_path.name
            print(f"从文件夹路径提取Lot ID: {lot_id}")
            return lot_id
        except Exception as e:
            print(f"从文件夹路径提取Lot ID失败: {e}")
            # 回退到基于文件名的提取
            return super().extract_lot_id(file_path) 