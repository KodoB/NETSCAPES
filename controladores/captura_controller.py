import datetime
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QTime
from controladores.base_controller import BaseController
from modelos.trafico import Trafico

try:
    from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP, ARP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class HiloSniffer(QThread):
    # Señal para enviar el paquete procesado a la interfaz
    paquete_capturado = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.timeout_segundos = None # Control de timeout desde UI

    def format_size(self, size_in_bytes):
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B"
        elif size_in_bytes < 1024 * 1024:
            return f"{size_in_bytes / 1024:.1f} KB"
        else:
            return f"{size_in_bytes / (1024 * 1024):.1f} MB"

    def procesar_paquete(self, pkt):
        try:
            ts = float(pkt.time)
            dt_object = datetime.datetime.fromtimestamp(ts)
            timestamp_str = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            hora_visual = dt_object.strftime('%H:%M:%S')
        except Exception:
            ahora = datetime.datetime.now()
            timestamp_str = ahora.strftime('%Y-%m-%d %H:%M:%S')
            hora_visual = ahora.strftime('%H:%M:%S')

        ip_src = "Desconocido"
        ip_dst = "Desconocido"
        port_src = 0
        port_dst = 0
        protocol = "Otros"
        size = len(pkt)
        size_str = self.format_size(size)

        if IP in pkt:
            ip_src = pkt[IP].src
            ip_dst = pkt[IP].dst
            protocol = "IP"
        elif IPv6 in pkt:
            ip_src = pkt[IPv6].src
            ip_dst = pkt[IPv6].dst
            protocol = "IPv6"
        elif ARP in pkt:
            ip_src = pkt[ARP].psrc
            ip_dst = pkt[ARP].pdst
            protocol = "ARP"

        if TCP in pkt:
            protocol = "TCP"
            port_src = pkt[TCP].sport
            port_dst = pkt[TCP].dport
        elif UDP in pkt:
            protocol = "UDP"
            port_src = pkt[UDP].sport
            port_dst = pkt[UDP].dport
        elif ICMP in pkt:
            protocol = "ICMP"

        if port_dst == 80 or port_src == 80: protocol = "HTTP"
        elif port_dst == 443 or port_src == 443: protocol = "HTTPS"
        elif port_dst == 53 or port_src == 53: protocol = "DNS"
        elif port_dst == 22 or port_src == 22: protocol = "SSH"

        # Solo emitir la señal con los datos formateados (No insertar en BD)
        self.paquete_capturado.emit({
            'fecha_db': timestamp_str, 
            'tiempo': hora_visual,
            'ip_origen': ip_src,
            'ip_destino': ip_dst,
            'puerto_origen': port_src,
            'puerto_destino': port_dst,
            'protocolo': protocol,
            'tamano': size_str
        })

    def detener_filtro(self, pkt):
        return not self.is_running

    def run(self):
        self.is_running = True
        try:
            if self.timeout_segundos:
                sniff(timeout=self.timeout_segundos, prn=self.procesar_paquete, stop_filter=self.detener_filtro, store=False)
            else:
                sniff(prn=self.procesar_paquete, stop_filter=self.detener_filtro, store=False)
        except Exception as e:
            print(f"Error en sniffer: {e}")
        
        self.is_running = False

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()


class CapturaController(BaseController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/captura.ui")
        self.btn_nav_captura.setEnabled(False)
        
        if not SCAPY_AVAILABLE:
            QMessageBox.critical(self, "Error Crítico", "Scapy no instalado o sin permisos.")
            self.btn_iniciar_captura.setEnabled(False)
            return

        self.btn_detener_captura.setEnabled(False)
        self.modelo_trafico = Trafico()
        
        # Almacenamiento en memoria para los paquetes antes de guardar
        self.paquetes_pendientes = []

        self.hilo_sniffer = HiloSniffer()
        self.hilo_sniffer.paquete_capturado.connect(self.actualizar_tabla_y_stats)
        self.hilo_sniffer.finished.connect(self.detener_captura) # Autodetener si el timeout se acaba

        # Variables de estadísticas en tiempo real
        self.conteo_total = 0
        self.conteo_tcp = 0
        self.conteo_udp = 0
        self.conteo_http = 0

        self.timer_duracion = QTimer()
        self.timer_duracion.timeout.connect(self.actualizar_duracion)
        self.tiempo_inicio = None

        # Conectar botones
        self.btn_iniciar_captura.clicked.connect(self.iniciar_captura)
        self.btn_detener_captura.clicked.connect(self.detener_captura)
        self.btn_guardar_captura.clicked.connect(self.guardar_captura)
        self.btn_limpiar_captura.clicked.connect(self.limpiar_captura)

        self.tableWidget_captura.setRowCount(0)

    def iniciar_captura(self):
        # Leer el campo de segundos
        try:
            segundos = int(self.lineEdit_segundos.text())
            self.hilo_sniffer.timeout_segundos = segundos
        except ValueError:
            self.hilo_sniffer.timeout_segundos = None # Infinito si está vacío o es texto no válido

        self.lineEdit_busqueda.setEnabled(False)
        self.lineEdit_segundos.setEnabled(False)
        
        self.btn_iniciar_captura.setEnabled(False)
        self.btn_detener_captura.setEnabled(True)
        
        # Bloquear botones de guardar y limpiar mientras captura
        self.btn_guardar_captura.setEnabled(False)
        self.btn_limpiar_captura.setEnabled(False)
        
        self.lbl_status_texto.setText("Capturando...")

        self.tiempo_inicio = QTime.currentTime()
        self.timer_duracion.start(1000)
        self.hilo_sniffer.start()

    def detener_captura(self):
        self.hilo_sniffer.stop()
        self.timer_duracion.stop()

        self.lineEdit_busqueda.setEnabled(True)
        self.lineEdit_segundos.setEnabled(True)
        
        self.btn_iniciar_captura.setEnabled(True)
        self.btn_detener_captura.setEnabled(False)
        
        # Habilitar botones de acción si hay datos que guardar
        if len(self.paquetes_pendientes) > 0:
            self.btn_guardar_captura.setEnabled(True)
        self.btn_limpiar_captura.setEnabled(True)

        self.lbl_status_texto.setText("Detenido")

    def guardar_captura(self):
        if not self.paquetes_pendientes:
            QMessageBox.information(self, "Información", "No hay paquetes nuevos para guardar.")
            return
        
        # Iterar sobre los paquetes en memoria e insertarlos en DB
        for pkt in self.paquetes_pendientes:
            self.modelo_trafico.insertar_paquete(
                pkt['fecha_db'], pkt['ip_origen'], pkt['ip_destino'], 
                pkt['puerto_origen'], pkt['puerto_destino'], 
                pkt['protocolo'], pkt['tamano']
            )
            
        QMessageBox.information(self, "Éxito", f"Se han guardado {len(self.paquetes_pendientes)} paquetes correctamente.")
        # Limpiar la lista después de guardar para no duplicar datos si presiona guardar dos veces
        self.paquetes_pendientes.clear()
        self.btn_guardar_captura.setEnabled(False)

    def limpiar_captura(self):
        # Resetear UI y memoria
        self.tableWidget_captura.setRowCount(0)
        self.paquetes_pendientes.clear()
        
        self.conteo_total = 0
        self.conteo_tcp = 0
        self.conteo_udp = 0
        self.conteo_http = 0
        
        self.lbl_stat_total.setText("Total: 0")
        self.lbl_stat_tcp.setText("TCP: 0")
        self.lbl_stat_udp.setText("UDP: 0")
        self.lbl_stat_http.setText("HTTP: 0")
        self.lbl_total_registros.setText("0 registros")
        self.lbl_stat_duracion.setText("Duración: 00:00:00")
        
        self.btn_guardar_captura.setEnabled(False)

    def actualizar_duracion(self):
        tiempo_actual = QTime.currentTime()
        tiempo_transcurrido = self.tiempo_inicio.secsTo(tiempo_actual)
        horas = tiempo_transcurrido // 3600
        minutos = (tiempo_transcurrido % 3600) // 60
        segundos = tiempo_transcurrido % 60
        self.lbl_stat_duracion.setText(f"Duración: {horas:02d}:{minutos:02d}:{segundos:02d}")

    def actualizar_tabla_y_stats(self, paquete):
        # Guardar en memoria
        self.paquetes_pendientes.append(paquete)

        # ID visual temporal
        id_visual = f"#{self.conteo_total + 1}"

        self.tableWidget_captura.insertRow(0)
        self.tableWidget_captura.setItem(0, 0, QTableWidgetItem(id_visual))
        self.tableWidget_captura.setItem(0, 1, QTableWidgetItem(paquete['tiempo']))
        self.tableWidget_captura.setItem(0, 2, QTableWidgetItem(paquete['ip_origen']))
        self.tableWidget_captura.setItem(0, 3, QTableWidgetItem(paquete['ip_destino']))
        
        pto_o = str(paquete['puerto_origen']) if paquete['puerto_origen'] else "---"
        pto_d = str(paquete['puerto_destino']) if paquete['puerto_destino'] else "---"
        
        self.tableWidget_captura.setItem(0, 4, QTableWidgetItem(pto_o))
        self.tableWidget_captura.setItem(0, 5, QTableWidgetItem(pto_d))
        self.tableWidget_captura.setItem(0, 6, QTableWidgetItem(paquete['protocolo']))
        self.tableWidget_captura.setItem(0, 7, QTableWidgetItem(paquete['tamano']))

        self.conteo_total += 1
        proto = paquete['protocolo']
        if proto == "TCP": self.conteo_tcp += 1
        elif proto == "UDP": self.conteo_udp += 1
        elif proto in ["HTTP", "HTTPS"]: self.conteo_http += 1

        self.lbl_stat_total.setText(f"Total: {self.conteo_total}")
        self.lbl_stat_tcp.setText(f"TCP: {self.conteo_tcp}")
        self.lbl_stat_udp.setText(f"UDP: {self.conteo_udp}")
        self.lbl_stat_http.setText(f"HTTP: {self.conteo_http}")
        self.lbl_total_registros.setText(f"{self.conteo_total} registros")