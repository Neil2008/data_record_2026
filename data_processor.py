"""
数据处理模块
负责：数据解析、滤波算法、数据缓存
"""
from collections import deque
from typing import List, Optional, Callable, Dict
import statistics
import math


class DataProcessor:
    
    def __init__(self, max_cache_size: int = 10000):
        self.raw_data = deque(maxlen=max_cache_size)
        self.filtered_data = deque(maxlen=max_cache_size)
        self.max_cache_size = max_cache_size
        self._on_new_data: Optional[Callable] = None
        self._on_new_line: Optional[Callable] = None
        
        # 滤波设置
        self.filter_type = "去极值平均滤波"
        self.window_size = 5
        self.num_channels = 16
        
        # 按通道存储滤波历史
        self._history: Dict[int, deque] = {}
        self._median_buffer: Dict[int, deque] = {}
        self._last_lowpass: Dict[int, float] = {}
        self._trimmed_buffer: Dict[int, deque] = {}
        
        # FIR/IIR 滤波器系数
        self._fir_buffer: Dict[int, deque] = {}
        self._iir_prev: Dict[int, float] = {}
        
        for ch in range(self.num_channels):
            self._history[ch] = deque(maxlen=self.window_size)
            self._median_buffer[ch] = deque(maxlen=self.window_size)
            self._last_lowpass[ch] = 0.0
            self._trimmed_buffer[ch] = deque(maxlen=self.window_size)
            self._fir_buffer[ch] = deque(maxlen=self.window_size)
            self._iir_prev[ch] = 0.0
        
        self._line_buffer = []
    
    def set_data_callback(self, callback: Callable):
        self._on_new_data = callback
    
    def set_line_callback(self, callback: Callable):
        self._on_new_line = callback
    
    def set_filter(self, filter_type: str, window_size: int = 5):
        self.filter_type = filter_type
        self.window_size = window_size
        
        for ch in range(self.num_channels):
            self._history[ch] = deque(maxlen=window_size)
            self._median_buffer[ch] = deque(maxlen=window_size)
            self._last_lowpass[ch] = 0.0
            self._trimmed_buffer[ch] = deque(maxlen=window_size)
            self._fir_buffer[ch] = deque(maxlen=window_size)
            self._iir_prev[ch] = 0.0
        
        print(f"🔧 滤波设置: {filter_type}, 窗口={window_size}")
    
    def set_window_size(self, window_size: int):
        if window_size < 2:
            window_size = 2
        self.window_size = window_size
        
        for ch in range(self.num_channels):
            self._history[ch] = deque(maxlen=window_size)
            self._median_buffer[ch] = deque(maxlen=window_size)
            self._trimmed_buffer[ch] = deque(maxlen=window_size)
            self._fir_buffer[ch] = deque(maxlen=window_size)
    
    def process_serial_data(self, raw_string: str):
        try:
            if not raw_string:
                return
            
            if not raw_string.strip():
                return
            
            has_newline = raw_string.endswith('\n') or raw_string.endswith('\r\n')
            clean_string = raw_string.replace('\r', '').replace('\n', '')
            clean_string = clean_string.strip()
            
            if not clean_string:
                return
            
            parts = [p.strip() for p in clean_string.split(',') if p.strip()]
            
            if not parts:
                return
            
            for idx, part in enumerate(parts):
                try:
                    raw_value = float(part)
                    if 0 < raw_value < 4096:
                        self.raw_data.append(raw_value)
                        channel = idx % self.num_channels
                        filtered_value = self._apply_filters(raw_value, channel)
                        self.filtered_data.append(filtered_value)
                        self._line_buffer.append(filtered_value)
                        if self._on_new_data:
                            self._on_new_data(raw_value, filtered_value)
                except ValueError:
                    continue
            
            if has_newline and self._line_buffer:
                self._flush_line()
        except Exception as e:
            print(f"⚠️ 数据解析异常: {e}")
    
    def _flush_line(self):
        if self._line_buffer and self._on_new_line:
            self._on_new_line(self._line_buffer)
        self._line_buffer.clear()
    
    def _apply_filters(self, value: float, channel: int) -> float:
        if self.filter_type == "无":
            return value
        elif self.filter_type == "滑动平均":
            return self._moving_average(value, channel)
        elif self.filter_type == "中值滤波":
            return self._median_filter(value, channel)
        elif self.filter_type == "低通滤波":
            return self._lowpass_filter(value, channel)
        elif self.filter_type == "去极值平均滤波":
            return self._trimmed_mean_filter(value, channel)
        elif self.filter_type == "FIR滤波":
            return self._fir_filter(value, channel)
        elif self.filter_type == "IIR滤波":
            return self._iir_filter(value, channel)
        else:
            return value
    
    def _moving_average(self, value: float, channel: int) -> float:
        """滑动平均滤波"""
        self._history[channel].append(value)
        if len(self._history[channel]) < self.window_size:
            return value
        return sum(self._history[channel]) / len(self._history[channel])
    
    def _median_filter(self, value: float, channel: int) -> float:
        """中值滤波"""
        self._median_buffer[channel].append(value)
        if len(self._median_buffer[channel]) < self.window_size:
            return value
        sorted_values = sorted(self._median_buffer[channel])
        return sorted_values[len(sorted_values) // 2]
    
    def _lowpass_filter(self, value: float, channel: int, alpha: float = 0.2) -> float:
        """一阶低通滤波 (指数平滑)"""
        if self._last_lowpass[channel] == 0.0:
            self._last_lowpass[channel] = value
        self._last_lowpass[channel] = alpha * value + (1 - alpha) * self._last_lowpass[channel]
        return self._last_lowpass[channel]
    
    def _trimmed_mean_filter(self, value: float, channel: int) -> float:
        """去极值平均滤波：去掉2个最大值和2个最小值，剩余取平均"""
        self._trimmed_buffer[channel].append(value)
        if len(self._trimmed_buffer[channel]) < self.window_size:
            return value
        
        data = list(self._trimmed_buffer[channel])
        if len(data) <= 4:
            return sum(data) / len(data)
        
        sorted_data = sorted(data)
        trimmed = sorted_data[2:-2]
        if not trimmed:
            return sum(sorted_data) / len(sorted_data)
        return sum(trimmed) / len(trimmed)
    
    def _fir_filter(self, value: float, channel: int) -> float:
        """FIR 有限脉冲响应滤波 (窗口大小作为阶数)"""
        self._fir_buffer[channel].append(value)
        if len(self._fir_buffer[channel]) < self.window_size:
            return value
        
        data = list(self._fir_buffer[channel])
        n = len(data)
        
        # 使用汉宁窗设计简单的 FIR 低通滤波器系数
        # 系数归一化，保证增益为1
        coeffs = []
        for i in range(n):
            # 汉宁窗系数
            w = 0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) if n > 1 else 1
            coeffs.append(w)
        
        # 归一化
        sum_coeffs = sum(coeffs)
        if sum_coeffs > 0:
            coeffs = [c / sum_coeffs for c in coeffs]
        
        # 卷积计算
        result = 0
        for i, c in enumerate(coeffs):
            result += data[i] * c
        
        return result
    
    def _iir_filter(self, value: float, channel: int) -> float:
        """IIR 无限脉冲响应滤波 (一阶 IIR，可调系数)"""
        # alpha 控制平滑程度，值越小越平滑
        alpha = 0.3
        
        if self._iir_prev[channel] == 0.0:
            self._iir_prev[channel] = value
        
        # y[n] = alpha * x[n] + (1 - alpha) * y[n-1]
        result = alpha * value + (1 - alpha) * self._iir_prev[channel]
        self._iir_prev[channel] = result
        return result
    
    def get_raw_data(self) -> List[float]:
        return list(self.raw_data)
    
    def get_filtered_data(self) -> List[float]:
        return list(self.filtered_data)
    
    def clear_data(self):
        self.raw_data.clear()
        self.filtered_data.clear()
        self._line_buffer.clear()
        for ch in range(self.num_channels):
            self._history[ch].clear()
            self._median_buffer[ch].clear()
            self._last_lowpass[ch] = 0.0
            self._trimmed_buffer[ch].clear()
            self._fir_buffer[ch].clear()
            self._iir_prev[ch] = 0.0