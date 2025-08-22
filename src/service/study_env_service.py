import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6.QtCore import *

from_class = uic.loadUiType("src/GUI/study_env.ui")[0]

class NextWindow(QMainWindow, from_class):
    def __init__(self, parent=None):
        super().__init__()
        parent.close()
        self.setupUi(self)