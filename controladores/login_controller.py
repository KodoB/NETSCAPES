from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.uic import loadUi
from modelos.usuario import Usuario

class LoginController(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("vistas/login.ui", self)
        self.modelo_usuario = Usuario()
        self.btn_login.clicked.connect(self.iniciar_sesion)

    def iniciar_sesion(self):
        usuario = self.lineEdit_usuario.text()
        password = self.lineEdit_password.text()
        user_data = self.modelo_usuario.verificar_credenciales(usuario, password)

        if user_data:
            from controladores.dashboard_controller import DashboardController
            self.dashboard = DashboardController(user_data)
            self.dashboard.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Credenciales incorrectas")