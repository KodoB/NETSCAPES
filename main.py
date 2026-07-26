import sys
from PyQt6.QtWidgets import QApplication
from controladores.login_controller import LoginController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginController()
    login_window.show()
    sys.exit(app.exec())
