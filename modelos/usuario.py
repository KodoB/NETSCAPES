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