from scapy.all import rdpcap, IP, TCP, UDP

def analizar_captura(ruta_archivo):
    print(f"[*] Importando el archivo: {ruta_archivo}...")
    
    try:
        paquetes = rdpcap(ruta_archivo)
    except FileNotFoundError:
        print("[-] Error: No se encontró el archivo pcap.")
        return

    print(f"[+] Se importaron {len(paquetes)} paquetes. Extrayendo datos...\n")
    print("-" * 50)
    
    for i, paquete in enumerate(paquetes):
        if IP in paquete:
            ip_origen = paquete[IP].src
            ip_destino = paquete[IP].dst
            tamano_paquete = len(paquete)
            
            puerto_origen = "N/A"
            puerto_destino = "N/A"
            nombre_protocolo = "Otro"
            
            if TCP in paquete:
                puerto_origen = paquete[TCP].sport
                puerto_destino = paquete[TCP].dport
                nombre_protocolo = "TCP"
            elif UDP in paquete:
                puerto_origen = paquete[UDP].sport
                puerto_destino = paquete[UDP].dport
                nombre_protocolo = "UDP"
            
            print(f"Paquete #{i+1}")
            print(f"  Protocolo: {nombre_protocolo}")
            print(f"  Origen:    {ip_origen}:{puerto_origen}")
            print(f"  Destino:   {ip_destino}:{puerto_destino}")
            print(f"  Tamaño:    {tamano_paquete} bytes")
            print("-" * 50)

if __name__ == "__main__":
    ruta_archivo_pcap = "exportados/sesion_001.pcap"
    analizar_captura(ruta_archivo_pcap)