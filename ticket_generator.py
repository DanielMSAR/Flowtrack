# ticket_generator.py
import os
import subprocess
import platform
import configparser
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def registrar_error_en_archivo(mensaje_contexto, excepcion):
    """Escribe el error detallado en un archivo local para que puedas revisarlo."""
    ruta_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.txt")
    try:
        with open(ruta_log, "a", encoding="utf-8") as f:
            f.write(f"--- ERROR: {mensaje_contexto} ---\n")
            f.write(f"Detalle: {str(excepcion)}\n")
            f.write("-" * 40 + "\n")
    except Exception:
        pass

def obtener_nombre_empresa():
    """Lee el nombre de la empresa desde el archivo config.ini."""
    config = configparser.ConfigParser()
    nombre_defecto = "DG SOLUCIONES"
    
    ruta_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    
    if not os.path.exists(ruta_config):
        return nombre_defecto

    try:
        config.read(ruta_config, encoding="utf-8")
        seccion = None
        if "Parametros" in config:
            seccion = "Parametros"
        elif "parametros" in config:
            seccion = "parametros"
            
        if not seccion:
            return nombre_defecto
            
        if "empresa" not in config[seccion]:
            return nombre_defecto
            
        nombre_config = config[seccion]["empresa"].strip()
        if nombre_config:
            return nombre_config.upper()
            
    except Exception as e:
        registrar_error_en_archivo("Lectura general de config.ini", e)
        
    return nombre_defecto

def generar_ticket_pdf(datos_ticket, filename="ticket_balanza.pdf"):
    # Dimensiones de A4 en vertical: 210mm de ancho x 297mm de alto
    ancho, alto = A4 
    c = canvas.Canvas(filename, pagesize=A4)
    
    nombre_empresa = obtener_nombre_empresa()
    
    # Ruta al archivo de imagen del logo
    # Buscamos en la carpeta "imagenes" dentro del mismo directorio del script
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    ruta_logo = os.path.join(ruta_script, "imagenes", "logo.png")
    
    def dibujar_ticket(y_offset, tipo_copia):
        # ----------------- BORDE EXTERNO DEL TICKET -----------------
        c.setStrokeColor(colors.HexColor("#2d3748"))
        c.setLineWidth(1)
        c.roundRect(10 * mm, y_offset, 190 * mm, 125 * mm, 3, stroke=1, fill=0)
        
        # ----------------- SELLO DE AGUA (LOGO EN EL FONDO) -----------------
        if os.path.exists(ruta_logo):
            c.saveState()
            # Definimos una transparencia del 8% para que sea muy sutil y no entorpezca la lectura
            c.setFillAlpha(0.30)  
            
            # Dimensiones deseadas para el logo dentro del ticket: 60mm x 60mm
            ancho_logo = 60 * mm
            alto_logo = 60 * mm
            
            # Calculamos las coordenadas para centrarlo horizontal y verticalmente en el ticket
            # El ticket mide 190mm de ancho y 125mm de alto. Empieza en X = 10mm
            x_logo = 10 * mm + (190 * mm - ancho_logo) / 2
            y_logo = y_offset + (125 * mm - alto_logo) / 2
            
            try:
                c.drawImage(ruta_logo, x_logo, y_logo, width=ancho_logo, height=alto_logo, mask='auto')
            except Exception as e:
                registrar_error_en_archivo("Dibujando marca de agua (logo)", e)
                
            c.restoreState() # Restauramos el estado de opacidad al 100% para el resto del diseño

        # ----------------- ENCABEZADO ESTILO TICKETERA -----------------
        c.setFillColor(colors.HexColor("#1a202c"))
        c.rect(10 * mm, y_offset + 113 * mm, 190 * mm, 12 * mm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(15 * mm, y_offset + 117 * mm, f"{nombre_empresa} - CONTROL DE PESAJES")
        
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(195 * mm, y_offset + 117 * mm, str(tipo_copia))

        # ----------------- GRILLA DE DATOS GENERALES -----------------
        c.setFillColor(colors.black)
        
        ticket_id = str(datos_ticket.get('id', 'N/A'))
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * mm, y_offset + 102 * mm, "TICKET N°:")
        c.setFont("Helvetica", 11)
        c.drawString(42 * mm, y_offset + 102 * mm, ticket_id)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(110 * mm, y_offset + 102 * mm, "FECHA / HORA:")
        c.setFont("Helvetica", 10)
        c.drawString(142 * mm, y_offset + 102 * mm, str(datos_ticket.get('fecha', '')))
        
        # Línea divisoria sutil
        c.setStrokeColor(colors.HexColor("#a0aec0"))
        c.setLineWidth(0.5)
        c.line(15 * mm, y_offset + 97 * mm, 195 * mm, y_offset + 97 * mm)
        
        # Fila 2: Patente y Chofer
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * mm, y_offset + 90 * mm, "PATENTE:")
        c.setFont("Helvetica-Bold", 11)
        c.drawString(42 * mm, y_offset + 90 * mm, str(datos_ticket.get('patente', 'N/A')).upper())
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(110 * mm, y_offset + 90 * mm, "CHOFER:")
        c.setFont("Helvetica", 10)
        c.drawString(142 * mm, y_offset + 90 * mm, str(datos_ticket.get('chofer', 'Asociado')))

        # Fila 3: Transporte y Producto
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * mm, y_offset + 80 * mm, "TRANSP.:")
        c.setFont("Helvetica", 10)
        c.drawString(42 * mm, y_offset + 80 * mm, str(datos_ticket.get('transporte', 'Asociado')))
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(110 * mm, y_offset + 80 * mm, "PRODUCTO:")
        c.setFont("Helvetica", 10)
        c.drawString(142 * mm, y_offset + 80 * mm, str(datos_ticket.get('producto', 'Gral.')))

        # Fila 4: Origen y Destino
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * mm, y_offset + 70 * mm, "ORIGEN:")
        c.setFont("Helvetica", 10)
        c.drawString(42 * mm, y_offset + 70 * mm, str(datos_ticket.get('origen', 'Establecimiento')))
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(110 * mm, y_offset + 70 * mm, "DESTINO:")
        c.setFont("Helvetica", 10)
        c.drawString(142 * mm, y_offset + 70 * mm, str(datos_ticket.get('destino', 'Establecimiento')))

        # Fila 5: Remito
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * mm, y_offset + 60 * mm, "REMITO:")
        c.setFont("Helvetica", 10)
        c.drawString(42 * mm, y_offset + 60 * mm, str(datos_ticket.get('remito', 'S/N')))

        # ----------------- RECUADRO DE PESOS -----------------
        c.setFillColor(colors.HexColor("#f7fafc"))
        c.rect(15 * mm, y_offset + 22 * mm, 180 * mm, 28 * mm, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(20 * mm, y_offset + 44 * mm, "PESO ENTRADA (BRUTO)")
        c.drawString(82 * mm, y_offset + 44 * mm, "PESO SALIDA (TARA)")
        c.drawString(145 * mm, y_offset + 44 * mm, "PESO NETO CARGA")
        
        try:
            val_entrada = f"{int(datos_ticket.get('entrada', 0)):,} Kg"
            val_salida = f"{int(datos_ticket.get('salida', 0)):,} Kg"
            val_neto = f"{int(datos_ticket.get('neto', 0)):,} Kg"
        except (ValueError, TypeError):
            val_entrada = f"{datos_ticket.get('entrada', 0)} Kg"
            val_salida = f"{datos_ticket.get('salida', 0)} Kg"
            val_neto = f"{datos_ticket.get('neto', 0)} Kg"

        c.setFont("Helvetica-Bold", 18)
        c.drawString(20 * mm, y_offset + 30 * mm, val_entrada)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72 * mm, y_offset + 32 * mm, "-")
        
        c.setFont("Helvetica-Bold", 18)
        c.drawString(82 * mm, y_offset + 30 * mm, val_salida)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(135 * mm, y_offset + 32 * mm, "=")
        
        c.setFillColor(colors.HexColor("#2f855a"))
        c.setFont("Helvetica-Bold", 20)
        c.drawString(145 * mm, y_offset + 30 * mm, val_neto)

        # ----------------- SECCIÓN DE FIRMAS -----------------
        c.setStrokeColor(colors.HexColor("#718096"))
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        
        c.line(25 * mm, y_offset + 10 * mm, 80 * mm, y_offset + 10 * mm)
        c.drawCentredString(52.5 * mm, y_offset + 6 * mm, "Firma del Transportista / Chofer")
        
        c.line(130 * mm, y_offset + 10 * mm, 185 * mm, y_offset + 10 * mm)
        c.drawCentredString(157.5 * mm, y_offset + 6 * mm, "Firma del Operador de Balanza")

    # 1. Dibujamos el Original arriba
    dibujar_ticket(155 * mm, "COPIA ORIGINAL")
    
    # 2. Línea punteada divisoria en el centro de la hoja A4 (Y = 148.5mm)
    c.setStrokeColor(colors.HexColor("#718096"))
    c.setLineWidth(1)
    
    c.setDash(4, 4)  
    c.line(5 * mm, 148.5 * mm, 205 * mm, 148.5 * mm)
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#4a5568"))
    c.drawString(10 * mm, 150 * mm, "✂ - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  Línea de corte  - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    
    c.setDash()

    # 3. Dibujamos el Duplicado abajo
    dibujar_ticket(12 * mm, "COPIA DUPLICADO")
    
    c.showPage()
    c.save()

def abrir_e_imprimir_pdf(filename="ticket_balanza.pdf"):
    filepath = os.path.abspath(filename)
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(filepath)
        elif sistema == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        print(f"No se pudo abrir automáticamente el visor de PDF: {e}")