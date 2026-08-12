"""
解析器基类
"""
from abc import ABC, abstractmethod
from typing import Optional, List


class BaseParser(ABC):
    """解析器基类"""
    
    def __init__(self):
        self.channels = 16
    
    @abstractmethod
    def parse(self, data: str) -> Optional[List[float]]:
        """解析数据，返回通道值列表"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取解析器名称"""
        pass
    
    def set_channels(self, channels: int):
        self.channels = channels