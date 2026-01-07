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
        # En Streamlit Cloud a veces el FS es de solo lectura
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
# TEXTOS RESUMIDOS (base)
# =====================================================
LECTURA_RESUMIDA = {
    1:  "Este año marca un renacer personal. La vida te coloca frente a decisiones que no pueden seguir postergándose. Se activa el fuego del inicio, la valentía de decir “sí” a lo nuevo y “no” a lo que ya no vibra contigo. Todo te empuja a tomar liderazgo sobre tu propia historia. No esperes señales externas: la señal eres tú. Lo que comiences ahora define el tono de los próximos años. Este es un año para actuar con claridad, coraje y propósito. La energía te respalda cuando confías en tu impulso interior.",
    2:  "Este año te invita a afinar la sensibilidad y profundizar los vínculos. La vida te enseña que no todo se logra empujando: algunas cosas florecen cuando aprendes a escuchar. Se activa la energía de la cooperación, la paciencia y la armonía. Es un ciclo para sanar relaciones, equilibrar emociones y reconocer que la verdadera fortaleza también sabe esperar. El crecimiento llega cuando honras los ritmos naturales y eliges la paz sin perderte a ti.",
    3:  "Este año despierta tu voz auténtica y tu creatividad. La energía te empuja a expresarte, a mostrarte y a disfrutar más del proceso de vivir. Se abre un ciclo donde la alegría no es superficial, sino medicina. Todo lo que comunicas tiene impacto, por eso es importante hablar desde la verdad. Es un año para crear, compartir, conectar y permitir que tu luz sea vista. Cuando te permites ser tú, la vida responde con expansión.",
    4:  "Este año te pide orden, estructura y compromiso contigo misma. No es un ciclo de velocidad, sino de construcción consciente. La energía te invita a poner bases sólidas para el futuro, incluso si eso requiere disciplina y constancia. Cada paso cuenta, aunque no lo veas de inmediato. Es un año para materializar con paciencia, organizar prioridades y fortalecer lo que realmente importa. Lo que edificas ahora tiene raíces profundas.",
    5:  "Este año trae cambio, movimiento y liberación. La vida sacude lo que estaba estancado y te invita a salir de lo conocido. Se activa una energía inquieta que pide experiencias nuevas, decisiones valientes y flexibilidad. Resistirse solo genera tensión: fluir abre caminos inesperados. Es un año para reinventarte, viajar interna o externamente, y recordar que la libertad también es una elección consciente.",
    6:  "Este año el foco está en el corazón, el cuidado y la responsabilidad emocional. La energía te lleva a revisar vínculos, compromisos y la forma en que das y recibes amor. Es un ciclo de sanación afectiva, donde se te pide equilibrio entre cuidar a otros y cuidarte a ti. El hogar interno se vuelve prioridad. Cuando eliges desde el amor consciente, todo se ordena con mayor armonía.",
    7:  "Este año te conduce hacia un viaje interior profundo. La vida baja el ruido externo para que puedas escuchar tu sabiduría interna. Se activa la introspección, la búsqueda de sentido y la conexión espiritual. No es un año para forzar resultados, sino para comprender procesos. El silencio se vuelve aliado. Las respuestas llegan cuando confías en tu intuición y honras tus tiempos internos.",
    8:  "Este año activa el poder personal, la autoridad interna y la manifestación. La energía te confronta con temas de merecimiento, límites y abundancia. Es un ciclo para tomar control consciente de tu vida material y emocional. El éxito llega cuando actúas con integridad y coherencia. Es un año para asumir tu fuerza sin culpa y reconocer el valor real de lo que aportas al mundo.",
    9:  "Este año marca un cierre de ciclo profundo. La vida te invita a soltar lo que ya cumplió su función: relaciones, patrones, historias y cargas emocionales. Es un año de limpieza, perdón y liberación. No se trata de pérdida, sino de preparación para un nuevo comienzo. Al dejar ir, recuperas energía vital. La sabiduría adquirida es tu mayor tesoro.",
    11: "Este año despierta una conciencia elevada y una sensibilidad espiritual intensa. La energía te convierte en canal de inspiración, intuición y guía. Puedes sentir todo más fuerte, pero también ver más claro. Es un año para confiar en tu percepción, cuidar tu energía y honrar tu luz. Cuando te alineas con tu verdad, impactas más de lo que imaginas.",
    22: "Este año activa la energía del gran constructor. La visión se une a la acción y te pide materializar algo con propósito colectivo. No es un ciclo liviano: implica responsabilidad, compromiso y enfoque. Pero también ofrece la posibilidad de crear algo duradero y significativo. Cuando alineas intención y acción, puedes dejar huella real en el mundo.",
    33: "Este año se orienta al amor consciente y al servicio con madurez emocional. Invita a acompañar sin rescatar y a dar sin vaciarte. Tu sensibilidad se vuelve fortaleza cuando hay límites, estructura y autocuidado.",
}

def lectura_resumida(num: int) -> str:
    return LECTURA_RESUMIDA.get(num, "Lectura no disponible para esta vibración.")

# =====================================================
#  (AMOR / DINERO / EMOCIONAL / PROTECCIÓN)
# Basadas en tu Año Personal (ap)
# =====================================================
FRASES_AMOR = {
    1:"Amor: inicia desde ti; el vínculo correcto nace cuando eliges con valentía y dejas de mendigar señales.",
    2:"Amor: escucha y suaviza; lo que crece en silencio se vuelve sólido cuando hay respeto y paciencia.",
    3:"Amor: habla claro; tu encanto abre puertas, pero tu verdad sostiene lo que merece quedarse.",
    4:"Amor: construye con hechos; promesas sin estructura se caen, límites sanos se quedan.",
    5:"Amor: cambia la dinámica; si te sientes atrapada, es hora de reinventar la manera de amar.",
    6:"Amor: cuida sin cargarte; equilibrio entre dar y recibir es la medicina del vínculo.",
    7:"Amor: baja el ruido; la intuición muestra quién suma paz y quién consume energía.",
    8:"Amor: merecimiento; el vínculo se ordena cuando tú te valoras y sostienes tu lugar.",
    9:"Amor: cierre limpio; lo que termina te libera para amar con más conciencia.",
    11:"Amor: sensibilidad elevada; protege tu energía, elige vínculos que honren tu luz.",
    22:"Amor: proyecto en común; el vínculo crece cuando hay visión, madurez y acuerdos reales.",
    33:"Amor: amor consciente; acompaña sin salvar y ama sin vaciarte."
}
FRASES_DINERO = {
    1:"Dinero: actúa y decide; este año premia el liderazgo y castiga la duda eterna.",
    2:"Dinero: alianza y paciencia; creces más si negocias con calma y construyes relaciones.",
    3:"Dinero: visibilidad; comunicar y mostrar tu talento abre oportunidades y expansión.",
    4:"Dinero: estructura; presupuesto, orden y disciplina convierten esfuerzo en estabilidad.",
    5:"Dinero: movimiento; diversifica, prueba, adapta: la rigidez aquí se rompe.",
    6:"Dinero: responsabilidad; prosperas cuando cuidas compromisos y pones precio a tu entrega.",
    7:"Dinero: estrategia; menos impulso, más análisis: invertir en conocimiento rinde.",
    8:"Dinero: poder y abundancia; liderazgo con ética = resultados reales.",
    9:"Dinero: cierre y depuración; suelta fugas y deudas emocionales para liberar flujo.",
    11:"Dinero: inspiración con enfoque; baja ideas a plan y sostén tu energía.",
    22:"Dinero: construcción grande; visión + método = legado material sostenible.",
    33:"Dinero: servicio consciente; prosperas cuando tu aporte transforma y tiene límites."
}
FRASES_EMOCIONAL = {
    1:"Emocional: reafirma tu voz; no te traiciones por encajar.",
    2:"Emocional: regula y escucha; tu calma es tu superpoder.",
    3:"Emocional: expresa sin drama; lo que nombras se ordena.",
    4:"Emocional: estabilidad; rutina y límites te devuelven centro.",
    5:"Emocional: libertad; el cambio es medicina si lo eliges con conciencia.",
    6:"Emocional: corazón; aprende a cuidar sin cargarte.",
    7:"Emocional: introspección; tu alma pide silencio y claridad.",
    8:"Emocional: fuerza; no confundas control con seguridad: elige coherencia.",
    9:"Emocional: cierre; perdonar es liberar energía, no justificar.",
    11:"Emocional: sensibilidad; filtra ambientes y respira antes de decidir.",
    22:"Emocional: responsabilidad; madurez afectiva para sostener lo grande.",
    33:"Emocional: compasión; amor con límites para no agotarte."
}
FRASES_PROTECCION = {
    1:"Protección: corta lo tibio; tu energía se protege cuando dices ‘no’ sin culpa.",
    2:"Protección: límites suaves; no todo merece acceso a tu intimidad.",
    3:"Protección: palabra consciente; evita prometer desde emoción, elige claridad.",
    4:"Protección: orden y tierra; tu rutina es tu escudo energético.",
    5:"Protección: evita excesos; libertad sí, caos no.",
    6:"Protección: hogar interno; cuida tu descanso, tu cuerpo y tus vínculos.",
    7:"Protección: silencio; menos exposición, más intuición.",
    8:"Protección: autoridad; protege tu valor y tu tiempo como oro.",
    9:"Protección: limpieza; suelta culpas, cierra puertas con dignidad.",
    11:"Protección: alta vibración; filtra personas y ambientes, elige lo sagrado.",
    22:"Protección: enfoque; grandes metas requieren límites firmes.",
    33:"Protección: amor consciente; dar con estructura, no desde sacrificio."
}

def frase_categoria(dic: dict, num: int) -> str:
    return dic.get(num, "Mensaje no disponible para esta vibración.")

# =====================================================
# TEXTOS PROFUNDOS (10–12 líneas aprox)
# Basados en tu Año Personal (ap) y modulados por mp/sp/dp
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

def parrafo_premium_categoria(ap: int, mp: int, sp: int, dp: int, categoria: str) -> str:
    a, b, c = NUM_RASGOS.get(ap, ("equilibrio", "conciencia", "claridad"))

    base = (
        f"En {categoria}, tu ciclo se ordena desde la vibración {ap}: un núcleo de {a} que marca el ritmo principal del año. "
        f"Esto no es teoría: es una energía que se nota en decisiones, personas que aparecen, límites que se piden y oportunidades que solo se abren cuando eliges con presencia."
    )
    detalle = (
        f"Tu Mes Personal {mp} ajusta el clima emocional y práctico de este momento, y tu Semana Personal {sp} revela el tema inmediato que está ‘pidiendo voz’. "
        f"Hoy, con Día Personal {dp}, la vida te muestra en pequeño lo que debes practicar en grande: coherencia, enfoque y verdad."
    )
    guia = (
        f"La llave está en refinar tu {b} y tu {c}: no reaccionar, sino decidir. "
        f"Si {categoria.lower()} se siente tenso, no es castigo: es señal de reorden. "
        f"El movimiento correcto es simple: un límite sano, una conversación clara o un hábito que te sostenga. "
        f"Cuando actúas alineada con tu vibración, el resultado se siente: menos desgaste, más paz, y una sensación real de avance."
    )
    return f"{base}\n\n{detalle}\n\n{guia}"

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
    nombre_normalizado = normalizar_clave_nombre(nombre_completo)
    payload = f"{nombre_normalizado}|{fecha_nac.isoformat()}".encode("utf-8")
    digest = hmac.new(APP_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest().upper()
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
La numerología, cuando se usa con consciencia, no limita: ordena, revela y enfoca.

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
# CÁLCULOS
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
# MOSTRAR RESUMIDA (GRATIS) SOLO AL PRESIONAR BOTÓN
# =====================================================
if calcular:
    incrementar_contador()

    with st.container():
        st.markdown("### ✨ Tu lectura resumida")

        # AÑO PERSONAL PRIMERO (más fuerte)
        st.write(f"🔥 Vibración de tu Año Personal ({hoy.year}) — Número {ap}")
        st.write(lectura_resumida(ap))
        st.markdown(
            "Este año funciona como tu campo de experiencia principal: ordena decisiones, cierres y oportunidades. "
            "Si actúas alineada con esta vibración, la vida se vuelve más clara: menos fricción, más coherencia, y un rumbo interno más firme."
        )

        st.write(f"Mi esencia — Número {es}")
        st.write(lectura_resumida(es))

        st.write(f"Mi nombre completo — Número {num_nombre if num_nombre else '—'}")
        if num_nombre:
            st.write(lectura_resumida(num_nombre))
        else:
            st.info("Escribe tu nombre completo para ver la energía de tu nombre.")

        st.write(f"Mi misión — Número {mis}")
        st.write(lectura_resumida(mis))

        st.write(f"Mi energía de hoy — Número {dp}")
        st.write(lectura_resumida(dp))

        # ✅ AQUÍ VAN LOS 4 BLOQUES CORTOS GRATIS (lo que me pediste)
        st.markdown("#### 💡 Pronóstico clave (gratis)")
        st.write(frase_categoria(FRASES_AMOR, ap))
        st.write(frase_categoria(FRASES_DINERO, ap))
        st.write(frase_categoria(FRASES_EMOCIONAL, ap))
        st.write(frase_categoria(FRASES_PROTECCION, ap))

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
            ("Año personal", f"Número {ap}\n\n{lectura_resumida(ap)}\n\n"
                            "Este año funciona como tu campo de experiencia principal: ordena decisiones, cierres y oportunidades. "
                            "Si actúas alineada con esta vibración, la vida se vuelve más clara: menos fricción, más coherencia."),
            ("Mi esencia", f"Número {es}\n\n{lectura_resumida(es)}"),
            ("Mi nombre completo", f"Número {num_nombre if num_nombre else '—'}\n\n{lectura_resumida(num_nombre) if num_nombre else 'Escribe tu nombre completo para ver esta sección.'}"),
            ("Mi misión", f"Número {mis}\n\n{lectura_resumida(mis)}"),
            ("Mi energía de hoy", f"Número {dp}\n\n{lectura_resumida(dp)}"),
            ("Pronóstico clave (gratis)",
             f"{frase_categoria(FRASES_AMOR, ap)}\n{frase_categoria(FRASES_DINERO, ap)}\n{frase_categoria(FRASES_EMOCIONAL, ap)}\n{frase_categoria(FRASES_PROTECCION, ap)}"),
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
    with st.expander("🔐 Eugenia Mystikos (Admin)", expanded=False):
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
# VERSIÓN COMPLETA - BLOQUEO POR CLAVE + NOMBRE + FECHA
# =====================================================
st.markdown("---")
st.markdown("🔒 *Versión Completa (Premium + PDF personalizado)*")
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
    type="password"
).strip().upper()

if clave_ingresada:
    if not nombre_compra.strip():
        st.warning("Escribe tu nombre tal como aparece en tu compra.")
        st.stop()

    if not fecha_compra:
        st.warning("Debes indicar la fecha de nacimiento usada en tu compra.")
        st.stop()

    clave_esperada = generar_clave_unica(nombre_compra, fecha_compra)

    if clave_ingresada != clave_esperada:
        st.error("Clave inválida. Verifica que tu nombre y fecha estén EXACTAMENTE como en tu compra.")
        st.stop()

    st.success("Versión completa desbloqueada ✅")

    # ✅ Forzar datos validados
    nombre_validado = nombre_compra.strip()
    fecha_validada = fecha_compra

    # Recalcular TODO
    es_p = esencia(fecha_validada)
    mis_p = sendero_vida(fecha_validada)
    vp_p = vida_pasada(fecha_validada)

    ap_p = ano_personal(fecha_validada, hoy.year)
    mp_p = mes_personal(ap_p, hoy.month)
    sp_p = semana_personal(mp_p, hoy.isocalendar()[1])
    dp_p = dia_personal(mp_p, hoy.day)

    arc_p = arcano_semanal()
    pin_p = pinaculo_piramide(fecha_validada)
    num_nombre_p = numero_nombre(nombre_validado) if nombre_validado else 0

    # Inputs extra premium (teléfono / dirección)
    st.markdown("### 📌 Datos opcionales Premium")
    cA, cB = st.columns(2)
    with cA:
        telefono = st.text_input("Teléfono (opcional)", value="", placeholder="Ej: +58 412 000 0000")
    with cB:
        direccion_apto = st.text_input("Dirección / Apto (opcional)", value="", placeholder="Ej: Torre A, Apto 12B")

    num_tel = numero_apto(telefono) if telefono.strip() else 0
    num_dir = numero_apto(direccion_apto) if direccion_apto.strip() else 0

    # =====================================================
    # UI – VERSIÓN COMPLETA
    # =====================================================
    st.markdown("## 💎 Lectura Completa")

    st.markdown("### 1) Esencia")
    st.write(f"Número {es_p}")
    st.write(parrafo_premium_categoria(es_p, mp_p, sp_p, dp_p, "Esencia"))

    st.markdown("### 2) Misión / Sendero de vida")
    st.write(f"Número {mis_p}")
    st.write(parrafo_premium_categoria(mis_p, mp_p, sp_p, dp_p, "Misión"))

    st.markdown("### 3) Vida pasada")
    st.write(f"Número {vp_p}")
    st.write(parrafo_premium_categoria(vp_p, mp_p, sp_p, dp_p, "Vida pasada"))

    st.markdown("### 4) Año personal")
    st.write(f"Número {ap_p}")
    st.write(parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Año personal"))

    st.markdown("### 5) Mes personal")
    st.write(f"Número {mp_p}")
    st.write(parrafo_premium_categoria(mp_p, mp_p, sp_p, dp_p, "Mes personal"))

    st.markdown("### 6) Semana personal")
    st.write(f"Número {sp_p}")
    st.write(parrafo_premium_categoria(sp_p, mp_p, sp_p, dp_p, "Semana personal"))

    st.markdown("### 7) Día personal")
    st.write(f"Número {dp_p}")
    st.write(parrafo_premium_categoria(dp_p, mp_p, sp_p, dp_p, "Día personal"))

    # ✅ AQUÍ VA TU BLOQUE PREMIUM (amor/dinero/emocional/protección)
    st.markdown("## ✨ Premium: Amor, Dinero, Emoción y Protección")
    st.markdown("### 💗 Amor y vínculos")
    st.write(parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Amor y vínculos"))

    st.markdown("### 💰 Dinero y prosperidad")
    st.write(parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Dinero y prosperidad"))

    st.markdown("### 🌊 Energía emocional")
    st.write(parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Energía emocional"))

    st.markdown("### 🛡️ Protección energética")
    st.write(parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Protección energética"))

    # ✅ Teléfono y dirección (como tú pediste, vuelve)
    st.markdown("## 📞🏠 Vibraciones de Teléfono y Hogar")
    if num_tel:
        st.markdown(f"### Teléfono — Número {num_tel}")
        st.write(parrafo_premium_categoria(num_tel, mp_p, sp_p, dp_p, "Teléfono"))
    else:
        st.info("Si deseas, agrega un teléfono para activar esta sección.")

    if num_dir:
        st.markdown(f"### Dirección / Apto — Número {num_dir}")
        st.write(parrafo_premium_categoria(num_dir, mp_p, sp_p, dp_p, "Hogar / Dirección"))
    else:
        st.info("Si deseas, agrega tu dirección o número de apto para activar esta sección.")

    st.markdown("### 8) Arcano mayor de la semana")
    st.write(f"Arcano {arc_p}")
    st.write(arcano_micro(arc_p))

    st.markdown("### 9) Pináculo (pirámide completa)")
    st.write(f"Base: {pin_p['base']} | Medio: {pin_p['medio']} | Cima: {pin_p['cima']}")
    st.write(pinaculo_micro(pin_p))

    # PDF COMPLETO
    secciones_completa = [
        ("Datos", f"Nombre: {nombre_validado or '—'}\nFecha de nacimiento: {fecha_validada}\nGenerado: {hoy}"),
        ("Esencia", f"Número {es_p}\n\n{parrafo_premium_categoria(es_p, mp_p, sp_p, dp_p, 'Esencia')}"),
        ("Misión / Sendero", f"Número {mis_p}\n\n{parrafo_premium_categoria(mis_p, mp_p, sp_p, dp_p, 'Misión')}"),
        ("Vida pasada", f"Número {vp_p}\n\n{parrafo_premium_categoria(vp_p, mp_p, sp_p, dp_p, 'Vida pasada')}"),
        ("Año personal", f"Número {ap_p}\n\n{parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, 'Año personal')}"),
        ("Mes personal", f"Número {mp_p}\n\n{parrafo_premium_categoria(mp_p, mp_p, sp_p, dp_p, 'Mes personal')}"),
        ("Semana personal", f"Número {sp_p}\n\n{parrafo_premium_categoria(sp_p, mp_p, sp_p, dp_p, 'Semana personal')}"),
        ("Día personal", f"Número {dp_p}\n\n{parrafo_premium_categoria(dp_p, mp_p, sp_p, dp_p, 'Día personal')}"),
        ("Premium: Amor y vínculos", parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Amor y vínculos")),
        ("Premium: Dinero y prosperidad", parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Dinero y prosperidad")),
        ("Premium: Energía emocional", parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Energía emocional")),
        ("Premium: Protección energética", parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Protección energética")),
        ("Teléfono", f"Número {num_tel if num_tel else '—'}\n\n{parrafo_premium_categoria(num_tel, mp_p, sp_p, dp_p, 'Teléfono') if num_tel else 'No se ingresó teléfono.'}"),
        ("Dirección / Apto", f"Número {num_dir if num_dir else '—'}\n\n{parrafo_premium_categoria(num_dir, mp_p, sp_p, dp_p, 'Hogar / Dirección') if num_dir else 'No se ingresó dirección/apto.'}"),
        ("Arcano semanal", f"Arcano {arc_p}\n\n{arcano_micro(arc_p)}"),
        ("Pináculo (pirámide completa)", f"Base: {pin_p['base']} | Medio: {pin_p['medio']} | Cima: {pin_p['cima']}\n\n{pinaculo_micro(pin_p)}"),
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

