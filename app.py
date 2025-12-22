import os
import unicodedata
import re
from datetime import date
from io import BytesIO
import textwrap

import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
APP_TITLE = "🔮 Lectura Numerológica"
BRAND = "Eugenia.Místico"

st.set_page_config(
    page_title=f"{APP_TITLE} | {BRAND}",
    page_icon="🔮",
    layout="centered"
)

st.title(APP_TITLE)
st.caption(f"{BRAND} · Versión Gratis + Paga (bloqueada) · Lectura simbólica · PDF")

# =====================================================
# UTILIDADES NUMEROLÓGICAS
# =====================================================
MASTER = {11, 22, 33}

def reducir_numero(n: int) -> int:
    n = abs(int(n))
    if n in MASTER:
        return n
    while n > 9:
        n = sum(int(d) for d in str(n))
        if n in MASTER:
            return n
    return n

def normalizar_texto(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.upper()

TABLA_PITAGORICA = {
    **{c: 1 for c in "AJS"},
    **{c: 2 for c in "BKT"},
    **{c: 3 for c in "CLU"},
    **{c: 4 for c in "DMV"},
    **{c: 5 for c in "ENW"},
    **{c: 6 for c in "FOX"},
    **{c: 7 for c in "GPY"},
    **{c: 8 for c in "HQZ"},
    **{c: 9 for c in "IR"},
}

def numero_nombre(nombre: str) -> int:
    total = 0
    for c in normalizar_texto(nombre):
        if c.isalpha():
            total += TABLA_PITAGORICA.get(c, 0)
    return reducir_numero(total)

def sumar_digitos_texto(txt: str) -> int:
    digs = re.findall(r"\d", str(txt))
    if not digs:
        return 0
    return reducir_numero(sum(int(d) for d in digs))

def numero_apto(apto: str) -> int:
    apto = str(apto).strip()
    if not apto:
        return 0
    if re.search(r"\d", apto):
        return sumar_digitos_texto(apto)
    return numero_nombre(apto)

# ---- Núcleos principales ----
def esencia(fecha: date) -> int:
    return reducir_numero(fecha.day)

def vida_pasada(fecha: date) -> int:
    return reducir_numero(fecha.month)

def sendero_vida(fecha: date) -> int:
    return reducir_numero(fecha.day + fecha.month + fecha.year)

def ano_personal(fecha: date, year: int) -> int:
    return reducir_numero(fecha.day + fecha.month + year)

def mes_personal(ano_p: int, mes: int) -> int:
    return reducir_numero(ano_p + mes)

def semana_personal(mes_p: int, semana_del_ano: int) -> int:
    return reducir_numero(mes_p + semana_del_ano)

def dia_personal(mes_p: int, dia_hoy: int) -> int:
    return reducir_numero(mes_p + dia_hoy)

# ---- Arcano semanal ----
def arcano_semanal() -> int:
    semana = date.today().isocalendar()[1]
    return (semana % 22) + 1

# ---- Pináculo pirámide completa ----
def pinaculo_piramide(fecha: date) -> dict:
    d = reducir_numero(fecha.day)
    m = reducir_numero(fecha.month)
    a = reducir_numero(fecha.year)

    p1 = reducir_numero(d + m)
    p2 = reducir_numero(d + a)
    p3 = reducir_numero(p1 + p2)

    p4 = reducir_numero(p1 + p2)
    p5 = reducir_numero(p2 + p3)

    p6 = reducir_numero(p4 + p5)

    return {"base": (p1, p2, p3), "medio": (p4, p5), "cima": p6}

# =====================================================
# TEXTOS GRATIS (1 PÁRRAFO “LARGO”)
# =====================================================
LECTURA_GRATIS = {
    1:  "Esta vibración marca un inicio real: te empuja a elegir, actuar y abrir camino sin depender de la aprobación externa. La vida te pide claridad en tus decisiones y firmeza para sostener tu identidad. Avanzas cuando alineas intención y acción, dando pasos pequeños pero constantes que construyen una base sólida.",
    2:  "Esta vibración invita a la cooperación y la sensibilidad con centro. Es energía de escucha profunda: percibes más y por eso aprendes a poner límites suaves pero firmes. El crecimiento llega cuando eliges armonía sin sacrificio, cultivando reciprocidad, respeto y calma.",
    3:  "Esta vibración activa creatividad y expresión: te pide mostrar tu voz, compartir ideas y permitir que la alegría sea parte del avance. La clave está en expresarte con enfoque: cuando tu mensaje es claro, lo que creas se vuelve atractivo y con propósito.",
    4:  "Esta vibración habla de orden y constancia: todo mejora cuando estructuras prioridades y avanzas paso a paso. Premia disciplina y paciencia; lo estable se construye con decisiones pequeñas sostenidas. Tu llave es coherencia práctica: menos improvisación, más método.",
    5:  "Esta vibración trae cambio y movimiento: te empuja a expandirte y abrir opciones nuevas. Su reto es la dispersión: no todo lo que aparece es para ti. Creces cuando eliges el cambio con conciencia, soltando rigidez con dirección clara.",
    6:  "Esta vibración se asocia con cuidado y amor consciente. Invita a equilibrar lo personal con lo familiar y a sostener vínculos con madurez. La lección es dar sin vaciarte: límites sanos también son amor. Tu estabilidad emocional es tu base.",
    7:  "Esta vibración pide una pausa sabia: observar, comprender y escuchar la voz interna. La claridad no viene de la prisa, sino de la profundidad. Es un tiempo ideal para estudiar patrones, ordenar pensamientos y fortalecer intuición con calma.",
    8:  "Esta vibración activa logro y materialización: pide decisiones estratégicas y administración consciente de recursos. La lección es ética y coherencia: el poder personal se sostiene cuando está alineado con valores. Ordena prioridades y verás estabilidad.",
    9:  "Esta vibración marca cierre e integración: invita a soltar lo que ya cumplió su función y quedarte con el aprendizaje. Favorece limpieza interna y madurez emocional. Cerrar con conciencia aligera la energía y abre un rumbo más coherente.",
    11: "Esta vibración amplifica intuición e inspiración: te vuelve más sensible y perceptiva. Es un tiempo para escuchar señales internas y evitar dispersión emocional. Cuando actúas desde tu verdad, la claridad aparece y tu intuición se vuelve dirección.",
    22: "Esta vibración une visión y construcción: no basta soñar, toca estructurar. Favorece proyectos grandes con pasos concretos y disciplina a largo plazo. Si te enfocas, materializas algo sólido con impacto real.",
    33: "Esta vibración se orienta al amor consciente y al servicio con madurez emocional. Invita a acompañar sin rescatar y a dar sin vaciarte. Tu sensibilidad se vuelve fortaleza cuando hay límites, estructura y autocuidado.",
}

PINACULO_TEXTO_GRATIS = (
    "Este pináculo describe la arquitectura interna de tu camino: cómo se organizan tus aprendizajes por etapas y qué tipo de crecimiento "
    "la vida te pide integrar. No actúa como una predicción rígida: funciona como un mapa de madurez. Cuando lo comprendes, dejas de "
    "resistirte a los ciclos y empiezas a usarlos a tu favor, avanzando con más coherencia, confianza y dirección."
)

ARCANOS_GRATIS = {
    1:"Inicio consciente.", 2:"Escucha interior.", 3:"Creatividad.", 4:"Orden.", 5:"Aprendizaje.",
    6:"Elección.", 7:"Dirección.", 8:"Equilibrio.", 9:"Pausa.", 10:"Cambio.", 11:"Fortaleza.",
    12:"Nueva mirada.", 13:"Transformación.", 14:"Armonía.", 15:"Conciencia.", 16:"Ruptura.",
    17:"Esperanza.", 18:"Sensibilidad.", 19:"Claridad.", 20:"Renacer.", 21:"Integración.", 22:"Apertura."
}

# =====================================================
# PDF helper (sirve para gratis y paga)
# =====================================================
def build_pdf_bytes(titulo: str, secciones: list[tuple[str, str]]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    x = 50
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, titulo)
    y -= 22

    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"{BRAND} · Generado automáticamente")
    y -= 18

    def draw_paragraph(text: str, y: int):
        c.setFont("Helvetica", 11)
        lines = []
        for para in str(text).split("\n"):
            para = para.strip()
            if not para:
                lines.append("")
                continue
            lines.extend(textwrap.wrap(para, width=95))
            lines.append("")
        for ln in lines:
            if y < 90:
                c.showPage()
                y = height - 60
            c.drawString(x, y, ln)
            y -= 14
        return y

    for head, body in secciones:
        if y < 120:
            c.showPage()
            y = height - 60
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x, y, head)
        y -= 18
        y = draw_paragraph(body, y)
        y -= 6

    c.save()
    buffer.seek(0)
    return buffer.read()

# =====================================================
# UI – GRATIS (fecha + nombre en la misma línea)
# =====================================================
st.subheader("🌟 Versión Gratis")

col1, col2 = st.columns(2)
with col1:
    fecha_nac = st.date_input(
        "Fecha de nacimiento",
        min_value=date(1940, 1, 1),
        max_value=date(2025, 12, 31),
        value=date(1990, 1, 1),
    )
with col2:
    nombre = st.text_input(
        "Nombre completo (máx. 40 caracteres)",
        max_chars=40,
        value="",
        placeholder="Ej: Mari Eugenia Verde Arrocha"
    )

calcular = st.button("✨ Ver mi lectura numerológica")

hoy = date.today()

es = esencia(fecha_nac)
mis = sendero_vida(fecha_nac)
vp = vida_pasada(fecha_nac)

ap = ano_personal(fecha_nac, hoy.year)
mp = mes_personal(ap, hoy.month)
sp = semana_personal(mp, hoy.isocalendar()[1])
dp = dia_personal(mp, hoy.day)

arc = arcano_semanal()
pin = pinaculo_piramide(fecha_nac)

st.markdown("### ✨ Tu lectura gratis")

# 1) ESENCIA
st.write(f"*Mi esencia — Número {es}*")
st.write(LECTURA_GRATIS.get(es, ""))

# 2) NOMBRE COMPLETO (ENERGÍA DEL NOMBRE)555555555555555555555555555555555555555555

if nombre.strip():
    num_nombre = numero_nombre(nombre)
else:
    num_nombre = 0

if num_nombre != 0:
    st.write(f"Mi nombre completo — Número {num_nombre}")
    st.write(LECTURA_GRATIS.get(num_nombre, ""))
else:
    st.info("Escribe tu nombre completo para ver la energía de tu nombre.")

st.write(f"*Mi misión — Número {mis}*")
st.write(LECTURA_GRATIS.get(mis, ""))

st.write(f"*Mi año personal ({hoy.year}) — Número {ap}*")
st.write(LECTURA_GRATIS.get(ap, ""))

st.write(f"*Mi energía de hoy — Número {dp}*")
st.write(LECTURA_GRATIS.get(dp, ""))

st.write("*Mi pináculo (pirámide completa)*")
st.write(f"Base: {pin['base']} | Medio: {pin['medio']} | Cima: {pin['cima']}")
st.write(PINACULO_TEXTO_GRATIS)

st.write(f"*Arcano semanal — Número {arc}*")
st.write(ARCANOS_GRATIS.get(arc, ""))

# PDF Gratis
pdf_gratis = build_pdf_bytes(
    f"{APP_TITLE} · Gratis",
    [
        ("Datos", f"Nombre: {nombre or '—'}\nFecha de nacimiento: {fecha_nac}"),
        ("Mi esencia", f"Número {es}\n\n{LECTURA_GRATIS.get(es, '')}"),
        ("Mi nombre completo", f"Número {num_nombre}\n\n{LECTURA_GRATIS.get(num_nombre, '')}"),
        ("Mi misión", f"Número {mis}\n\n{LECTURA_GRATIS.get(mis, '')}"),
        ("Mi año personal", f"Número {ap}\n\n{LECTURA_GRATIS.get(ap, '')}"),
        ("Mi energía de hoy", f"Número {dp}\n\n{LECTURA_GRATIS.get(dp, '')}"),
        ("Mi pináculo (pirámide)", f"Base: {pin['base']} | Medio: {pin['medio']} | Cima: {pin['cima']}\n\n{PINACULO_TEXTO_GRATIS}"),
        ("Arcano semanal", f"Número {arc}\n\n{ARCANOS_GRATIS.get(arc, '')}"),
    ]
)

st.download_button(
    "⬇️ Descargar PDF (Gratis)",
    data=pdf_gratis,
    file_name="Lectura_Numerologica_Gratis_Eugenia_Mistico.pdf",
    mime="application/pdf",
)

# =====================================================
# BLOQUE PAGA (Premium)
# =====================================================
st.markdown("---")
st.subheader("🔒 Versión Paga (Bloqueada)")

PASSWORD = os.getenv("APP_PASSWORD")
clave = st.text_input("Introduce la clave para desbloquear la lectura completa", type="password")

if not PASSWORD:
    st.warning("No hay clave configurada en este equipo. Define APP_PASSWORD en tu PC.")
    st.stop()

if clave != PASSWORD:
    st.info("La lectura completa se desbloquea al realizar la compra.")
    st.stop()

st.success("Versión paga desbloqueada ✅")

# =====================================================
# TEXTOS PROFUNDOS (3 párrafos)
# =====================================================
NUM_RASGOS = {
    1: ("iniciativa", "afirmación", "dirección"),
    2: ("sensibilidad", "cooperación", "armonía"),
    3: ("expresión", "creatividad", "comunicación"),
    4: ("estructura", "disciplina", "constancia"),
    5: ("cambio", "libertad", "movimiento"),
    6: ("cuidado", "responsabilidad", "vínculos"),
    7: ("introspección", "análisis", "intuición"),
    8: ("logro", "poder personal", "materialización"),
    9: ("cierre", "compasión", "integración"),
    11: ("inspiración", "intuición elevada", "visión"),
    22: ("construcción", "visión práctica", "impacto"),
    33: ("amor consciente", "servicio", "sabiduría emocional"),
}

def parrafos_profundos(num: int, titulo: str) -> str:
    a, b, c = NUM_RASGOS.get(num, ("equilibrio", "conciencia", "claridad"))
    p1 = (
        f"En {titulo}, tu vibración muestra un núcleo de {a} que se activa como brújula interna. "
        f"No es solo una cualidad: es una forma de percibir la vida y responder a ella. "
        f"Cuando esta energía está alineada, te sientes más {b}, más capaz de sostener decisiones y avanzar con sentido."
    )
    p2 = (
        f"El aprendizaje aparece cuando la energía se exagera o se contrae: allí surge el reto. "
        f"En este número, la sombra suele mostrarse como tensión entre lo que deseas y lo que realmente te nutre. "
        f"Tu crecimiento no está en forzar resultados, sino en refinar tu {c}: elegir desde la verdad, no desde la presión."
    )
    p3 = (
        f"Tu llave práctica es convertir esta vibración en acción concreta: una decisión clara, un límite sano o un hábito sostenido. "
        f"Lo místico se vuelve real cuando se vuelve cotidiano: orden, enfoque e intención. "
        f"Si actúas con coherencia, esta etapa te devuelve confianza, dirección y un sentimiento real de avance."
    )
    return f"{p1}\n\n{p2}\n\n{p3}"

def texto_arcano_profundo() -> str:
    p1 = ("Esta semana trae un arquetipo que funciona como espejo: no viene a asustarte, viene a mostrarte dónde estás creciendo. "
          "Su mensaje principal es simple: lo que estás viviendo tiene sentido, incluso si aún no lo entiendes completo.")
    p2 = ("El arquetipo señala un ajuste interno: una forma más madura de decidir, un cambio de perspectiva o una verdad que pide espacio. "
          "Si sientes tensión, no es castigo: es señal de que tu energía se está reordenando para avanzar con más autenticidad.")
    p3 = ("La recomendación mística práctica es sostener presencia: menos impulsividad y más intención. "
          "Esta semana gana quien elige con calma, se escucha y actúa con coherencia. "
          "Cuando integras el mensaje, se abren oportunidades con menos desgaste.")
    return f"{p1}\n\n{p2}\n\n{p3}"

def pinaculo_profundo_texto(pin: dict) -> str:
    p1 = ("Tu pináculo funciona como mapa de etapas: muestra cómo se construye tu fuerza interna a través de experiencias que te forman. "
          "La base habla de las lecciones que te empujan a madurar desde lo cotidiano y de cómo respondes cuando la vida te exige crecer.")
    p2 = ("El nivel medio refleja el punto donde tu carácter se vuelve más consciente: allí aprendes a sostener decisiones, a poner límites y a elegir con coherencia. "
          "Cuando te alineas, los ciclos se vuelven aliados en vez de obstáculos.")
    p3 = ("La cima es la síntesis: la versión de ti que emerge cuando integras lecciones sin resentimiento. "
          "La clave es transformar aprendizaje en hábito: palabras claras, acciones consistentes y rutinas que te sostengan. "
          "Así tu pirámide se vuelve dirección, confianza y estabilidad emocional.")
    return f"{p1}\n\n{p2}\n\n{p3}"

# =====================================================
# NOMBRE PROFUNDO (alma / expresión / personalidad)
# =====================================================
def vocales(nombre: str) -> str:
    n = normalizar_texto(nombre)
    return "".join(ch for ch in n if ch in "AEIOU")

def consonantes(nombre: str) -> str:
    n = normalizar_texto(nombre)
    return "".join(ch for ch in n if ch.isalpha() and ch not in "AEIOU")

def numero_alma(nombre: str) -> int:
    return numero_nombre(vocales(nombre)) if nombre.strip() else 0

def numero_expresion(nombre: str) -> int:
    return numero_nombre(nombre) if nombre.strip() else 0

def numero_personalidad(nombre: str) -> int:
    return numero_nombre(consonantes(nombre)) if nombre.strip() else 0

# =====================================================
# COMPATIBILIDAD (3 párrafos)
# =====================================================
def compatibilidad_profunda(n1: int, n2: int) -> str:
    a = reducir_numero(n1 if n1 not in MASTER else sum(int(d) for d in str(n1)))
    b = reducir_numero(n2 if n2 not in MASTER else sum(int(d) for d in str(n2)))
    p1 = ("La compatibilidad no es destino: es dinámica. Observamos cómo se encuentran dos ritmos internos y qué aprendizaje aparece "
          "cuando comparten espacio emocional. La atracción suele nacer de lo que se reconoce o se complementa.")
    p2 = (f"En esta combinación, se mezclan vibraciones ({a} y {b}) que pueden potenciarse si hay comunicación y acuerdos. "
          "El reto típico no es quererse, sino sostener el vínculo sin perder identidad ni caer en patrones repetidos.")
    p3 = ("La clave mística práctica es simple: claridad + límites + ternura. Si ambos nombran necesidades y respetan ritmos, el vínculo crece. "
          "Si no, se vuelve espejo de heridas. Úsenlo como conciencia: hablar a tiempo evita desgastes.")
    return f"{p1}\n\n{p2}\n\n{p3}"

# =====================================================
# UI – PAGA
# =====================================================
st.markdown("## 💎 Lectura Paga (Profunda)")

st.markdown("### 1) Esencia")
st.write(f"Número {es}")
st.write(parrafos_profundos(es, "tu Esencia"))

st.markdown("### 2) Misión / Sendero de vida")
st.write(f"Número {mis}")
st.write(parrafos_profundos(mis, "tu Misión"))

st.markdown("### 3) Vida pasada")
st.write(f"Número {vp}")
st.write(parrafos_profundos(vp, "tu Vida Pasada"))

st.markdown("### 4) Año personal")
st.write(f"Número {ap}")
st.write(parrafos_profundos(ap, "tu Año Personal"))

st.markdown("### 5) Mes personal")
st.write(f"Número {mp}")
st.write(parrafos_profundos(mp, "tu Mes Personal"))

st.markdown("### 6) Semana personal")
st.write(f"Número {sp}")
st.write(parrafos_profundos(sp, "tu Semana Personal"))

st.markdown("### 7) Día personal")
st.write(f"Número {dp}")
st.write(parrafos_profundos(dp, "tu Día Personal"))

st.markdown("### 8) Arcano mayor de la semana")
st.write(f"Arcano {arc}")
st.write(texto_arcano_profundo())

st.markdown("### 9) Pináculo (pirámide completa)")
st.write(f"Base: {pin['base']} | Medio: {pin['medio']} | Cima: {pin['cima']}")
st.write(pinaculo_profundo_texto(pin))

st.markdown("### 10) Nombre profundo")
if not nombre.strip():
    st.warning("Para esta sección escribe tu nombre arriba (en la parte gratis).")
    expr = alma = pers = 0
else:
    expr = numero_expresion(nombre)
    alma = numero_alma(nombre)
    pers = numero_personalidad(nombre)

    st.write(f"*Expresión (nombre completo): {expr}*")
    st.write(parrafos_profundos(expr, "tu Expresión"))

    st.write(f"*Alma (vocales): {alma}*")
    st.write(parrafos_profundos(alma, "tu Número del Alma"))

    st.write(f"*Personalidad (consonantes): {pers}*")
    st.write(parrafos_profundos(pers, "tu Personalidad"))

st.markdown("### 11) Teléfono / DNI / Hogar")
telefono = st.text_input("Teléfono (opcional)", value="")
dni = st.text_input("Cédula / DNI (opcional)", value="")
apto = st.text_input("Apartamento / casa (opcional)", value="")
edificio = st.text_input("Nombre del edificio (opcional)", value="", max_chars=40)

tel_num = sumar_digitos_texto(telefono) if telefono.strip() else 0
dni_num = sumar_digitos_texto(dni) if dni.strip() else 0
apto_num = numero_apto(apto) if apto.strip() else 0
edif_num = numero_nombre(edificio) if edificio.strip() else 0
hogar_sintesis = reducir_numero(apto_num + edif_num) if (apto.strip() and edificio.strip()) else 0

if telefono.strip():
    st.write(f"Teléfono: {tel_num}")
    st.write(parrafos_profundos(tel_num, "tu Comunicación (Teléfono)"))

if dni.strip():
    st.write(f"DNI: {dni_num}")
    st.write(parrafos_profundos(dni_num, "tu Identidad Numérica (DNI)"))

if apto.strip():
    st.write(f"Apartamento/Casa: {apto_num}")
    st.write(parrafos_profundos(apto_num, "tu Espacio (Apartamento/Casa)"))

if edificio.strip():
    st.write(f"Edificio: {edif_num}")
    st.write(parrafos_profundos(edif_num, "tu Entorno (Edificio)"))

if hogar_sintesis:
    st.write(f"Síntesis del hogar: {hogar_sintesis}")
    st.write(parrafos_profundos(hogar_sintesis, "la Síntesis del Hogar"))

st.markdown("### 12) Compatibilidad")
colc1, colc2 = st.columns(2)
with colc1:
    fecha_pareja = st.date_input(
        "Fecha de nacimiento de la pareja",
        min_value=date(1940, 1, 1),
        max_value=date(2025, 12, 31),
        value=date(1990, 1, 1),
        key="pareja_fecha"
    )
with colc2:
    calcular_cmp = st.checkbox("Calcular compatibilidad", value=True)

cmp_texto = ""
if calcular_cmp and fecha_pareja:
    sv_p = sendero_vida(fecha_pareja)
    st.write(f"Tu sendero: {mis} · Sendero pareja: {sv_p}")
    cmp_texto = compatibilidad_profunda(mis, sv_p)
    st.write(cmp_texto)

# =====================================================
# PDF PAGA (largo)
# =====================================================
secciones_paga = [
    ("Datos", f"Nombre: {nombre or '—'}\nFecha de nacimiento: {fecha_nac}\nGenerado: {hoy}"),
    ("Esencia", f"Número {es}\n\n{parrafos_profundos(es, 'tu Esencia')}"),
    ("Misión / Sendero", f"Número {mis}\n\n{parrafos_profundos(mis, 'tu Misión')}"),
    ("Vida pasada", f"Número {vp}\n\n{parrafos_profundos(vp, 'tu Vida Pasada')}"),
    ("Año personal", f"Número {ap}\n\n{parrafos_profundos(ap, 'tu Año Personal')}"),
    ("Mes personal", f"Número {mp}\n\n{parrafos_profundos(mp, 'tu Mes Personal')}"),
    ("Semana personal", f"Número {sp}\n\n{parrafos_profundos(sp, 'tu Semana Personal')}"),
    ("Día personal", f"Número {dp}\n\n{parrafos_profundos(dp, 'tu Día Personal')}"),
    ("Arcano semanal", f"Arcano {arc}\n\n{texto_arcano_profundo()}"),
    ("Pináculo (pirámide completa)", f"Base: {pin['base']} | Medio: {pin['medio']} | Cima: {pin['cima']}\n\n{pinaculo_profundo_texto(pin)}"),
]

if nombre.strip():
    secciones_paga.append(("Nombre – Expresión", f"{expr}\n\n{parrafos_profundos(expr, 'tu Expresión')}"))
    secciones_paga.append(("Nombre – Alma", f"{alma}\n\n{parrafos_profundos(alma, 'tu Número del Alma')}"))
    secciones_paga.append(("Nombre – Personalidad", f"{pers}\n\n{parrafos_profundos(pers, 'tu Personalidad')}"))

extras_lines = []
if telefono.strip(): extras_lines.append(f"Teléfono: {telefono} → {tel_num}")
if dni.strip(): extras_lines.append(f"DNI: {dni} → {dni_num}")
if apto.strip(): extras_lines.append(f"Apartamento/Casa: {apto} → {apto_num}")
if edificio.strip(): extras_lines.append(f"Edificio: {edificio} → {edif_num}")
if hogar_sintesis: extras_lines.append(f"Síntesis hogar → {hogar_sintesis}")
if extras_lines:
    secciones_paga.append(("Extras", "\n".join(extras_lines)))

if cmp_texto:
    secciones_paga.append(("Compatibilidad", cmp_texto))

pdf_paga = build_pdf_bytes(
    f"{APP_TITLE} · Premium",
    secciones_paga
)

st.download_button(
    "⬇️ Descargar PDF (Paga)",
    data=pdf_paga,
    file_name="Lectura_Numerologica_Paga_Eugenia_Mistico.pdf",
    mime="application/pdf",
)
#redeplot

st.caption("Lectura simbólica e interpretativa · Eugenia.Místico · Premium")
