"""
CSV/纯文本解析器
"""
from typing import Optional, List
from .base_parser import BaseParser


class CSVParser(BaseParser):
    """CSV/纯文本解析器"""
    
    def __init__(self):
        super().__init__()
        self.delimiter = ','
    
    def get_name(self) -> str:
        return "CSV/纯文本"
    
    def parse(self, data: str) -> Optional[List[float]]:
        try:
            if not data or data.startswith('#') or data.startswith('//'):
                return None
            
            parts = [p.strip() for p in data.split(self.delimiter) if p.strip()]
            values = []
            for part in parts:
                try:
                    values.append(float(part))
                except ValueError:
                    continue
            
            if not values:
                return None
            
            if len(values) < self.channels:
                values.extend([0] * (self.channels - len(values)))
            elif len(values) > self.channels:
                values = values[:self.channels]
            
            return values
            
        except Exception as e:
            print(f"CSV解析错误: {e}")
            return None