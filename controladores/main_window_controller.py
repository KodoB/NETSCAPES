from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class MainWindowController(QWidget):

    def __init__(self, user_data):
        super().__init__()
        loadUi("vistas/main_window.ui", self)
        self.user_data = user_data

        if hasattr(self, "lbl_usuario_sesion"):
            self.lbl_usuario_sesion.setText(self.user_data[1])
        if hasattr(self, "label_avatar"):
            self.label_avatar.setText(self._obtener_iniciales(self.user_data[1]))

        self._crear_paginas()
        self._conectar_navegacion()

        self.ir_dashboard()

    @staticmethod
    def _obtener_iniciales(nombre_completo):
        partes = [p for p in nombre_completo.strip().split() if p]
        if not partes:
            return "??"
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[-1][0]).upper()

    def _crear_paginas(self):
        from controladores.dashboard_controller import DashboardController
        from controladores.captura_controller import CapturaController
        from controladores.paquetes_controller import PaquetesController
        from controladores.reportes_controller import ReportesController
        from controladores.bitacora_controller import BitacoraController
        from controladores.admin_controller import AdminController

        self.pagina_dashboard = DashboardController(self.user_data)
        self.pagina_captura = CapturaController(self.user_data)
        self.pagina_paquetes = PaquetesController(self.user_data)
        self.pagina_reportes = ReportesController(self.user_data)
        self.pagina_bitacora = BitacoraController(self.user_data)
        self.pagina_admin = AdminController(self.user_data)

        if self.stackedWidget_contenido.count() > 0:
            placeholder = self.stackedWidget_contenido.widget(0)
            self.stackedWidget_contenido.removeWidget(placeholder)
            placeholder.deleteLater()

        for pagina in (
            self.pagina_dashboard,
            self.pagina_captura,
            self.pagina_paquetes,
            self.pagina_reportes,
            self.pagina_bitacora,
            self.pagina_admin,
        ):
            self.stackedWidget_contenido.addWidget(pagina)

        self.pagina_captura.estadisticas_actualizadas.connect(
            self.pagina_dashboard.actualizar_estadisticas_captura
        )
        self.pagina_dashboard.actualizar_estadisticas_captura(
            self.pagina_captura.calcular_stats_snapshot()
        )

    def _conectar_navegacion(self):
        self.btn_nav_dashboard.clicked.connect(self.ir_dashboard)
        self.btn_nav_captura.clicked.connect(self.ir_captura)
        self.btn_nav_paquetes.clicked.connect(self.ir_paquetes)
        self.btn_nav_reportes.clicked.connect(self.ir_reportes)
        self.btn_nav_bitacora.clicked.connect(self.ir_bitacora)
        self.btn_nav_admin.clicked.connect(self.ir_admin)
        self.btn_logout.clicked.connect(self.cerrar_sesion)

    def _marcar_activo(self, boton_activo):
        botones = (
            self.btn_nav_dashboard,
            self.btn_nav_captura,
            self.btn_nav_paquetes,
            self.btn_nav_reportes,
            self.btn_nav_bitacora,
            self.btn_nav_admin,
        )
        for btn in botones:
            btn.setEnabled(btn is not boton_activo)

    def ir_dashboard(self):
        self.stackedWidget_contenido.setCurrentWidget(self.pagina_dashboard)
        self._marcar_activo(self.btn_nav_dashboard)

    def ir_captura(self):
        self.stackedWidget_contenido.setCurrentWidget(self.pagina_captura)
        self._marcar_activo(self.btn_nav_captura)

    def ir_paquetes(self):
        self.stackedWidget_contenido.setCurrentWidget(self.pagina_paquetes)
        self._marcar_activo(self.btn_nav_paquetes)
        self.pagina_paquetes.cargar_todos_paquetes()

    def ir_reportes(self):
        self.stackedWidget_contenido.setCurrentWidget(self.pagina_reportes)
        self._marcar_activo(self.btn_nav_reportes)
        self.pagina_reportes.cargar_historial_reportes()

    def ir_bitacora(self):
        self.stackedWidget_contenido.setCurrentWidget(self.pagina_bitacora)
        self._marcar_activo(self.btn_nav_bitacora)
        self.pagina_bitacora.cargar_bitacora()

    def ir_admin(self):
        self.stackedWidget_contenido.setCurrentWidget(self.pagina_admin)
        self._marcar_activo(self.btn_nav_admin)
        self.pagina_admin.cargar_usuarios()

    def cerrar_sesion(self):
        from controladores.login_controller import LoginController

        if hasattr(self.pagina_dashboard, "timer_refresh"):
            self.pagina_dashboard.timer_refresh.stop()
        if hasattr(self.pagina_captura, "hilo_sniffer") and self.pagina_captura.hilo_sniffer.is_running:
            self.pagina_captura.hilo_sniffer.stop()

        self.ventana_login = LoginController()
        self.ventana_login.show()
        self.close()

    def closeEvent(self, event):
        if hasattr(self.pagina_dashboard, "timer_refresh"):
            self.pagina_dashboard.timer_refresh.stop()
        if hasattr(self.pagina_captura, "hilo_sniffer") and self.pagina_captura.hilo_sniffer.is_running:
            self.pagina_captura.hilo_sniffer.stop()
        super().closeEvent(event)
