  #####################################################
# =====================================================
# 📘 LECTURA EXCEL PREMIUM (MOTOR INTERNO)
# =====================================================
from openpyxl import load_workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import HexColor
from io import BytesIO
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Numerologia_Eugenia.xlsx")


def leer_excel_completo():
    wb = load_workbook(EXCEL_PATH, data_only=True)
    data = {}

    for hoja in wb.sheetnames:
        ws = wb[hoja]
        filas = []
        for row in ws.iter_rows(values_only=True):
            if any(cell not in (None, "", "None") for cell in row):
                filas.append(row)
        data[hoja] = filas

    return data


def obtener_estudio_completo(data_excel):
    for nombre_hoja, filas in data_excel.items():
        if nombre_hoja.strip().lower() == "estudio completo":
            return filas
    return []

def build_pdf_premium_desde_excel(nombre_cliente, data_excel):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # =========================
    # 🎨 ESTILOS EUGENIA MÍSTICA
    # =========================

    styles.add(ParagraphStyle(
        name="PortadaTitulo",
        fontSize=26,
        leading=30,
        alignment=1,  # centrado
        textColor=HexColor("#7A1E3A"),  # rojo místico
        spaceAfter=24
    ))

    styles.add(ParagraphStyle(
        name="PortadaSub",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=HexColor("#9C7A3F"),  # dorado elegante
        spaceAfter=30
    ))

    styles.add(ParagraphStyle(
        name="SeccionTitulo",
        fontSize=17,
        leading=22,
        textColor=HexColor("#7A1E3A"),
        spaceBefore=24,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="TextoCuerpo",
        fontSize=11,
        leading=16,
        textColor=HexColor("#2E2E2E"),
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="Marca",
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=HexColor("#666666"),
        spaceBefore=40
    ))

    elementos = []

    # =========================
    # 🌙 PORTADA
    # =========================

    elementos.append(Spacer(1, 80))
    elementos.append(Paragraph("Lectura Numerológica Premium", styles["PortadaTitulo"]))
    elementos.append(Paragraph(f"Informe personalizado para<br/><b>{nombre_cliente}</b>", styles["PortadaSub"]))
    elementos.append(Spacer(1, 60))
    elementos.append(Paragraph("Eugenia Mística · Numerología & Conciencia", styles["Marca"]))
    elementos.append(PageBreak())

    # =========================
    # 🔮 CONTENIDO DESDE EXCEL
    # =========================

    for seccion, filas in data_excel.items():

        # Título de sección
        elementos.append(Paragraph(seccion, styles["SeccionTitulo"]))

        for fila in filas:
            if isinstance(fila, (list, tuple)):
                texto = " · ".join(str(x) for x in fila if x not in (None, "", "None"))
            else:
                texto = str(fila)

            if texto.strip():
                elementos.append(Paragraph(texto, styles["TextoCuerpo"]))

        elementos.append(Spacer(1, 16))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()
