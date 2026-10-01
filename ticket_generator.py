import os
import subprocess
import platform
import configparser
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def registrar_error_en_archivo(mensaje_contexto, excepcion):
    """Escribe el error detallado en un archivo local para revisión."""
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
        elif "EMPRESA" in config:
            seccion = "EMPRESA"
        elif "empresa" in config:
            seccion = "empresa"
            
        if not seccion:
            return nombre_defecto
            
        opcion_empresa = "empresa" if "empresa" in config[seccion] else "nombre"
        if opcion_empresa in config[seccion]:
            nombre_config = config[seccion][opcion_empresa].strip()
            if nombre_config:
                return nombre_config.upper()
            
    except Exception as e:
        registrar_error_en_archivo("Lectura general de config.ini", e)
        
    return nombre_defecto

def abrir_e_imprimir_pdf(filename="detalle_lote.pdf"):
    """Abre el archivo PDF generado utilizando el visor predeterminado del sistema operativo."""
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    carpeta_impresiones = os.path.join(ruta_script, "impresiones")
    
    if not os.path.isabs(filename):
        posible_ruta_impresiones = os.path.join(carpeta_impresiones, filename)
        if os.path.exists(posible_ruta_impresiones):
            filepath = posible_ruta_impresiones
        else:
            filepath = os.path.abspath(filename)
    else:
        filepath = filename

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

def generar_detalle_lote_a4_pdf(datos, filename="detalle_lote.pdf"):
    """Genera un PDF A4 dividido al medio (Original arriba, Duplicado abajo) con el detalle del Lote."""
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    carpeta_impresiones = os.path.join(ruta_script, "impresiones")
    os.makedirs(carpeta_impresiones, exist_ok=True)
    
    if not os.path.isabs(filename) and not os.path.dirname(filename):
        filepath = os.path.join(carpeta_impresiones, filename)
    else:
        filepath = filename

    c = canvas.Canvas(filepath, pagesize=A4)
    nombre_empresa = obtener_nombre_empresa()
    
    def dibujar_copia_lote(y_offset, tipo_copia):
        c.setStrokeColor(colors.HexColor("#2d3748"))
        c.setLineWidth(1)
        c.roundRect(10 * mm, y_offset, 190 * mm, 130 * mm, 3, stroke=1, fill=0)
        
        c.setFillColor(colors.HexColor("#1a202c"))
        c.rect(10 * mm, y_offset + 118 * mm, 190 * mm, 12 * mm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(15 * mm, y_offset + 122 * mm, f"{nombre_empresa} - DETALLE Y TRAZABILIDAD DE LOTE")
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(195 * mm, y_offset + 122 * mm, str(tipo_copia))
        
        c.setFillColor(colors.black)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(15 * mm, y_offset + 110 * mm, "Nº LOTE:")
        c.setFont("Helvetica-Bold", 11)
        c.drawString(32 * mm, y_offset + 110 * mm, str(datos.get('lote', '-')))
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(75 * mm, y_offset + 110 * mm, "F. INICIO:")
        c.setFont("Helvetica", 9)
        c.drawString(93 * mm, y_offset + 110 * mm, str(datos.get('f_inicio', '-')))
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(140 * mm, y_offset + 110 * mm, "F. PROCESO:")
        c.setFont("Helvetica", 9)
        c.drawString(162 * mm, y_offset + 110 * mm, str(datos.get('f_proc', '-')))
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(15 * mm, y_offset + 103 * mm, "ORIGEN:")
        c.setFont("Helvetica", 9)
        c.drawString(32 * mm, y_offset + 103 * mm, f"{datos.get('id_origen', '')} - {datos.get('nombre_origen', '-')}")
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(140 * mm, y_offset + 103 * mm, "ESTADO:")
        c.setFont("Helvetica", 9)
        c.drawString(162 * mm, y_offset + 103 * mm, "PROCESADO" if datos.get('es_proc') == 1 else "PENDIENTE")

        c.setStrokeColor(colors.HexColor("#cbd5e0"))
        c.line(15 * mm, y_offset + 98 * mm, 195 * mm, y_offset + 98 * mm)

        # Sección Pesajes
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#2b5c8f"))
        c.drawString(15 * mm, y_offset + 92 * mm, "PESAJES INCLUIDOS")
        c.setFillColor(colors.black)

        y_p = y_offset + 84 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(15 * mm, y_p, "ID Pes.")
        c.drawString(30 * mm, y_p, "Kgs")
        c.drawString(50 * mm, y_p, "Origen Pesaje")
        
        c.setLineWidth(0.5)
        c.line(15 * mm, y_p - 2 * mm, 95 * mm, y_p - 2 * mm)
        
        y_p -= 7 * mm
        c.setFont("Helvetica", 8)
        pesajes = datos.get('pesajes', [])
        for p in pesajes[:5]:
            c.drawString(15 * mm, y_p, str(p.get('idpesaje', '')))
            c.drawString(30 * mm, y_p, f"{p.get('kgs', 0):,} kg")
            c.drawString(50 * mm, y_p, str(p.get('origen', ''))[:22])
            y_p -= 5 * mm

        if len(pesajes) > 5:
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(15 * mm, y_p, f"... y {len(pesajes) - 5} pesajes más.")

        # Sección Bolsones
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#2b5c8f"))
        c.drawString(105 * mm, y_offset + 92 * mm, "DETALLE DE BOLSONES / ENVASES")
        c.setFillColor(colors.black)

        y_b = y_offset + 84 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(105 * mm, y_b, "Nº Bol.")
        c.drawString(125 * mm, y_b, "Producto")
        c.drawString(165 * mm, y_b, "Turno")
        c.drawString(180 * mm, y_b, "Kgs")
        
        c.line(105 * mm, y_b - 2 * mm, 195 * mm, y_b - 2 * mm)
        
        y_b -= 7 * mm
        c.setFont("Helvetica", 8)
        bolsones = datos.get('bolsones', [])
        for b in bolsones[:5]:
            c.drawString(105 * mm, y_b, str(b.get('num', '')))
            c.drawString(125 * mm, y_b, str(b.get('prod', ''))[:20])
            c.drawString(165 * mm, y_b, str(b.get('turno', '')))
            c.drawString(180 * mm, y_b, f"{b.get('kg', 0)} kg")
            y_b -= 5 * mm

        if len(bolsones) > 5:
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(105 * mm, y_b, f"... y {len(bolsones) - 5} bolsones más.")

        # Recuadro Totales
        c.setFillColor(colors.HexColor("#f7fafc"))
        c.rect(15 * mm, y_offset + 22 * mm, 180 * mm, 18 * mm, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(20 * mm, y_offset + 33 * mm, "TOTAL KGS INGRESADOS")
        c.drawString(110 * mm, y_offset + 33 * mm, "TOTAL KGS ENVASADOS")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20 * mm, y_offset + 25 * mm, f"{datos.get('kgs_ingreso', 0):,} Kg")
        
        c.setFillColor(colors.HexColor("#2f855a"))
        c.drawString(110 * mm, y_offset + 25 * mm, f"{datos.get('kgs_env', 0):,} Kg")

        # Firmas
        c.setStrokeColor(colors.HexColor("#718096"))
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        
        c.line(25 * mm, y_offset + 8 * mm, 80 * mm, y_offset + 8 * mm)
        c.drawCentredString(52.5 * mm, y_offset + 4 * mm, "Firma Encargado de Producción")
        
        c.line(130 * mm, y_offset + 8 * mm, 185 * mm, y_offset + 8 * mm)
        c.drawCentredString(157.5 * mm, y_offset + 4 * mm, "Firma Control / Calidad")

    # Copia Original arriba
    dibujar_copia_lote(152 * mm, "COPIA ORIGINAL")
    
    # Línea de corte
    c.setStrokeColor(colors.HexColor("#a0aec0"))
    c.setLineWidth(1)
    c.setDash(4, 4)
    c.line(5 * mm, 148.5 * mm, 205 * mm, 148.5 * mm)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#4a5568"))
    c.drawString(10 * mm, 150 * mm, "✂ - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  Línea de corte  - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    c.setDash()

    # Copia Duplicado abajo
    dibujar_copia_lote(10 * mm, "COPIA DUPLICADO")
    
    c.showPage()
    c.save()
    
    return filepath