from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.uic import loadUi
from modelos.usuario import Usuario


class DialogoUsuarioController(QDialog):

    def __init__(self, usuario_existente=None, parent=None):
        super().__init__(parent)
        loadUi("vistas/dialogo_usuario.ui", self)
        self.modelo_usuario = Usuario()
        self.usuario_existente = usuario_existente
        self.modo_edicion = usuario_existente is not None

        if self.modo_edicion:
            titulo = f"Editar Usuario - {usuario_existente['usuario']}"
            self.setWindowTitle(titulo)
            self.lbl_titulo_dialogo.setText(titulo)
            self.btn_confirmar.setText("Guardar Cambios")

            self.lineEdit_nombre_completo.setText(usuario_existente['nombre_completo'])
            self.lineEdit_usuario.setText(usuario_existente['usuario'])

            if usuario_existente['rol'] == 'Administrador':
                self.radioButton_administrador.setChecked(True)
            else:
                self.radioButton_analista.setChecked(True)


            self.lineEdit_password.setPlaceholderText("Dejar en blanco para no cambiarla")
        else:
            self.setWindowTitle("Crear Nuevo Usuario")
            self.lbl_titulo_dialogo.setText("Crear Nuevo Usuario")
            self.btn_confirmar.setText("+ Añadir Usuario")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_cerrar.clicked.connect(self.reject)
        self.btn_confirmar.clicked.connect(self.guardar)

    def guardar(self):
        nombre_completo = self.lineEdit_nombre_completo.text().strip()
        usuario = self.lineEdit_usuario.text().strip()
        password = self.lineEdit_password.text()
        rol = "Administrador" if self.radioButton_administrador.isChecked() else "Analista"

        if not nombre_completo or not usuario:
            QMessageBox.warning(self, "Campos obligatorios", "Nombre completo y usuario son obligatorios.")
            return

        if self.modo_edicion:
            id_usuario = self.usuario_existente['id']
            if self.modelo_usuario.usuario_existe(usuario, excluir_id=id_usuario):
                QMessageBox.warning(self, "Usuario duplicado", "Ya existe otro usuario con ese nombre de usuario.")
                return

            self.modelo_usuario.actualizar_usuario(
                id_usuario, nombre_completo, usuario, rol,
                password if password else None
            )
        else:
            if not password:
                QMessageBox.warning(self, "Campo obligatorio", "La contraseña es obligatoria para crear un usuario.")
                return
            if self.modelo_usuario.usuario_existe(usuario):
                QMessageBox.warning(self, "Usuario duplicado", "Ya existe un usuario con ese nombre de usuario.")
                return

            self.modelo_usuario.crear_usuario(nombre_completo, usuario, rol, password)

        self.accept()
