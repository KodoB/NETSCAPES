import datetime
from collections import Counter, defaultdict
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QTime, Qt
from controladores.base_controller import PageController
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
            'tamano': size_str,
            'tamano_bytes': size  # tamaño crudo, para sumar totales en el Dashboard
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


class CapturaController(PageController):
    # Se emite cada vez que cambian las estadísticas de la sesión de captura.
    # El Dashboard se suscribe a esta señal para actualizarse en vivo.
    estadisticas_actualizadas = pyqtSignal(dict)

    # Umbral para marcar una IP como sospechosa: si una misma IP origen toca
    # más de este número de puertos destino distintos, se considera un
    # patrón típico de escaneo de puertos. Ajustable según tu criterio.
    UMBRAL_PUERTOS_SOSPECHOSO = 10

    def __init__(self, user_data):
        super().__init__(user_data, "vistas/captura.ui")

        # --- Estadísticas de la sesión actual (para el Dashboard) ---
        # Van antes del chequeo de scapy para que calcular_stats_snapshot()
        # nunca falle, incluso si scapy no está disponible.
        self.total_bytes = 0
        self.protocolos_contador = Counter()
        self.ips_vistas = set()
        self.puertos_por_ip = defaultdict(set)
        self.ips_sospechosas = set()
        self.marcas_tiempo_paquetes = []

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

        # --- Buscador en vivo (filtra ocultando filas, nunca borra datos) ---
        self.filtro_activo = ""
        self.timer_busqueda = QTimer(self)
        self.timer_busqueda.setSingleShot(True)
        self.timer_busqueda.setInterval(150)  # pequeño debounce, evita filtrar en cada tecla
        self.timer_busqueda.timeout.connect(self.aplicar_filtro)
        self.lineEdit_busqueda.textChanged.connect(self._on_busqueda_cambiada)

    def iniciar_captura(self):
        # Leer el campo de segundos
        try:
            segundos = int(self.lineEdit_segundos.text())
            self.hilo_sniffer.timeout_segundos = segundos
        except ValueError:
            self.hilo_sniffer.timeout_segundos = None # Infinito si está vacío o es texto no válido

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
        self.lbl_stat_duracion.setText("Duración: 00:00:00")

        self.btn_guardar_captura.setEnabled(False)

        # Reiniciar también las estadísticas de sesión que ve el Dashboard
        self.total_bytes = 0
        self.protocolos_contador = Counter()
        self.ips_vistas = set()
        self.puertos_por_ip = defaultdict(set)
        self.ips_sospechosas = set()
        self.marcas_tiempo_paquetes = []
        self._emitir_estadisticas()
        self._actualizar_contador_visible()

    def actualizar_duracion(self):
        tiempo_actual = QTime.currentTime()
        tiempo_transcurrido = self.tiempo_inicio.secsTo(tiempo_actual)
        horas = tiempo_transcurrido // 3600
        minutos = (tiempo_transcurrido % 3600) // 60
        segundos = tiempo_transcurrido % 60
        self.lbl_stat_duracion.setText(f"Duración: {horas:02d}:{minutos:02d}:{segundos:02d}")
        # También refrescamos el Dashboard aquí (no solo al llegar un
        # paquete) para que "paquetes / min" baje solo cuando el tráfico
        # se detiene, en vez de quedarse pegado en el último valor.
        self._emitir_estadisticas()

    def actualizar_tabla_y_stats(self, paquete):
        # Guardar en memoria
        self.paquetes_pendientes.append(paquete)

        # ID visual temporal
        id_visual = f"#{self.conteo_total + 1}"

        self.tableWidget_captura.insertRow(0)

        item_id = QTableWidgetItem(id_visual)
        # Guardamos el paquete completo (dict) en la propia celda. Así el
        # buscador puede filtrar sobre los datos reales sin depender de
        # una lista aparte que se pueda desincronizar con la tabla.
        item_id.setData(Qt.ItemDataRole.UserRole, paquete)
        self.tableWidget_captura.setItem(0, 0, item_id)

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

        # Si hay un filtro activo, la fila recién insertada respeta ese
        # filtro de inmediato (no aparece un instante y luego se oculta).
        if self.filtro_activo:
            self.tableWidget_captura.setRowHidden(0, not self._coincide(paquete, self.filtro_activo))
        self._actualizar_contador_visible()

        # --- Acumular estadísticas de sesión (para el Dashboard) ---
        self.total_bytes += paquete.get('tamano_bytes', 0)
        self.protocolos_contador[proto] += 1

        for ip in (paquete['ip_origen'], paquete['ip_destino']):
            if ip and ip != "Desconocido":
                self.ips_vistas.add(ip)

        ip_origen = paquete['ip_origen']
        puerto_destino = paquete['puerto_destino']
        if ip_origen != "Desconocido" and puerto_destino:
            self.puertos_por_ip[ip_origen].add(puerto_destino)
            if len(self.puertos_por_ip[ip_origen]) > self.UMBRAL_PUERTOS_SOSPECHOSO:
                self.ips_sospechosas.add(ip_origen)

        self.marcas_tiempo_paquetes.append(datetime.datetime.now())
        self._emitir_estadisticas()

    # ------------------------------------------------------------------
    # Estadísticas de sesión para el Dashboard
    # ------------------------------------------------------------------
    def _limpiar_marcas_antiguas(self):
        """Descarta marcas de tiempo de más de 60s, así 'paquetes/min' es
        siempre una ventana móvil real (no un acumulado desde el inicio)."""
        limite = datetime.datetime.now() - datetime.timedelta(seconds=60)
        self.marcas_tiempo_paquetes = [t for t in self.marcas_tiempo_paquetes if t >= limite]

    def calcular_stats_snapshot(self):
        self._limpiar_marcas_antiguas()
        total = self.conteo_total

        def porcentaje(valor):
            return int((valor / total) * 100) if total > 0 else 0

        http_https = self.protocolos_contador.get('HTTP', 0) + self.protocolos_contador.get('HTTPS', 0)
        tcp = self.protocolos_contador.get('TCP', 0)
        udp = self.protocolos_contador.get('UDP', 0)
        dns = self.protocolos_contador.get('DNS', 0)

        return {
            'paquetes_totales': total,
            'paquetes_por_minuto': len(self.marcas_tiempo_paquetes),
            'total_bytes': self.total_bytes,
            'protocolos_distintos': len(self.protocolos_contador),
            'ips_unicas': len(self.ips_vistas),
            'ips_sospechosas': len(self.ips_sospechosas),
            'porcentaje_http': porcentaje(http_https),
            'porcentaje_tcp': porcentaje(tcp),
            'porcentaje_udp': porcentaje(udp),
            'porcentaje_dns': porcentaje(dns),
        }

    def _emitir_estadisticas(self):
        self.estadisticas_actualizadas.emit(self.calcular_stats_snapshot())

    # ------------------------------------------------------------------
    # Buscador en vivo
    # ------------------------------------------------------------------
    # Soporta:
    #   - Texto libre: "192.168"  -> busca en IP origen, IP destino,
    #     protocolo, puertos y tamaño (coincidencia parcial).
    #   - IP exacta o parcial:    "192.168.1.127" o "192.168"
    #   - Puerto:                 "500"  (coincide si aparece en cualquier
    #     campo, incluyendo puertos)
    #   - Protocolo:               "udp", "https", "dns", etc.
    #   - Varias palabras = AND:   "udp 192.168.1"  -> debe cumplir ambas
    #   - Negación con "-":        "-arp"  -> oculta todo lo que sea ARP
    #   - Campo específico "campo:valor" para precisión total:
    #         ip:192.168.1.127   origen:192.168   destino:10.0.0.1
    #         puerto:500         proto:https      tamano:kb
    #
    # Nada de esto borra o modifica los datos capturados: solo oculta
    # filas de la tabla (setRowHidden). Si borras el texto del buscador,
    # todo lo capturado reaparece tal cual, aunque no se haya guardado
    # en la base de datos.
    def _on_busqueda_cambiada(self, texto):
        self.filtro_activo = texto.strip()
        self.timer_busqueda.start()  # reinicia el debounce en cada tecla

    def aplicar_filtro(self):
        texto = self.filtro_activo
        total_filas = self.tableWidget_captura.rowCount()

        for fila in range(total_filas):
            item_id = self.tableWidget_captura.item(fila, 0)
            paquete = item_id.data(Qt.ItemDataRole.UserRole) if item_id else None
            visible = self._coincide(paquete, texto) if paquete else True
            self.tableWidget_captura.setRowHidden(fila, not visible)

        self._actualizar_contador_visible()

    def _actualizar_contador_visible(self):
        total = self.tableWidget_captura.rowCount()
        if self.filtro_activo:
            visibles = sum(
                1 for fila in range(total) if not self.tableWidget_captura.isRowHidden(fila)
            )
            self.lbl_total_registros.setText(f"{visibles} de {total} registros (filtrado)")
        else:
            self.lbl_total_registros.setText(f"{total} registros")

    def _coincide(self, paquete, consulta):
        """True si el paquete cumple con TODOS los términos de la consulta
        (AND). Cada término puede llevar '-' para negarlo o 'campo:valor'
        para apuntar a un campo específico."""
        if not consulta.strip():
            return True

        for termino in consulta.strip().split():
            negar = termino.startswith('-') and len(termino) > 1
            termino_real = termino[1:] if negar else termino

            resultado = self._coincide_termino(paquete, termino_real)
            if negar and resultado:
                return False
            if not negar and not resultado:
                return False

        return True

    def _coincide_termino(self, paquete, termino):
        # --- Sintaxis campo:valor (búsqueda precisa) ---
        if ':' in termino:
            campo, valor = termino.split(':', 1)
            campo = campo.lower()
            valor = valor.lower()

            if campo in ('ip', 'ips'):
                return valor in paquete['ip_origen'].lower() or valor in paquete['ip_destino'].lower()
            elif campo in ('origen', 'src', 'ip_origen'):
                return valor in paquete['ip_origen'].lower()
            elif campo in ('destino', 'dst', 'ip_destino'):
                return valor in paquete['ip_destino'].lower()
            elif campo in ('puerto', 'port'):
                return valor == str(paquete['puerto_origen']) or valor == str(paquete['puerto_destino'])
            elif campo in ('proto', 'protocolo'):
                return valor == paquete['protocolo'].lower()
            elif campo in ('tamano', 'size', 'tamaño'):
                return valor in paquete['tamano'].lower()
            # Campo no reconocido: caemos a búsqueda libre usando solo el valor
            termino = valor

        # --- Búsqueda libre: coincide si aparece en cualquier campo relevante ---
        termino_lower = termino.lower()
        campos = (
            paquete['ip_origen'].lower(),
            paquete['ip_destino'].lower(),
            paquete['protocolo'].lower(),
            str(paquete['puerto_origen']),
            str(paquete['puerto_destino']),
            paquete['tamano'].lower(),
            paquete['tiempo'].lower(),
        )
        return any(termino_lower in campo for campo in campos)
