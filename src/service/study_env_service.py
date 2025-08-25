import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

import serial
import struct
import requests

# from id_service import WindowClass
from card_enroll import CardEnrollApp, NotificationDialog

from_class = uic.loadUiType("src/GUI/study_env.ui")[0]

class apiReceiver(QThread):
    result = pyqtSignal()

    def __init__(self, name, bright, blind, window, parent=None):
        super().__init__(parent)
        self.name = name
        self.bright = bright
        self.blind = blind
        self.window = window

    def run(self):
        try:
            api_url = f"http://127.0.0.1:8000/users/setting/{self.name}"

            data = {'bright': self.bright, 'blind': self.blind, 'window': self.window}

            response = requests.put(api_url, json=data, timeout=10)
            status_code = str(response.status_code)
            # response.raise_for_status()

            if status_code.startswith("2"):

                self.result.emit()

        except Exception as e:
            print(f"Error : {e}")


class RfidReceiver(QThread):
    detected = pyqtSignal(bytes)
    exit = pyqtSignal()

    def __init__(self, conn, parent=None):
        super(RfidReceiver, self).__init__(parent)
        self.is_running = False
        self.conn = conn
        print("RFID receiver init")

    def run(self):
        print("RFID receiver start")
        self.is_running = True
        while (self.is_running):
            if self.conn and self.conn.is_open and self.conn.readable():
                res = self.conn.read_until(b'\n')
                if len(res) > 0:
                    cmd = res[:2]
                    print(f"res : {res}")
                    print(len(res))
                    if cmd == b'IA':
                        print('message detected')
                        self.detected.emit(res[3:7])
                    elif cmd == b'IG':
                        print('out tag detected(wrong)')
                        # id1 = res[3:7]
                        # id2 = res[7:11]
                        # print(f"id1 : {id1.hex().upper()}")
                        # print(f"id2 : {id2.hex().upper()}")
                    elif cmd == b'IZ':
                        print('out tag detected(pass)')
                        self.exit.emit()
                    else:
                        print('unknown')
                        print(f"cmd : {cmd}")

    def stop(self):
        print("RFID receiver stop")
        self.is_running = False

class NextWindow(QMainWindow, from_class):
    def __init__(self, parent=None, settings=None, conn=None):
        super().__init__()
        # parent.close()
        self.setupUi(self)

        self.new_window = None
        self.APIRecv = None

        self.name = settings['name']
        self.bright = settings['bright']
        self.blind = settings['blind']
        self.windows = settings['window']

        # self.conn = serial.Serial(port="/dev/cu.usbmodem11301", baudrate=9600, timeout=1)
        self.conn = conn
        self.outBtn.clicked.connect(self.tryOut)

        self.RFIDRecv = RfidReceiver(self.conn)
        self.RFIDRecv.exit.connect(self.save_setting_values)
        self.RFIDRecv.start()
        print(f"User settings in NextWindow: {settings}")

    def tryOut(self):
        self.scan_dialog = NotificationDialog(f"카드를 리더기에 태그해주세요.", self)

        self.send(b'IY', 0x00, b'\x00'*8)

        self.scan_dialog.exec()

    def send(self, command, status, data):
        req_data = struct.pack('<2sB8sc', command, status, data, b'\n')
        self.conn.write(req_data)
        print("send")
        return
    
    def save_setting_values(self):
        # from id_service import WindowClass

        self.APIRecv = apiReceiver(self.name, self.bright, self.blind, self.windows)
        self.APIRecv.result.connect(self.open_rfid_window)
        self.APIRecv.start()

        # if self.new_window is None:
        #     self.new_window = WindowClass(conn = self.conn)
        # self.new_window.show()
        # self.conn = None
        # self.scan_dialog.close()
        # self.close()
    
    def open_rfid_window(self):
        QMessageBox.information(self, "Success", f"{self.name}님, 안녕히 가세요")

        from id_service import WindowClass

        if self.APIRecv and self.APIRecv.isRunning():
            self.APIRecv.stop()
            self.APIRecv.wait()
        if self.RFIDRecv and self.RFIDRecv.isRunning():
            self.RFIDRecv.stop()
            self.RFIDRecv.wait()

        if self.new_window is None:
            self.new_window = WindowClass(conn = self.conn)
        self.new_window.show()
        self.conn = None
        self.scan_dialog.close()
        self.close()
