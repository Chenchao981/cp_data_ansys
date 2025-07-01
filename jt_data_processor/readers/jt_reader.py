#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT公司Excel格式CP数据读取器

基于HH公司DCPReader的成熟设计模式，专门用于读取JT公司的Excel格式CP测试数据。

特点：
- 从Summary information工作表读取元数据
- 从DUT_DATA工作表读取测试数据和规格信息
- 支持详细的日志记录和异常处理
- 标记数据无需单位转换

作者: CP Data Analysis Team
版本: 1.0.0
"""

import os
import sys
import logging
import pandas as pd
import re
from typing import List, Union, Dict, Tuple, Optional
from pathlib import Path

# 添加项目根目录到路径以导入现有模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter

# 设置日志
logger = logging.getLogger(__name__)


class JTReader:
    """
    JT公司Excel格式CP数据读取器
    
    基于HH公司DCPReader的设计模式，专门处理JT公司的Excel文件格式。
    
    数据结构：
    - Summary information: 元数据（Lot ID, Wafer ID）
    - Statistics Information: 跳过不处理
    - DUT_DATA: 测试数据和规格信息
    
    重要：JT数据无需单位转换，rawdata已与unit匹配
    """
    
    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        """
        初始化JT数据读取器
        
        Args:
            file_paths: Excel文件路径，可以是单个文件或文件列表
            pass_bin: 合格bin值，默认为1
        """
        self.file_paths = [file_paths] if isinstance(file_paths, str) else file_paths
        self.pass_bin = pass_bin
        self.lot = None
        
        # 设置日志
        self.logger = logging.getLogger(f"{__name__}.JTReader")
        self.logger.info(f"初始化JT读取器，文件数: {len(self.file_paths)}")
        
        # 验证文件存在
        self._validate_files()
    
    def _validate_files(self) -> None:
        """验证所有指定的文件是否存在且为Excel格式"""
        valid_extensions = ['.xls', '.xlsx']
        
        for file_path in self.file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in valid_extensions:
                raise ValueError(f"不支持的文件格式: {file_ext}，支持格式: {valid_extensions}")
        
        self.logger.info(f"文件验证通过，共 {len(self.file_paths)} 个有效文件")
    
    def read(self) -> CPLot:
        """
        读取所有JT Excel文件并生成CPLot对象
        
        Returns:
            CPLot: 包含所有读取数据的CPLot对象
        """
        self.logger.info("开始读取JT数据文件...")
        
        # 从第一个文件提取Lot ID作为主批次ID
        first_file = self.file_paths[0]
        lot_id = self._extract_lot_id_from_summary(first_file)
        
        # 创建CPLot对象
        self.lot = CPLot(lot_id=lot_id, pass_bin=self.pass_bin)
        self.logger.info(f"创建CPLot对象，Lot ID: {lot_id}")
        
        # 处理每个文件
        for file_path in self.file_paths:
            try:
                self._process_single_file(file_path)
            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时出错: {e}")
                continue
        
        # 更新批次统计信息
        self.lot.update_counts()
        self.logger.info(f"JT数据读取完成，晶圆数: {len(self.lot.wafers)}, 参数数: {self.lot.param_count}")
        
        return self.lot
    
    def _extract_lot_id_from_summary(self, file_path: str) -> str:
        """
        从文件夹路径提取Lot ID
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            str: 提取的Lot ID（文件夹名称）
        """
        try:
            self.logger.debug(f"从文件路径 {file_path} 提取Lot ID...")
            
            # 获取文件所在的文件夹名称作为Lot ID
            folder_path = Path(file_path).parent
            lot_id = folder_path.name
            
            self.logger.info(f"成功从文件夹路径提取Lot ID: {lot_id}")
            return lot_id
                
        except Exception as e:
            self.logger.error(f"从文件夹路径提取Lot ID失败: {e}")
            # 回退到文件名提取
            filename = Path(file_path).stem
            self.logger.warning(f"回退到文件名提取Lot ID: {filename}")
            return filename
    
    def _extract_wafer_id_from_summary(self, file_path: str) -> str:
        """
        从Summary information工作表的第9行用正则表达式提取Wafer ID
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            str: 提取的Wafer ID（冒号后的数字）
        """
        try:
            self.logger.debug(f"从 {file_path} 提取Wafer ID...")
            
            # 读取Summary information工作表
            summary_df = pd.read_excel(file_path, sheet_name='Summary information', header=None, engine='xlrd')
            
            # 根据用户确认：第9行获取WAFER_ID（索引为8）
            if len(summary_df) > 8:
                wafer_id_text = str(summary_df.iloc[8, 0])  # 第9行第1列（数据只有一列）
                
                # 使用正则表达式提取冒号右边的数字
                match = re.search(r':(\d+)', wafer_id_text)
                if match:
                    wafer_id = match.group(1)
                    self.logger.info(f"成功用正则表达式提取Wafer ID: {wafer_id} (原文本: {wafer_id_text})")
                    return wafer_id
                else:
                    self.logger.warning(f"未找到冒号格式的Wafer ID，使用原文本: {wafer_id_text}")
                    return wafer_id_text
            else:
                raise ValueError("Summary information工作表行数不足，无法读取第9行")
                
        except Exception as e:
            self.logger.error(f"从 {file_path} 提取Wafer ID失败: {e}")
            # 回退到默认值
            default_wafer_id = f"WAFER_{Path(file_path).stem}"
            self.logger.warning(f"回退到默认Wafer ID: {default_wafer_id}")
            return default_wafer_id
    
    def _process_single_file(self, file_path: str) -> None:
        """
        处理单个JT Excel文件
        
        Args:
            file_path: 要处理的Excel文件路径
        """
        self.logger.info(f"开始处理文件: {file_path}")
        
        try:
            # 1. 提取元数据
            wafer_id = self._extract_wafer_id_from_summary(file_path)
            
            # 2. 读取DUT_DATA工作表
            dut_data, unit_info, spec_info = self._read_dut_data_sheet(file_path)
            
            # 3. 提取基础列数据
            basic_data = self._extract_basic_columns(dut_data)
            
            # 4. 提取参数数据
            param_data = self._extract_parameter_columns(dut_data, unit_info, spec_info)
            
            # 5. 🔥 创建CPParameter对象 - 这是之前缺失的关键步骤
            self._create_cp_parameters(param_data, unit_info, spec_info)
            
            # 6. 创建CPWafer对象
            wafer = self._create_cp_wafer(
                wafer_id=wafer_id,
                file_path=file_path,
                basic_data=basic_data,
                param_data=param_data
            )
            
            # 7. 添加到批次
            self.lot.wafers.append(wafer)
            self.logger.info(f"成功处理文件: {file_path}，芯片数: {wafer.chip_count}")
            
        except Exception as e:
            self.logger.error(f"处理文件 {file_path} 失败: {e}")
            raise
    
    def _read_dut_data_sheet(self, file_path: str) -> Tuple[pd.DataFrame, Dict, Dict]:
        """
        读取DUT_DATA工作表的数据和规格信息
        
        根据用户确认的结构：
        - 第1行：参数列表头
        - 第2行：单位信息
        - 第3-4行：规格限制
        - 第6行开始：实际测试数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Tuple[pd.DataFrame, Dict, Dict]: (测试数据, 单位信息, 规格信息)
        """
        try:
            self.logger.debug(f"读取 {file_path} 的DUT_DATA工作表...")
            
            # 读取DUT_DATA工作表的所有数据
            full_df = pd.read_excel(file_path, sheet_name='DUT_DATA', header=None, engine='xlrd')
            
            if len(full_df) < 6:
                raise ValueError("DUT_DATA工作表数据不足，至少需要6行")
            
            # 提取表头（第1行，索引0）
            headers = full_df.iloc[0].tolist()
            
            # 提取单位信息（第2行，索引1）
            units = full_df.iloc[1].tolist()
            unit_info = dict(zip(headers, units))
            
            # 提取规格信息（第3-4行，索引2-3）
            limit_u = full_df.iloc[2].tolist()  # 上限
            limit_l = full_df.iloc[3].tolist()  # 下限
            spec_info = {
                'limit_u': dict(zip(headers, limit_u)),
                'limit_l': dict(zip(headers, limit_l))
            }
            
            # 提取实际测试数据（从第6行开始，索引5开始）
            data_df = full_df.iloc[5:].copy()
            data_df.columns = headers
            data_df = data_df.reset_index(drop=True)
            
            self.logger.info(f"DUT_DATA读取成功，数据行数: {len(data_df)}, 参数列数: {len(headers)}")
            
            return data_df, unit_info, spec_info
            
        except Exception as e:
            self.logger.error(f"读取DUT_DATA工作表失败: {e}")
            raise
    
    def _extract_basic_columns(self, dut_data: pd.DataFrame) -> Dict:
        """
        提取基础列数据（坐标、bin、序号等）
        
        根据用户确认的字段映射：
        - Seq = DUT_NO
        - Bin = SOFT_BIN  
        - X = X_COORD
        - Y = Y_COORD
        - CONT = TEST_NUM
        
        Args:
            dut_data: DUT_DATA数据
            
        Returns:
            Dict: 基础列数据字典
        """
        basic_data = {}
        
        # 字段映射（JT字段名 -> 标准字段名）
        field_mapping = {
            'DUT_NO': 'Seq',
            'SOFT_BIN': 'Bin',
            'X_COORD': 'X', 
            'Y_COORD': 'Y',
            'TEST_NUM': 'CONT'
        }
        
        for jt_field, std_field in field_mapping.items():
            if jt_field in dut_data.columns:
                basic_data[std_field] = dut_data[jt_field].values
                self.logger.debug(f"提取基础列: {jt_field} -> {std_field}")
            else:
                self.logger.warning(f"未找到基础列: {jt_field}")
                basic_data[std_field] = None
        
        return basic_data
    
    def _extract_parameter_columns(self, dut_data: pd.DataFrame, unit_info: Dict, spec_info: Dict) -> pd.DataFrame:
        """
        提取参数列数据（TEST_NUM及其右边的所有字段都是参数）
        
        Args:
            dut_data: DUT_DATA数据
            unit_info: 单位信息
            spec_info: 规格信息
            
        Returns:
            pd.DataFrame: 参数数据
        """
        # 基础列名（需要排除的列，按照用户确认的字段映射）
        basic_columns = ['DUT_NO', 'SOFT_BIN', 'X_COORD', 'Y_COORD']
        
        # 找到TEST_NUM列的位置
        if 'TEST_NUM' in dut_data.columns:
            test_num_idx = dut_data.columns.get_loc('TEST_NUM')
            self.logger.info(f"找到TEST_NUM列，位置: {test_num_idx}")
            
            # TEST_NUM及其右边的所有列都是参数
            param_columns = dut_data.columns[test_num_idx:].tolist()
        else:
            # 如果没有TEST_NUM列，则提取除基础列外的所有列
            param_columns = [col for col in dut_data.columns if col not in basic_columns]
            self.logger.warning("未找到TEST_NUM列，使用默认参数列提取方式")
        
        # 创建参数数据DataFrame
        param_data = dut_data[param_columns].copy()
        
        self.logger.info(f"提取参数列: {len(param_columns)}个参数")
        self.logger.debug(f"参数列名: {param_columns[:10]}{'...' if len(param_columns) > 10 else ''}")  # 只显示前10个参数名
        
        # 🔥 重要：JT数据无需单位转换，直接返回原始数据
        self.logger.info("JT数据无需单位转换，保持原始数值")
        
        return param_data
    
    def _create_cp_parameters(self, param_data: pd.DataFrame, unit_info: Dict, spec_info: Dict) -> None:
        """
        为参数数据创建CPParameter对象（支持去重）
        
        🔥 修复：避免多文件处理时重复创建相同参数
        
        Args:
            param_data: 参数数据DataFrame
            unit_info: 单位信息字典
            spec_info: 规格信息字典
        """
        # 获取已存在的参数ID列表，用于去重
        existing_param_ids = {param.id for param in self.lot.params}
        new_params_count = 0
        
        for param_name in param_data.columns:
            # 跳过基础列（如果还有的话）
            if param_name in ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT']:
                continue
            
            # 🔥 去重检查：如果参数已存在，跳过创建
            if param_name in existing_param_ids:
                self.logger.debug(f"参数 {param_name} 已存在，跳过重复创建")
                continue
                
            # 获取参数信息
            unit = unit_info.get(param_name, None)
            limit_l = spec_info.get('limit_l', {}).get(param_name, None)
            limit_u = spec_info.get('limit_u', {}).get(param_name, None)
            
            # 转换限制值为数值类型
            try:
                sl = float(limit_l) if limit_l is not None and str(limit_l).replace('.', '').replace('-', '').isdigit() else None
            except (ValueError, TypeError):
                sl = None
                
            try:
                su = float(limit_u) if limit_u is not None and str(limit_u).replace('.', '').replace('-', '').isdigit() else None
            except (ValueError, TypeError):
                su = None
            
            # 创建CPParameter对象
            cp_param = CPParameter(
                id=param_name,
                unit=unit,
                sl=sl,
                su=su,
                test_cond=[]  # JT公司测试条件为空
            )
            
            # 添加到批次参数列表（仅新参数）
            self.lot.params.append(cp_param)
            existing_param_ids.add(param_name)  # 更新已存在参数集合
            new_params_count += 1
            self.logger.debug(f"✅ 新增参数: {param_name}, 单位: {unit}, 下限: {sl}, 上限: {su}")
        
        self.logger.info(f"✅ 参数创建完成: 新增 {new_params_count} 个参数，总计 {len(self.lot.params)} 个参数")
    
    def _create_cp_wafer(self, wafer_id: str, file_path: str, 
                        basic_data: Dict, param_data: pd.DataFrame) -> CPWafer:
        """
        创建CPWafer对象
        
        Args:
            wafer_id: 晶圆ID
            file_path: 文件路径
            basic_data: 基础数据字典
            param_data: 参数数据
            
        Returns:
            CPWafer: 创建的晶圆对象
        """
        # 首先创建基础数据DataFrame
        chip_count = len(next(iter(basic_data.values())))
        
        # 初始化芯片数据DataFrame
        chip_data = pd.DataFrame()
        
        # 添加Lot_ID和Wafer_ID
        chip_data['Lot_ID'] = [self.lot.lot_id] * chip_count
        chip_data['Wafer_ID'] = [wafer_id] * chip_count
        
        # 添加基础列到芯片数据
        for field, values in basic_data.items():
            if values is not None:
                chip_data[field] = values
                
        # 合并参数数据（确保不包含基础列）
        # 基础列的原始名称（JT格式）+ 映射后的标准名称 + Lot和Wafer ID列
        basic_column_names = ['DUT_NO', 'SOFT_BIN', 'X_COORD', 'Y_COORD', 'TEST_NUM'] + \
                           list(basic_data.keys()) + ['Lot_ID', 'Wafer_ID']
        param_only_data = param_data.drop(columns=[col for col in param_data.columns 
                                                  if col in basic_column_names], errors='ignore')
        
        # 将参数数据添加到芯片数据中
        for col in param_only_data.columns:
            chip_data[col] = param_only_data[col].values
        
        self.logger.info(f"芯片数据创建完成: {len(chip_data)}行 x {len(chip_data.columns)}列")
        self.logger.debug(f"最终列名: {list(chip_data.columns)}")
        
        # 创建CPWafer对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=file_path,
            source_lot_id=self.lot.lot_id,
            chip_count=len(chip_data),
            x=basic_data.get('X'),
            y=basic_data.get('Y'),
            bin=basic_data.get('Bin'),
            seq=basic_data.get('Seq'),
            chip_data=chip_data
        )
        
        return wafer
    
    def get_unit_info(self, file_path: str) -> Dict:
        """
        获取指定文件的单位信息（用于规格文件生成）
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Dict: 单位信息字典
        """
        try:
            _, unit_info, _ = self._read_dut_data_sheet(file_path)
            return unit_info
        except Exception as e:
            self.logger.error(f"获取单位信息失败: {e}")
            return {}
    
    def get_spec_info(self, file_path: str) -> Dict:
        """
        获取指定文件的规格信息（用于规格文件生成）
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Dict: 规格信息字典
        """
        try:
            _, _, spec_info = self._read_dut_data_sheet(file_path)
            return spec_info
        except Exception as e:
            self.logger.error(f"获取规格信息失败: {e}")
            return {}


# 简化的函数接口（保持与现有代码兼容）
def read_jt_files(file_paths: Union[str, List[str]], pass_bin: int = 1) -> CPLot:
    """
    简化的JT文件读取函数
    
    Args:
        file_paths: 文件路径
        pass_bin: 合格bin值
        
    Returns:
        CPLot: 读取的数据对象
    """
    reader = JTReader(file_paths, pass_bin)
    return reader.read()


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"测试读取JT文件: {file_path}")
        
        try:
            reader = JTReader(file_path)
            lot = reader.read()
            print(f"读取成功: Lot ID = {lot.lot_id}, 晶圆数 = {len(lot.wafers)}")
        except Exception as e:
            print(f"读取失败: {e}")
    else:
        print("用法: python jt_reader.py <excel_file_path>") 