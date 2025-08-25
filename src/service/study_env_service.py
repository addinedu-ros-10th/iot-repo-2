import sys, time, struct, serial, json
from PyQt6 import uic, QtCore
from PyQt6.QtCore import * 
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

# ===== 고정 포트 경로 =====
PORT_ENV      = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_12624551266422712165-if00"  # (원래 PRES)
PORT_PRESENCE = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_12624551266417512681-if00"  # (원래 ENV)
# PORT_ENV      = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_12424551266429728000-if00"  # (lying)
# PORT_PRESENCE = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_12424551266429728000-if00"  # (lying)



BAUD = 9600

# ===== UI 로드(동일 폴더) =====
#from_class = uic.loadUiType("/home/geonchang/dev_ws/iot-repo-2/src/GUI/study_env.ui")[0]
from_class = uic.loadUiType("/home/dj/dev_ws/iot_project/src/GUI/study_env.ui")[0]

def i10(v: float) -> int:
    return int(round(float(v)*10.0))

STATUS_OK        = 0x00
STATUS_READ_FAIL = 0x01

STYLE_PRESENT = (
    "QLabel{background:#10b981;color:#fff;border-radius:24px;"
    "padding:16px 24px;font-weight:800;font-size:48px;}"
)
STYLE_ABSENT = (
    "QLabel{background:#fbbf24;color:#111;border-radius:24px;"
    "padding:16px 24px;font-weight:800;font-size:48px;}"
)

# ===== ENV(바이너리 프레임) 리더 =====
class ReceiverEnv(QThread):
    data   = pyqtSignal(float, float)   # t, h
    thr    = pyqtSignal(str, float)     # 'RF'/'RA'/'RH', value
    status = pyqtSignal(str, int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._run = True

    def stop(self): self._run = False

    def _readline_safe(self) -> bytes:
        """read_until 대체: 항상 read(1)로 '\n'까지 모아서 반환"""
        if self.conn is None or not getattr(self.conn, "is_open", False):
            return b""
        buf = bytearray()
        try:
            while self._run and self.conn and self.conn.is_open:
                b1 = self.conn.read(1)  # size=1 고정 → pyserial 내부 size=None 경로 회피
                if not b1:
                    continue  # timeout
                buf += b1
                if b1 == b'\n':
                    break
        except (serial.SerialException, OSError, TypeError):
            return b""
        return bytes(buf)

    def run(self):
        while self._run:
            if self.conn is None or not getattr(self.conn, "is_open", False):
                break

            res = self._readline_safe()
            if not res:
                continue

            if res.endswith(b'\r\n'):
                res = res[:-2]
            elif res.endswith(b'\n'):
                res = res[:-1]
            if len(res) < 3:
                continue

            cmd = res[:2].decode(errors="ignore")
            st  = res[2]
            if cmd == 'RD' and st == STATUS_OK and len(res) >= 7:
                t10 = int.from_bytes(res[3:5], 'little', signed=True)
                h10 = int.from_bytes(res[5:7], 'little', signed=True)
                self.data.emit(t10/10.0, h10/10.0)
            elif cmd in ('RF','RA','RH') and st == STATUS_OK and len(res) >= 7:
                v10 = int.from_bytes(res[3:7], 'little', signed=True)
                self.thr.emit(cmd, v10/10.0)
            else:
                self.status.emit(cmd, st)

# ===== PRESENCE(JSON) 리더 — 부재→재실만 지연 =====
class ReceiverPresence(QThread):
    presentChanged = pyqtSignal(bool)
    status = pyqtSignal(str, int)

    def __init__(self, conn, parent=None, hold_ms_present: int = 1000, hold_ms_absent: int = 1000):
        """
        hold_ms_present: '부재 -> 재실' 전환 지연(ms)
        hold_ms_absent : '재실 -> 부재' 전환 지연(ms), 0이면 즉시
        """
        super().__init__(parent)
        self.conn = conn
        self._run = True
        self._raw_prev = None           # 센서가 마지막으로 보고한 원시 상태
        self._stable_present = None     # emit 된 안정 상태
        self._last_change_ts = time.monotonic()
        self._hold_ms_present = int(hold_ms_present)
        self._hold_ms_absent  = int(hold_ms_absent)

    def stop(self): self._run = False

    @staticmethod
    def _to_bool(v):
        if isinstance(v, bool): return v
        try: return bool(int(v))
        except: return str(v).strip().lower() in ("true","t","yes","y","on")

    def run(self):
        while self._run:
            if self.conn is None or not getattr(self.conn, "is_open", False):
                break
            try:
                line = self.conn.readline()
            except (serial.SerialException, OSError, TypeError):
                self.status.emit("IO", 0xEF); break
            if not line:
                continue
            try:
                d = json.loads(line.decode("utf-8", "ignore").strip())
            except Exception:
                continue

            blue = self._to_bool(d.get("blue", 0))
            red  = self._to_bool(d.get("red",  0))
            raw_present = not (blue and red)  # True=재실, False=부재

            now = time.monotonic()
            if raw_present != self._raw_prev:
                self._raw_prev = raw_present
                self._last_change_ts = now  # 상태 바뀐 시각

            elapsed_ms = (now - self._last_change_ts) * 1000.0
            required_ms = self._hold_ms_present if raw_present else self._hold_ms_absent

            if elapsed_ms >= required_ms:
                if raw_present != self._stable_present:
                    self._stable_present = raw_present
                    self.presentChanged.emit(raw_present)

# ===== 메인 윈도우 =====
class NextWindow(QMainWindow, from_class):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # UI 핸들
        self.statusLabel   = self._el(QLabel, "statusLabel", "label_2", "label")
        self.label_elapsed = self._el(QLabel, "label__time", "label_time")
        self.label_start   = self._el(QLabel, "label__time_2", "label_time_2")
        self.label_end     = self._el(QLabel, "label__time_3", "label_time_3")
        self.TempEdit      = self._el(QLineEdit, "TempEdit", "TempLineEdit", "lineEditTemp")
        self.HumidEdit     = self._el(QLineEdit, "HumidEdit", "HumidLineEdit", "lineEditHumid")
        self.checkAuto     = self._el(QCheckBox, "checkAuto", "checkBoxAuto")
        self.btnFan        = self._el(QPushButton, "btnFan", "pushButtonFan")
        self.btnAC         = self._el(QPushButton, "btnAC", "pushButtonAC")
        self.btnHeat       = self._el(QPushButton, "btnHeat", "pushButtonHeat")
        self.spinFan       = self._el(QDoubleSpinBox, "spinFan", "doubleSpinBoxFan")
        self.spinAC        = self._el(QDoubleSpinBox, "spinAC", "doubleSpinBoxAC")
        self.spinHeat      = self._el(QDoubleSpinBox, "spinHeat", "doubleSpinBoxHeat")

        self.label_13.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_14.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_15.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_16.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.groupBox_5.setStyleSheet("color: black")
        self.label_13.setStyleSheet("color: black; font-weight: bold ")
        self.label_14.setStyleSheet("font-size: 24px; padding: 10px; color: black;font-weight: bold")
        self.label_15.setStyleSheet("color: black;font-weight: bold")

        # +++ 조명/창문 작동 패러미터 +++
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

        self.brightSlider.valueChanged.connect(self.brightControl)
        self.brightSetSavedBtn.clicked.connect(self.brightSavedSetControl)
        self.brightOffBtn.clicked.connect(self.brightOffControl)

        self.blindDial.valueChanged.connect(self.blindControl)
        self.blindSetSavedBtn.clicked.connect(self.blindSavedSetControl)
        self.blindOffBtn.clicked.connect(self.blindCloseControl)
        
        self.windowDial.valueChanged.connect(self.windowControl)
        self.windowConditioningModeBtn.clicked.connect(self.windowConditioningModeControl)
        self.windowCloseBtn.clicked.connect(self.windowCloseControl)
        # +++ 조명/창문 작동 패러미터 +++

        self.conn = \
            serial.Serial(port= "/dev/ttyACM0", baudrate= 9600 , timeout=1) # 근접센서용 
        
        self.conn_bw = \
            serial.Serial(port= "/dev/ttyACM1", baudrate= 9600 , timeout=1) # 조명/창문 조정용
        
        self.initSettings()
        
        # === QTimer 설정 (0.5초마다 아두이노 데이터 확인) ===
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_sensor_data)
        self.timer.start(50)




        # 초기 UI 상태
        self.time_fmt = "HH:mm:ss"
        self.absent_start_dt = None
        self.current_present = None
        self.label_elapsed.setText("00:00")
        self.label_start.setText("--:--:--")
        self.label_end.setText("--:--:--")
        self.set_present(True)

        self._elapsed_timer = QtCore.QTimer(self)
        self._elapsed_timer.timeout.connect(self.update_elapsed)
        self._elapsed_timer.start(200)

        for sb in (self.spinFan, self.spinAC, self.spinHeat):
            sb.setDecimals(1); sb.setRange(-50.0, 100.0)
            sb.setSingleStep(0.1); sb.setKeyboardTracking(False)

        self.checkAuto.setChecked(True)
        self._setManualEnabled(False)

        # 포트 열기
        self.ser_env = None
        self.ser_presence = None
        self._open_ports()

        self.setWindowTitle(
            f"Study Env - ENV: {getattr(self.ser_env,'port',None)} / PRES: {getattr(self.ser_presence,'port',None)}"
        )

        # 스레드 시작
        self.rx_env = None
        if self.ser_env:
            self.rx_env = ReceiverEnv(self.ser_env)
            self.rx_env.data.connect(self.onData)
            self.rx_env.thr.connect(self.onThr)
            self.rx_env.start()

        self.rx_presence = None
        if self.ser_presence:
            # ★ 여기서 '부재→재실 2초 지연 / 재실→부재 즉시' 설정
            self.rx_presence = ReceiverPresence(self.ser_presence, hold_ms_present=2000, hold_ms_absent=0)
            self.rx_presence.presentChanged.connect(self.set_present)
            self.rx_presence.start()

        # 신호 연결
        self.checkAuto.toggled.connect(self.onAuto)
        self.btnFan.clicked.connect(self.onFan)
        self.btnAC.clicked.connect(self.onAC)
        self.btnHeat.clicked.connect(self.onHeat)
        self.spinFan.valueChanged.connect(lambda v: self.send_env('SF', i10(v)))
        self.spinAC.valueChanged.connect(lambda v: self.send_env('SA', i10(v)))
        self.spinHeat.valueChanged.connect(lambda v: self.send_env('SH', i10(v)))

        # ENV 폴링 및 초기 질의
        if self.ser_env:
            self.timer_env = QTimer(self); self.timer_env.setInterval(1000)
            self.timer_env.timeout.connect(lambda: self.send_env('RD'))
            QTimer.singleShot(800, self.timer_env.start)
            QTimer.singleShot(200, lambda: self.send_env('SM', 1))
            QTimer.singleShot(400, lambda: self.send_env('RF'))
            QTimer.singleShot(500, lambda: self.send_env('RA'))
            QTimer.singleShot(600, lambda: self.send_env('RH'))

    # ---- 내부 유틸 ----
    def read_sensor_data(self):
        """아두이노에서 센서값과 부저 상태 읽어서 라벨에 표시"""
        if self.conn.in_waiting > 0:
            try:
                data = self.conn.readline().decode('utf-8').strip()
                if "," in data:
                    sensor_val, buzzer_val = data.split(",")
                    self.label_14.setText(f"{sensor_val}")
                    if buzzer_val == "1":
                        self.label_16.setText("On")
                        self.label_16.setStyleSheet("font-size: 24px; color: red;font-weight: bold")
                    else:
                        self.label_16.setText("Off")
                        self.label_16.setStyleSheet("font-size: 24px; color: black;font-weight: bold")
            except Exception as e:
                print("데이터 읽기 오류:", e)


    def _el(self, cls, *names):
        for n in names:
            w = getattr(self, n, None) or self.findChild(cls, n)
            if w is not None: return w
        raise RuntimeError(f"{cls.__name__}({', '.join(names)}) 를 .ui에서 찾지 못했습니다.")

    def _setManualEnabled(self, enabled: bool):
        self.btnFan.setEnabled(enabled); self.btnAC.setEnabled(enabled); self.btnHeat.setEnabled(enabled)

    def _open_ports(self):
        try:
            self.ser_env = serial.Serial(PORT_ENV, BAUD, timeout=2)
            time.sleep(1.2); self.ser_env.reset_input_buffer()
        except Exception:
            self.ser_env = None
        try:
            self.ser_presence = serial.Serial(PORT_PRESENCE, BAUD, timeout=1)
            time.sleep(1.2); self.ser_presence.reset_input_buffer()
        except Exception:
            self.ser_presence = None

    # ---- ENV 전송 ----
    def send_env(self, cmd2: str, data: int | None = None):
        if not self.ser_env or not self.ser_env.is_open: return
        pkt = bytearray(cmd2.encode('ascii'))
        pkt += (struct.pack('<i', int(data)) if data is not None else b'\x00\x00\x00\x00')
        pkt += b'\n'
        try:
            self.ser_env.write(pkt)
        except serial.SerialException:
            pass

    # ---- 슬롯 ----
    @pyqtSlot(float, float)
    def onData(self, t, h):
        self.TempEdit.setText(f"{t:.1f}")
        self.HumidEdit.setText(f"{h:.1f}")

    @pyqtSlot(str, float)
    def onThr(self, cmd, v):
        if cmd == 'RF':
            self.spinFan.blockSignals(True);  self.spinFan.setValue(v);  self.spinFan.blockSignals(False)
        elif cmd == 'RA':
            self.spinAC.blockSignals(True);   self.spinAC.setValue(v);   self.spinAC.blockSignals(False)
        elif cmd == 'RH':
            self.spinHeat.blockSignals(True); self.spinHeat.setValue(v); self.spinHeat.blockSignals(False)

    def onAuto(self, checked: bool):
        self.send_env('SM', 1 if checked else 0)
        self._setManualEnabled(not checked)
        if checked:
            self.btnFan.setText("FAN (AUTO)")
            self.btnAC.setText("A/C (AUTO)")
            self.btnHeat.setText("HEAT (AUTO)")
        else:
            self.btnFan.setText("FAN: OFF")
            self.btnAC.setText("A/C: OFF")
            self.btnHeat.setText("HEAT: OFF")
            self.send_env('SC', 0)

    def _send_mask(self):
        mask = (1 if "ON" in self.btnFan.text() else 0) \
             | ((1 if "ON" in self.btnAC.text()  else 0) << 1) \
             | ((1 if "ON" in self.btnHeat.text() else 0) << 2)
        self.send_env('SC', mask)

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

    # ---- 상태/타이머 ----
    def set_present(self, present: bool):
        prev = self.current_present
        self.current_present = present
        now = QtCore.QDateTime.currentDateTime()

        if present:
            if prev is False:
                self.label_end.setText(now.toString(self.time_fmt))
            self.statusLabel.setText("재실")
            self.statusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.statusLabel.setStyleSheet(STYLE_PRESENT)
            self.label_elapsed.setText("00:00")
        else:
            if prev is not False:
                self.absent_start_dt = now
                self.label_start.setText(now.toString(self.time_fmt))
                self.label_end.setText("--:--:--")
            self.statusLabel.setText("부재")
            self.statusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.statusLabel.setStyleSheet(STYLE_ABSENT)

    def update_elapsed(self):
        if self.current_present is False and self.absent_start_dt is not None:
            secs = self.absent_start_dt.secsTo(QtCore.QDateTime.currentDateTime())
            m, s = divmod(max(secs, 0), 60)
            self.label_elapsed.setText(f"{m:02d}:{s:02d}")
        else:
            self.label_elapsed.setText("00:00")

    # ---- 종료 정리 ----
    def closeEvent(self, e):
        try:
            for th in (getattr(self, "rx_env", None), getattr(self, "rx_presence", None)):
                try:
                    if th and th.isRunning():
                        th.stop(); th.wait(800)
                except Exception:
                    pass
            for ser in (getattr(self, "ser_env", None), getattr(self, "ser_presence", None)):
                try:
                    if ser and ser.is_open: ser.close()
                except Exception:
                    pass
        finally:
            super().closeEvent(e)

    # +++ 조명/창문 작동 함수 일람 +++
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

        self.conn_bw.write(set_value_string.encode())

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

        self.conn_bw.write(set_value_string.encode())

    def windowCloseControl(self): # 창문 닫기
        self.isWindowCloseControl = True    
        self.windowControl()

    def windowConditioningModeControl(self): # 창문 환기모드
        if self.isWindowConditioningModeControl == False:
            if self.isInit == True:
                self.windowConditioningModeBtn.setText("환기 모드 실행")
            else:
                self.windowConditioningModeBtn.setText("환기 모드 중지")
                self.conn_bw.write("wo".encode())
                self.labelWindowDeg.setDisabled(True)
                self.windowDial.setDisabled(True)
                self.windowCloseBtn.setDisabled(True)
                self.conn_bw.write("wc\n".encode())
                self.isWindowConditioningModeControl = True
        else:
            self.windowConditioningModeBtn.setText("환기 모드 실행")
            self.conn_bw.write("wf".encode())
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

        self.conn_bw.write(set_value_string.encode())
    # +++ 조명/창문 작동 함수 일람 +++

# ===== main =====
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = NextWindow()
    w.show()
    sys.exit(app.exec())
