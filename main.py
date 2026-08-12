"""
程序入口文件 - PyQt5 版本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from src.gui import MainWindow


def main():
    """程序主入口"""
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序异常退出: {e}")
        raise


if __name__ == "__main__":
    main()