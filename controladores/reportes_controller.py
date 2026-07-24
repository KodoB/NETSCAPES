import os
import shutil
import json
import csv
from datetime import datetime
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QPushButton
from PyQt6.QtCore import Qt, QDate
from controladores.base_controller import BaseController
from modelos.trafico import Trafico

# Librerías para el PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class ReportesController(BaseController):
    def __init__(self, user_data):
        super().__init__(user_data, "vistas/reportes.ui")
        self.btn_nav_reportes.setEnabled(False)
        self.modelo_trafico = Trafico()
        
        # 1. Configurar fechas predeterminadas al día actual
        fecha_actual = QDate.currentDate()
        self.dateEdit_inicio.setDate(fecha_actual)
        self.dateEdit_fin.setDate(fecha_actual)

        # 2. Conectar eventos de los radio buttons para bloquear/desbloquear checkboxes
        self.radio_pdf.toggled.connect(self.actualizar_estado_secciones)
        self.radio_csv.toggled.connect(self.actualizar_estado_secciones)
        self.radio_json.toggled.connect(self.actualizar_estado_secciones)
        
        # Ejecutar una vez al inicio para establecer el estado base (PDF activado)
        self.actualizar_estado_secciones()

        # Crear carpeta de exportados si no existe en la raíz del proyecto
        self.carpeta_exportados = os.path.join(os.getcwd(), "exportados")
        if not os.path.exists(self.carpeta_exportados):
            os.makedirs(self.carpeta_exportados)

        # Buscar la carpeta de Descargas del usuario (Windows/Linux/Mac)
        self.carpeta_descargas = os.path.join(os.path.expanduser('~'), 'Downloads')

        self.btn_generar_reporte_accion.clicked.connect(self.generar_reporte)
        self.cargar_historial_reportes()

    def actualizar_estado_secciones(self):
        """Bloquea o desbloquea las secciones dependiendo del formato elegido"""
        # Solo PDF soporta las secciones visuales
        es_pdf = self.radio_pdf.isChecked()
        
        self.chk_resumen.setEnabled(es_pdf)
        self.chk_distribucion.setEnabled(es_pdf)
        self.chk_ips.setEnabled(es_pdf)
        
        # Si se deshabilita, quitar las palomitas para que no haya confusiones visuales
        if not es_pdf:
            self.chk_resumen.setChecked(False)
            self.chk_distribucion.setChecked(False)
            self.chk_ips.setChecked(False)

    def cargar_historial_reportes(self):
        """Lee la carpeta exportados y llena la tabla del historial"""
        self.tableWidget_historial.setRowCount(0)
        
        if not os.path.exists(self.carpeta_exportados):
            return

        archivos = os.listdir(self.carpeta_exportados)
        archivos_validos = [f for f in archivos if f.endswith(('.pdf', '.csv', '.json'))]
        archivos_ordenados = sorted(archivos_validos, 
                                    key=lambda x: os.path.getmtime(os.path.join(self.carpeta_exportados, x)), 
                                    reverse=True)

        for row_idx, nombre_archivo in enumerate(archivos_ordenados):
            ruta_completa = os.path.join(self.carpeta_exportados, nombre_archivo)
            fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta_completa)).strftime('%Y-%m-%d %H:%M')
            formato = nombre_archivo.split('.')[-1].upper()

            self.tableWidget_historial.insertRow(row_idx)
            self.tableWidget_historial.setItem(row_idx, 0, QTableWidgetItem(nombre_archivo))
            self.tableWidget_historial.setItem(row_idx, 1, QTableWidgetItem(fecha_mod))
            self.tableWidget_historial.setItem(row_idx, 2, QTableWidgetItem(formato))

            btn_descargar = QPushButton("📥")
            btn_descargar.setStyleSheet("background-color: transparent; font-size: 16px;")
            btn_descargar.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn_descargar.clicked.connect(lambda checked, ruta=ruta_completa: self.descargar_copia(ruta))
            self.tableWidget_historial.setCellWidget(row_idx, 3, btn_descargar)

    def descargar_copia(self, ruta_origen):
        """Toma el archivo de 'exportados' y lo copia a la carpeta de 'Downloads'"""
        nombre_archivo = os.path.basename(ruta_origen)
        ruta_destino = os.path.join(self.carpeta_descargas, nombre_archivo)
        
        try:
            shutil.copy2(ruta_origen, ruta_destino)
            QMessageBox.information(self, "Descarga Exitosa", f"Archivo guardado en:\n{ruta_destino}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo descargar el archivo: {e}")

    def generar_reporte(self):
        nombre = self.lineEdit_nombre_reporte.text().strip()
        fecha_inicio = self.dateEdit_inicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.dateEdit_fin.date().toString("yyyy-MM-dd")
        
        if not nombre:
            QMessageBox.warning(self, "Campo Obligatorio", "El nombre del reporte es obligatorio.")
            return

        datos = self.modelo_trafico.obtener_trafico_por_fechas(fecha_inicio, fecha_fin)
        if not datos:
            QMessageBox.information(self, "Sin datos", "No se encontró tráfico de red en ese intervalo de fechas.")
            return

        formato = "PDF"
        extension = ".pdf"
        if self.radio_csv.isChecked(): 
            formato = "CSV"
            extension = ".csv"
        elif self.radio_json.isChecked(): 
            formato = "JSON"
            extension = ".json"

        nombre_archivo = f"{nombre.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}{extension}"
        ruta_guardado = os.path.join(self.carpeta_exportados, nombre_archivo)

        incluir_resumen = self.chk_resumen.isChecked()
        incluir_distribucion = self.chk_distribucion.isChecked()
        incluir_ips = self.chk_ips.isChecked()

        try:
            if formato == "CSV":
                self._generar_csv(datos, ruta_guardado)
            elif formato == "JSON":
                self._generar_json(datos, ruta_guardado, incluir_resumen)
            elif formato == "PDF":
                self._generar_pdf(datos, ruta_guardado, incluir_resumen, incluir_ips)

            ruta_descarga = os.path.join(self.carpeta_descargas, nombre_archivo)
            shutil.copy2(ruta_guardado, ruta_descarga)

            QMessageBox.information(self, "Éxito", f"Reporte generado y guardado en tu carpeta de Descargas:\n{ruta_descarga}")
            
            self.cargar_historial_reportes()
            self.lineEdit_nombre_reporte.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Ocurrió un error al generar el reporte:\n{e}")

    # --- MÉTODOS INTERNOS DE EXPORTACIÓN ---

    def _generar_csv(self, datos, ruta):
        with open(ruta, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Fecha", "IP Origen", "IP Destino", "Puerto Origen", "Puerto Destino", "Protocolo", "Tamaño"])
            for row in datos:
                writer.writerow([row['id'], row['fecha'], row['ip_origen'], row['ip_destino'], 
                                 row['puerto_origen'], row['puerto_destino'], row['protocolo'], row['tamano']])

    def _generar_json(self, datos, ruta, incluir_resumen):
        for d in datos:
            if isinstance(d['fecha'], datetime):
                d['fecha'] = d['fecha'].strftime('%Y-%m-%d %H:%M:%S')

        estructura = {"trafico_crudo": datos}
        
        if incluir_resumen:
            estructura["metadata"] = {
                "total_paquetes": len(datos),
                "generado_el": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        with open(ruta, mode='w', encoding='utf-8') as file:
            json.dump(estructura, file, indent=4)

    def _generar_pdf(self, datos, ruta, incluir_resumen, incluir_ips):
        doc = SimpleDocTemplate(ruta, pagesize=letter)
        elementos = []
        estilos = getSampleStyleSheet()

        elementos.append(Paragraph("Reporte de Análisis de Red - NETSCAPES", estilos['Title']))
        elementos.append(Spacer(1, 12))

        if incluir_resumen:
            protocolos = [p['protocolo'] for p in datos]
            proto_mas_comun = max(set(protocolos), key=protocolos.count) if protocolos else "N/A"
            texto_resumen = f"<b>Resumen:</b> Se capturaron un total de {len(datos)} paquetes en este intervalo. El protocolo más frecuente fue {proto_mas_comun}."
            elementos.append(Paragraph(texto_resumen, estilos['Normal']))
            elementos.append(Spacer(1, 12))

        if incluir_ips:
            ips = set([p['ip_origen'] for p in datos] + [p['ip_destino'] for p in datos])
            texto_ips = f"<b>IPs Únicas detectadas:</b> {len(ips)} direcciones distintas."
            elementos.append(Paragraph(texto_ips, estilos['Normal']))
            elementos.append(Spacer(1, 12))

        datos_tabla = [["ID", "Fecha", "IP Origen", "IP Destino", "Protocolo", "Tamaño"]]
        for d in datos:
            fecha_str = d['fecha'].strftime('%Y-%m-%d %H:%M') if isinstance(d['fecha'], datetime) else d['fecha']
            datos_tabla.append([
                str(d['id']), fecha_str, d['ip_origen'], d['ip_destino'], d['protocolo'], d['tamano']
            ])

        tabla = Table(datos_tabla, repeatRows=1)
        estilo_tabla = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A253A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EEEEEE')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        tabla.setStyle(estilo_tabla)
        elementos.append(tabla)

        doc.build(elementos)