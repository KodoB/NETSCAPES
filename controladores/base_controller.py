from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class PageController(QWidget):
    def __init__(self, user_data, ui_file):
        super().__init__()
        loadUi(ui_file, self)
        self.user_data = user_data

BaseController = PageController
