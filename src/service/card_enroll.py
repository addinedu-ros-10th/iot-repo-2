from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

import sys
import serial
import struct
import requests

class RFIDRecv(QThread):
    card_detected = pyqtSignal(bytes)

    def __init__(self, conn, parent=None):
        super(RFIDRecv, self).__init__(parent)
        self.conn = conn
        self.is_running = False

    def run(self):
        print("RFIDRecv: 쓰레드 시작.")
        self.is_running = True
        while self.is_running:
            if self.conn and self.conn.is_open and self.conn.readable():
                try:
                    response = self.conn.read(12)
                    if len(response) == 12:
                        header, status, data, term = struct.unpack('<2sB8sc', response)
                        header_str = header.decode(errors='ignore')
                    
                        if header_str == "IR":
                            print("RFIDRecv: IR 패킷 수신됨.")
                            uid_bytes = data[:4]
                            self.card_detected.emit(uid_bytes)
                # 만약 12바이트가 아니라면 (0~11바이트), 해당 데이터는 무시하고 다음 루프로 넘어갑니다.

                except Exception as e:
                    # 위 로직으로 대부분의 unpack 에러는 사라지지만, 다른 예외를 위해 남겨둡니다.
                    print(f"RFIDRecv error: {e}")
            
    def stop(self):
        print("RFIDRecv: 쓰레드 정지 요청 수신.")
        self.is_running = False

class apiReceiver(QThread):
    # putUser = pyqtSignal()

    def __init__(self, name, uid, parent=None):
        super().__init__(parent)
        self.name = name
        self.uid = uid

    def run(self):
        try:
            api_url = f"http://127.0.0.1:8000/users"

            print(f"self.name: {self.name}")
            print(f"self.uid: {self.uid.hex().upper()}")
            payload = {
                'name': self.name,
                'uid': self.uid.hex().upper(),
            }

            response = requests.post(api_url, json=payload, timeout=10)

            response.raise_for_status()

            print(f"데이터 전송 성공: {response.status_code} - {response.json()}")

            # self.putUser.emit()

        except Exception as e:
            print(f"Error : {e}")

# UI 파일 로드 및 다이얼로그 (수정 없음)
from_class = uic.loadUiType("src/GUI/card_enroll.ui")[0]

class NotificationDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("알림")
        self.label = QLabel(message)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

# class CardEnrollApp(QMainWindow, from_class):
class CardEnrollApp(QDialog, from_class):
    send_packet_signal = pyqtSignal(str, int)
    stop_worker_signal = pyqtSignal()
    registration_finished = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("카드 등록")

        self.recv = None

        # self.conn = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        self.conn = conn
        self.recv = RFIDRecv(self.conn)
        self.recv.card_detected.connect(self.on_card_scanned)
        self.recv.start()

        self.cardScanBtn.setEnabled(False)

        self.nameEdit.textChanged.connect(self.check_name_edit)
        self.nameEdit.editingFinished.connect(self.check_name_edit)

        self.cardScanBtn.clicked.connect(self.start_card_scan)

    def closeEvent(self, event):
        if self.recv and self.recv.isRunning():
            self.recv.stop()
            self.recv.wait()
        self.registration_finished.emit()
        super().closeEvent(event)

    def start_card_scan(self):
        print("Main: 카드스캔 버튼 클릭. REGISTER 모드 시작 요청")
        self.send_packet("IS", 0x00)

        self.cardScanBtn.setFocus()
        name = self.nameEdit.text()
        print(f"Start card scan for name: {name}")

        self.scan_dialog = NotificationDialog(f"{name}님의 카드를 리더기에 태그해주세요.", self)
        self.scan_dialog.exec()

    def on_card_scanned(self, uid):
        if hasattr(self, 'scan_dialog') and self.scan_dialog.isVisible():
            self.scan_dialog.accept()
        name = self.nameEdit.text()
        print(f"Registration process: Name={name}, UID={uid}")

        self.apiRecv = apiReceiver(name, uid)
        self.apiRecv.finished.connect(lambda: self.on_registration_complete(name, uid))
        self.apiRecv.start()

    def on_registration_complete(self, name, uid):
        QMessageBox.information(self, "등록 완료", f"이름: {name}님의 카드가 성공적으로 등록되었습니다.")
        self.send_packet("IT", 0x00)
        self.nameEdit.clear()

        self.close()
        # 등록이 완료되면 아두이노는 자동으로 WAIT 모드로 돌아갑니다.
        # 만약 다시 등록 모드로 진입시키고 싶다면 아래 줄의 주석을 해제하세요.
        # self.start_registration_mode()

    def check_name_edit(self):
        name = self.nameEdit.text()
        self.cardScanBtn.setEnabled(len(name) >= 2)

    def send_packet(self, header, status, data=b'\x00'*8):
        if self.conn and self.conn.is_open:
            terminator = b'\n'
            packet = struct.pack('<2sB8sc', header.encode(), status, data, terminator)
            self.conn.write(packet)
            print(f"Sent Packet via Worker: Header={header}, Status={status}")
        else:
            print(f"Worker: 포트가 닫혀있어 {header} 신호를 보낼 수 없음.")

# 프로그램 실행 부분 (수정 없음)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    myWindows = CardEnrollApp()
    myWindows.show()
    sys.exit(app.exec())