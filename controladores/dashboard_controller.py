from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import QTimer
from controladores.base_controller import PageController
from controladores.utilidades import formatear_tamano
from modelos.trafico import Trafico

class DashboardController(PageController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/monitoreo.ui")
        self.modelo_trafico = Trafico()

        self.cargar_ultimos_paquetes()

        self.timer_refresh = QTimer(self)
        self.timer_refresh.timeout.connect(self.cargar_ultimos_paquetes)
        self.timer_refresh.start(3000)

    def cargar_ultimos_paquetes(self):
        datos = self.modelo_trafico.obtener_ultimos_paquetes(3)

        self.tableWidget_ultimos.setRowCount(0)

        for row_idx, row_data in enumerate(datos):
            self.tableWidget_ultimos.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                self.tableWidget_ultimos.setItem(row_idx, col_idx, item)

    def actualizar_estadisticas_captura(self, stats):
        self.lbl_t1_valor.setText(str(stats['paquetes_totales']))
        self.lbl_t1_sub.setText(f"+{stats['paquetes_por_minuto']} / min")

        self.lbl_t2_valor.setText(formatear_tamano(stats['total_bytes']))

        self.lbl_t3_valor.setText(str(stats['protocolos_distintos']))

        self.lbl_t4_valor.setText(str(stats['ips_unicas']))
        self.lbl_t4_sub.setText(f"{stats['ips_sospechosas']} sospechosas")

        self.progressBar_http.setValue(stats['porcentaje_http'])
        self.lbl_val_http.setText(f"{stats['porcentaje_http']}%")

        self.progressBar_tcp.setValue(stats['porcentaje_tcp'])
        self.lbl_val_tcp.setText(f"{stats['porcentaje_tcp']}%")

        self.progressBar_udp.setValue(stats['porcentaje_udp'])
        self.lbl_val_udp.setText(f"{stats['porcentaje_udp']}%")

        self.progressBar_dns.setValue(stats['porcentaje_dns'])
        self.lbl_val_dns.setText(f"{stats['porcentaje_dns']}%")
