import mysql.connector
from mysql.connector import Error

class ConexionBD:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "codybryce" 
        self.database = "red_trafico2"

    def conectar(self):
        try:
            conexion = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return conexion
        except Error as e:
            print(f"Error de conexión a MySQL: {e}")
            return None