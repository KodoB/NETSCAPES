from basededatos.conexion import ConexionBD
from datetime import datetime

class Bitacora:
    def __init__(self):
        self.bd = ConexionBD()

    def obtener_actividad_sistema(self):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor(dictionary=True) 
            cursor.execute("SELECT * FROM bitacora ORDER BY id DESC")
            datos = cursor.fetchall()
            cursor.close()
            conexion.close()
            return datos
        return []