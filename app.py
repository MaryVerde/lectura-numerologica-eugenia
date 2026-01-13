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

if "premium_activo" not in st.session_state:
    st.session_state.premium_activo = False

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
A# ==============================================
# CONFIGURACIÓN GENERAL
# ==============================================

# ==============================================
# CONFIGURACIÓN GENERAL
# ==============================================

APP_TITLE = "🔮 Lectura Numerológica"
BRAND = "Eugenia.Mystikos"

st.set_page_config(
    page_title=f"{APP_TITLE} · {BRAND}",
    page_icon="🔮",
    layout="centered"
)

# --- ESTILO VISUAL (marca en rojo) ---
st.markdown("""
<style>
h1 {
    color: #b11226;
    font-weight: 700;
}
.brand {
    color: #b11226;
    font-weight: 600;
}
.subtitle {
    color: #444444;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

# --- TÍTULO ---
st.markdown(
    "<h1>🔮 Lectura Numerológica · <span class='brand'>Eugenia.Mystikos</span></h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>"
    "Versión Resumida · Interpretación completa disponible en versión Premium (PDF personalizado)"
    "</div>",
    unsafe_allow_html=True
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
# GRATIS: FRASES CORTAS (AMOR / DINERO / EMOCIONAL / PROTECCIÓN)
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
# # 🌅 ENERGÍA DEL DÍA (365 mensajes) — REGALO (EXPRESS)
# =====================================================
ENERGIA_DIA_365 = {
    1: "Hoy no apresures nada. La energía se ordena cuando eliges presencia en lugar de urgencia.",
    2: "Confía en tu ritmo. No todo florece el mismo día, pero todo responde a la intención correcta.",
    3: "Lo que hoy parece pequeño está sembrando una verdad más grande.",
    4: "Respira antes de decidir. La claridad llega cuando el cuerpo se relaja.",
    5: "No te adaptes a lo que te apaga. Ajusta el entorno, no tu esencia.",
    6: "Hoy es un buen día para poner un límite amoroso.",
    7: "El silencio también es una respuesta sabia.",
    8: "Suelta el control: lo verdadero no necesita ser forzado.",
    9: "Hoy honra lo que ya lograste. Reconocer tu avance cambia la energía.",
    10: "La coherencia vale más que la velocidad.",
    11: "Tu sensibilidad es una brújula, no una debilidad.",
    12: "Escucha lo que incomoda: ahí hay información valiosa.",
    13: "Cerrar a tiempo también es un acto de amor propio.",
    14: "Hoy elige con calma, incluso si otros apuran.",
    15: "No todo merece tu energía. Sé selectiva.",
    16: "La verdad se sostiene sola. No la justifiques.",
    17: "Hoy el cuerpo sabe más que la mente.",
    18: "Avanza un paso real, no diez imaginarios.",
    19: "Tu intuición está clara cuando no la discutes.",
    20: "Orden externo, paz interna.",
    21: "Hoy se afloja una carga que no era tuya.",
    22: "Confía: lo que se acomoda hoy libera futuro.",
    23: "No te traiciones para evitar conflicto.",
    24: "La energía responde a la honestidad.",
    25: "Descansar también es avanzar.",
    26: "Hoy elige lo simple. Ahí está la fuerza.",
    27: "No rescates procesos ajenos.",
    28: "Tu claridad inspira sin que hables.",
    29: "Hoy es mejor decir menos y sentir más.",
    30: "La estabilidad se construye con decisiones pequeñas.",
    31: "Cierra el mes soltando expectativas irreales.",
    32: "Hoy tu energía pide enfoque, no dispersión.",
    33: "Elegir paz no es rendirse.",
    34: "No negocies lo esencial.",
    35: "La vida te responde cuando te alineas.",
    36: "Hoy se ordena algo interno si no lo fuerzas.",
    37: "Observa sin juzgar: ahí está la enseñanza.",
    38: "No todo se resuelve hoy, y está bien.",
    39: "Respeta tu proceso aunque otros no lo entiendan.",
    40: "Tu energía vale más que tu explicación.",
    41: "Hoy es día de sostener, no de empujar.",
    42: "Cuando te eliges, todo se reacomoda.",
    43: "No respondas desde la herida.",
    44: "El equilibrio se construye con límites claros.",
    45: "Hoy tu presencia es suficiente.",
    46: "La calma también es poder.",
    47: "No corrijas lo que aún está aprendiendo.",
    48: "Hoy escucha tu cansancio con respeto.",
    49: "Lo que se va libera espacio.",
    50: "Avanza sin ruido, pero con certeza.",
    51: "No prometas desde la emoción.",
    52: "El cuerpo pide verdad, no discurso.",
    53: "Hoy cuida tu energía como algo sagrado.",
    54: "No todo merece respuesta inmediata.",
    55: "Elegir distinto es evolución.",
    56: "La claridad llega cuando dejas de justificar.",
    57: "Hoy honra tus límites.",
    58: "No cargues con lo que no te corresponde.",
    59: "La coherencia se siente.",
    60: "Suelta la expectativa, sostén la intención.",
    61: "Hoy el orden interno es prioridad.",
    62: "Tu energía se expande cuando te respetas.",
    63: "No expliques tu verdad: vívela.",
    64: "Hoy es mejor avanzar lento que dudar rápido.",
    65: "La estabilidad nace de decisiones honestas.",
    66: "No te adaptes a lo que te drena.",
    67: "La vida responde a tu claridad.",
    68: "Hoy escucha sin interrumpirte.",
    69: "El silencio ordena más de lo que crees.",
    70: "Tu intuición está afinada.",
    71: "No todo cierre es pérdida.",
    72: "Hoy suelta la autoexigencia innecesaria.",
    73: "Respeta tus tiempos internos.",
    74: "Elegir calma es elegir poder.",
    75: "No te distraigas de lo importante.",
    76: "Hoy cuida tu energía emocional.",
    77: "La claridad no grita.",
    78: "No rescates procesos que no son tuyos.",
    79: "Tu paz es prioridad.",
    80: "Hoy se ordena algo si no intervienes de más.",
    81: "Avanza con firmeza tranquila.",
    82: "No fuerces acuerdos.",
    83: "El equilibrio se construye.",
    84: "Hoy escucha tu cuerpo.",
    85: "No todo se decide hoy.",
    86: "La coherencia te sostiene.",
    87: "Suelta lo que pesa.",
    88: "Hoy confía en lo que sientes.",
    89: "No te justifiques.",
    90: "La energía responde a tu honestidad.",
    91: "Hoy elige presencia antes que reacción.",
    92: "La claridad se activa cuando dejas de forzar.",
    93: "Hoy confía en lo que ya sabes internamente.",
    94: "No todo requiere respuesta inmediata.",
    95: "Tu energía se ordena cuando te respetas.",
    96: "Hoy menos palabras, más verdad.",
    97: "El equilibrio nace de decisiones pequeñas.",
    98: "Hoy tu cuerpo habla: escúchalo.",
    99: "La calma también es acción.",
    100: "Hoy sostén tu centro sin explicarte.",
    101: "No te disperses: vuelve a lo esencial.",
    102: "Hoy suelta la prisa, no el rumbo.",
    103: "Elegir paz es un acto de poder.",
    104: "Hoy honra tus límites.",
    105: "Lo alineado no se siente pesado.",
    106: "Respira antes de decidir.",
    107: "No cargues lo que no te corresponde.",
    108: "Hoy la coherencia es protección.",
    109: "Avanza sin justificarte.",
    110: "Tu energía responde a tu honestidad.",
    111: "Hoy tu intuición está afinada.",
    112: "No fuerces acuerdos.",
    113: "El orden interno se refleja afuera.",
    114: "Hoy elige calidad, no cantidad.",
    115: "Suelta el control excesivo.",
    116: "Lo simple también es sagrado.",
    117: "Hoy cuida tu energía emocional.",
    118: "No todo se decide hoy.",
    119: "Escucha más de lo que hablas.",
    120: "Tu presencia es suficiente.",
    121: "Hoy el silencio trae claridad.",
    122: "No te traiciones por comodidad.",
    123: "El descanso también es productividad.",
    124: "Hoy avanza sin ruido.",
    125: "Confía en el proceso que ya empezó.",
    126: "Tu centro es tu guía.",
    127: "No expliques lo que ya sentiste.",
    128: "Hoy baja el ritmo conscientemente.",
    129: "Lo verdadero no se apura.",
    130: "Tu paz es prioridad.",
    131: "Hoy observa antes de actuar.",
    132: "No todo requiere intervención.",
    133: "La claridad llega cuando paras.",
    134: "Hoy cuida tus palabras.",
    135: "No cargues expectativas ajenas.",
    136: "El equilibrio se construye.",
    137: "Hoy elige presencia corporal.",
    138: "La calma ordena decisiones.",
    139: "Suelta la necesidad de convencer.",
    140: "Tu energía se reajusta sola.",
    141: "Hoy vuelve a lo esencial.",
    142: "No te disperses emocionalmente.",
    143: "El foco es medicina.",
    144: "Hoy honra tu ritmo interno.",
    145: "No todo merece respuesta.",
    146: "Tu coherencia abre camino.",
    147: "La claridad no grita.",
    148: "Hoy confía sin forzar.",
    149: "Sostén tu verdad con calma.",
    150: "Menos ruido, más centro.",
    151: "Hoy elige estabilidad emocional.",
    152: "No reacciones desde el cansancio.",
    153: "El orden interno se nota.",
    154: "Hoy no te sobreexijas.",
    155: "La pausa es parte del avance.",
    156: "Tu energía se regula con límites.",
    157: "Hoy respira conscientemente.",
    158: "No fuerces resultados.",
    159: "El cuerpo marca el camino.",
    160: "Hoy sostén tu eje.",
    161: "No te adelantes al proceso.",
    162: "Hoy escucha sin defenderte.",
    163: "La serenidad es poder.",
    164: "No todo es urgente.",
    165: "Hoy elige claridad interna.",
    166: "Suelta la autoexigencia.",
    167: "La calma te ordena.",
    168: "Hoy cuida tu energía vital.",
    169: "No cargues lo innecesario.",
    170: "Tu centro te sostiene.",
    171: "Hoy confía en el paso presente.",
    172: "No todo se resuelve hoy.",
    173: "La coherencia te protege.",
    174: "Hoy elige sobriedad emocional.",
    175: "No te pierdas por complacer.",
    176: "El silencio también comunica.",
    177: "Hoy baja expectativas externas.",
    178: "Tu energía se afina sola.",
    179: "El equilibrio es práctica diaria.",
    180: "Hoy sostén lo que es real.",
    181: "No fuerces conversaciones.",
    182: "Hoy prioriza tu estabilidad.",
    183: "La claridad se construye.",
    184: "No tomes decisiones cansada.",
    185: "Hoy honra tu intuición.",
    186: "La calma es dirección.",
    187: "No te expliques de más.",
    188: "Hoy elige sencillez.",
    189: "Tu energía pide orden.",
    190: "Suelta lo que pesa.",
    191: "Hoy vuelve a tu cuerpo.",
    192: "No persigas respuestas.",
    193: "La presencia es suficiente.",
    194: "Hoy cuida tus límites.",
    195: "No cargues culpas ajenas.",
    196: "El centro se recupera.",
    197: "Hoy actúa con mesura.",
    198: "La calma estabiliza.",
    199: "No todo se explica.",
    200: "Hoy elige coherencia.",
    201: "Respeta tu energía.",
    202: "No te fuerces a rendir.",
    203: "La claridad llega sola.",
    204: "Hoy baja el ruido mental.",
    205: "No te disperses emocionalmente.",
    206: "El equilibrio es interno.",
    207: "Hoy confía en tu proceso.",
    208: "No todo se comparte.",
    209: "La sobriedad protege.",
    210: "Hoy vuelve a tu eje.",
    211: "No te adelantes.",
    212: "La pausa es sabia.",
    213: "Hoy escucha tu cuerpo.",
    214: "No cargues tensiones viejas.",
    215: "El presente basta.",
    216: "Hoy elige calma.",
    217: "No reacciones por hábito.",
    218: "Tu energía se regula.",
    219: "La claridad no se fuerza.",
    220: "Hoy sostén tu verdad.",
    221: "No te pierdas en ruido externo.",
    222: "Hoy cuida tu centro.",
    223: "El equilibrio se siente.",
    224: "No todo es prioridad.",
    225: "Hoy baja el ritmo.",
    226: "La calma es estrategia.",
    227: "No te disperses.",
    228: "Hoy respira profundo.",
    229: "La coherencia ordena.",
    230: "Tu energía responde.",
    231: "No fuerces soluciones.",
    232: "Hoy elige presencia.",
    233: "El silencio aclara.",
    234: "No todo se resuelve hoy.",
    235: "Hoy confía en tu centro.",
    236: "La calma guía.",
    237: "No cargues expectativas.",
    238: "Hoy sostén tu eje.",
    239: "La sobriedad es fuerza.",
    240: "Tu energía se ordena.",
    241: "No te disperses mentalmente.",
    242: "Hoy prioriza lo esencial.",
    243: "El equilibrio se construye.",
    244: "No fuerces ritmos.",
    245: "Hoy escucha más.",
    246: "La presencia sana.",
    247: "No cargues tensiones.",
    248: "Hoy elige coherencia.",
    249: "La calma sostiene.",
    250: "Tu centro es guía.",
    251: "No todo se decide hoy.",
    252: "Hoy baja la exigencia.",
    253: "El silencio protege.",
    254: "No reacciones automáticamente.",
    255: "Hoy honra tu cuerpo.",
    256: "La claridad llega.",
    257: "No fuerces respuestas.",
    258: "Hoy confía en ti.",
    259: "El equilibrio se afina.",
    260: "Tu energía responde.",
    261: "No cargues lo innecesario.",
    262: "Hoy elige calma interna.",
    263: "La coherencia guía.",
    264: "No te disperses.",
    265: "Hoy respira profundo.",
    266: "La sobriedad ordena.",
    267: "No fuerces procesos.",
    268: "Hoy sostén tu centro.",
    269: "La presencia basta.",
    270: "Tu energía se alinea.",
    271: "No te adelantes.",
    272: "Hoy cuida tu ritmo.",
    273: "El silencio aclara.",
    274: "No cargues ruido.",
    275: "Hoy elige estabilidad.",
    276: "La calma es dirección.",
    277: "No fuerces acuerdos.",
    278: "Hoy escucha tu cuerpo.",
    279: "El equilibrio protege.",
    280: "Tu centro responde.",
    281: "No reacciones por costumbre.",
    282: "Hoy baja el ritmo.",
    283: "La claridad se siente.",
    284: "No te sobreexijas.",
    285: "Hoy honra tu energía.",
    286: "La coherencia sostiene.",
    287: "No cargues tensiones.",
    288: "Hoy elige presencia.",
    289: "El silencio ordena.",
    290: "Tu energía responde.",
    291: "No fuerces resultados.",
    292: "Hoy vuelve a lo simple.",
    293: "La calma guía.",
    294: "No te disperses.",
    295: "Hoy escucha más.",
    296: "El equilibrio se ajusta.",
    297: "No cargues expectativas.",
    298: "Hoy confía en tu centro.",
    299: "La presencia basta.",
    300: "Tu energía se ordena.",
    301: "No todo se resuelve hoy.",
    302: "Hoy baja la prisa.",
    303: "La coherencia protege.",
    304: "No te fuerces.",
    305: "Hoy honra tu ritmo.",
    306: "El silencio aclara.",
    307: "No cargues ruido.",
    308: "Hoy elige calma.",
    309: "El equilibrio sostiene.",
    310: "Tu centro guía.",
    311: "No reacciones automáticamente.",
    312: "Hoy escucha tu cuerpo.",
    313: "La claridad se siente.",
    314: "No te disperses.",
    315: "Hoy cuida tu energía.",
    316: "La coherencia ordena.",
    317: "No fuerces procesos.",
    318: "Hoy sostén tu centro.",
    319: "El silencio protege.",
    320: "Tu energía responde.",
    321: "No cargues lo innecesario.",
    322: "Hoy baja el ritmo.",
    323: "La calma guía.",
    324: "No te adelantes.",
    325: "Hoy confía en tu proceso.",
    326: "El equilibrio se afina.",
    327: "No fuerces acuerdos.",
    328: "Hoy escucha más.",
    329: "La presencia basta.",
    330: "Tu centro sostiene.",
    331: "No todo es urgente.",
    332: "Hoy honra tu cuerpo.",
    333: "La coherencia protege.",
    334: "No cargues ruido.",
    335: "Hoy elige calma.",
    336: "El silencio aclara.",
    337: "No te disperses.",
    338: "Hoy vuelve a lo esencial.",
    339: "La claridad se siente.",
    340: "Tu energía responde.",
    341: "No fuerces decisiones.",
    342: "Hoy baja la exigencia.",
    343: "La calma es poder.",
    344: "No cargues tensiones.",
    345: "Hoy cuida tu centro.",
    346: "El equilibrio guía.",
    347: "No reacciones por hábito.",
    348: "Hoy confía en ti.",
    349: "La presencia basta.",
    350: "Tu energía se ordena.",
    351: "No todo se explica.",
    352: "Hoy escucha tu intuición.",
    353: "La coherencia sostiene.",
    354: "No fuerces ritmos.",
    355: "Hoy elige sobriedad.",
    356: "El silencio protege.",
    357: "No te disperses.",
    358: "Hoy vuelve a tu eje.",
    359: "La claridad se siente.",
    360: "Tu centro responde.",
    361: "No cargues lo innecesario.",
    362: "Hoy baja el ruido.",
    363: "La calma guía.",
    364: "No te adelantes.",
    365: "Cierra el año en coherencia y verdad."
}



def energia_del_dia(hoy: date) -> str:
    return ENERGIA_DIA_365.get(dia_del_ano(hoy), "Hoy: respira, ordena y elige con amor.")
COMPATIBILIDAD_EXPRES = {
    1: (
        "Relación basada en iniciativa y empuje mutuo.\n"
        "Ambos necesitan respetar la independencia.\n"
        "La clave está en no competir entre sí.\n"
        "Cuando cooperan, avanzan con fuerza."
    ),
    2: (
        "Relación de apoyo, sensibilidad y cooperación.\n"
        "Existe una fuerte necesidad de estar juntos.\n"
        "La clave es no perder la individualidad.\n"
        "El vínculo crece con cuidado emocional."
    ),
    3: (
        "Relación dinámica, comunicativa y creativa.\n"
        "El diálogo es el cuerpo del vínculo.\n"
        "Necesitan expresar emociones con claridad.\n"
        "Cuando se escuchan, la relación florece."
    ),
    4: (
        "Relación que busca estabilidad y compromiso.\n"
        "Se construye paso a paso.\n"
        "La clave es flexibilizar sin perder estructura.\n"
        "Juntos pueden crear una base sólida."
    ),
    5: (
        "Relación marcada por cambio y movimiento.\n"
        "Necesitan libertad y experiencias compartidas.\n"
        "El reto es sostener continuidad.\n"
        "La relación crece con acuerdos claros."
    ),
    6: (
        "Relación protectora y orientada al cuidado.\n"
        "Existe sentido de familia y pertenencia.\n"
        "El reto es no sobrecargarse emocionalmente.\n"
        "El amor se sostiene con equilibrio."
    ),
    7: (
        "Relación introspectiva y profunda.\n"
        "Ambos necesitan espacios personales.\n"
        "La clave es respetar silencios.\n"
        "La conexión se fortalece desde la conciencia."
    ),
    8: (
        "Relación intensa y orientada a objetivos.\n"
        "Existe ambición y empuje conjunto.\n"
        "El reto es no caer en control.\n"
        "El vínculo se equilibra con sensibilidad."
    ),
    9: (
        "Relación de cierre, sanación y aprendizaje.\n"
        "Vínculo que transforma profundamente.\n"
        "Puede remover emociones pasadas.\n"
        "El amor crece al soltar lo viejo."
    ),
    11: (
        "Relación altamente sensible e intuitiva.\n"
        "Existe conexión energética fuerte.\n"
        "El reto es anclarse a lo concreto.\n"
        "La relación pide coherencia emocional."
    ),
    22: (
        "Relación con propósito y visión compartida.\n"
        "Juntos construyen algo significativo.\n"
        "El reto es no cargar demasiado peso.\n"
        "El vínculo crece con organización."
    ),
    33: (
        "Relación de entrega y servicio mutuo.\n"
        "Existe amor profundo y compasivo.\n"
        "El reto es cuidar la energía personal.\n"
        "El vínculo sana cuando hay límites."
    )
}
    
COMPATIBILIDAD_PROFUNDA = {

    1: (
        "Esta relación se construye desde la iniciativa y la fuerza personal.\n"
        "Ambos sienten el impulso de avanzar y liderar.\n"
        "Existe admiración mutua cuando se respetan los espacios.\n"
        "El reto aparece cuando ninguno quiere ceder.\n"
        "La relación pide reconocer al otro sin competir.\n"
        "El amor crece cuando hay apoyo y no imposición.\n"
        "Es un vínculo que necesita objetivos compartidos.\n"
        "La admiración sostiene el deseo.\n"
        "La independencia es una base, no una amenaza.\n"
        "Cuando se acompañan, avanzan con más claridad.\n"
        "La relación florece con respeto.\n"
        "El orgullo debe transformarse en cooperación.\n"
        "Ambos aprenden a liderar juntos.\n"
        "El amor se fortalece con reconocimiento.\n"
        "La unión se consolida cuando hay propósito común."
    ),

    2: (
        "Esta relación se basa en la sensibilidad y el acompañamiento emocional.\n"
        "Existe una fuerte necesidad de cercanía.\n"
        "Ambos perciben profundamente al otro.\n"
        "La relación busca cooperación y apoyo mutuo.\n"
        "El riesgo es perder la individualidad.\n"
        "El amor crece cuando hay equilibrio entre dar y recibir.\n"
        "Es un vínculo que se nutre del cuidado.\n"
        "La ternura es un lenguaje central.\n"
        "La relación se resiente si uno se anula.\n"
        "La clave está en apoyarse sin depender.\n"
        "El vínculo se fortalece con diálogo emocional.\n"
        "La unión es suave, pero profunda.\n"
        "Ambos aprenden a sostenerse.\n"
        "El amor se expresa en gestos pequeños.\n"
        "La relación prospera con armonía consciente."
    ),

    3: (
        "Esta relación se construye a través de la comunicación consciente.\n"
        "El vínculo necesita palabra, expresión y diálogo constante.\n"
        "Ambos se estimulan mental y emocionalmente.\n"
        "La creatividad es un puente de unión.\n"
        "Cuando callan lo que sienten, surge distancia.\n"
        "El cuerpo de la relación es la conversación.\n"
        "Existe potencial para alegría compartida.\n"
        "También puede aparecer dispersión emocional.\n"
        "El vínculo mejora al expresar necesidades reales.\n"
        "No se trata de hablar más, sino de hablar con verdad.\n"
        "La relación pide escucha activa.\n"
        "Cuando se comunican desde el corazón, crecen.\n"
        "El humor sana tensiones.\n"
        "La relación florece con autenticidad.\n"
        "El amor se sostiene en la palabra clara."
    ),

    4: (
        "Esta relación busca estabilidad, orden y compromiso.\n"
        "Ambos necesitan seguridad emocional.\n"
        "El vínculo se construye paso a paso.\n"
        "La constancia es una base importante.\n"
        "El riesgo es caer en rigidez.\n"
        "La relación crece cuando hay flexibilidad.\n"
        "El amor se expresa en hechos concretos.\n"
        "Ambos valoran la lealtad.\n"
        "El vínculo se fortalece con acuerdos claros.\n"
        "La rutina puede ser sostén o desgaste.\n"
        "La clave es renovar sin destruir.\n"
        "El compromiso une profundamente.\n"
        "La relación se vuelve sólida con confianza.\n"
        "Ambos aprenden a sostenerse en el tiempo.\n"
        "El amor se consolida con coherencia."
    ),

    5: (
        "Esta relación está marcada por el cambio y la libertad.\n"
        "Ambos necesitan movimiento.\n"
        "El vínculo se alimenta de experiencias compartidas.\n"
        "La rutina debilita la conexión.\n"
        "El reto es sostener continuidad emocional.\n"
        "La relación florece con acuerdos claros.\n"
        "Existe curiosidad mutua.\n"
        "La atracción se renueva con novedad.\n"
        "El riesgo es la inestabilidad.\n"
        "La libertad necesita responsabilidad.\n"
        "El amor crece cuando hay confianza.\n"
        "Ambos aprenden a elegir conscientemente.\n"
        "La relación se expande con flexibilidad.\n"
        "El vínculo se fortalece con honestidad.\n"
        "El amor se sostiene con compromiso libre."
    ),

    6: (
        "Esta relación se basa en el cuidado y la protección.\n"
        "Existe una fuerte energía de hogar.\n"
        "Ambos buscan contención emocional.\n"
        "El amor se expresa en responsabilidad afectiva.\n"
        "El riesgo es sobrecargarse.\n"
        "La relación necesita equilibrio.\n"
        "Cuidar no es controlar.\n"
        "El vínculo se fortalece con ternura.\n"
        "La familia y el entorno pesan.\n"
        "El amor madura con límites sanos.\n"
        "Ambos aprenden a dar sin agotarse.\n"
        "La relación florece con reciprocidad.\n"
        "El compromiso es profundo.\n"
        "La unión se nutre del respeto.\n"
        "El amor se sostiene con cuidado consciente."
    ),

    7: (
        "Esta relación es introspectiva y profunda.\n"
        "Existe conexión espiritual.\n"
        "Ambos necesitan espacios personales.\n"
        "El silencio también comunica.\n"
        "El riesgo es el aislamiento.\n"
        "La relación crece con comprensión.\n"
        "No todo se expresa con palabras.\n"
        "El vínculo se fortalece con confianza.\n"
        "La conexión es sutil pero intensa.\n"
        "El amor pide paciencia.\n"
        "Ambos aprenden a respetar procesos internos.\n"
        "La unión se afina con conciencia.\n"
        "El vínculo se profundiza con honestidad.\n"
        "La relación madura lentamente.\n"
        "El amor se sostiene desde la verdad interior."
    ),

    8: (
        "Esta relación es intensa y orientada a objetivos.\n"
        "Existe ambición compartida.\n"
        "Ambos buscan crecer.\n"
        "El poder puede unir o separar.\n"
        "El reto es evitar luchas de control.\n"
        "La relación florece con respeto mutuo.\n"
        "El amor se fortalece con equilibrio emocional.\n"
        "La unión pide sensibilidad.\n"
        "El éxito compartido une.\n"
        "La relación se debilita sin empatía.\n"
        "Ambos aprenden a liderar juntos.\n"
        "El vínculo madura con conciencia.\n"
        "El amor necesita humanidad.\n"
        "La relación se equilibra con humildad.\n"
        "El vínculo prospera con coherencia."
    ),

    9: (
        "Esta relación es profundamente transformadora.\n"
        "Remueve memorias emocionales.\n"
        "Existe aprendizaje mutuo.\n"
        "El vínculo invita a sanar.\n"
        "El reto es soltar el pasado.\n"
        "La relación pide compasión.\n"
        "El amor crece con perdón.\n"
        "No es una relación ligera.\n"
        "La unión cierra ciclos.\n"
        "Ambos evolucionan.\n"
        "El vínculo se profundiza con aceptación.\n"
        "La relación libera cargas emocionales.\n"
        "El amor se vuelve consciente.\n"
        "El vínculo transforma a ambos.\n"
        "La unión deja huella."
    ),

    11: (
        "Esta relación es altamente sensible e intuitiva.\n"
        "Existe conexión energética fuerte.\n"
        "Ambos perciben emociones profundas.\n"
        "El vínculo es inspirador.\n"
        "El reto es sostener lo práctico.\n"
        "La relación florece con coherencia.\n"
        "La intuición guía el vínculo.\n"
        "El amor es sutil.\n"
        "La relación puede ser intensa.\n"
        "Ambos deben cuidarse emocionalmente.\n"
        "El vínculo pide equilibrio.\n"
        "La unión inspira crecimiento.\n"
        "La relación se fortalece con verdad.\n"
        "El amor es profundo.\n"
        "La conexión es espiritual."
    ),

    22: (
        "Esta relación tiene propósito y visión compartida.\n"
        "Ambos sienten misión conjunta.\n"
        "El vínculo busca construir algo duradero.\n"
        "El reto es no cargar demasiado.\n"
        "La relación pide organización.\n"
        "El amor crece con estructura.\n"
        "La unión se fortalece con metas claras.\n"
        "El compromiso es profundo.\n"
        "Ambos se apoyan.\n"
        "El vínculo se consolida con paciencia.\n"
        "La relación madura con esfuerzo consciente.\n"
        "El amor se sostiene en hechos.\n"
        "La unión deja legado.\n"
        "El vínculo se fortalece con coherencia.\n"
        "La relación construye futuro."
    ),

    33: (
        "Esta relación es de amor profundo y servicio mutuo.\n"
        "Existe compasión intensa.\n"
        "Ambos sienten responsabilidad emocional.\n"
        "El amor es incondicional.\n"
        "El reto es no sacrificarse en exceso.\n"
        "La relación pide límites sanos.\n"
        "El vínculo sana.\n"
        "La unión es transformadora.\n"
        "El amor es generoso.\n"
        "Ambos deben cuidarse.\n"
        "La relación florece con equilibrio.\n"
        "El vínculo se fortalece con conciencia.\n"
        "La unión eleva.\n"
        "El amor es profundo.\n"
        "La relación es sanadora."
    ),
}
def compatibilidad_numero(fecha_a: date, fecha_b: date) -> int:
    return reducir_numero(
        (fecha_a.day + fecha_a.month + fecha_a.year) +
        (fecha_b.day + fecha_b.month + fecha_b.year)
    )

def compatibilidad_express_texto(n: int) -> str:
    return COMPATIBILIDAD_EXPRES.get(int(n), "Compatibilidad express no disponible.")

def compatibilidad_profunda_texto(n: int) -> str:
    return COMPATIBILIDAD_PROFUNDA.get(int(n), "Compatibilidad profunda no disponible.")

TEXTO_HOGAR = {
    1: (
        "La vibración 1 en el hogar habla de independencia y nuevos comienzos.\n"
        "Es un espacio que impulsa iniciativa, decisiones propias y liderazgo.\n"
        "Puede sentirse solitario si no hay propósito claro.\n"
        "Conviene activar orden, intención y metas visibles.\n"
        "El hogar pide acción consciente, no dispersión.\n"
        "Cuando se honra esta energía, se fortalece la autonomía interna."
    ),
    2: (
        "La vibración 2 en el hogar enfatiza unión, cooperación y contención emocional.\n"
        "Es un espacio sensible al clima emocional de quienes lo habitan.\n"
        "Favorece vínculos, diálogo y apoyo mutuo.\n"
        "Puede generar dependencia si no hay límites claros.\n"
        "El equilibrio llega con armonía y respeto.\n"
        "Un hogar 2 pide cuidado, escucha y suavidad."
    ),
    3: (
        "La vibración 3 activa expresión, creatividad y movimiento interno.\n"
        "Es un hogar que necesita comunicación y alegría.\n"
        "Favorece reuniones, ideas y dinamismo.\n"
        "El desorden emocional puede reflejarse físicamente.\n"
        "Conviene sostener rutinas mínimas para estabilizar la energía.\n"
        "Cuando fluye bien, el hogar se vuelve inspirador."
    ),
    4: (
        "La vibración 4 aporta estructura, estabilidad y base sólida.\n"
        "Es un hogar que sostiene procesos largos y compromiso.\n"
        "Favorece disciplina, constancia y sensación de seguridad.\n"
        "Puede sentirse rígido si no se flexibiliza.\n"
        "El orden consciente es clave para su equilibrio.\n"
        "Aquí se construye a largo plazo."
    ),
    5: (
        "La vibración 5 trae cambio, movimiento y necesidad de libertad.\n"
        "Es un hogar inquieto, con entradas y salidas constantes.\n"
        "Favorece adaptación y experiencias nuevas.\n"
        "Puede generar inestabilidad si no hay centro.\n"
        "Conviene crear anclajes energéticos claros.\n"
        "El hogar pide flexibilidad con conciencia."
    ),
    6: (
        "La vibración 6 está ligada al cuidado, la familia y la responsabilidad.\n"
        "Es un hogar protector, contenedor y emocionalmente fuerte.\n"
        "Favorece vínculos afectivos y sentido de pertenencia.\n"
        "Puede sobrecargar a quien cuida de todos.\n"
        "El equilibrio llega al repartir responsabilidades.\n"
        "Un hogar 6 sana cuando hay reciprocidad."
    ),
    7: (
        "La vibración 7 invita a introspección y silencio interior.\n"
        "Es un hogar que pide momentos de soledad y reflexión.\n"
        "Favorece estudio, espiritualidad y conexión interna.\n"
        "Puede aislar si no se equilibra con lo social.\n"
        "Conviene respetar los tiempos de retiro.\n"
        "Aquí se ordena la mente y el espíritu."
    ),
    8: (
        "La vibración 8 activa poder personal y estructura material.\n"
        "Es un hogar que refleja logros, responsabilidades y metas.\n"
        "Favorece enfoque, dirección y autoridad interna.\n"
        "Puede generar tensión si todo se vuelve control.\n"
        "El equilibrio surge al unir propósito y bienestar.\n"
        "El hogar sostiene el crecimiento consciente."
    ),
    9: (
        "La vibración 9 habla de cierre, limpieza y liberación emocional.\n"
        "Es un hogar que invita a soltar lo viejo.\n"
        "Favorece procesos de sanación y perdón.\n"
        "Puede remover memorias profundas.\n"
        "Conviene acompañar los cierres con intención.\n"
        "Aquí se prepara un nuevo comienzo."
    ),
    11: (
        "La vibración 11 eleva la sensibilidad y la percepción.\n"
        "Es un hogar altamente energético y emocional.\n"
        "Favorece intuición, inspiración y conciencia.\n"
        "Puede generar sobreestimulación si no hay orden.\n"
        "El equilibrio llega con anclaje y rutina.\n"
        "Un hogar 11 pide coherencia interna."
    ),
    22: (
        "La vibración 22 sostiene construcción consciente y propósito elevado.\n"
        "Es un hogar que materializa proyectos importantes.\n"
        "Favorece estabilidad con visión a largo plazo.\n"
        "Puede sentirse exigente si no hay descanso.\n"
        "Conviene equilibrar acción y cuidado.\n"
        "Aquí se construye legado."
    ),
    33: (
        "La vibración 33 es servicio, amor consciente y entrega.\n"
        "Es un hogar que sostiene a otros emocionalmente.\n"
        "Favorece compasión, contención y guía.\n"
        "Puede generar desgaste si no hay autocuidado.\n"
        "El equilibrio nace al cuidarse para cuidar.\n"
        "Un hogar 33 sana cuando hay límites amorosos."
    ),
}

def texto_hogar(num_dir: int) -> str:
    return TEXTO_HOGAR.get(num_dir, "Hogar: equilibrio, limpieza y armonía.")


TEXTO_TELEFONO = {
    1: (
        "Tu número de teléfono vibra en 1, una energía de iniciativa y liderazgo.\n"
        "Las llamadas activan decisiones rápidas y comienzos importantes.\n"
        "Es un número que impulsa a tomar la palabra sin rodeos.\n"
        "Cuidado con la impulsividad o el tono autoritario.\n"
        "La clave es comunicar con claridad y propósito.\n"
        "Cuando lideras desde la conciencia, la comunicación fluye."
    ),
    2: (
        "Tu número de teléfono vibra en 2, una energía de cooperación y escucha.\n"
        "Las conversaciones buscan acuerdos, apoyo y entendimiento mutuo.\n"
        "Es ideal para mediación, vínculos y trabajo en equipo.\n"
        "Puede haber tendencia a callar por evitar conflicto.\n"
        "La clave es expresar lo que sientes sin perder armonía.\n"
        "La comunicación consciente fortalece los vínculos."
    ),
    3: (
        "Tu número de teléfono vibra en 3, energía de expresión y creatividad.\n"
        "Las llamadas activan ideas, contactos y movimiento social.\n"
        "Favorece conversaciones ligeras, inspiradoras y expansivas.\n"
        "Riesgo de dispersión o hablar sin profundidad.\n"
        "La clave es enfocar el mensaje.\n"
        "Cuando comunicas con intención, tu voz inspira."
    ),
    4: (
        "Tu número de teléfono vibra en 4, energía de orden y estructura.\n"
        "Las llamadas se orientan a temas prácticos y concretos.\n"
        "Favorece acuerdos claros, compromisos y organización.\n"
        "Puede sentirse rígido o poco flexible.\n"
        "La clave es abrir espacio a la escucha.\n"
        "La comunicación firme y clara genera estabilidad."
    ),
    5: (
        "Tu número de teléfono vibra en 5, energía de cambio y movimiento.\n"
        "Las llamadas traen novedades, viajes y oportunidades inesperadas.\n"
        "Favorece la adaptabilidad y la negociación.\n"
        "Puede generar inestabilidad o exceso de estímulos.\n"
        "La clave es no dispersarte.\n"
        "Comunicar con conciencia ordena el cambio."
    ),
    6: (
        "Tu número de teléfono vibra en 6, energía de cuidado y responsabilidad.\n"
        "Las llamadas suelen vincularse con familia, trabajo y compromiso.\n"
        "Favorece conversaciones protectoras y empáticas.\n"
        "Riesgo de cargar problemas ajenos.\n"
        "La clave es poner límites sanos.\n"
        "La comunicación equilibrada cuida sin desgastarte."
    ),
    7: (
        "Tu número de teléfono vibra en 7, energía de introspección y análisis.\n"
        "Las llamadas invitan a reflexionar antes de hablar.\n"
        "Favorece conversaciones profundas y selectivas.\n"
        "Puede generar distancia o silencio prolongado.\n"
        "La clave es compartir lo que piensas.\n"
        "Comunicar desde la verdad interna fortalece tu voz."
    ),
    8: (
        "Tu número de teléfono vibra en 8, energía de poder y concreción.\n"
        "Las llamadas se asocian a trabajo, decisiones y autoridad.\n"
        "Favorece negociaciones y temas materiales.\n"
        "Riesgo de control o dureza verbal.\n"
        "La clave es liderar con ética.\n"
        "La comunicación consciente sostiene tu poder."
    ),
    9: (
        "Tu número de teléfono vibra en 9, energía de cierre y conciencia.\n"
        "Las llamadas traen mensajes importantes de liberación.\n"
        "Favorece conversaciones empáticas y sanadoras.\n"
        "Puede haber cansancio emocional.\n"
        "La clave es no absorberlo todo.\n"
        "Comunicar con compasión eleva la vibración."
    ),
    11: (
        "Tu número de teléfono vibra en 11, energía maestra de intuición.\n"
        "Las llamadas activan mensajes clave y señales importantes.\n"
        "Favorece la inspiración y la guía.\n"
        "Puede generar nerviosismo o sobrecarga mental.\n"
        "La clave es bajar la información a tierra.\n"
        "La comunicación consciente canaliza tu visión."
    ),
    22: (
        "Tu número de teléfono vibra en 22, energía maestra de construcción.\n"
        "Las llamadas están ligadas a proyectos grandes y responsabilidad.\n"
        "Favorece acuerdos de largo alcance.\n"
        "Puede sentirse peso o exigencia.\n"
        "La clave es delegar y ordenar.\n"
        "Comunicar con estructura sostiene grandes logros."
    ),
    33: (
        "Tu número de teléfono vibra en 33, energía maestra de servicio.\n"
        "Las llamadas activan ayuda, enseñanza y acompañamiento.\n"
        "Favorece mensajes compasivos y orientadores.\n"
        "Riesgo de sacrificio excesivo.\n"
        "La clave es cuidarte al comunicar.\n"
        "La palabra consciente se vuelve sanadora."
    ),
}
def texto_telefono(num_tel: int) -> str:
    return TEXTO_TELEFONO.get( num_tel, "Teléfono: comunicación consciente y límites sanos.")

# =====================================================
# PAGO: TEXTOS PROFUNDOS (10–12 líneas aprox)
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

hoy = date.today()
dia_del_ano = hoy.timetuple().tm_yday  # 1 a 365 (366 en bisiesto)

mensaje_365 = ENERGIA_DIA_365 .get(
                dia_del_ano,
                "Hoy es un día para observar, integrar y no forzar."
            )

st.markdown("### 🌞 Mensaje universal del día")
st.write(mensaje_365)

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
st.markdown("### 💞 Compatibilidad (opcional)")
activar_compat_express = st.checkbox("Activar compatibilidad express", value=False)

fecha_pareja_express = st.date_input(
    "Fecha de nacimiento de la pareja",
    min_value=date(1936, 1, 1),
    max_value=date(2036, 12, 31),
    value=date(2000, 1, 1),
    disabled=not activar_compat_express
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

       

        if activar_compat_express:
            comp_ex = compatibilidad_numero(fecha_nac, fecha_pareja_express)
            st.markdown(f"### 💞 Compatibilidad Express · Número {comp_ex}")
            st.write(compatibilidad_express_texto(comp_ex))


        # ✅ AQUÍ VAN LOS 4 BLOQUES CORTOS GRATIS (lo que me pediste)
        st.markdown("#### 💡 Pronóstico clave")
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


# =========================================================
# 🔐 VERSIÓN COMPLETA (PAGO) - BLOQUEO POR CLAVE + NOMBRE + FECHA
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
    type="password"
).strip().upper()

# 👉 BOTÓN CLAVE (ESTO ES LO QUE FALTABA)
confirmar_datos = st.button("🔓 Confirmar datos y desbloquear")

# =========================================================
# VALIDACIÓN (SOLO SE EJECUTA AL PRESIONAR EL BOTÓN)
# =========================================================

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

    # ✅ DESBLOQUEO
    st.session_state.premium_activo = True
    st.success("Versión completa desbloqueada ✅") 

if st.session_state.premium_activo:
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
if st.session_state.premium_activo:
    st.markdown("### 📌 Datos opcionales Premium")
    cA, cB = st.columns(2)
    with cA:
        telefono = st.text_input("Teléfono (opcional)", value="", placeholder="Ej: +58 412 000 0000")
        key="telefono_premiun"
    with cB:
        direccion_apto = st.text_input("Dirección / Apto (opcional)", value="", placeholder="Ej: Torre A, Apto 12B")
        key="dirreccion_apto_premiun"

    num_tel = numero_apto(telefono) if telefono.strip() else 0
    num_dir = numero_apto(direccion_apto) if direccion_apto.strip() else 0

    st.markdown("### 💞 Compatibilidad (Premium)")
    activar_compat_premium = st.checkbox("Activar compatibilidad profunda", value=False, key="compat_premium")

    fecha_pareja_premium = st.date_input(
    "Fecha de nacimiento de la pareja (Premium)",
    min_value=date(1936, 1, 1),
    max_value=date(2036, 12, 31),
    value=date(2000, 1, 1),
    disabled=not activar_compat_premium,
    key="fecha_pareja_premium"
)

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
        st.write(texto_telefono(num_tel))
    else:
        st.info("Si deseas, agrega un teléfono para activar esta sección.")

    if num_dir:
        st.markdown(f"### Dirección / Apto — Número {num_dir}")
        st.write(texto_hogar(num_dir))
    else:
        st.info("Si deseas, agrega tu dirección o número de apto para activar esta sección.")

    st.markdown("### 8) Arcano mayor de la semana")
    st.write(f"Arcano {arc_p}")
    st.write(arcano_micro(arc_p))

    st.markdown("### 9) Pináculo (pirámide completa)")
    st.write(f"Base: {pin_p['base']} | Medio: {pin_p['medio']} | Cima: {pin_p['cima']}")
    st.write(pinaculo_micro(pin_p))

    if activar_compat_premium:
        comp_pr = compatibilidad_numero(fecha_validada, fecha_pareja_premium)
        st.markdown(f"### 💞 Compatibilidad Profunda · Número {comp_pr}")
        st.write(compatibilidad_profunda_texto(comp_pr))


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

