# =========================================================
# 🔐 VERSIÓN COMPLETA (PAGO) - BLOQUEO POR CLAVE + NOMBRE + FECHA
#   - Premium NO muestra Excel en pantalla
#   - Premium SOLO entrega PDF del "Estudio completo"
#   - Motor Excel se ejecuta internamente y bajo demanda
# =========================================================

import os
from io import BytesIO
from datetime import date, datetime

import streamlit as st
from openpyxl import load_workbook

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import HexColor


# -----------------------------
# 📌 RUTA DEL EXCEL (en repo)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(_file_))
EXCEL_PATH = os.path.join(BASE_DIR, "Numerologia_Eugenia.xlsx")  # OJO: debe llamarse EXACTO así en GitHub


# -----------------------------
# 🧼 Helpers de texto/formatos
# -----------------------------
def _fmt_cell(x):
    """Convierte celdas a texto bonito y estable (evita None, tuplas raras, datetimes crudos)."""
    if x is None:
        return ""
    if isinstance(x, str):
        s = x.strip()
        if s.lower() == "none":
            return ""
        return s
    if isinstance(x, (datetime,)):
        return x.strftime("%d/%m/%Y")
    # openpyxl a veces trae date/datetime como datetime; date lo dejamos:
    if hasattr(x, "strftime"):
        try:
            return x.strftime("%d/%m/%Y")
        except Exception:
            pass
    return str(x).strip()


def _fila_a_texto(fila):
    """Une valores útiles sin llenar de 'None'."""
    if isinstance(fila, (list, tuple)):
        parts = [_fmt_cell(v) for v in fila]
        parts = [p for p in parts if p]  # filtra vacíos
        return " · ".join(parts).strip()
    return _fmt_cell(fila).strip()


# -----------------------------
# 📘 LECTURA EXCEL (motor interno)
#   Lee todas las hojas (por si Excel depende de cálculos ya guardados)
#   Pero el PDF se alimenta SOLO de "Estudio completo"
# -----------------------------
@st.cache_data(show_spinner=False)
def leer_excel_completo_cached(excel_path: str) -> dict:
    wb = load_workbook(excel_path, data_only=True)
    data = {}

    for hoja in wb.sheetnames:
        ws = wb[hoja]
        filas = []
        for row in ws.iter_rows(values_only=True):
            # fila útil si al menos una celda tiene algo real
            if any(_fmt_cell(cell) for cell in row):
                filas.append(row)
        data[hoja] = filas

    return data


def obtener_estudio_completo(data_excel: dict) -> list:
    # Busca "Estudio completo" sin sensibilidad a mayúsculas/espacios
    for nombre_hoja, filas in data_excel.items():
        if nombre_hoja and nombre_hoja.strip().lower() == "estudio completo":
            return filas
    return []


# -----------------------------
# 🧾 PDF Premium (solo Estudio completo)
# -----------------------------
@st.cache_data(show_spinner=False)
def build_pdf_premium_estudio_completo(nombre_cliente: str, excel_path: str) -> bytes:
    # 1) Lee todo (interno), 2) extrae estudio completo, 3) crea PDF bonito
    data_excel = leer_excel_completo_cached(excel_path)
    estudio = obtener_estudio_completo(data_excel)

    # Si no existe esa hoja, fallamos con mensaje dentro del PDF (para no romper UX)
    if not estudio:
        estudio = [("No se encontró la hoja 'Estudio completo' en el Excel.",)]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=52,
        leftMargin=52,
        topMargin=60,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Paleta: rojo místico + dorado elegante
    ROJO = HexColor("#7A1E3A")
    DORADO = HexColor("#9C7A3F")
    GRIS_TXT = HexColor("#2E2E2E")
    GRIS_SOFT = HexColor("#666666")

    # Estilos (limpios, aire, sin tablas)
    styles.add(ParagraphStyle(
        name="EM_PortadaTitulo",
        fontSize=26,
        leading=30,
        alignment=1,
        textColor=ROJO,
        spaceAfter=18
    ))
    styles.add(ParagraphStyle(
        name="EM_PortadaSub",
        fontSize=13.5,
        leading=18,
        alignment=1,
        textColor=DORADO,
        spaceAfter=26
    ))
    styles.add(ParagraphStyle(
        name="EM_Marca",
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=GRIS_SOFT,
        spaceBefore=36
    ))
    styles.add(ParagraphStyle(
        name="EM_SeccionTitulo",
        fontSize=17,
        leading=22,
        textColor=ROJO,
        spaceBefore=10,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name="EM_Texto",
        fontSize=11,
        leading=16,
        textColor=GRIS_TXT,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="EM_Divider",
        fontSize=10,
        leading=12,
        textColor=DORADO,
        alignment=1,
        spaceAfter=10
    ))

    elementos = []

    # 🌙 Portada mística (sobria)
    elementos.append(Spacer(1, 86))
    elementos.append(Paragraph("Lectura Numerológica Premium", styles["EM_PortadaTitulo"]))
    elementos.append(Paragraph(f"Informe personalizado para<br/><b>{_fmt_cell(nombre_cliente) or 'Cliente'}</b>", styles["EM_PortadaSub"]))
    elementos.append(Paragraph("✦ ✧ ✦", styles["EM_Divider"]))
    elementos.append(Spacer(1, 52))
    elementos.append(Paragraph("Eugenia Mística · Numerología & Conciencia", styles["EM_Marca"]))
    elementos.append(PageBreak())

    # ✅ Contenido: SOLO “Estudio completo”
    elementos.append(Paragraph("Estudio completo", styles["EM_SeccionTitulo"]))
    for fila in estudio:
        texto = _fila_a_texto(fila)
        if texto:
            # Evitar líneas kilométricas pegadas: deja respirar
            elementos.append(Paragraph(texto, styles["EM_Texto"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


# =========================================================
# UI Premium (solo desbloqueo + PDF)
# =========================================================
st.markdown("---")
st.markdown("## 🔐 Versión Completa (Premium + PDF personalizado)")
st.write("Desbloquea tu lectura completa con tu clave personal.")

colv1, colv2 = st.columns(2)

with colv1:
    nombre_compra = st.text_input(
        "Nombre (exactamente como en tu compra)",
        key="nombre_compra",
        max_chars=40,
        placeholder="Ej: Eugenia Mystikos"
    )

with colv2:
    fecha_compra = st.date_input(
        "Fecha de nacimiento (como en tu compra)",
        key="fecha_compra",
        min_value=date(1940, 1, 1),
        max_value=date(2040, 12, 31),
        value=date(1990, 1, 1),
    )

clave_ingresada = st.text_input(
    "Introduce tu clave personal",
    type="password",
    key="clave_ingresada"
).strip().upper()

confirmar_datos = st.button("🔓 Confirmar datos y desbloquear", key="btn_confirmar_premium")


if confirmar_datos:
    if not nombre_compra.strip():
        st.warning("Escribe tu nombre tal como aparece en tu compra.")
        st.stop()

    if not fecha_compra:
        st.warning("Debes indicar la fecha de nacimiento usada en tu compra.")
        st.stop()

    if not clave_ingresada:
        st.warning("Debes introducir tu clave personal.")
        st.stop()

    clave_esperada = generar_clave_unica(nombre_compra, fecha_compra)

    if clave_ingresada != clave_esperada:
        st.error("Clave inválida. Verifica que tu nombre y fecha estén EXACTAMENTE como en tu compra.")
        st.stop()

    st.session_state.premium_activo = True
    st.session_state.premium_nombre = nombre_compra.strip()
    st.success("Versión completa desbloqueada ✅")


# =========================================================
# SOLO SI PREMIUM ACTIVO → mostrar SOLO el botón PDF
# (nada de Excel en pantalla)
# =========================================================
if st.session_state.get("premium_activo"):
    nombre_cliente_pdf = st.session_state.get("premium_nombre") or nombre_compra.strip() or "Cliente"

    # Validación de archivo (el error real de Streamlit Cloud)
    if not os.path.exists(EXCEL_PATH):
        st.error(
            "No encuentro el archivo 'Numerologia_Eugenia.xlsx' en el servidor. "
            "Solución: súbelo al repositorio (misma carpeta que app.py) y verifica el nombre EXACTO."
        )
        st.stop()

    # Generación bajo demanda (cacheada)
    with st.spinner("Preparando tu PDF premium..."):
        pdf_bytes = build_pdf_premium_estudio_completo(nombre_cliente_pdf, EXCEL_PATH)

    st.download_button(
        "📄 Descargar Estudio Completo (PDF Premium)",
        data=pdf_bytes,
        file_name=f"Estudio_Completo_{normalizar_clave_nombre(nombre_cliente_pdf)}.pdf",
        mime="application/pdf",
        key="dl_pdf_premium"
    )
