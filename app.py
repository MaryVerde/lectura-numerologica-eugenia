import os
import unicodedata
import re
from datetime import date
from io import BytesIO
import textwrap
import hmac
import hashlib

import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# =====================================================
# SECRETOS (STREAMLIT CLOUD + LOCAL)
# =====================================================
def get_secret(key: str, default=None):
    # 1) Streamlit Secrets
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # 2) Variables de entorno (local)
    return os.getenv(key, default)

APP_SECRET = get_secret("APP_SECRET")
ADMIN_PIN = get_secret("ADMIN_PIN")

if not APP_SECRET:
    st.error("❌ Falta APP_SECRET. Ve a Settings → Secrets y agrega APP_SECRET.")
    st.stop()

# =====================================================
# CONTADOR (INTERNO) - SOLO PANEL ADMIN
# =====================================================
COUNTER_FILE = "contador_resumida.txt"

def leer_contador():
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except:
        return 0

def incrementar_contador():
    total = leer_contador() + 1
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(total))
    except:
        # En Streamlit Cloud a veces el FS es de solo lectura; si pasa, igual no mostramos nada al cliente.
        pass
    return total

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
APP_TITLE = "🔮 Lectura Numerológica"
BRAND = "Eugenia.Mystikos"

st.set_page_config(
    page_title=f"{APP_TITLE} · {BRAND}",
    page_icon="🔮",
    layout="centered"
)

st.title(f"{APP_TITLE} · {BRAND}")
st.markdown(
    f"{BRAND}  \n"
    "Versión Resumida · Interpretación completa en versión completa (PDF personalizado)"
)

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
# TEXTOS RESUMIDOS (1 párrafo)
# =====================================================
LECTURA_RESUMIDA = {
    1:  "Esta vibración marca un inicio real: te empuja a elegir, actuar y abrir camino sin depender de la aprobación externa. La vida te pide claridad en tus decisiones y firmeza para sostener tu identidad. Avanzas cuando alineas intención y acción, dando pasos pequeños pero constantes que construyen una base sólida.",
    2:  "Esta vibración invita a la cooperación y la sensibilidad con centro. Es energía de escucha profunda: percibes más y por eso aprendes a poner límites suaves pero firmes. El crecimiento llega cuando eliges armonía sin sacrificio, cultivando reciprocidad, respeto y calma.",
    3:  "Esta vibración activa creatividad y expresión: te pide mostrar tu voz, compartir ideas y permitir que la alegría sea parte del avance. La clave está en expresarte con enfoque: cuando tu mensaje es claro, lo que creas se vuelve atractivo y con propósito.",
    4:  "Esta vibración habla de orden y constancia: todo mejora cuando estructuras prioridades y avanzas paso a paso. Premia disciplina y paciencia; lo estable se construye con decisiones pequeñas sostenidas. Tu llave es coherencia práctica: menos improvisación, más método.",
    5:  "Esta vibración trae cambio y movimiento: te empuja a expandirte y abrir opciones nuevas. Su reto es la dispersión: no todo lo que aparece es para ti. Creces cuando eliges el cambio con conciencia, soltando rigidez con dirección clara.",
    6:  "Esta vibración se asocia con cuidado y amor consciente. Invita a equilibrar lo personal con lo familiar y a sostener vínculos con madurez. La lección es dar sin vaciarte: límites sanos también son amor. Tu estabilidad emocional es tu base.",
    7:  "Esta vibración pide un momento sabio de observación: comprender y escuchar la voz interna. La claridad no viene de la prisa, sino de la profundidad. Es un tiempo ideal para estudiar patrones, ordenar pensamientos y fortalecer intuición con calma.",
    8:  "Esta vibración activa logro y materialización: pide decisiones estratégicas y administración consciente de recursos. La lección es ética y coherencia: el poder personal se sostiene cuando está alineado con valores. Ordena prioridades y verás estabilidad.",
    9:  "Esta vibración marca cierre e integración: invita a soltar lo que ya cumplió su función y quedarte con el aprendizaje. Favorece limpieza interna y madurez emocional. Cerrar con conciencia aligera la energía y abre un rumbo más coherente.",
    11: "Esta vibración amplifica intuición e inspiración: te vuelve más sensible y perceptiva. Es un tiempo para escuchar señales internas y evitar dispersión emocional. Cuando actúas desde tu verdad, la claridad aparece y tu intuición se vuelve dirección.",
    22: "Esta vibración une visión y construcción: no basta soñar, toca estructurar. Favorece proyectos grandes con pasos concretos y disciplina a largo plazo. Si te enfocas, materializas algo sólido con impacto real.",
    33: "Esta vibración se orienta al amor consciente y al servicio con madurez emocional. Invita a acompañar sin rescatar y a dar sin vaciarte. Tu sensibilidad se vuelve fortaleza cuando hay límites, estructura y autocuidado.",
}

def lectura_resumida(num: int) -> str:
    return LECTURA_RESUMIDA.get(num, "Lectura no disponible para esta vibración.")

# =====================================================
# PINÁCULO + ARCANO (micro)
# =====================================================
def pinaculo_micro(pin: dict) -> str:
    b1, b2, b3 = pin["base"]
    m1, m2 = pin["medio"]
    cima = pin["cima"]
    return (
        f"Tu pináculo muestra cómo se ordena tu crecimiento por etapas: la base ({b1}, {b2}, {b3}) describe aprendizajes que te forman; "
        f"el nivel medio ({m1}, {m2}) revela el punto donde se afina tu carácter; y la cima ({cima}) marca la síntesis de tu fuerza interna. "
        "Úsalo como brújula: cuando alineas hábitos y decisiones con esta estructura, avanzas con más dirección y menos desgaste."
    )

ARCANOS_RESUMIDOS = {
    1: "Inicio consciente: una decisión clara abre camino.",
    2: "Escucha interior: la respuesta se forma desde adentro.",
    3: "Creatividad: nutre lo que está creciendo.",
    4: "Orden: estructura y límites te devuelven estabilidad.",
    5: "Aprendizaje: elige desde valores, no desde presión.",
    6: "Elección: coherencia entre deseo y verdad.",
    7: "Dirección: enfoque y disciplina para avanzar.",
    8: "Equilibrio: ordena lo pendiente con honestidad.",
    9: "Introspección: comprender primero mejora tu decisión.",
    10: "Cambio: adaptarte te abre oportunidades.",
    11: "Fortaleza: calma interna por encima de la reacción.",
    12: "Nueva mirada: cambia el ángulo y aparece la salida.",
    13: "Transformación: cerrar a tiempo libera espacio.",
    14: "Armonía: ajusta extremos y cuida tu ritmo.",
    15: "Conciencia: reconoce lo que ata para recuperar poder.",
    16: "Ruptura: cae lo falso para reconstruir con verdad.",
    17: "Esperanza: guía interna y visión más amable.",
    18: "Sensibilidad: cuida emociones, evita decidir por miedo.",
    19: "Claridad: vitalidad y confianza para avanzar.",
    20: "Renacer: cierre consciente y elección con propósito.",
    21: "Integración: culminación y preparación del siguiente ciclo.",
    22: "Apertura: comienza con confianza y presencia.",
}

def arcano_micro(arc: int) -> str:
    return ARCANOS_RESUMIDOS.get(arc, "Mensaje no disponible.")

# =====================================================
# PDF helper
# =====================================================
def build_pdf_bytes(titulo: str, secciones: list[tuple[str, str]]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    _, height = LETTER
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
# CLAVE (estable, reutilizable infinitamente)
# =====================================================
def normalizar_clave_nombre(txt: str) -> str:
    txt = unicodedata.normalize("NFD", str(txt))
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[^A-Za-z\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip().upper()
    return txt

def generar_clave_unica(nombre_completo: str, fecha_nac: date) -> str:
    # Usa NOMBRE COMPLETO EXACTO (todos los nombres y apellidos)
    nombre_normalizado = normalizar_clave_nombre(nombre_completo)

    payload = f"{nombre_normalizado}|{fecha_nac.isoformat()}".encode("utf-8")

    digest = hmac.new(
        APP_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest().upper()

    core = digest[:16]

    return f"EM-{core[:4]}-{core[4:8]}-{core[8:12]}-{core[12:16]}"

# =====================================================
# TEXTO INTRO
# =====================================================
st.markdown("""
Esta lectura no es una predicción ni una promesa externa.  
Es una orientación energética consciente, basada en la vibración que se activa a partir de tu fecha de nacimiento y tu nombre.  
Cada nombre refleja una frecuencia, y cada frecuencia describe una forma de transitar la vida en este momento.

Aquí no buscamos decirte qué va a pasar, sino ayudarte a comprender qué energía está disponible para ti ahora, cómo se manifiesta internamente y qué tipo de decisiones se alinean mejor con tu proceso actual.  
La numerología, cuando se usa con consciencia, no limita: *ordena, revela y enfoca*.

Esta versión resumida te muestra el núcleo de tu vibración: la energía que te atraviesa, lo que se está moviendo en tu camino y el tipo de aprendizaje que se presenta.  
Es una lectura clara y simbólica, pensada para que puedas *reconocerte*, no para que dependas de ella.

Si algo de lo que lees resuena, no es casualidad: la energía no grita, *reconoce*.  
Y cuando reconoces, recuperas poder personal.

La versión completa profundiza mucho más: explora ciclos, capas internas y patrones que se repiten, para ayudarte a recordar con claridad, sostener tu rumbo y elegir con presencia.

✨ Esta lectura no te quita responsabilidad: te la devuelve.  
Tómala como una brújula, no como un destino.
""")

# =====================================================
# INPUTS
# =====================================================
col1, col2 = st.columns(2)
with col1:
    fecha_nac = st.date_input(
        "Fecha de nacimiento",
        min_value=date(1940, 1, 1),
        max_value=date(2040, 12, 31),
        value=date(1990, 1, 1),
    )
with col2:
    nombre = st.text_input(
        "Nombre completo (máx. 40 caracteres)",
        max_chars=40,
        value="",
        placeholder="Ej: Eugenia Mystikos"
    )

calcular = st.button("✨ Ver mi lectura ahora")
hoy = date.today()


# =====================================================
# CÁLCULOS (se calculan siempre)
# =====================================================
es = esencia(fecha_nac)
mis = sendero_vida(fecha_nac)
vp = vida_pasada(fecha_nac)

ap = ano_personal(fecha_nac, hoy.year)
mp = mes_personal(ap, hoy.month)
sp = semana_personal(mp, hoy.isocalendar()[1])
dp = dia_personal(mp, hoy.day)

arc = arcano_semanal()
pin = pinaculo_piramide(fecha_nac)
num_nombre = numero_nombre(nombre) if nombre.strip() else 0

# =====================================================
# MOSTRAR RESUMIDA SOLO AL PRESIONAR BOTÓN
# =====================================================
if calcular:
    incrementar_contador()
    with st.container():

         st.markdown("### ✨ Tu lectura resumida")

         st.write(f"Mi esencia — Número {es}")
         st.write(lectura_resumida(es))

         st.write(f"Mi nombre completo — Número {num_nombre if num_nombre else '—'}")
         if num_nombre:
          st.write(lectura_resumida(num_nombre))
         else:
           st.info("Escribe tu nombre completo para ver la energía de tu nombre.")

         st.write(f"Mi misión — Número {mis}")
         st.write(lectura_resumida(mis))

         st.write(f"Mi año personal ({hoy.year}) — Número {ap}")
         st.write(lectura_resumida(ap))

         st.write(f"Mi energía de hoy — Número {dp}")
         st.write(lectura_resumida(dp))

         st.write("Mi pináculo (pirámide completa)")
         st.write(f"Base: {pin['base']} | Medio: {pin['medio']} | Cima: {pin['cima']}")
         st.write(pinaculo_micro(pin))

         st.write(f"Arcano semanal — Número {arc}")
         st.write(arcano_micro(arc))

    # PDF Resumido
    pdf_resumido = build_pdf_bytes(
        f"{APP_TITLE} · Versión Resumida · {BRAND}",
        [
            ("Datos", f"Nombre: {nombre or '—'}\nFecha de nacimiento: {fecha_nac}\nGenerado: {hoy}"),
            ("Mi esencia", f"Número {es}\n\n{lectura_resumida(es)}"),
            ("Mi nombre completo", f"Número {num_nombre if num_nombre else '—'}\n\n{lectura_resumida(num_nombre) if num_nombre else 'Escribe tu nombre completo para ver esta sección.'}"),
            ("Mi misión", f"Número {mis}\n\n{lectura_resumida(mis)}"),
            ("Mi año personal", f"Número {ap}\n\n{lectura_resumida(ap)}"),
            ("Mi energía de hoy", f"Número {dp}\n\n{lectura_resumida(dp)}"),
            ("Mi pináculo (pirámide completa)", f"Base: {pin['base']} | Medio: {pin['medio']} | Cima: {pin['cima']}\n\n{pinaculo_micro(pin)}"),
            ("Arcano semanal", f"Número {arc}\n\n{arcano_micro(arc)}"),
        ]
    )

    st.download_button(
        "⬇️ Descargar PDF (Versión Resumida)",
        data=pdf_resumido,
        file_name=f"Lectura_Numerologica_Resumida_{BRAND}.pdf",
        mime="application/pdf",
    )
else:
    st.caption("Tip: completa tu nombre y fecha, luego toca el botón para ver tu lectura.")

    # =====================================================
# PANEL ADMIN (OCULTO POR PIN) - SOLO AQUÍ SE VE CONTADOR Y GENERADOR
# =====================================================
if ADMIN_PIN:
    with st.expander("🔐 Eugenia Mstikos", expanded=False):
        pin_ingresado = st.text_input("PIN de administración", type="password")
        if pin_ingresado:
            if pin_ingresado == ADMIN_PIN:
                st.success("Acceso concedido ✅")
                st.info(f"📊 Uso interno · Total activaciones resumida: {leer_contador()}")
                if nombre.strip():
                    st.caption("Clave del cliente (según nombre+fecha actuales):")
                    st.code(generar_clave_unica(nombre, fecha_nac), language="text")
            else:
                st.error("PIN incorrecto")


# =====================================================
# VERSIÓN COMPLETA (CLIENTE) - BLOQUEO POR CLAVE
# =====================================================
st.markdown("---")
st.markdown("🔒 *Versión Completa (PDF personalizado)*")
st.write("Desbloquea tu lectura completa con tu clave personal.")

clave_ingresada = st.text_input("Introduce tu clave personal", type="password").strip().upper()
if clave_ingresada:
    st.success("Versión completa desbloqueada ✅")
  

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
        p3 = ("La recomendación práctica es sostener presencia: menos impulsividad y más intención. "
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
    # UI – VERSIÓN COMPLETA
    # =====================================================
    st.markdown("## 💎 Lectura Completa")

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

    # PDF COMPLETO
    secciones_completa = [
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

    pdf_completa = build_pdf_bytes(
        f"{APP_TITLE} · Versión Completa · {BRAND}",
        secciones_completa
    )

    st.download_button(
        "⬇️ Descargar PDF (Versión Completa)",
        data=pdf_completa,
        file_name=f"Lectura_Numerologica_Completa_{BRAND}.pdf",
        mime="application/pdf",
    )

st.caption(f"{BRAND} · Lectura Numerológica")



