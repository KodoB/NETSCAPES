import datetime

# Intentar importar scapy de forma segura
try:
    from scapy.all import rdpcap, sniff, IP, IPv6, TCP, UDP, ICMP, ARP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class Packet:
    def __init__(self, id=None, captura_id=None, timestamp=None, ip_origen="", ip_destino="", 
                 puerto_origen=None, puerto_destino=None, protocolo="", tamanio_bytes=0, 
                 info_adicional="", categoria="No Identificado"):
        self.id = id
        self.captura_id = captura_id
        self.timestamp = timestamp
        self.ip_origen = ip_origen
        self.ip_destino = ip_destino
        self.puerto_origen = puerto_origen
        self.puerto_destino = puerto_destino
        self.protocolo = protocolo
        self.tamanio_bytes = tamanio_bytes
        self.info_adicional = info_adicional
        self.categoria = categoria

class CaptureService:
    """Servicio para capturar e importar paquetes de tráfico de red."""

    @staticmethod
    def is_scapy_available():
        return SCAPY_AVAILABLE
    
    @classmethod
    def live_capture(cls, interface, duration_seconds, capture_name, description, user_id, packet_callback=None):
        """
        Inicia captura en vivo en una interfaz de red, procesando cada paquete.
        Este método es síncrono. Debe ser llamado desde un hilo secundario (QThread).
        """
        if not SCAPY_AVAILABLE:
            raise RuntimeError("Scapy no está instalado en el entorno de Python.")

        total_captured = 0

        def packet_handler(pkt):
            nonlocal total_captured
            parsed_pkt = cls._parse_packet(pkt)
            if parsed_pkt:
                total_captured += 1
                
                print(parsed_pkt.__dict__) # Para depuración, imprimir el paquete parseado

        # Iniciar el sniffing
        try:
            # sniff de scapy.
            if interface == "Auto" or not interface:
                sniff(timeout=duration_seconds, prn=packet_handler, store=False)
            else:
                sniff(iface=interface, timeout=duration_seconds, prn=packet_handler, store=False)
        except Exception as e:
            # Limpiar captura si hay error al iniciar interfaz
            raise RuntimeError(f"Error durante la captura en vivo: {str(e)}")

    @staticmethod
    def _parse_packet(pkt):
        """Helper para extraer la metadata relevante de un paquete scapy."""
        try:
            # Timestamp del paquete
            ts = float(pkt.time)
            dt_object = datetime.datetime.fromtimestamp(ts)
            timestamp_str = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        except Exception:
            timestamp_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # Valores por defecto
        ip_src = "Desconocido"
        ip_dst = "Desconocido"
        port_src = None
        port_dst = None
        protocol = "Otros"
        size = len(pkt)
        info = "Paquete crudo"

        # Identificación de Capa de Red e IP
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
            info = f"ARP Who has {pkt[ARP].pdst}? Tell {pkt[ARP].psrc}"
            return Packet(
                timestamp=timestamp_str,
                ip_origen=ip_src,
                ip_destino=ip_dst,
                puerto_origen=None,
                puerto_destino=None,
                protocolo=protocol,
                tamanio_bytes=size,
                info_adicional=info
            )

        # Identificación de Capa de Transporte y Puertos
        if TCP in pkt:
            protocol = "TCP"
            port_src = pkt[TCP].sport
            port_dst = pkt[TCP].dport
            # Analizar banderas TCP comunes
            flags = []
            f = pkt[TCP].flags
            if f & 0x01: flags.append("FIN")
            if f & 0x02: flags.append("SYN")
            if f & 0x04: flags.append("RST")
            if f & 0x08: flags.append("PSH")
            if f & 0x10: flags.append("ACK")
            if f & 0x20: flags.append("URG")
            flags_str = "|".join(flags)
            info = f"TCP Flags: {flags_str} Seq: {pkt[TCP].seq}"
        elif UDP in pkt:
            protocol = "UDP"
            port_src = pkt[UDP].sport
            port_dst = pkt[UDP].dport
            info = "Datagrama UDP"
        elif ICMP in pkt:
            protocol = "ICMP"
            info = f"ICMP Tipo: {pkt[ICMP].type} Código: {pkt[ICMP].code}"

        # Refinar protocolo de aplicación común si es posible
        if port_dst == 80 or port_src == 80:
            protocol = "HTTP"
        elif port_dst == 443 or port_src == 443:
            protocol = "HTTPS"
        elif port_dst == 53 or port_src == 53:
            protocol = "DNS"
        elif port_dst == 22 or port_src == 22:
            protocol = "SSH"

        return Packet(
            timestamp=timestamp_str,
            ip_origen=ip_src,
            ip_destino=ip_dst,
            puerto_origen=port_src,
            puerto_destino=port_dst,
            protocolo=protocol,
            tamanio_bytes=size,
            info_adicional=info
        )

captura = CaptureService()
captura.live_capture(
    interface="Auto",
    duration_seconds=300,
    capture_name="Test Capture",
    description="Captura de prueba",
    user_id=1
    )