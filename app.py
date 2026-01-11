
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

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
APP_TITLE = "🔮 Lectura Numerológica"
BRAND = "Eugenia.Mystikos"

st.set_page_config(
    page_title=f"{APP_TITLE} · {BRAND}",
    page_icon="🔮",
    layout="centered",
)

# =====================================================
# ESTILO VISUAL (CSS)
# =====================================================
st.markdown("""
<style>
/* Fondo general */
html, body, [data-testid="stApp"] {
    background-color: #FBF9FD;
}

/* Títulos principales */
h1, h2, h3 {
    color: #3E2A5E;
    letter-spacing: 0.4px;
}

/* Subtítulos */
h4, h5 {
    color: #5A3E85;
}

/* Texto normal */
p, li, span {
    color: #3B2F4A;
    font-size: 1.02rem;
    line-height: 1.65;
}

/* Tarjetas suaves */
.card {
    background: linear-gradient(135deg, #F6EEF8, #EFE6F5);
    padding: 22px;
    border-radius: 22px;
    border: 1px solid #E3D6ED;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}

/* Separadores */
.divider {
    height: 1px;
    background: linear-gradient(to right, transparent, #C9B6E4, transparent);
    margin: 30px 0;
}

/* Botón principal */
button[kind="primary"] {
    background: linear-gradient(135deg, #7B4AE2, #A88CF0);
    border-radius: 18px;
    border: none;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
}

/* Eugenia.Mystikos UI system */
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
.em-sep{
  height: 1px;
  background: linear-gradient(to right, transparent, #C9B6E4, transparent);
  margin: 26px 0;
}
</style>
""", unsafe_allow_html=True)

# Helper para tarjetas con estilo Eugenia.Mystikos
def em_card(titulo: str, icono: str, contenido: str, muted: str = ""):
    st.markdown(f"""
        <div class="em-card">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <div style="font-size:1.25rem;">{icono}</div>
                <div style="font-weight:700; font-size:1.05rem;">{titulo}</div>
            </div>
            <div style="font-size:1.02rem; line-height:1.7;">{contenido}</div>
            {f'<div class="em-muted">{muted}</div>' if muted else ''}
        </div>
    """, unsafe_allow_html=True)

# =====================================================
# MENSAJES MYSTIKOS DEL DÍA (1-365)
# =====================================================
MENSAJES_MYSTIKOS = {
    1: "Hoy no apresures nada. La energía se ordena cuando eliges presencia en lugar de urgencia.",
    2: "Confía en tu ritmo. No todo florece el mismo día, pero todo responde a la intención correcta.",
    3: "Lo que hoy parece pequeño está sembrando una verdad más grande.",
    4: "La estructura no es cárcel, es sostén. Hoy organiza tu espacio para liberar tu mente.",
    5: "El cambio es la única constante. No te resistas al movimiento, fluye con la curiosidad.",
    6: "Vuelve al centro del corazón. Hoy el equilibrio nace de cuidar tus vínculos más cercanos.",
    7: "El silencio es una respuesta. Regálate un momento de pausa para escuchar tu propia voz.",
    8: "Tu poder personal reside en la coherencia. Actúa hoy según lo que realmente valoras.",
    9: "Suelta lo que ya cumplió su ciclo. Para que algo nuevo llegue, debe haber espacio.",
    10: "Un nuevo comienzo se asoma. Confía en tu capacidad de reinventarte hoy.",
    11: "Tu intuición está afinada. No busques fuera lo que tu sabiduría interna ya te está susurrando.",
    12: "Mira las cosas desde otro ángulo. La flexibilidad mental abre puertas que antes no veías.",
    13: "Transformar es morir a lo viejo para nacer a lo auténtico. No temas a la metamorfosis.",
    14: "La moderación es tu aliada. Encuentra el punto medio entre el hacer y el ser.",
    15: "Observa tus sombras sin juicio. Reconocerlas es el primer paso para integrarlas.",
    16: "Lo que se derrumba libera terreno. No llores las ruinas, celebra el espacio para lo nuevo.",
    17: "La esperanza es una dirección, no una espera. Camina hoy hacia tu propia luz.",
    18: "Tus sueños hablan. Presta atención a los mensajes que surgen del inconsciente.",
    19: "Brilla con luz propia. No necesitas permiso para ocupar tu lugar en el mundo.",
    20: "Hoy es un día de cosecha interna. Reconoce cuánto has crecido en este tiempo.",
    21: "El éxito es vivir en plenitud. Hoy celebra estar presente y consciente de tu camino.",
    22: "Tus sueños grandes requieren bases sólidas. Construye hoy con visión y paciencia.",
    23: "La comunicación es un puente. Elige palabras que construyan y sanen.",
    24: "El amor empieza por casa. Trátate hoy con la misma ternura que ofreces a los demás.",
    25: "La introspección te dará la clave. Busca el silencio para encontrar la claridad.",
    26: "La justicia interna es equilibrio. Sé justo contigo mismo antes de pedir justicia fuera.",
    27: "Tu voluntad es tu motor. No dejes que las dudas externas apaguen tu determinación.",
    28: "La paciencia es una forma de fe. Todo llega en el momento en que estás listo para recibirlo.",
    29: "La sabiduría se encuentra en lo simple. Hoy menos es más.",
    30: "Tu creatividad pide paso. Exprésate sin miedo al qué dirán.",
    31: "Cierra este ciclo con gratitud. Todo lo vivido te ha preparado para lo que viene.",
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

# =====================================================
# CONTINUACIÓN DE LÓGICA DE MENSAJES
# =====================================================
def mensaje_Mystikos_del_dia() -> str:
    """Devuelve el mensaje del día según el día del año (1–365)."""
    dia = datetime.now().timetuple().tm_yday  # 1..365
    return MENSAJES_MYSTIKOS.get(dia) or MENSAJES_MYSTIKOS.get(((dia - 1) % 365) + 1) or "Hoy vuelve a tu centro."

# =====================================================
# SECRETOS (STREAMLIT CLOUD + LOCAL)
# =====================================================
def get_secret(key: str, default=None):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
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
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
    except:
        pass
    return 0

def incrementar_contador():
    total = leer_contador() + 1
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(total))
    except:
        pass
    return total

# =====================================================
# 🌞 ENERGÍA MÍSTICA DEL DÍA (Bloque visual)
# =====================================================
hoy = date.today()
hoy_actual = hoy  # alias para evitar confusiones
dia_del_ano = hoy.timetuple().tm_yday

html_energia = f"""
<div style="font-family: inherit;">
  <div style="text-align:center; max-width:520px; margin:auto; padding:22px; border-radius:22px; border:1px solid #E3D6ED; background:linear-gradient(135deg,#F6EEF8,#EFE6F5); box-shadow:0 6px 18px rgba(0,0,0,0.06);">
    <div style="font-size:0.78rem; letter-spacing:0.14em; text-transform:uppercase; color:#6b5a7a; margin-bottom:6px;">
      Energía mística del día · {hoy.strftime('%d/%m/%Y')}
    </div>
    <div style="font-size:1.05rem; line-height:1.7; margin-top:10px;">
      ☀️ <strong>{mensaje_Mystikos_del_dia()}</strong>
    </div>
    <div style="margin-top:10px; font-size:0.85rem; color:#6b5a7a;">
      Pulso energético correspondiente al día {dia_del_ano} del ciclo anual.
    </div>
  </div>
</div>
"""

components.html(html_energia, height=180)

# =====================================================
# TEXTO INTRODUCTORIO
# =====================================================
st.markdown(
    """
    <div class="em-card">
      <strong>🧭 Sobre esta lectura</strong><br/><br/>
      Esta lectura no es una predicción ni una promesa externa.  
      Es una orientación energética consciente, basada en la vibración que se activa a partir de tu fecha de nacimiento y tu nombre.  
      Cada nombre refleja una frecuencia, y cada frecuencia describe una forma de transitar la vida en este momento.<br/><br/>
      Aquí no buscamos decirte qué va a pasar, sino ayudarte a comprender qué energía está disponible para ti ahora, cómo se manifiesta internamente
      y qué tipo de decisiones se alinean mejor con tu proceso actual.  
      La numerología, cuando se usa con consciencia, no limita: ordena, revela y enfoca.<br/><br/>
      ✨ <strong>Esta lectura no te quita responsabilidad: te la devuelve.</strong><br/>
      Tómala como una brújula, no como un destino.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="em-sep"></div>', unsafe_allow_html=True)

# =====================================================
# UTILIDADES NUMEROLÓGICAS (CÁLCULOS)
# =====================================================
MASTER = {11, 22, 33}

def reducir_numero(n: int) -> int:
    n = abs(int(n))
    if n == 0: return 0
    if n in MASTER: return n
    while n > 9:
        n = sum(int(d) for d in str(n))
        if n in MASTER: return n
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
    total = sum(TABLA_PITAGORICA.get(char, 0) for char in normalizar_texto(nombre) if char.isalpha())
    return reducir_numero(total)

def sumar_digitos_texto(txt: str) -> int:
    digs = re.findall(r"\d", str(txt))
    if not digs: return 0
    return reducir_numero(sum(int(d) for d in digs))

def numero_apto(apto: str) -> int:
    apto = str(apto).strip()
    if not apto: return 0
    if re.search(r"\d", apto): return sumar_digitos_texto(apto)
    return numero_nombre(apto)

# Funciones de Tiempo y Vibración
def esencia(f: date) -> int: return reducir_numero(f.day)
def imagen_externa(f: date) -> int: return reducir_numero(f.month)
def vida_pasada(f: date) -> int: return reducir_numero(f.year)
def sendero_vida(f: date) -> int: return reducir_numero(f.day + f.month + f.year)
def ano_personal(f: date, y: int) -> int: return reducir_numero(f.day + f.month + y)
def mes_personal(ap: int, m: int) -> int: return reducir_numero(ap + m)
def semana_personal(mp: int, s: int) -> int: return reducir_numero(mp + s)
def dia_personal(mp: int, d: int) -> int: return reducir_numero(mp + d)

def pinaculo_piramide(f: date) -> dict:
    d, m, a = reducir_numero(f.day), reducir_numero(f.month), reducir_numero(f.year)
    p1, p2 = reducir_numero(d + m), reducir_numero(d + a)
    p3 = reducir_numero(p1 + p2)
    p4 = reducir_numero(m + a)
    return {"base": (p1, p2, p4), "medio": (p1+p2, p2+p4), "cima": p3}

# =====================================================
# 📚 BLOQUE COMPLETO DE DICCIONARIOS (Copia aquí tus textos)
# =====================================================

## =====================================================
# COMPATIBILIDAD DE PAREJA (EXPRESS / PREMIUM)
# =====================================================
COMPAT_EXPRESS = {
    1: "Compatibilidad 1: chispa de inicio. Funciona si hay acuerdos claros y espacio personal.",
    2: "Compatibilidad 2: sensibilidad y cooperación. Se sostiene con comunicación suave y paciencia.",
    3: "Compatibilidad 3: alegría y expresión. Cuiden el respeto para que la energía no se disperse.",
    4: "Compatibilidad 4: estabilidad y construcción. Requiere constancia, límites y proyecto real.",
    5: "Compatibilidad 5: libertad y cambio. Pide flexibilidad; eviten controlar al otro.",
    6: "Compatibilidad 6: hogar y cuidado. Se fortalece con compromiso emocional y equilibrio.",
    7: "Compatibilidad 7: profundidad y espacio. Necesitan silencio, confianza y tiempos propios.",
    8: "Compatibilidad 8: poder y logro. Funciona con ética, acuerdos y sin competencia.",
    9: "Compatibilidad 9: cierre y madurez. Sana si sueltan expectativas y practican perdón.",
    11: "Compatibilidad 11: vínculo espejo. Alta sensibilidad: cuiden límites energéticos.",
    22: "Compatibilidad 22: construcción grande. Si hay visión compartida, deja legado.",
    33: "Compatibilidad 33: amor consciente. Acompañar sin rescatar es la clave.",
}

def compatibilidad_numero(fecha1: date, fecha2: date) -> int:
    total = (
        fecha1.day + fecha1.month + fecha1.year +
        fecha2.day + fecha2.month + fecha2.year
    )
    return reducir_numero(total)

def compatibilidad_express_texto(num: int) -> str:
    return COMPAT_EXPRESS.get(num, "Compatibilidad: lectura no disponible para este número.")


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
# FRASES CLAVE (AMOR / DINERO / EMOCIONAL / PROTECCIÓN)
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
# PAGO: TEXTOS PROFUNDOS (10–12 líneas aprox)
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
        f"En {categoria}, tu ciclo se ordena desde la vibración {ap}: un núcleo de {a} que marca el ritmo principal. "
        f"Esto se expresa en decisiones, personas que aparecen, límites que se piden y oportunidades que solo se abren cuando eliges con presencia."
    )
    detalle = (
        f"Tu Mes Personal {mp} ajusta el clima emocional y práctico del momento, y tu Semana Personal {sp} revela el tema inmediato. "
        f"Hoy, con Día Personal {dp}, la vida te muestra en pequeño lo que debes practicar en grande: coherencia, enfoque y verdad."
    )
    guia = (
        f"La llave está en refinar tu {b} y tu {c}: no reaccionar, sino decidir. "
        f"Si {categoria.lower()} se siente tenso, no es castigo: es señal de reorden. "
        f"El movimiento correcto suele ser uno: un límite sano, una conversación clara o un hábito sostenido. "
        f"Cuando actúas alineada con tu vibración, el resultado se siente: menos desgaste, más paz, y avance real."
    )
    return f"{base}\n\n{detalle}\n\n{guia}"

# =====================================================
# TEXTOS PREMIUM PROPIOS (TELÉFONO / HOGAR)
# =====================================================

# -------------------------------------------------
# FRASE CLAVE (SENDEROS / NÚMEROS BASE)
# -------------------------------------------------
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

# -------------------------------------------------
# TEXTOS PREMIUM POR CATEGORÍA
# (Puedes ampliar estos textos cuando quieras)
# -------------------------------------------------
TEXTOS_PREMIUM = {
    "Amor y vínculos": FRASES_AMOR,
    "Dinero y prosperidad": FRASES_DINERO,
    "Energía emocional": FRASES_EMOCIONAL,
    "Protección energética": FRASES_PROTECCION,
    # Para tiempo: usamos los mismos diccionarios como base.
    "Año personal": FRASES_EMOCIONAL,
    "Mes personal": FRASES_EMOCIONAL,
    "Día personal": FRASES_EMOCIONAL,
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


def texto_telefono(numero: int) -> str:
    return TEXTO_TELEFONO.get(
        numero,
        "La vibración del teléfono no pudo ser interpretada con claridad."
    )

# =====================================================
# HOGAR / DIRECCIÓN — DEFINICIONES (PREMIUM)
# =====================================================

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

# -------------------------------------------------
# TEXTOS BASE (ESENCIA / IMAGEN / VIDA PASADA / SENDERO)
# Nota: estos textos son "micro". Puedes personalizarlos a tu estilo.
# -------------------------------------------------
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


def texto_hogar(numero: int) -> str:
    return TEXTO_HOGAR.get(
        numero,
        "La vibración del hogar no pudo determinarse con claridad. "
        "Revisa los datos ingresados o ajusta la información para obtener una lectura precisa."
    )


# =====================================================
# COMPATIBILIDAD DE PAREJA — EXPRES (NO PREMIUM)
# Basada SOLO en fecha de nacimiento
# =====================================================

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


  
# =====================================================
# COMPATIBILIDAD DE PAREJA — PROFUNDA (PREMIUM)
# Basada en FECHA DE NACIMIENTO
# =====================================================

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
 ####=====================================================
# ARCANOS MAYORES
# =====================================================
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

## =====================================================
# 🔍 FUNCIONES DE BÚSQUEDA (CONECTAN CÁLCULOS CON TUS TEXTOS)
# =====================================================

def obtener_texto_esencia(n: int) -> str:
    """Busca en tu diccionario TEXTO_ESENCIA."""
    return TEXTO_ESENCIA.get(n, "Vibración de esencia en proceso de ajuste.")

def obtener_texto_imagen(n: int) -> str:
    """Busca en tu diccionario TEXTO_IMAGEN."""
    return TEXTO_IMAGEN.get(n, "Vibración de imagen en proceso de ajuste.")

def obtener_texto_vida_pasada(n: int) -> str:
    """Busca en tu diccionario TEXTO_VIDA_PASADA."""
    return TEXTO_VIDA_PASADA.get(n, "Vibración de vida pasada en proceso de ajuste.")

def obtener_texto_sendero(n: int) -> str:
    """Busca en tu diccionario TEXTO_SENDERO_VIDA."""
    return TEXTO_SENDERO_VIDA.get(n, "Vibración de sendero en proceso de ajuste.")

def obtener_frase_clave(n: int) -> str:
    """Busca en tu diccionario FRASE_CLAVE."""
    return FRASE_CLAVE.get(n, "Frecuencia en resonancia.")

def arcano_micro(arc: int) -> str:
    """Busca en tu diccionario ARCANOS_RESUMIDOS o DICCIONARIO_ARCANOS."""
    # Intentamos buscar en el diccionario de Arcanos que tengas definido
    return ARCANOS_RESUMIDOS.get(arc, "Mensaje del arcano no disponible.")

def texto_hogar(n: int) -> str:
    """Busca en tu diccionario TEXTO_HOGAR."""
    return TEXTO_HOGAR.get(n, "Vibración del hogar no calculada.")


# =====================================================
# 💎 FUNCIÓN PREMIUM (BUSCA POR CATEGORÍAS)
# =====================================================
def parrafo_premium_categoria(num, mp, sp, dp, categoria):
    """
    Busca en el diccionario TEXTOS_PREMIUM según la categoría solicitada:
    'Amor y vínculos', 'Dinero y prosperidad', 'Energía emocional', etc.
    """
    # Verificamos que el diccionario TEXTOS_PREMIUM exista y tenga la categoría
    if 'TEXTOS_PREMIUM' in globals() and categoria in TEXTOS_PREMIUM:
        return TEXTOS_PREMIUM[categoria].get(num, f"Contenido de {categoria} en desarrollo.")
    return "Análisis detallado en preparación."

def obtener_compatibilidad_profunda(n: int) -> str:
    """Busca en tu diccionario COMPATIBILIDAD_PROFUNDA."""
    return COMPATIBILIDAD_PROFUNDA.get(n, "Texto de compatibilidad no disponible.")
def obtener_compatibilidad(n: int, tipo="express") -> str:
    """Busca según el tipo: express, resumen o profunda."""
    if tipo == "express": return COMPATIBILIDAD_EXPRES.get(n, "")
    if tipo == "profunda": return COMPATIBILIDAD_PROFUNDA.get(n, "")
    return ""


# =====================================================
# DICCIONARIOS ADICIONALES (Los que estaban al final)
# =====================================================
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

def arcano_micro(arc: int) -> str:
    """Función de búsqueda para el mensaje del Arcano."""
    return ARCANOS_RESUMIDOS.get(arc, "Mensaje no disponible por el momento.")

# =====================================================
# GENERACIÓN DE CLAVE ÚNICA (HMAC/SHA256)
# =====================================================
def normalizar_clave_nombre(txt: str) -> str:
    txt = unicodedata.normalize("NFD", str(txt))
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[^A-Za-z\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip().upper()
    return txt

def generar_clave_unica(nombre_completo: str, fecha_nac: date) -> str:
    """Crea una clave EM-XXXX-XXXX-XXXX-XXXX única para cada persona."""
    nombre_normalizado = normalizar_clave_nombre(nombre_completo)
    # Usamos APP_SECRET para que la clave sea segura e incuificable
    payload = f"{nombre_normalizado}|{fecha_nac.isoformat()}".encode("utf-8")
    digest = hmac.new(APP_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest().upper()
    core = digest[:16]
    return f"EM-{core[:4]}-{core[4:8]}-{core[8:12]}-{core[12:16]}"

# =====================================================
# CONSTRUCTOR DE PDF (REPORTLAB)
# =====================================================
def build_pdf_bytes(titulo: str, secciones: list[tuple[str, str]]) -> bytes:
    """Crea el archivo PDF con todas las interpretaciones numerológicas."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    x = 50
    y = height - 60

    # Título y Branding
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, titulo)
    y -= 22
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"{BRAND} · Lectura Energética Personalizada")
    y -= 18

    def draw_paragraph(text: str, current_y: int):
        c.setFont("Helvetica", 11)
        wrapped_lines = []
        for para in str(text).split("\n"):
            para = para.strip()
            if not para:
                wrapped_lines.append("")
                continue
            wrapped_lines.extend(textwrap.wrap(para, width=90))
            wrapped_lines.append("")
            
        for ln in wrapped_lines:
            if current_y < 80: # Salto de página
                c.showPage()
                current_y = height - 60
            c.drawString(x, current_y, ln)
            current_y -= 14
        return current_y

    # Escribir cada sección (Esencia, Pareja, etc.)
    for head, body in secciones:
        if y < 120:
            c.showPage()
            y = height - 60
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x, y, head)
        y -= 18
        y = draw_paragraph(body, y)
        y -= 8

    c.save()
    buffer.seek(0)
    return buffer.read()
# =====================================================
# 🖥️ LÓGICA DE VISUALIZACIÓN (DENTRO DEL IF NOMBRE Y FECHA)
# =====================================================

# =====================================================
# 🧾 FORMULARIO (ENTRADAS)
# =====================================================
st.markdown("## ✍️ Ingresa tus datos")

with st.form("form_lectura"):
    nombre_completo = st.text_input("Nombre completo", value="", placeholder="Ej: Eugenia Místico")
    fecha_nac = st.date_input("Fecha de nacimiento", value=date(2000, 1, 1), format="DD/MM/YYYY")

    st.markdown("### Opcional (pareja)")
    nombre_pareja = st.text_input("Nombre de tu pareja (opcional)", value="", placeholder="Ej: Carlos")
    fecha_pareja = st.date_input("Fecha de nacimiento de tu pareja (opcional)", value=date(2000, 1, 1), format="DD/MM/YYYY")

    st.markdown("### Opcional (entorno)")
    direccion_apto = st.text_input("Dirección / Apto (opcional)", value="", placeholder="Ej: Torre A, Apto 12B")
    telefono = st.text_input("Teléfono (opcional)", value="", placeholder="Ej: +58 412 123 4567")

    generar = st.form_submit_button("🔮 Generar lectura")

# Normalización de opcionales
nombre_pareja = nombre_pareja.strip() or None
direccion_apto = direccion_apto.strip() or None
telefono = telefono.strip() or None

# En Streamlit, date_input devuelve un datetime.date o None.
# Si la usuaria no selecciona fecha, queda None.
if not generar:
    st.stop()

# =====================================================
# 🔢 CÁLCULOS PRINCIPALES (TIEMPOS Y NÚMEROS)
# =====================================================
# Hoy (para año/mes/día personal)
anio_actual = hoy.year
mes_actual = hoy.month
dia_actual = hoy.day
semana_actual = hoy.isocalendar().week

# Personal (Año/Mes/Semana/Día) - SIEMPRE que haya fecha_nac
ap_p = ano_personal(fecha_nac, anio_actual)
mp_p = mes_personal(ap_p, mes_actual)
sp_p = semana_personal(mp_p, semana_actual)
dp_p = dia_personal(mp_p, dia_actual)

# Vibración base (Esencia / Imagen / Vida pasada / Sendero)
n_esencia = esencia(fecha_nac)
n_imagen = imagen_externa(fecha_nac)
n_pasada = vida_pasada(fecha_nac)
n_sendero = sendero_vida(fecha_nac)

# Entorno (hogar / teléfono)
num_dir = numero_apto(direccion_apto) if direccion_apto else 0
num_tel = numero_apto(telefono) if telefono else 0

# Arcano semanal (1..22)
arc_p = semana_actual % 22
arc_p = 22 if arc_p == 0 else arc_p


if nombre_completo and fecha_nac:
    # Mostramos la clave única que generamos en la Parte 4
    clave_lectura = generar_clave_unica(nombre_completo, fecha_nac)
    st.success(f"Lectura generada con éxito. Clave: *{clave_lectura}*")

    # --- 1. BLOQUE DE ESENCIA Y SENDERO (TEXTOS PROFUNDOS) ---
    st.markdown("### 🏺 Tu Vibración Base")
    em_card("Tu Esencia (Día)", "✨", obtener_texto_esencia(n_esencia))
    em_card("Imagen Externa (Mes)", "🎭", obtener_texto_imagen(n_imagen))
    em_card("Vida Pasada (Año)", "📜", obtener_texto_vida_pasada(n_pasada))
    
    st.markdown('<div class="em-sep"></div>', unsafe_allow_html=True)
    
    em_card(f"Sendero de Vida: {n_sendero}", "🛣️", 
            obtener_texto_sendero(n_sendero), 
            f"Frase Maestra: {obtener_frase_clave(n_sendero)}")

    # --- 2. BLOQUE PREMIUM (USANDO EL DICCIONARIO TEXTOS_PREMIUM) ---
    with st.expander("💎 Análisis Premium Detallado"):
        st.markdown("#### Energía de este momento")
        st.write(f"*Año Personal {ap_p}:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, 'Año personal'))
        st.write(f"*Mes Personal {mp_p}:* " + parrafo_premium_categoria(mp_p, mp_p, sp_p, dp_p, 'Mes personal'))
        
        st.markdown("#### Pilares de Vida")
        st.info("*Amor y vínculos:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Amor y vínculos"))
        st.info("*Dinero y prosperidad:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Dinero y prosperidad"))
        st.info("*Protección energética:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Protección energética"))

    # --- 3. COMPATIBILIDAD DE PAREJA (SI SE INGRESÓ) ---
    if nombre_pareja and fecha_pareja:
        n_p_sendero = sendero_vida(fecha_pareja)
        n_comp_final = reducir_numero(n_sendero + n_p_sendero)
        st.markdown(f"### 💞 Compatibilidad con {nombre_pareja}")
        st.write(obtener_compatibilidad_profunda(n_comp_final))

    # --- 4. ENTORNO Y ARCANOS ---
    col_a, col_b = st.columns(2)
    with col_a:
        if direccion_apto:
            em_card(f"Hogar: {num_dir}", "🏠", texto_hogar(num_dir))
    with col_b:
        if telefono:
            em_card(f"Teléfono: {num_tel}", "📱", texto_telefono(num_tel))

    st.markdown("### 🃏 Arcano de la Semana")
    st.info(arcano_micro(arc_p))

    # --- 5. BOTÓN DE DESCARGA PDF ---
    # Aquí unimos todos los textos para el archivo final
    secciones_pdf = [
        ("Esencia", obtener_texto_esencia(n_esencia)),
        ("Sendero de Vida", obtener_texto_sendero(n_sendero)),
        ("Amor y Vínculos", parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Amor y vínculos")),
        ("Dinero y Prosperidad", parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Dinero y prosperidad")),
        ("Vibración del Hogar", texto_hogar(num_dir) if direccion_apto else "No ingresado"),
        ("Mensaje del Arcano", arcano_micro(arc_p))
    ]
    
    pdf_bytes = build_pdf_bytes(f"Lectura de {nombre_completo}", secciones_pdf)
    st.download_button("📥 Descargar Lectura PDF", pdf_bytes, f"{nombre_completo}_Lectura.pdf", "application/pdf")

# =====================================================
    # 🎨 RESULTADOS VISUALES (LA PARTE BONITA)
    # =====================================================
    
    # 1. Hero / Cabecera de la lectura
    st.markdown(f"""
        <div class="em-hero">
            <div class="em-hero-badge">🔮 {BRAND}</div>
            <div class="em-hero-title">Tu Mapa Vibracional</div>
            <div class="em-hero-sub">Clave única: {clave_lectura}</div>
        </div>
    """, unsafe_allow_html=True)

    # 2. Bloque de Vibraciones de Nacimiento (Iconos diseñados)
    st.markdown("### 🏺 Tu Configuración de Origen")
    
    c1, c2 = st.columns(2)
    with c1:
        em_card("Tu Esencia", "✨", obtener_texto_esencia(n_esencia), 
                f"Vibración de tu día de nacimiento ({fecha_nac.day})")
        
        em_card("Imagen Externa", "🎭", obtener_texto_imagen(n_imagen), 
                f"Vibración de tu mes de nacimiento ({fecha_nac.month})")

    with c2:
        em_card("Talento Heredado", "📜", obtener_texto_vida_pasada(n_pasada), 
                f"Vibración de tu año de nacimiento ({fecha_nac.year})")
        
        em_card("Misión de Vida", "🛣️", obtener_texto_sendero(n_sendero), 
                f"Tu Sendero de Vida es el número {n_sendero}")

    st.markdown('<div class="em-sep"></div>', unsafe_allow_html=True)

    # 3. Bloque de Tiempos (Métricas Visuales)
    st.markdown("### ⏳ Tu Clima Energético Actual")
    m1, m2, m3 = st.columns(3)
    m1.metric("Año Personal", ap_p)
    m2.metric("Mes Personal", mp_p)
    m3.metric("Día Personal", dp_p)

    with st.expander("📖 Leer interpretación de mis tiempos"):
        st.write(f"*Este Año ({hoy_actual.year}):* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, 'Año personal'))
        st.write(f"*Este Mes:* " + parrafo_premium_categoria(mp_p, mp_p, sp_p, dp_p, 'Mes personal'))
        st.write(f"*Esta Semana:* " + parrafo_premium_categoria(sp_p, mp_p, sp_p, dp_p, 'Semana personal'))

    # 4. Bloque Premium (Amor, Dinero y Protección con iconos)
    st.markdown("### 💎 Análisis Premium")
    
    st.info("💞 *Amor y vínculos:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Amor y vínculos"))
    st.success("💰 *Dinero y prosperidad:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Dinero y prosperidad"))
    st.warning("🛡️ *Protección energética:* " + parrafo_premium_categoria(ap_p, mp_p, sp_p, dp_p, "Protección energética"))

    # 5. Compatibilidad (Si aplica)
    if nombre_pareja:
        st.markdown(f"### 💞 Compatibilidad con {nombre_pareja}")
        em_card("Vínculo Profundo", "💘", obtener_compatibilidad_profunda(n_comp_final))

    # 6. Entorno y Arcanos
    st.markdown("### 🏠 Tu Entorno y Guía")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if direccion_apto:
            em_card(f"Hogar: {num_dir}", "🏠", texto_hogar(num_dir))
    with col_e2:
        if telefono:
            em_card(f"Teléfono: {num_tel}", "📱", texto_telefono(num_tel))

    st.markdown('<div class="em-card" style="border-left: 5px solid #7B4AE2;">'
                f'<strong>🃏 Arcano de la Semana:</strong><br>{arcano_micro(arc_p)}'
                '</div>', unsafe_allow_html=True)
