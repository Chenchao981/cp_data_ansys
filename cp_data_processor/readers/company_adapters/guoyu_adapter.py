"""扬州国宇 FRD 数据适配器。"""

from pathlib import Path
from typing import Dict

from cp_data_processor.data_models.cp_data import CPLot

from .base_company_adapter import BaseCompanyAdapter


class GUOYUAdapter(BaseCompanyAdapter):
    """国宇 Reader 已输出标准字段，适配器负责契约校验。"""

    def __init__(self, config: Dict):
        super().__init__("GUOYU", config)

    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        if not self.validate_data_format(lot):
            raise ValueError("国宇 FRD 数据格式验证失败")
        lot.pass_bin = 1
        return lot

    def get_field_mapping(self) -> Dict[str, str]:
        return self.field_mapping

    def can_process_file(self, file_path: str) -> bool:
        path = Path(file_path)
        if path.suffix.lower() not in {".xls", ".xlsx"} or not path.exists():
            return False
        from guoyu.guoyu_reader import GuoyuFRDReader

        return GuoyuFRDReader().can_read(str(path))
