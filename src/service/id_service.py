import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

from study_env_service import NextWindow

from_class = uic.loadUiType("src/GUI/id.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.setWindowTitle("RFID 출입 시스템 (단순 버전)")
        self.new_window = None
        self.tLabel.setText("RFID 태그를 스캔하세요.")

        self.nwBtn.clicked.connect(self.openNewWindow)

    def openNewWindow(self):
        if self.new_window is None:
            self.new_window = NextWindow(self)
        
        self.new_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec())