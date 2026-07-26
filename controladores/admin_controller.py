from PyQt6.QtWidgets import QTableWidgetItem, QWidget, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from controladores.base_controller import PageController
from controladores.dialogo_usuario_controller import DialogoUsuarioController
from modelos.usuario import Usuario


class AdminController(PageController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/admin.ui")
        self.modelo_usuario = Usuario()

        self.btn_anadir_usuario.clicked.connect(self.abrir_dialogo_crear)
        self.cargar_usuarios()

    def cargar_usuarios(self):
        self.tableWidget_usuarios.setRowCount(0)
        usuarios = self.modelo_usuario.obtener_todos_usuarios()

        for row_idx, usr in enumerate(usuarios):
            self.tableWidget_usuarios.insertRow(row_idx)
            self.tableWidget_usuarios.setItem(row_idx, 0, QTableWidgetItem(usr['nombre_completo']))
            self.tableWidget_usuarios.setItem(row_idx, 1, QTableWidgetItem(usr['rol']))
            self.tableWidget_usuarios.setCellWidget(row_idx, 2, self._crear_botones_acciones(usr))

    def _crear_botones_acciones(self, usr):
        """Arma la celda con los dos botones (editar/eliminar) para una fila."""
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        btn_editar = QPushButton("✏️")
        btn_editar.setToolTip("Editar usuario")
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_editar.setStyleSheet(
            "background-color: #90EE90; border-radius: 4px; padding: 4px 8px;"
        )
        btn_editar.clicked.connect(lambda checked, u=usr: self.abrir_dialogo_editar(u))

        btn_eliminar = QPushButton("🗑️")
        btn_eliminar.setToolTip("Eliminar usuario")
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.setStyleSheet(
            "background-color: #FF6B6B; border-radius: 4px; padding: 4px 8px;"
        )
        btn_eliminar.clicked.connect(lambda checked, u=usr: self.confirmar_eliminacion(u))

        layout.addWidget(btn_editar)
        layout.addWidget(btn_eliminar)
        layout.addStretch()

        return contenedor

    def abrir_dialogo_crear(self):
        dialogo = DialogoUsuarioController(usuario_existente=None, parent=self)
        if dialogo.exec():
            self.cargar_usuarios()

    def abrir_dialogo_editar(self, usuario_existente):
        # Volvemos a pedir el registro completo por si cambió desde que
        # se cargó la tabla (evita editar con datos desactualizados).
        datos_actuales = self.modelo_usuario.obtener_usuario_por_id(usuario_existente['id']) or usuario_existente
        dialogo = DialogoUsuarioController(usuario_existente=datos_actuales, parent=self)
        if dialogo.exec():
            self.cargar_usuarios()

    def confirmar_eliminacion(self, usuario_existente):
        cuadro = QMessageBox(self)
        cuadro.setWindowTitle("Eliminar Usuario")
        cuadro.setIcon(QMessageBox.Icon.Warning)
        cuadro.setText(
            f"¿Seguro que quieres eliminar a \"{usuario_existente['nombre_completo']}\"?\n"
            "Esta acción no se puede deshacer."
        )

        btn_cancelar = cuadro.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        btn_confirmar = cuadro.addButton("Confirmar Eliminación", QMessageBox.ButtonRole.DestructiveRole)
        cuadro.setDefaultButton(btn_cancelar)

        cuadro.exec()

        if cuadro.clickedButton() == btn_confirmar:
            self.modelo_usuario.eliminar_usuario(usuario_existente['id'])
            self.cargar_usuarios()
