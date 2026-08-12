"""
串口通信底层处理模块
负责：打开/关闭串口、读取数据、列出可用端口
"""
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Callable


class SerialHandler:
    """串口通信处理器"""
    
    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self._reading_thread: Optional[threading.Thread] = None
        self._running = False
        self._data_callback: Optional[Callable] = None
    
    def list_ports(self) -> list:
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]
    
    def connect(self, port: str, baudrate: int = 38400, timeout: float = 1.0) -> bool:
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.is_connected = True
            print(f"✅ 成功连接到 {port}，波特率 {baudrate}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def disconnect(self):
        self._running = False
        if self._reading_thread and self._reading_thread.is_alive():
            self._reading_thread.join(timeout=1.0)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.is_connected = False
            print("✅ 已断开串口连接")
    
    def start_reading(self, callback: Callable):
        if not self.is_connected:
            print("❌ 未连接到串口，无法开始读取")
            return
        self._data_callback = callback
        self._running = True
        self._reading_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reading_thread.start()
        print("📡 开始接收数据...")
    
    def stop_reading(self):
        self._running = False
        print("⏹️ 停止接收数据")
    
    def _read_loop(self):
        buffer = ""
        last_byte_time = time.time()
        line_timeout = 0.05
        
        while self._running and self.is_connected:
            try:
                if self.serial_port and self.serial_port.is_open:
                    byte = self.serial_port.read(1)
                    if byte:
                        char = byte.decode('utf-8', errors='ignore')
                        buffer += char
                        last_byte_time = time.time()
                        
                        if char == '\n':
                            if buffer and self._data_callback:
                                self._data_callback(buffer)
                            buffer = ""
                            last_byte_time = time.time()
                    else:
                        if buffer and (time.time() - last_byte_time) > line_timeout:
                            if buffer and self._data_callback:
                                self._data_callback(buffer)
                            buffer = ""
                            last_byte_time = time.time()
                        time.sleep(0.001)
                else:
                    break
            except Exception as e:
                print(f"❌ 读取数据异常: {e}")
                break
        
        if buffer and self._data_callback:
            self._data_callback(buffer)
    
    def write_data(self, data: str):
        if not self.is_connected or not self.serial_port:
            print("❌ 未连接到串口")
            return
        try:
            self.serial_port.write(data.encode('utf-8'))
        except Exception as e:
            print(f"❌ 发送数据失败: {e}")