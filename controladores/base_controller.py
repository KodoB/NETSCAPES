from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi

class BaseController(QWidget):
    def __init__(self, user_data, ui_file):
        super().__init__()
        loadUi(ui_file, self)
        self.user_data = user_data
        
        if hasattr(self, 'lbl_usuario_sesion'):
            self.lbl_usuario_sesion.setText(self.user_data[1]) 
            
        self.configurar_navegacion()

    def configurar_navegacion(self):
        """Conecta todos los botones del menú lateral a sus funciones"""
        self.btn_nav_dashboard.clicked.connect(self.ir_dashboard)
        self.btn_nav_captura.clicked.connect(self.ir_captura)
        self.btn_nav_paquetes.clicked.connect(self.ir_paquetes)
        self.btn_nav_reportes.clicked.connect(self.ir_reportes)
        self.btn_nav_bitacora.clicked.connect(self.ir_bitacora)
        self.btn_logout.clicked.connect(self.cerrar_sesion)

    def ir_dashboard(self):
        from controladores.dashboard_controller import DashboardController
        self.ventana = DashboardController(self.user_data)
        self.ventana.show()
        self.close()

    def ir_captura(self):
        from controladores.captura_controller import CapturaController
        self.ventana = CapturaController(self.user_data)
        self.ventana.show()
        self.close()

    def ir_paquetes(self):
        from controladores.paquetes_controller import PaquetesController
        self.ventana = PaquetesController(self.user_data)
        self.ventana.show()
        self.close()

    def ir_reportes(self):
        from controladores.reportes_controller import ReportesController
        self.ventana = ReportesController(self.user_data)
        self.ventana.show()
        self.close()

    def ir_bitacora(self):
        from controladores.bitacora_controller import BitacoraController
        self.ventana = BitacoraController(self.user_data)
        self.ventana.show()
        self.close()

    def cerrar_sesion(self):
        from controladores.login_controller import LoginController
        self.ventana = LoginController()
        self.ventana.show()
        self.close()