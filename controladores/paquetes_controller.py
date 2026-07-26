from PyQt6.QtWidgets import QTableWidgetItem
from controladores.base_controller import PageController
from modelos.trafico import Trafico

class PaquetesController(PageController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/paquetes.ui")
        self.modelo_trafico = Trafico()

        self.cargar_todos_paquetes()

        self.tableWidget_paquetes.itemSelectionChanged.connect(self.mostrar_detalles)

    def cargar_todos_paquetes(self):
        datos = self.modelo_trafico.obtener_todos_paquetes()
        self.tableWidget_paquetes.setRowCount(0)
        for row_idx, row_data in enumerate(datos):
            self.tableWidget_paquetes.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                self.tableWidget_paquetes.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def mostrar_detalles(self):
        fila_seleccionada = self.tableWidget_paquetes.currentRow()
        if fila_seleccionada >= 0:
            id_paquete = self.tableWidget_paquetes.item(fila_seleccionada, 0).text()

            detalle = self.modelo_trafico.buscar_paquete_por_id(id_paquete)

            if detalle:
                self.lbl_detalles_id.setText(f"Información del paquete #{id_paquete}")
                self.lbl_val_ip_origen.setText(str(detalle[2]))
                self.lbl_val_ip_destino.setText(str(detalle[3]))
                self.lbl_val_protocolo.setText(str(detalle[4]))
                self.lbl_val_tiempo.setText(str(detalle[1]))
                self.lbl_val_tamano.setText(str(detalle[5]))
