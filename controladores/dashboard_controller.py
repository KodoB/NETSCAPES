from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import QTimer
from controladores.base_controller import BaseController
from modelos.trafico import Trafico

class DashboardController(BaseController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/monitoreo.ui")
        self.modelo_trafico = Trafico()
        self.btn_nav_dashboard.setEnabled(False) 
        
        # Carga inicial
        self.cargar_ultimos_paquetes()

        # Configurar un temporizador para refrescar la tabla cada 3 segundos
        self.timer_refresh = QTimer(self)
        self.timer_refresh.timeout.connect(self.cargar_ultimos_paquetes)
        self.timer_refresh.start(3000)

    def cargar_ultimos_paquetes(self):
        """Extrae los paquetes y actualiza la tabla inferior visualmente"""
        datos = self.modelo_trafico.obtener_ultimos_paquetes(3)
        
        # Guardar la selección actual si la hubiera
        self.tableWidget_ultimos.setRowCount(0)
        
        for row_idx, row_data in enumerate(datos):
            self.tableWidget_ultimos.insertRow(row_idx)
            # row_data = (id, ip_origen, ip_destino, protocolo, tamano)
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                self.tableWidget_ultimos.setItem(row_idx, col_idx, item)

    def closeEvent(self, event):
        """Detiene el temporizador cuando se cambia de ventana"""
        self.timer_refresh.stop()
        super().closeEvent(event)