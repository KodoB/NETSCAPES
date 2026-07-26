from scapy.all import sniff, wrpcap
import os

def generar_captura(ruta_exportacion, numero_paquetes=15):
    print(f"[*] Iniciando la captura de {numero_paquetes} paquetes...")
    
    paquetes_capturados = sniff(count=numero_paquetes)
    
    os.makedirs(os.path.dirname(ruta_exportacion), exist_ok=True)
    
    wrpcap(ruta_exportacion, paquetes_capturados)
    
    print(f"[+] Captura finalizada con éxito.")
    print(f"[+] Archivo exportado en: {ruta_exportacion}")

if __name__ == "__main__":
    ruta_archivo_pcap = "exportados/sesion_001.pcap"
    generar_captura(ruta_archivo_pcap)