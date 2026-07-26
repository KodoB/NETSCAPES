from basededatos.conexion import ConexionBD

class Usuario:
    def __init__(self):
        self.bd = ConexionBD()

    def verificar_credenciales(self, usuario, password):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE usuario=%s AND password=%s", (usuario, password))
            user = cursor.fetchone()
            cursor.close()
            conexion.close()
            return user
        return None

    # ------------------------------------------------------------------
    # CRUD para el Panel de Administración
    #
    # NOTA: se asume que la tabla "usuarios" tiene las columnas
    # id, nombre_completo, usuario, password, rol. Si tu tabla real usa
    # otros nombres de columna, solo hay que ajustar los SELECT/INSERT/
    # UPDATE de aquí abajo — el resto del código no depende del nombre
    # exacto de las columnas.
    # ------------------------------------------------------------------

    def obtener_todos_usuarios(self):
        """Devuelve la lista de usuarios (sin password) para la tabla de Admin."""
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre_completo, usuario, rol FROM usuarios ORDER BY nombre_completo ASC")
            datos = cursor.fetchall()
            cursor.close()
            conexion.close()
            return datos
        return []

    def obtener_usuario_por_id(self, id_usuario):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre_completo, usuario, rol FROM usuarios WHERE id=%s", (id_usuario,))
            dato = cursor.fetchone()
            cursor.close()
            conexion.close()
            return dato
        return None

    def usuario_existe(self, usuario, excluir_id=None):
        """Revisa si ya existe ese nombre de usuario (login). excluir_id
        se usa al editar, para no chocar contra el propio registro."""
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            if excluir_id is not None:
                cursor.execute("SELECT id FROM usuarios WHERE usuario=%s AND id<>%s", (usuario, excluir_id))
            else:
                cursor.execute("SELECT id FROM usuarios WHERE usuario=%s", (usuario,))
            existe = cursor.fetchone() is not None
            cursor.close()
            conexion.close()
            return existe
        return False

    def crear_usuario(self, nombre_completo, usuario, rol, password):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nombre_completo, usuario, password, rol) VALUES (%s, %s, %s, %s)",
                (nombre_completo, usuario, password, rol)
            )
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        return False

    def actualizar_usuario(self, id_usuario, nombre_completo, usuario, rol, password=None):
        """Si password es None, no se toca la contraseña actual (para
        permitir editar nombre/usuario/rol sin forzar a escribir una
        contraseña nueva cada vez)."""
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            if password:
                cursor.execute(
                    "UPDATE usuarios SET nombre_completo=%s, usuario=%s, rol=%s, password=%s WHERE id=%s",
                    (nombre_completo, usuario, rol, password, id_usuario)
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET nombre_completo=%s, usuario=%s, rol=%s WHERE id=%s",
                    (nombre_completo, usuario, rol, id_usuario)
                )
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        return False

    def eliminar_usuario(self, id_usuario):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=%s", (id_usuario,))
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        return False
