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

        self.brightSavedValue = 50
        self.blindSavedValue = 45
        self.windowSavedValue = 45

        self.initBright = 0
        self.initBlindAngle = 0
        self.initWindowAngle = 0

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

    def initSettings(self):
        if self.isInit == True:
            self.brightControl()
            time.sleep(2)
            self.blindControl()
            time.sleep(2)
            self.windowControl()
            self.windowConditioningModeControl()
            self.isInit = False

    def brightOffControl(self):
        self.isBrightOffControl = True
        self.brightControl()

    def brightSavedSetControl(self):
        self.isBrightSavedSetControl = True
        self.brightControl()

    def brightControl(self):
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

        self.labelBrightPct.setText(str(set_value) + " %")

        set_value_string = "la" + str(set_value) + "\n"

        self.conn.write(set_value_string.encode())

    def blindSavedSetControl(self):
        self.isBlindSavedSetControl = True
        self.blindControl()

    def blindCloseControl(self):
        self.isBlindOffControl = True
        self.blindControl()

    def blindControl(self):
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

        self.labelBlindDeg.setText(str(set_value) + " Deg")

        set_value_string = "wa" + str(set_value) + "\n"

        self.conn.write(set_value_string.encode())

    def windowCloseControl(self):
        self.isWindowCloseControl = True    
        self.windowControl()

    def windowConditioningModeControl(self):
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

    def windowControl(self):
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