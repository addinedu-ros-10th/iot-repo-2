
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import * 
import serial
import struct

from_class = uic.loadUiType("/home/qatest/iot-repo-2/src/GUI/lying.ui")[0]

class windowclass (QMainWindow, from_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle("Lying Detect and prevention")

        self.groupBox.setStyleSheet("color: black;font-weight: bold")

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        self.label.setStyleSheet("color: black; font-weight: bold ")
        self.label_2.setStyleSheet("font-size: 24px; padding: 10px; color: black;font-weight: bold")
        self.label_3.setStyleSheet("color: black;font-weight: bold")


        self.conn = \
            serial.Serial(port= "/dev/ttyACM0", baudrate= 9600 , timeout=1)
        
        # === QTimer 설정 (0.5초마다 아두이노 데이터 확인) ===
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_sensor_data)
        self.timer.start(50)


    
    def read_sensor_data(self):
        """아두이노에서 센서값과 부저 상태 읽어서 라벨에 표시"""
        if self.conn.in_waiting > 0:
            try:
                data = self.conn.readline().decode('utf-8').strip()
                if "," in data:
                    sensor_val, buzzer_val = data.split(",")
                    self.label_2.setText(f"{sensor_val}")
                    if buzzer_val == "1":
                        self.label_4.setText("On")
                        self.label_4.setStyleSheet("font-size: 24px; color: red;font-weight: bold")
                    else:
                        self.label_4.setText("Off")
                        self.label_4.setStyleSheet("font-size: 24px; color: black;font-weight: bold")
            except Exception as e:
                print("데이터 읽기 오류:", e)
        

   

if __name__ == "__main__" :

    app = QApplication(sys.argv)
    myWindows = windowclass()
    myWindows.show()

    sys.exit(app.exec())    

