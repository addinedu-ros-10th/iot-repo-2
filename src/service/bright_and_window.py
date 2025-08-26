import sys
import serial
import time
import struct

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

from_class = uic.loadUiType("GUI/bright_and_window.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.uid = bytes(4)
        self.conn = serial.Serial(port = "/dev/ttyACM0", baudrate = 9600, timeout = 1)
        self.recv = Receiver(self.conn) # Gui 시작 시 스레드 시작
        self.recv.start()

        self.brightSavedValue = 50 #정보가 저장되어야 하는 값
        self.blindSavedValue = 45 #정보가 저장되어야 하는 값
        self.windowSavedValue = 45 #정보가 저장되어야 하는 값

        self.initBright = 0 # 조명 초기화 값
        self.initBlindAngle = 0 # 블라인드 초기화 값
        self.initWindowAngle = 0 # 창문 초기화 값

        bright_min = self.brightSlider.minimum()
        bright_max = self.brightSlider.maximum()
        bright_step = self.brightSlider.singleStep()

        blind_min = self.blindDial.minimum()
        blind_max = self.blindDial.maximum()
        blind_step = self.blindDial.singleStep()

        window_min = self.windowDial.minimum()
        window_max = self.windowDial.maximum()
        window_step = self.windowDial.singleStep()

        self.isInit = True
        self.isBrightSavedSetControl = False
        self.isBrightOffControl = False

        self.isBlindSavedSetControl = False
        self.isBlindOffControl = False

        self.isWindowCloseControl = False
        self.isWindowConditioningModeControl = False

        self.brightSlider.setRange(bright_min, bright_max)
        self.brightSlider.setSingleStep(bright_step)

        self.blindDial.setRange(blind_min, blind_max)
        self.blindDial.setSingleStep(blind_step)

        self.windowDial.setRange(window_min, window_max)
        self.windowDial.setSingleStep(window_step)

        self.initSettings()

        self.brightSlider.valueChanged.connect(self.brightControl)
        self.brightSetSavedBtn.clicked.connect(self.brightSavedSetControl)
        self.brightOffBtn.clicked.connect(self.brightOffControl)

        self.blindDial.valueChanged.connect(self.blindControl)
        self.blindSetSavedBtn.clicked.connect(self.blindSavedSetControl)
        self.blindOffBtn.clicked.connect(self.blindCloseControl)
        
        self.windowDial.valueChanged.connect(self.windowControl)
        self.windowConditioningModeBtn.clicked.connect(self.windowConditioningModeControl)
        self.windowCloseBtn.clicked.connect(self.windowCloseControl)

    def initSettings(self): # 등화, 서보모터 초기 설정
        if self.isInit == True:
            self.brightControl()
            time.sleep(2)
            self.blindControl()
            time.sleep(2)
            self.windowControl()
            self.windowConditioningModeControl()
            self.isInit = False

    def brightOffControl(self): # 조명 끄기
        self.isBrightOffControl = True
        self.brightControl()

    def brightSavedSetControl(self): # 저장된 설정으로 조명 작동
        self.isBrightSavedSetControl = True
        self.brightControl()

    def brightControl(self): # 조명 작동
        if (self.isInit == True) or (self.isBrightOffControl == True):
            set_value = self.brightSlider.minimum()
            self.brightSlider.setValue(set_value)
            self.isBrightOffControl = False

        elif self.isBrightSavedSetControl == True:
            set_value = self.brightSavedValue
            self.brightSlider.setValue(set_value)
            self.isBrightSavedSetControl = False

        else:
            set_value = self.brightSlider.value()
            self.brightSavedValue = set_value

        self.labelBrightPct.setText(str(set_value) + " %")

        set_value_string = "la" + str(set_value) + "\n"

        self.conn.write(set_value_string.encode())

    def blindSavedSetControl(self): # 저장된 설정으로 블라인드 작동 
        self.isBlindSavedSetControl = True
        self.blindControl()

    def blindCloseControl(self): # 블라인드 닫기
        self.isBlindOffControl = True
        self.blindControl()

    def blindControl(self): # 블라인드 작동
        if (self.isInit == True) or (self.isBlindOffControl == True):
            set_value = self.initBlindAngle
            self.blindDial.setValue(set_value)
            self.isBlindOffControl = False
        elif self.isBlindSavedSetControl == True:
            set_value = self.blindSavedValue
            self.blindDial.setValue(set_value)
            self.isBlindSavedSetControl = False
        else:
            set_value = self.blindDial.value()
            self.blindSavedValue = set_value

        self.labelBlindDeg.setText(str(set_value) + " Deg")

        set_value_string = "wa" + str(set_value) + "\n"

        self.conn.write(set_value_string.encode())

    def windowCloseControl(self): # 창문 닫기
        self.isWindowCloseControl = True    
        self.windowControl()

    def windowConditioningModeControl(self): # 창문 환기모드
        if self.isWindowConditioningModeControl == False:
            if self.isInit == True:
                self.windowConditioningModeBtn.setText("환기 모드 실행")
            else:
                self.windowConditioningModeBtn.setText("환기 모드 중지")
                #self.conn.write("wo".encode())
                self.labelWindowDeg.setDisabled(True)
                self.windowDial.setDisabled(True)
                self.windowCloseBtn.setDisabled(True)
                self.conn.write("wc\n".encode())
                self.isWindowConditioningModeControl = True
        else:
            self.windowConditioningModeBtn.setText("환기 모드 실행")
            #self.conn.write("wf".encode())
            self.windowCloseControl()
            self.labelWindowDeg.setEnabled(True)
            self.windowDial.setEnabled(True)
            self.windowCloseBtn.setEnabled(True)
            self.isWindowConditioningModeControl = False

    def windowControl(self): # 창문 작동
        if (self.isInit == True) or (self.isWindowCloseControl == True):
            set_value = self.initWindowAngle
            self.windowDial.setValue(set_value)
            self.isWindowCloseControl = False
        else:
            set_value = self.windowDial.value()

        self.labelWindowDeg.setText(str(set_value) + " Deg")

        set_value_string = "wb" + str(set_value) + "\n"

        self.conn.write(set_value_string.encode())

class Receiver(QThread):
    detected = pyqtSignal(str)

    def __init__(self, conn, parent = None):
        super(Receiver, self).__init__(parent)

    def run(self):
        print("recv start")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec())