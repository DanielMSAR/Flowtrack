import os
import datetime
import configparser
import platform
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

def obtener_nombre_empresa():
    config = configparser.ConfigParser()
    nombre_defecto = "MI EMPRESA"
    ruta_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    if os.path.exists(ruta_config):
        try:
            config.read(ruta_config, encoding="utf-8")
            sec = "Parametros" if "Parametros" in config else ("parametros" if "parametros" in config else None)
            if sec and "empresa" in config[sec]:
                return config[sec]["empresa"].strip().upper()
        except Exception:
            pass
    return nombre_defecto

def generar_pdf_ctacte(nombre_cliente, movimientos, total_debe, total_haber, saldo_total, filename=None):
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    carpeta_impresiones = os.path.join(ruta_script, "impresiones")
    os.makedirs(carpeta_impresiones, exist_ok=True)

    if not filename:
        fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CtaCte_{nombre_cliente.replace(' ', '_')}_{fecha_str}.pdf"

    filepath = os.path.join(carpeta_impresiones, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    story = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=18,
        textColor=colors.HexColor("#1a202c"),
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#4a5568")
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10
    )
    cell_style_bold = ParagraphStyle(
        'CellTextBold',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold"
    )

    # 1. Encabezado
    empresa = obtener_nombre_empresa()
    fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    story.append(Paragraph(f"<b>{empresa}</b>", title_style))
    story.append(Paragraph(f"<b>Estado de Cuenta Corriente:</b> {nombre_cliente}", subtitle_style))
    story.append(Paragraph(f"<b>Fecha de Emisión:</b> {fecha_emision}", subtitle_style))
    story.append(Spacer(1, 10))

    # 2. Tabla de Datos
    # Columnas: Fecha (55pt), Comp (70pt), Detalle (180pt), Debe (65pt), Haber (65pt), Saldo (65pt) = 500pt
    headers = ["Fecha", "Comprobante", "Detalle", "Debe (+)", "Haber (-)", "Saldo"]
    table_data = [[Paragraph(f"<b>{h}</b>", cell_style_bold) for h in headers]]

    for m in movimientos:
        table_data.append([
            Paragraph(str(m['fecha']), cell_style),
            Paragraph(str(m['comprobante']), cell_style),
            Paragraph(str(m['detalle']), cell_style),
            Paragraph(f"${m['debe']}", cell_style),
            Paragraph(f"${m['haber']}", cell_style),
            Paragraph(f"${m['saldo']}", cell_style_bold)
        ])

    t = Table(table_data, colWidths=[55, 70, 180, 65, 65, 65], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # 3. Resumen de Totales
    resumen_data = [
        [
            Paragraph("<b>TOTAL DEBE:</b>", cell_style_bold), Paragraph(f"${total_debe:,.2f}", cell_style),
            Paragraph("<b>TOTAL HABER:</b>", cell_style_bold), Paragraph(f"${total_haber:,.2f}", cell_style),
            Paragraph("<b>SALDO ACTUAL:</b>", cell_style_bold), Paragraph(f"${saldo_total:,.2f}", cell_style_bold)
        ]
    ]
    t_resumen = Table(resumen_data, colWidths=[80, 80, 80, 80, 90, 90])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#d6e4f0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1a5276")),
    ]))
    story.append(t_resumen)

    doc.build(story)
    return filepath

def abrir_pdf(filepath):
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(filepath)
        elif sistema == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        print(f"Error al abrir el PDF: {e}")