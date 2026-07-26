from basededatos.conexion import ConexionBD

class Trafico:
    def __init__(self):
        self.bd = ConexionBD()

    def obtener_ultimos_paquetes(self, limite=3):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT id, ip_origen, ip_destino, protocolo, tamano FROM trafico ORDER BY id DESC LIMIT %s", (limite,))
            datos = cursor.fetchall()
            cursor.close()
            conexion.close()
            return datos
        return []

    def obtener_todos_paquetes(self):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT id, ip_origen, ip_destino, puerto_destino, protocolo, tamano FROM trafico ORDER BY id DESC")
            datos = cursor.fetchall()
            cursor.close()
            conexion.close()
            return datos
        return []

    def buscar_paquete_por_id(self, id_paquete):
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM trafico WHERE id = %s", (id_paquete,))
            dato = cursor.fetchone()
            cursor.close()
            conexion.close()
            return dato
        return None

    def insertar_paquete(self, fecha, ip_origen, ip_destino, puerto_origen, puerto_destino, protocolo, tamano):
        """Guarda un paquete en la base de datos y retorna el ID autogenerado"""
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor()
            query = """INSERT INTO trafico 
                       (fecha, ip_origen, ip_destino, puerto_origen, puerto_destino, protocolo, tamano) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (fecha, ip_origen, ip_destino, puerto_origen, puerto_destino, protocolo, tamano))
            id_insertado = cursor.lastrowid
            conexion.commit()
            cursor.close()
            conexion.close()
            return id_insertado
        return None
    
    def obtener_trafico_por_fechas(self, fecha_inicio, fecha_fin):
        """Obtiene los paquetes capturados en un intervalo de fechas"""
        conexion = self.bd.conectar()
        if conexion:
            cursor = conexion.cursor(dictionary=True)
            query = "SELECT * FROM trafico WHERE fecha >= %s AND fecha <= %s ORDER BY fecha DESC"
            cursor.execute(query, (f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59"))
            datos = cursor.fetchall()
            cursor.close()
            conexion.close()
            return datos
        return []