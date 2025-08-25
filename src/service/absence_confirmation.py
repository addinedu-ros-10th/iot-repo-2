import sys, json, serial
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic, QtCore
from PyQt6.QtCore import *

from_class = uic.loadUiType("project.ui")[0]

BAUD = 9600          
READ_PERIOD_MS = 1000   
DEBOUNCE_N = 1        

STYLE_PRESENT = (
    "QLabel{background:#10b981;color:#fff;border-radius:24px;"
    "padding:16px 24px;font-weight:800;font-size:48px;}"
)
STYLE_ABSENT = (
    "QLabel{background:#fbbf24;color:#111;border-radius:24px;"
    "padding:16px 24px;font-weight:800;font-size:48px;}"
)

class NextWindow(QMainWindow, from_class):
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent:
            parent.close()
        self.setupUi(self) 

        self.statusLabel   = self._el(QLabel, "statusLabel", "label_2", "label")
        self.label_elapsed = self._el(QLabel, "label__time", "label_time")
        self.label_start   = self._el(QLabel, "label__time_2", "label_time_2")
        self.label_end     = self._el(QLabel, "label__time_3", "label_time_3")

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

        try:
            self.ser = serial.Serial("/dev/ttyACM0", BAUD, timeout=2)
            self.setWindowTitle(f"Study Env - {self.ser.port}")
        except Exception:
            self.ser = None
            self.setWindowTitle("Study Env - (no port)")

        self._prev_present = None
        self._same_cnt = 0
        self._read_timer = QtCore.QTimer(self)
        self._read_timer.timeout.connect(self.poll_serial)
        if self.ser:
            self._read_timer.start(READ_PERIOD_MS)

    def _el(self, cls, *names):
        for n in names:
            w = getattr(self, n, None) or self.findChild(cls, n)
            if w is not None:
                return w
        raise RuntimeError(f"{cls.__name__} {'/'.join(names)} 를(을) 찾지 못했습니다.")

    def _to_bool(self, v):
        if isinstance(v, bool): return v
        try: return bool(int(v))
        except: return str(v).strip().lower() in ("true","t","yes","y","on")

    def poll_serial(self):
        if not self.ser:
            return
        try:
            line = b""
            while self.ser.in_waiting:
                line = self.ser.readline()
            if not line:
                line = self.ser.readline()
            if not line:
                return
            d = json.loads(line.decode("utf-8", "ignore").strip())
        except Exception:
            return

        blue = self._to_bool(d.get("blue", 0))
        red  = self._to_bool(d.get("red",  0))
        present = not (blue and red)

        if present == self._prev_present:
            self._same_cnt += 1
        else:
            self._prev_present = present
            self._same_cnt = 1

        if self._same_cnt >= DEBOUNCE_N and present != self.current_present:
            self.set_present(present)

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

    def closeEvent(self, e):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        finally:
            super().closeEvent(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = NextWindow()
    w.show()
    sys.exit(app.exec())
