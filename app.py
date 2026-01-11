
import hashlib
import hmac
import os
import re
import textwrap
import unicodedata
from datetime import date, datetime
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas



def normalizar_texto(texto):
    """
    Convierte el texto a mayúsculas, elimina acentos
    y deja solo letras A-Z.
    """
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^A-Z]", "", texto)
    return texto



## =====================================================
# CONFIGURACIÓN GENERAL (PRIMERO EN STREAMLIT)
# =====================================================
APP_TITLE = "🔮 Lectura Numerológica"
BRAND = "Eugenia.Místico"

st.set_page_config(
    page_title=f"{APP_TITLE} · {BRAND}",
    page_icon="🔮",
    layout="centered",
)

st.markdown("""
<style>
/* =====================================================
   FONDO GENERAL
   ===================================================== */
html, body, [data-testid="stApp"] {
    background-color: #FBF9FD;
}

/* =====================================================
   TIPOGRAFÍA
   ===================================================== */
h1, h2, h3 {
    color: #3E2A5E;
    letter-spacing: 0.4px;
}

h4, h5 {
    color: #5A3E85;
}

p, li, span {
    color: #3B2F4A;
    font-size: 1.02rem;
    line-height: 1.65;
}

/* =====================================================
   BOTÓN PRINCIPAL (STREAMLIT ACTUAL)
   ===================================================== */
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #7B4AE2, #A88CF0) !important;
    border-radius: 18px !important;
    border: none !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 600 !important;
    color: white !important;
}

/* =====================================================
   SISTEMA UI EUGENIA.MÍSTICO
   ===================================================== */

/* Sección / encabezado de bloque */
.em-hero{
    background: linear-gradient(135deg, #F6EEF8, #EFE6F5);
    border: 1px solid #E3D6ED;
    border-radius: 22px;
    padding: 18px 18px;
    margin: 10px 0 18px 0;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}

.em-hero-badge{
    display:inline-block;
    font-size:0.78rem;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#5A3E85;
    margin-bottom:8px;
}

.em-hero-title{
    font-size:1.65rem;
    font-weight:800;
    color:#3E2A5E;
    line-height:1.2;
}

.em-hero-sub{
    margin-top:8px;
    font-size:1.02rem;
    color:#3B2F4A;
    line-height:1.6;
}

/* Tarjetas */
.em-card{
    background: linear-gradient(135deg, #F6EEF8, #EFE6F5);
    padding: 20px 22px;
    border-radius: 22px;
    border: 1px solid #E3D6ED;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

.em-muted{
    color: #6B5A7A;
    font-size: 0.92rem;
    margin-top: 10px;
}

/* Separador suave */
.em-sep{
    height: 1px;
    background: linear-gradient(to right, transparent, #C9B6E4, transparent);
    margin: 26px 0;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# COMPONENTES UI
# =====================================================
def em_card(titulo: str, icono: str, contenido: str, nota: str = ""):
    st.markdown(
        f"""
<div class="em-card">
  <h4>{icono} {titulo}</h4>
  <div class="em-muted">{nota}</div>
  <p>{contenido}</p>
</div>
""",
        unsafe_allow_html=True,
    )

# =====================================================
# NORMALIZACIÓN PARA CLAVES (USO: PAGO / TOKENS)
# =====================================================
def normalizar_clave_nombre(txt: str) -> str:
    """
    Normaliza nombre para generación de claves:
    - Quita acentos
    - Mantiene espacios
    - Convierte a MAYÚSCULAS
    """
    txt = unicodedata.normalize("NFD", str(txt))
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[^A-Za-z\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip().upper()
    return txt


def generar_clave_unica(nombre_completo: str, fecha_nac: date) -> str:
    """
    Crea una clave única EM-XXXX-XXXX-XXXX-XXXX
    segura e incuantificable (hash + APP_SECRET).
    """
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
# UTILIDADES NUMÉRICAS AUXILIARES (USADAS EN VARIOS BLOQUES)
# =====================================================
def sumar_digitos_texto(txt: str) -> int:
    digs = re.findall(r"\d", str(txt))
    if not digs:
        return 0
    return reducir_numero(sum(int(d) for d in digs))


def numero_nombre(nombre: str) -> int:
    total = sum(
        TABLA_PITAGORICA.get(char, 0)
        for char in normalizar_texto(nombre)
        if char.isalpha()
    )
    return reducir_numero(total)


def numero_apto(apto: str) -> int:
    apto = str(apto).strip()
    if not apto:
        return 0
    if re.search(r"\d", apto):
        return sumar_digitos_texto(apto)
    return numero_nombre(apto)


# =====================================================
# UTILIDADES NUMEROLÓGICAS (UNA SOLA VEZ)
# =====================================================

TABLA_PITAGORICA = {
    "A": 1, "J": 1, "S": 1,
    "B": 2, "K": 2, "T": 2,
    "C": 3, "L": 3, "U": 3,
    "D": 4, "M": 4, "V": 4,
    "E": 5, "N": 5, "W": 5,
    "F": 6, "O": 6, "X": 6,
    "G": 7, "P": 7, "Y": 7,
    "H": 8, "Q": 8, "Z": 8,
    "I": 9, "R": 9
}



def reducir_numero(n: int) -> int:
    """Reduce a 1–9, preservando 11, 22 y 33."""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n

def sendero_vida(fecha: date) -> int:
    return reducir_numero(fecha.day + fecha.month + fecha.year)

def ano_personal(fecha_nac: date, hoy: date) -> int:
    return reducir_numero(fecha_nac.day + fecha_nac.month + hoy.year)

def mes_personal(fecha_nac: date, hoy: date) -> int:
    return reducir_numero(ano_personal(fecha_nac, hoy) + hoy.month)

def dia_personal(fecha_nac: date, hoy: date) -> int:
    return reducir_numero(mes_personal(fecha_nac, hoy) + hoy.day)

def esencia(nombre: str) -> int:
    return reducir_numero(numero_nombre(nombre))

def imagen_externa(nombre: str) -> int:
    nombre = normalizar_texto(nombre)
    consonantes = re.sub(r"[AEIOU]", "", nombre)
    total = sum(TABLA_PITAGORICA.get(c, 0) for c in consonantes)
    return reducir_numero(total)

def vida_pasada(fecha_nac: date) -> int:
    return reducir_numero(fecha_nac.day)

def arcano_personal(fecha_nac: date) -> int:
    # Arcano por día del año, mapeado a 1..22
    d = fecha_nac.timetuple().tm_yday
    return ((d - 1) % 22) + 1

def dia_del_ano(hoy: date) -> int:
    # 1..365 (si es bisiesto y cae 366, lo mapeamos a 365)
    n = hoy.timetuple().tm_yday
    return 365 if n > 365 else n



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

TEXTO_ESENCIA = {
    1:"Esencia 1: iniciativa, liderazgo y decisión.",
    2:"Esencia 2: sensibilidad, cooperación y armonía.",
    3:"Esencia 3: comunicación, creatividad y gozo.",
    4:"Esencia 4: estructura, constancia y orden.",
    5:"Esencia 5: cambio, libertad y aprendizaje.",
    6:"Esencia 6: amor, responsabilidad y belleza.",
    7:"Esencia 7: introspección, estudio y fe.",
    8:"Esencia 8: poder personal, logro y merecimiento.",
    9:"Esencia 9: cierre, compasión y servicio.",
    11:"Esencia 11: intuición elevada y visión.",
    22:"Esencia 22: construcción grande y propósito.",
    33:"Esencia 33: guía amorosa y servicio consciente."
}

TEXTO_IMAGEN = {
    1:"Imagen 1: presencia directa; te perciben firme y clara.",
    2:"Imagen 2: dulzura y escucha; inspiras confianza.",
    3:"Imagen 3: carisma; tu energía social abre puertas.",
    4:"Imagen 4: seriedad; transmites estabilidad.",
    5:"Imagen 5: versatilidad; te ven dinámica y libre.",
    6:"Imagen 6: calidez; proyectas cuidado y estética.",
    7:"Imagen 7: misterio; te ven profunda y selectiva.",
    8:"Imagen 8: autoridad; proyectas fuerza y enfoque.",
    9:"Imagen 9: humanidad; inspiras empatía.",
    11:"Imagen 11: magnetismo; conectas por intuición.",
    22:"Imagen 22: madurez; proyectas capacidad de sostener.",
    33:"Imagen 33: presencia sanadora; inspiras protección."
}

TEXTO_VIDA_PASADA = {
    1:"Vida pasada 1: independencia; aprender a liderar sin aislarte.",
    2:"Vida pasada 2: vínculos; aprender a elegir sin perderte.",
    3:"Vida pasada 3: expresión; aprender a decir lo que sientes.",
    4:"Vida pasada 4: deber; aprender a flexibilizar el control.",
    5:"Vida pasada 5: cambio; aprender a comprometerte sin sentir cárcel.",
    6:"Vida pasada 6: familia; aprender a cuidar sin cargarte.",
    7:"Vida pasada 7: búsqueda; aprender a confiar en tu intuición.",
    8:"Vida pasada 8: poder; aprender a usar recursos con ética.",
    9:"Vida pasada 9: servicio; aprender a cerrar ciclos con paz.",
    11:"Vida pasada 11: canal; aprender a sostener tu sensibilidad.",
    22:"Vida pasada 22: gran obra; aprender a construir con calma.",
    33:"Vida pasada 33: maestría; aprender amor con límites."
}

TEXTO_SENDERO_VIDA = {
    1:"Sendero 1: vienes a abrir caminos y tomar decisiones.",
    2:"Sendero 2: vienes a armonizar, mediar y conectar.",
    3:"Sendero 3: vienes a comunicar y crear belleza.",
    4:"Sendero 4: vienes a construir con método y paciencia.",
    5:"Sendero 5: vienes a cambiar, viajar y evolucionar.",
    6:"Sendero 6: vienes a cuidar, enseñar y embellecer.",
    7:"Sendero 7: vienes a estudiar, profundizar y creer.",
    8:"Sendero 8: vienes a liderar recursos y sostener poder personal.",
    9:"Sendero 9: vienes a cerrar ciclos y servir con compasión.",
    11:"Sendero 11: vienes a inspirar desde la intuición.",
    22:"Sendero 22: vienes a materializar visión y legado.",
    33:"Sendero 33: vienes a guiar con amor consciente."
}

ARCANOS_RESUMIDOS = {
    1:  "Arcano I — El Mago.\nInicio consciente y poder personal: actuar con intención abre caminos reales.",
    2:  "Arcano II — La Sacerdotisa.\nIntuición y silencio fértil: la respuesta llega cuando escuchas hacia adentro.",
    3:  "Arcano III — La Emperatriz.\nCreatividad y expansión: nutre lo que amas y crecerá con fuerza y belleza.",
    4:  "Arcano IV — El Emperador.\nOrden y estructura: los límites sanos sostienen lo que quieres construir.",
    5:  "Arcano V — El Hierofante.\nAprendizaje y valores: elegir desde la ética evita repetir errores.",
    6:  "Arcano VI — Los Enamorados.\nElección consciente: coherencia entre deseo, verdad y compromiso.",
    7:  "Arcano VII — El Carro.\nDirección y avance: disciplina enfocada vence dispersión y dudas.",
    8:  "Arcano VIII — La Justicia.\nEquilibrio y causa-efecto: ordenar lo pendiente trae claridad y estabilidad.",
    9:  "Arcano IX — El Ermitaño.\nIntrospección y sabiduría: mirar hacia adentro aclara el camino.",
    10: "Arcano X — La Rueda de la Fortuna.\nCambio de ciclo: adaptarte a tiempo evita resistencia innecesaria.",
    11: "Arcano XI — La Fuerza.\nDominio interno: calma consciente por encima del impulso.",
    12: "Arcano XII — El Colgado.\nNueva perspectiva: soltar control revela soluciones que no veías.",
    13: "Arcano XIII — La Muerte.\nTransformación profunda: cerrar a tiempo libera energía vital.",
    14: "Arcano XIV — La Templanza.\nArmonía y ajuste: integrar extremos devuelve equilibrio.",
    15: "Arcano XV — El Diablo.\nConciencia de ataduras: reconocerlas es el primer paso para liberarte.",
    16: "Arcano XVI — La Torre.\nRuptura necesaria: cae lo falso para reconstruir con verdad y fuerza.",
    17: "Arcano XVII — La Estrella.\nEsperanza y guía: fe serena, visión amable y recuperación de confianza.",
    18: "Arcano XVIII — La Luna.\nSensibilidad emocional: evita decidir desde miedo o confusión.",
    19: "Arcano XIX — El Sol.\nClaridad y vitalidad: la verdad trae expansión y alegría.",
    20: "Arcano XX — El Juicio.\nRenacer consciente: responder al llamado interno cambia tu rumbo.",
    21: "Arcano XXI — El Mundo.\nIntegración y culminación: cierre exitoso y paso al siguiente nivel.",
    22: "Arcano XXII — El Loco.\nInicio libre: confiar es el primer paso, pero con presencia."
}

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

FRASE_CLAVE = {
    1: "Inicia con valentía: tu decisión abre camino.",
    2: "Escucha y armoniza: tu intuición ordena el vínculo.",
    3: "Exprésate con verdad: tu voz crea realidad.",
    4: "Construye con disciplina: lo sólido te sostiene.",
    5: "Atrévete al cambio: la libertad también es un plan.",
    6: "Cuida con límites: amor sin sacrificio.",
    7: "Silencio consciente: claridad antes de actuar.",
    8: "Merecimiento y poder: sostén tu lugar.",
    9: "Cierre limpio: suelta para renacer.",
    11: "Sensibilidad maestra: protege tu energía y elige paz.",
    22: "Arquitecta del destino: visión + estructura = expansión.",
    33: "Servicio con límites: amor consciente que transforma."
}

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


# =====================================================
# TEXTOS (UNA SOLA VEZ)
# =====================================================
# =====================================================
# TEXTOS / RESOLVERS (UNA SOLA VEZ)
# =====================================================

def get_dict_text(dic: dict, n, default: str = "Texto no disponible."):
    try:
        return dic.get(int(n), default)
    except (TypeError, ValueError):
        return default


def texto_esencia(n: int) -> str:
    return get_dict_text(TEXTO_ESENCIA, n)


def texto_imagen(n: int) -> str:
    return get_dict_text(TEXTO_IMAGEN, n)


def texto_vida_pasada(n: int) -> str:
    return get_dict_text(TEXTO_VIDA_PASADA, n)


def texto_sendero(n: int) -> str:
    return get_dict_text(TEXTO_SENDERO_VIDA, n)


def texto_arcano(n: int) -> str:
    return get_dict_text(ARCANOS_RESUMIDOS, n, "Arcano: integración y conciencia.")


def texto_hogar(num_dir: int) -> str:
    return get_dict_text(TEXTO_HOGAR, num_dir, "Hogar: equilibrio, limpieza y armonía.")


def texto_telefono(num_tel: int) -> str:
    return get_dict_text(TEXTO_TELEFONO, num_tel, "Teléfono: comunicación consciente y límites sanos.")


def compatibilidad_express_texto(n: int) -> str:
    return get_dict_text(COMPATIBILIDAD_EXPRES, n, "Compatibilidad express no disponible.")


def compatibilidad_profunda_texto(n: int) -> str:
    return get_dict_text(COMPATIBILIDAD_PROFUNDA, n, "Compatibilidad profunda no disponible.")


def compatibilidad_numero(fecha_a: date, fecha_b: date) -> int:
    return reducir_numero(
        (fecha_a.day + fecha_a.month + fecha_a.year) +
        (fecha_b.day + fecha_b.month + fecha_b.year)
    )


def parrafo_premium_categoria(categoria: str, n: int) -> str:
    """
    Devuelve texto Premium por categoría (amor, dinero, emocional, proteccion)
    combinando frase + rasgos.
    """
    cat = str(categoria).strip().lower()

    rasgos = NUM_RASGOS.get(int(n), [])
    rtxt = " · ".join(rasgos) if isinstance(rasgos, (list, tuple)) else str(rasgos)

    if cat == "amor":
        frase = FRASES_AMOR.get(int(n), "")
    elif cat == "dinero":
        frase = FRASES_DINERO.get(int(n), "")
    elif cat == "emocional":
        frase = FRASES_EMOCIONAL.get(int(n), "")
    else:
        frase = FRASES_PROTECCION.get(int(n), "")

    return f"{frase}\n\nRasgos: {rtxt}".strip()



    # =====================================================
# 4. FORMULARIO ÚNICO — SOLO EXPRESS
# =====================================================
with st.form("lectura_express"):

    st.markdown("## ✍️ Ingresa tus datos")

    nombre_completo = st.text_input(
        "Nombre completo *"
    )

    fecha_nac = st.date_input(
        "Fecha de nacimiento *",
        min_value=date(1936, 1, 1),
        max_value=date(2036, 12, 31)
    )

    st.markdown("### 💞 Compatibilidad (opcional)")
    activar_compat_express = st.checkbox(
        "Activar compatibilidad express (Gratis)",
        value=False
    )

    fecha_pareja_express = st.date_input(
        "Fecha de nacimiento de la pareja",
        value=date(2000, 1, 1)
    )

    enviar = st.form_submit_button("✨ Generar lectura express")

    
 #==================================================   
# VALIDACIÓN
# =====================================================
if not nombre_completo or not fecha_nac:
    st.error("⚠️ La lectura requiere obligatoriamente el nombre completo y la fecha de nacimiento.")
    st.stop()

hoy = date.today()


# =====================================================
# CONTROL PREMIUM (DEMO + TOKEN + STRIPE LINK OPCIONAL)
# =====================================================
#def stripe_configurada() -> bool:
    #return bool(st.secrets.get("STRIPE_PRICE_URL", "")) or bool(os.getenv("STRIPE_PRICE_URL", ""))

#def obtener_stripe_url() -> str:
    ##return st.secrets.get("STRIPE_PRICE_URL", "") or os.getenv("STRIPE_PRICE_URL", "")

#def obtener_token_premium(nombre: str, fecha: date) -> str:
    #base = f"{nombre.strip().lower()}|{fecha.isoformat()}|Eugenia.Mistico"
    #return hashlib.sha256(base.encode("utf-8")).hexdigest()[:10].upper()



# =====================================================
## =====================================================
# EXPORTADORES / SALIDAS — PDF (SOLO PREMIUM)
# Código latente: se activa con validación premium
# =====================================================
# =====================================================
def build_pdf_bytes(
    nombre_completo: str,
    fecha_nac: date,
    n_sendero: int,
    n_esencia: int,
    n_imagen: int,
    n_pasada: int,
    ap: int,
    mp: int,
    dp: int,
    arcano: int,
    energia: str,
) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Eugenia.Místico · Lectura Numerológica (Premium)")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Nombre: {nombre_completo}")
    y -= 14
    c.drawString(50, y, f"Fecha de nacimiento: {fecha_nac.isoformat()}")
    y -= 18

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, f"Sendero de Vida: {n_sendero}")
    y -= 14
    c.drawString(50, y, f"Esencia: {n_esencia} · Imagen: {n_imagen} · Vida Pasada: {n_pasada}")
    y -= 14
    c.drawString(50, y, f"Ciclo: Año {ap} · Mes {mp} · Día {dp}")
    y -= 14
    c.drawString(50, y, f"Arcano: {arcano}")
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Energía del Día")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in textwrap.wrap(energia, width=90):
        c.drawString(50, y, line)
        y -= 12
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()



# =====================================================
# CÁLCULOS
# =====================================================
n_sendero = sendero_vida(fecha_nac)
n_esencia = esencia(nombre_completo)
n_imagen = imagen_externa(nombre_completo)
n_pasada = vida_pasada(fecha_nac)

ap = ano_personal(fecha_nac, hoy)
mp = mes_personal(fecha_nac, hoy)
dp = dia_personal(fecha_nac, hoy)

arc_p = arcano_personal(fecha_nac)

# Premium (se activará luego)
# num_dir = numero_apto(direccion_apto) if direccion_apto else None
# num_tel = numero_apto(telefono) if telefono else None


 #=====================================================
# 🟢 LECTURA GRATUITA (GENEROSA)
# =====================================================
st.markdown("## 🟢 Lectura Gratuita")

em_card(
    f"Sendero de Vida · {n_sendero}",
    "🧭",
    texto_sendero(n_sendero),
    "Tu dirección vital y aprendizaje"
)

em_card(
    f"Esencia · {n_esencia}",
    "💎",
    texto_esencia(n_esencia),
    "Tu vibración interna (nombre)"
)

em_card(
    f"Imagen · {n_imagen}",
    "✨",
    texto_imagen(n_imagen),
    "Cómo te perciben / tu proyección"
)

em_card(
    f"Vida Pasada · {n_pasada}",
    "🕯️",
    texto_vida_pasada(n_pasada),
    "Herencia energética del día de nacimiento"
)

em_card(
    f"Tu ciclo de hoy · Año {ap} · Mes {mp} · Día {dp}",
    "🗓️",
    "Este es tu clima numérico actual. Úsalo para tomar decisiones con coherencia."
)

if activar_compat_express:
    comp_ex = compatibilidad_numero(fecha_nac, fecha_pareja_express)
    em_card(
        f"Compatibilidad Express · Número {comp_ex}",
        "💞",
        compatibilidad_express_texto(comp_ex),
        "Express = orientación rápida. La lectura profunda está en Premium."
    )

# =====================================================
# 🔐 CORTE PREMIUM (VERSIÓN FINANCE · CON CLAVE)
# =====================================================
st.markdown("---")
st.markdown("## 🔐 Lectura Premium")
st.info(
    "Premium incluye: Energía del Día (365), Arcanos, compatibilidad profunda, "
    "hogar y teléfono energéticos, frases avanzadas y resumen extendido."
)

# Estado premium en sesión
es_premium = st.session_state.get("es_premium", False)

# ---- Entrada de CLAVE ----
st.markdown("### 🔑 Ingresa tu clave Premium")
clave_ingresada = st.text_input(
    "Clave Premium",
    type="password",
    placeholder="Ej: EM-AB12-CD34-EF56-GH78"
)

# ---- Validación de clave ----
# (usa la clave única que ya definiste por persona)
if clave_ingresada:
    clave_valida = generar_clave_unica(nombre_completo, fecha_nac)

    if clave_ingresada.strip().upper() == clave_valida:
        st.session_state["es_premium"] = True
        es_premium = True
        st.success("✅ Clave válida. Acceso Premium activado.")
    else:
        st.error("❌ Clave incorrecta. Verifica e intenta nuevamente.")

# =====================================================
# 💎 LECTURA PREMIUM (SOLO SI CLAVE ES VÁLIDA)
# =====================================================
if es_premium:

    # 🌅 Energía del día (365)
    em_card("Energía del Día", "🌅", energia_del_dia(hoy))

    # 🃏 Arcano personal
    em_card(f"Tu Arcano · {arc_p}", "🃏", texto_arcano(arc_p))

    # 💞 Compatibilidad profunda (solo si activó compatibilidad)
    if activar_compat_express:
        comp_pr = compatibilidad_numero(fecha_nac, fecha_pareja_express)
        em_card(
            f"Compatibilidad Profunda · Número {comp_pr}",
            "💞",
            compatibilidad_profunda_texto(comp_pr),
            "Lectura profunda y orientadora"
        )

    # 🏠 Energía del hogar
    if num_dir is not None:
        em_card("Energía del Hogar", "🏠", texto_hogar(num_dir))

    # 📞 Energía del teléfono
    if num_tel is not None:
        em_card("Energía del Teléfono", "📞", texto_telefono(num_tel))

    # 🔮 Resumen premium
    st.markdown("### 🔮 Resumen Final Premium")
    resumen = [
        f"1) Tu Sendero {n_sendero} marca tu dirección vital.",
        f"2) Tu Esencia {n_esencia} es tu motor interno.",
        f"3) Tu Imagen {n_imagen} define tu proyección.",
        f"4) Tu Vida Pasada {n_pasada} deja aprendizajes activos.",
        f"5) Hoy vibras en Año {ap}, Mes {mp}, Día {dp}.",
        "6) La coherencia es tu protección.",
        "7) Menos ruido, más verdad.",
        "8) Tu intuición se aclara cuando descansas.",
        "9) Pon límites con amor.",
        "10) Orden externo, paz interna.",
        "11) Cuida tu energía como ritual.",
        "12) Elige lo esencial.",
        "13) La claridad no grita.",
        "14) Agradece y suelta.",
        "15) Hoy, elegirte es suficiente."
    ]
    st.write("\n".join(resumen))

    # 📄 PDF Premium
    st.markdown("---")
    st.markdown("### 📄 Descargar PDF (Premium)")
    pdf_bytes = build_pdf_bytes(
        nombre_completo=nombre_completo,
        fecha_nac=fecha_nac,
        n_sendero=n_sendero,
        n_esencia=n_esencia,
        n_imagen=n_imagen,
        n_pasada=n_pasada,
        ap=ap,
        mp=mp,
        dp=dp,
        arcano=arc_p,
        energia=energia_del_dia(hoy),
    )
    st.download_button(
        "⬇️ Descargar lectura en PDF",
        data=pdf_bytes,
        file_name=f"Eugenia_Mistico_Lectura_{normalizar_clave_nombre(nombre_completo)}.pdf",
        mime="application/pdf",
    )

else:
    st.caption(
        "🔒 El acceso Premium requiere una clave válida. "
        "Si ya realizaste el pago, ingresa tu clave para desbloquear todo el contenido."
    )

