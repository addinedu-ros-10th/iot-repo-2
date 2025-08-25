from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

import sys
import serial
import struct
import requests

from study_env_service import NextWindow
from card_enroll import CardEnrollApp, NotificationDialog

from_class = uic.loadUiType("src/GUI/id.ui")[0]

class apiReceiver(QThread):
    getUids = pyqtSignal(list)

    def __init__(self, uid, parent=None):
        super().__init__(parent)
        self.uid = uid

    def run(self):
        try:
            api_url = f"http://127.0.0.1:8000/users/uid"

            params = {'uid': self.uid.hex().upper()}

            response = requests.get(api_url, params=params, timeout=10)
            status_code = str(response.status_code)
            # response.raise_for_status()

            if status_code.startswith("2"):
                uids = []
                for map_obj in response.json():
                    del map_obj['id']
                    del map_obj['created_at']
                    uids.append(map_obj)

                self.getUids.emit(uids)
            else:
                self.getUids.emit(list(["error", status_code]))

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
                    else:
                        print('unknown')
                        print(f"cmd : {cmd}")

    def stop(self):
        print("RFID receiver stop")
        self.is_running = False


class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.new_window = None
        self.tLabel.setText("RFID 태그를 스캔하세요.")

        self.nwBtn.clicked.connect(self.openNewWindow)
        self.enrollBtn.clicked.connect(self.open_enroll_window)

        # DB 스레드를 담아둘 변수. None으로 초기화.
        self.apiReceiver = None
        self.conn = None
        self.enroll_window = None

        try:
            self.conn = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=1)
            self.rfid_worker = RfidReceiver(self.conn)
            self.rfid_worker.detected.connect(self.handle_rfid_detection)
            self.rfid_worker.start()
        except serial.SerialException as e:
            self.tLabel.setText(f"시리얼 포트 오류: {e}")
        
        self.outBtn.clicked.connect(self.tryOut)

    def open_enroll_window(self):
        if self.enroll_window is None:
            self.rfid_worker.stop()
            self.rfid_worker.wait(1000)
            self.enroll_window = CardEnrollApp(conn=self.conn)
            self.enroll_window.registration_finished.connect(self.close_enroll_window)
            self.enroll_window.show()

    def close_enroll_window(self):
        self.enroll_window = None
        self.rfid_worker.start()


    def tryOut(self):
        self.scan_dialog = NotificationDialog(f"카드를 리더기에 태그해주세요.", self)

        self.send(b'IY', 0x00, b'\x00'*8)

        self.scan_dialog.exec()


    #RFID 스레드에서 UID가 감지되면 호출될 함수
    def handle_rfid_detection(self, uid_bytes):
        uid_string = uid_bytes.hex().upper() # 화면 표시용으로만 문자열 변환
        self.tLabel.setText(f"UID: {uid_string}\n사용자 조회 중...")

        self.apiReceiver = apiReceiver(uid_bytes)
        self.apiReceiver.getUids.connect(self.getDBResult)
        self.apiReceiver.start()

    def getDBResult(self, resultList):
        if resultList[0] != "error":
            user_name = resultList[0]['name']

            # 사용자의 모든 uid 보내기
            uids = b''
            for user_info in resultList:
                uids += bytes.fromhex(user_info['uid'])

            self.send(b'IB', status=0x00, data=uids)
            print(uids.hex().upper())

            self.tLabel.setText(f"{user_name}님, 환영합니다!")
        else:
            self.send(b'IB', status=0xA1, data = b'\x00' * 8)
            if (resultList[1] == "404"):
                self.tLabel.setText(f"등록되지 않은 사용자입니다.")

    def send(self, command, status, data):
        req_data = struct.pack('<2sB8sc', command, status, data, b'\n')
        self.conn.write(req_data)
        print("send")
        return

    def openNewWindow(self):
        if self.new_window is None:
            self.new_window = NextWindow(self)
        
        self.new_window.show()

    def closeEvent(self, event):
        if self.rfid_worker and self.rfid_worker.isRunning():
            self.rfid_worker.stop()
            self.rfid_worker.wait()
        if self.conn and self.conn.is_open:
            self.conn.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec())