import sys, time, struct, serial
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

from_class = uic.loadUiType("src/GUI/study_env.ui")[0]

# 실수(℃)를 0.1℃ 단위 정수로 ex) 28.3℃ → 283
def i10(v: float) -> int:
    return int(round(float(v)*10.0))

# STATUS 코드
STATUS_OK        = 0x00
STATUS_READ_FAIL = 0x01

# 수신 Thread
class Receiver(QThread):
    data   = pyqtSignal(float, float)   # RD
    thr    = pyqtSignal(str, float)     # RF/RA/RH
    status = pyqtSignal(str, int)       # 기타

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._run = True

    def stop(self): self._run = False
    
    def run(self):
        while self._run:
            res = self.conn.read_until(b'\n')
            if not res:
                continue
            if res.endswith(b'\r\n'): res = res[:-2]
            elif res.endswith(b'\n'): res = res[:-1]
            if len(res) < 3:
                continue

            cmd = res[:2].decode(errors="ignore")
            st  = res[2]
            
            # RD 응답: temp:int16 + humid:int16(LE, 0.1단위)를 받아 **실수(℃, %)**로 변환
            if cmd == 'RD' and st == STATUS_OK and len(res) >= 7:
                t10 = int.from_bytes(res[3:5], 'little', signed=True)
                h10 = int.from_bytes(res[5:7], 'little', signed=True)
                self.data.emit(t10/10.0, h10/10.0)
            
            # 임계값 조회 응답(RF/RA/RH): int32(LE, 0.1단위) → 실수로 변환
            elif cmd in ('RF','RA','RH') and st == STATUS_OK and len(res) >= 7:
                v10 = int.from_bytes(res[3:7], 'little', signed=True)
                self.thr.emit(cmd, v10/10.0)
            
            #그 외 응답/에러는 로그용으로 신호 보냄
            else:
                self.status.emit(cmd, st)

class Win(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 초기 UI: 자동 모드, 수동 버튼 비활성
        self.checkAuto.setChecked(True)
        self._setManualEnabled(False)

        # 스핀박스 기본 설정
        for sb in (self.spinFan, self.spinAC, self.spinHeat):
            sb.setDecimals(1)
            sb.setRange(-50.0, 100.0)
            sb.setSingleStep(0.1)
            sb.setKeyboardTracking(False)

        # 시리얼 오픈 → 대기(안정화) → 입력버퍼 비우기(초기 쓰레기 바이트 제거를 위해 입력 버퍼 비움) 
        self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        time.sleep(2.0)
        self.ser.reset_input_buffer()

        # 수신 스레드: start 전에 시그널 연결
        self.rx = Receiver(self.ser)
        self.rx.data.connect(self.onData)
        self.rx.thr.connect(self.onThr)
        self.rx.status.connect(self.onStatus)
        self.rx.start()

        # UI 신호
        self.checkAuto.toggled.connect(self.onAuto)
        self.btnFan.clicked.connect(self.onFan)
        self.btnAC.clicked.connect(self.onAC)
        self.btnHeat.clicked.connect(self.onHeat)

        # 값 변경 → 쓰기 > (spinbox/버튼)
        self.spinFan.valueChanged.connect(lambda v: self.send('SF', i10(v)))
        self.spinAC.valueChanged.connect(lambda v: self.send('SA', i10(v)))
        self.spinHeat.valueChanged.connect(lambda v: self.send('SH', i10(v)))

        # RD 타이머는 약간 지연해서 시작 (1초마다 RD(센서값 요청) 송신. 시작은 0.8초 지연(안정 후 전송))
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: self.send('RD'))
        QTimer.singleShot(800, self.timer.start)

        # 초기 동기화
        QTimer.singleShot(200, lambda: self.send('SM', 1))  # AUTO
        QTimer.singleShot(400, lambda: self.send('RF'))     # Fan 임계
        QTimer.singleShot(500, lambda: self.send('RA'))     # AC  임계
        QTimer.singleShot(600, lambda: self.send('RH'))     # Heat 임계

    def _setManualEnabled(self, enabled: bool):
        self.btnFan.setEnabled(enabled)
        self.btnAC.setEnabled(enabled)
        self.btnHeat.setEnabled(enabled)

    # 공통 송신: <2B CMD><4B DATA><'\n'>
    def send(self, cmd2: str, data: int | None = None):
        pkt = bytearray(cmd2.encode('ascii'))
        pkt += (struct.pack('<i', int(data)) if data is not None else b'\x00\x00\x00\x00')
        pkt += b'\n'
        self.ser.write(pkt)

    # 수신 콜백
    @pyqtSlot(float, float)
    def onData(self, t, h):
        self.TempEdit.setText(f"{t:.1f}")
        self.HumidEdit.setText(f"{h:.1f}")
        
    # 스핀박스에 초기 값 바인딩 시 불필요한 재전송 방지
    @pyqtSlot(str, float)
    def onThr(self, cmd, v):
        if cmd == 'RF':
            self.spinFan.blockSignals(True);  self.spinFan.setValue(v);  self.spinFan.blockSignals(False)
        elif cmd == 'RA':
            self.spinAC.blockSignals(True);   self.spinAC.setValue(v);   self.spinAC.blockSignals(False)
        elif cmd == 'RH':
            self.spinHeat.blockSignals(True); self.spinHeat.setValue(v); self.spinHeat.blockSignals(False)

    @pyqtSlot(str, int)
    def onStatus(self, cmd, st):
        print(f"{cmd} status=0x{st:02X}")

    # 모드 토글
    def onAuto(self, checked: bool):
        self.send('SM', 1 if checked else 0)
        self._setManualEnabled(not checked)
        if checked:
            self.btnFan.setText("FAN (AUTO)")
            self.btnAC.setText("A/C (AUTO)")
            self.btnHeat.setText("HEAT (AUTO)")
        else:
            # 수동 진입 시 OFF 초기화 + 보드에 즉시 반영
            self.btnFan.setText("FAN: OFF")
            self.btnAC.setText("A/C: OFF")
            self.btnHeat.setText("HEAT: OFF")
            self.send('SC', 0)

    # 수동 토글 핸들러
    def _send_mask(self):
        mask = (1 if "ON" in self.btnFan.text() else 0) \
             | ((1 if "ON" in self.btnAC.text()  else 0) << 1) \
             | ((1 if "ON" in self.btnHeat.text() else 0) << 2)
        self.send('SC', mask)

    def onFan(self):
        t = self.btnFan.text()
        self.btnFan.setText("FAN: OFF" if "ON" in t else "FAN: ON")
        self._send_mask()

    def onAC(self):
        t = self.btnAC.text()
        self.btnAC.setText("A/C: OFF" if "ON" in t else "A/C: ON")
        self._send_mask()

    def onHeat(self):
        t = self.btnHeat.text()
        self.btnHeat.setText("HEAT: OFF" if "ON" in t else "HEAT: ON")
        self._send_mask()

    def closeEvent(self, e):
        try:
            self.rx.stop()
            self.rx.wait(800)
            try:
                self.ser.close()
            except Exception:
                pass
        finally:
            super().closeEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Win()
    w.setWindowTitle("Temp/Humid Controller")
    w.show()
    sys.exit(app.exec())


class NextWindow(QMainWindow, from_class):
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is not None:
            try:
                parent.close()
            except Exception:
                pass
        self.setupUi(self)