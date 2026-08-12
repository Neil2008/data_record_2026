"""
串口发送对话框
负责：向下位机发送指令
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTextEdit, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class SendDialog(QDialog):
    """串口发送对话框"""
    
    # 发送信号
    send_data_signal = pyqtSignal(bytes)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("串口发送")
        self.setGeometry(200, 200, 500, 350)
        self.setModal(False)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # ===== 发送模式 =====
        mode_group = QGroupBox("发送模式")
        mode_layout = QHBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['字符串', '十六进制'])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(QLabel("模式:"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        
        layout.addWidget(mode_group)
        
        # ===== 输入区域 =====
        input_group = QGroupBox("发送内容")
        input_layout = QVBoxLayout(input_group)
        
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入要发送的内容...")
        self.input_edit.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_edit)
        
        # 十六进制提示
        self.hex_hint = QLabel("十六进制格式: FF AA 01 02 (空格分隔)")
        self.hex_hint.setStyleSheet("color: #7f8c8d; font-size: 9px;")
        self.hex_hint.setVisible(False)
        input_layout.addWidget(self.hex_hint)
        
        layout.addWidget(input_group)
        
        # ===== 预设指令 =====
        preset_group = QGroupBox("预设指令")
        preset_layout = QHBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['', 'AT', 'AT+RESET', 'AT+INFO', 'AT+START', 'AT+STOP'])
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)
        
        self.append_btn = QPushButton("追加到输入框")
        self.append_btn.clicked.connect(self._on_preset_append)
        preset_layout.addWidget(self.append_btn)
        preset_layout.addStretch()
        
        layout.addWidget(preset_group)
        
        # ===== 历史记录 =====
        history_group = QGroupBox("发送历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_text = QTextEdit()
        self.history_text.setFont(QFont("Consolas", 9))
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(100)
        history_layout.addWidget(self.history_text)
        
        layout.addWidget(history_group)
        
        # ===== 按钮 =====
        btn_layout = QHBoxLayout()
        
        self.send_btn = QPushButton("📤 发送")
        self.send_btn.clicked.connect(self._on_send)
        self.send_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_layout.addWidget(self.send_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空历史")
        self.clear_btn.clicked.connect(self._on_clear_history)
        btn_layout.addWidget(self.clear_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # 设置默认焦点
        self.input_edit.setFocus()
    
    def _on_mode_changed(self, mode: str):
        """发送模式切换"""
        if mode == '十六进制':
            self.hex_hint.setVisible(True)
            self.input_edit.setPlaceholderText("输入十六进制数据，如: FF AA 01")
        else:
            self.hex_hint.setVisible(False)
            self.input_edit.setPlaceholderText("输入要发送的内容...")
    
    def _on_preset_selected(self, text: str):
        """预设指令选择"""
        pass
    
    def _on_preset_append(self):
        """追加预设指令到输入框"""
        text = self.preset_combo.currentText()
        if text:
            current = self.input_edit.text()
            if current and not current.endswith(' '):
                self.input_edit.setText(current + ' ' + text)
            else:
                self.input_edit.setText(current + text)
            self.input_edit.setFocus()
    
    def _on_send(self):
        """发送数据"""
        text = self.input_edit.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入要发送的内容")
            return
        
        try:
            mode = self.mode_combo.currentText()
            if mode == '字符串':
                data = text.encode('utf-8')
            else:  # 十六进制
                # 去除空格，检查是否合法
                hex_str = text.replace(' ', '').replace('\t', '')
                if len(hex_str) % 2 != 0:
                    QMessageBox.warning(self, "错误", "十六进制字符串长度必须为偶数")
                    return
                data = bytes.fromhex(hex_str)
            
            # 发送信号
            self.send_data_signal.emit(data)
            
            # 添加到历史
            timestamp = datetime.now().strftime("%H:%M:%S")
            display_text = text if len(text) < 50 else text[:50] + "..."
            self.history_text.append(f"[{timestamp}] 发送: {display_text} ({len(data)} bytes)")
            self.history_text.verticalScrollBar().setValue(
                self.history_text.verticalScrollBar().maximum()
            )
            
            # 清空输入框（可选）
            # self.input_edit.clear()
            
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"数据格式错误: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送失败: {e}")
    
    def _on_clear_history(self):
        """清空历史记录"""
        self.history_text.clear()
    
    def keyPressEvent(self, event):
        """键盘事件 - Enter发送"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.input_edit.hasFocus():
                self._on_send()
        else:
            super().keyPressEvent(event)


# 导入 datetime
from datetime import datetime