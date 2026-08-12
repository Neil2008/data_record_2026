"""
Modbus RTU 解析器
"""
from typing import Optional, List
from .base_parser import BaseParser


class ModbusParser(BaseParser):
    """Modbus RTU 解析器"""
    
    def __init__(self):
        super().__init__()
        self.slave_id = 1
        self.function_code = 3
        self.register_count = 8
        self._buffer = b""
    
    def get_name(self) -> str:
        return "Modbus RTU"
    
    def set_slave_id(self, slave_id: int):
        self.slave_id = slave_id
    
    def set_function_code(self, func: int):
        self.function_code = func
    
    def set_register_count(self, count: int):
        self.register_count = count
    
    def parse(self, data: str) -> Optional[List[float]]:
        # Modbus 解析需要二进制数据，这里简化处理
        # 实际使用时需要从串口接收 bytes
        return None
    
    def parse_bytes(self, data: bytes) -> Optional[List[float]]:
        """解析二进制 Modbus 帧"""
        self._buffer += data
        
        if len(self._buffer) < 4:
            return None
        
        # 检查从机地址和功能码
        if self._buffer[0] != self.slave_id:
            self._buffer = self._buffer[1:]
            return None
        
        if self._buffer[1] != self.function_code:
            self._buffer = self._buffer[1:]
            return None
        
        byte_count = self._buffer[2] if len(self._buffer) > 2 else 0
        expected_len = 3 + byte_count + 2
        
        if len(self._buffer) < expected_len:
            return None
        
        frame = self._buffer[:expected_len]
        self._buffer = self._buffer[expected_len:]
        
        values = []
        for i in range(byte_count // 2):
            idx = 3 + i * 2
            if idx + 1 < len(frame):
                val = (frame[idx] << 8) | frame[idx + 1]
                values.append(float(val))
        
        if not values:
            return None
        
        if len(values) < self.channels:
            values.extend([0] * (self.channels - len(values)))
        elif len(values) > self.channels:
            values = values[:self.channels]
        
        return values