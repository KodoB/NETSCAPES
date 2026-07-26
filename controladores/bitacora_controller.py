from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from controladores.base_controller import PageController
from modelos.bitacora import Bitacora


class BitacoraController(PageController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/bitacora.ui")
        self.modelo_bitacora = Bitacora()

        self.cargar_bitacora()

    def _limpiar_lista(self):
        layout = self.verticalLayout_lista_logs
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def cargar_bitacora(self):
        self._limpiar_lista()
        datos = self.modelo_bitacora.obtener_actividad_sistema()

        for log in datos:

            frame_log = QFrame()
            layout_log = QVBoxLayout(frame_log)


            lbl_titulo = QLabel(f"Usuario: {log['usuario']} | Rol: {log['rol']}")
            font_titulo = lbl_titulo.font()
            font_titulo.setPointSize(11)
            font_titulo.setBold(True)
            lbl_titulo.setFont(font_titulo)
            layout_log.addWidget(lbl_titulo)

            layout_desc = QHBoxLayout()
            lbl_icon = QLabel("➜")
            lbl_icon.setStyleSheet("font-size: 14pt; font-weight: bold;")

            lbl_desc = QLabel(log['comentario'])
            lbl_desc.setWordWrap(True)

            layout_desc.addWidget(lbl_icon)
            layout_desc.addWidget(lbl_desc)
            layout_desc.addStretch()
            layout_log.addLayout(layout_desc)


            lbl_fecha = QLabel(str(log['fecha']))
            lbl_fecha.setStyleSheet("color: #555555;")
            layout_log.addWidget(lbl_fecha)


            linea = QFrame()
            linea.setFrameShape(QFrame.Shape.HLine)
            linea.setStyleSheet("color: #aaaaaa;")
            layout_log.addWidget(linea)
            self.verticalLayout_lista_logs.insertWidget(0, frame_log)
