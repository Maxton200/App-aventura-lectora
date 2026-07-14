import streamlit as st
import time
import json
import random
import os
import base64
from datetime import datetime

# --- LIBRERÍAS ---
try:
    import google.generativeai as genai
    IA_DISPONIBLE = True
except ImportError:
    IA_DISPONIBLE = False

try:
    from gtts import gTTS
    from io import BytesIO
    AUDIO_DISPONIBLE = True
except ImportError:
    AUDIO_DISPONIBLE = False

st.set_page_config(page_title="Aventura Lectora Premium", layout="wide", page_icon="📚")

# --- DISEÑO VISUAL FLEXIBLE ---
ESTILO_CSS = """
    <style>
    @import url('[https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap](https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap)');
    html, body, [class*="css"]  { font-family: 'Nunito', sans-serif; }
    
    .tarjeta {
        background-color: var(--secondary-background-color); 
        border-radius: 15px; padding: 25px; margin-bottom: 25px;
        border-top: 5px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: var(--text-color);
    }
    
    .texto-lectura {
        font-size: 26px; line-height: 1.9;
        background-color: var(--secondary-background-color); 
        padding: 40px; border-radius: 20px;
        border: 2px solid #4CAF50;
        color: var(--text-color);
    }
    
    .instrucciones-api { 
        background-color: var(--secondary-background-color); 
        padding: 20px; border-radius: 12px; font-size: 16px; 
        margin-bottom: 25px; border-left: 6px solid #0284C7; 
        color: var(--text-color);
    }
    
    .cofre-palabras { 
        background-color: var(--secondary-background-color); 
        padding: 20px; border-radius: 15px; 
        margin-bottom: 15px; border-left: 5px solid #3B82F6; 
        color: var(--text-color);
    }
    
    .explicacion-ia { 
        background-color: var(--secondary-background-color); 
        padding: 15px; border-radius: 10px; 
        border-left: 5px solid #22C55E; margin-top: 10px; font-size: 18px; 
        color: var(--text-color);
    }
    
    div.stButton > button {
        font-size: 18px !important; font-weight: 800; border-radius: 12px;
        height: auto; padding: 10px 20px; transition: all 0.3s ease;
        width: 100%; border: 1px solid #4CAF50;
    }
    </style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- SISTEMA DE GESTIÓN DE PERFILES ---
def cargar_historial():
    if os.path.exists("historial_alumnos.json"):
        try:
            with open("historial_alumnos.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def guardar_historial(data):
    with open("historial_alumnos.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# --- INICIALIZACIÓN DE MEMORIA SEGURA ---
if 'bd_alumnos' not in st.session_state: st.session_state.bd_alumnos = cargar_historial()
if 'api_key_guardada' not in st.session_state:
    try: st.session_state.api_key_guardada = st.secrets.get("GOOGLE_API_KEY", "")
    except: st.session_state.api_key_guardada = ""

VALORES_POR_DEFECTO = {
    'estado': 'configuracion',
    'tiempo_inicio': 0,
    'tiempo_total': 0,
    'preguntas': [],
    'evaluado': False,
    'perfil_activo': None,
    'texto_original': "",
    'texto_lectura': "",
    'ajustes': {},
    'diccionario': [],
    'fragmento_idx': 0,
    'aventura_paso': 0,
    'aventura_opciones': [],
    'respuestas_usuario': {},
    'txt_base': "",
    'txt_manual': ""
}

for k, v in VALORES_POR_DEFECTO.items():
    if k not in st.session_state: st.session_state[k] = v

# --- FUNCIONES DE APOYO ---
def formato_bionico(texto):
    palabras = texto.split()
    res = []
    for w in palabras:
        if len(w) > 2: mitad = len(w)//2 + (len(w)%2); res.append(f"<b>{w[:mitad]}</b>{w[mitad:]}")
        else: res.append(f"<b>{w}</b>")
    return " ".join(res)

def generar_audio(texto):
    if not AUDIO_DISPONIBLE: return None
    try:
        tts = gTTS(text=texto, lang='es', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        return f'<audio controls src="data:audio/mp3;base64,{b64}" style="width:100%; margin-bottom: 20px;"></audio>'
    except: return None

# Truco matemático para evitar errores de sintaxis en GitHub
def limpiar_json(texto):
    texto = texto.strip()
    marcador = chr(96) + chr(96) + chr(96) 
    if marcador + "json" in texto: texto = texto.split(marcador + "json")[1]
    if marcador in texto: texto = texto.split(marcador)[0]
    inicio = texto.find('[')
    fin = texto.rfind(']') + 1
    return texto[inicio:fin] if inicio != -1 else texto

def obtener_ia():
    genai.configure(api_key=st.session_state.api_key_guardada)
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower():
            return genai.GenerativeModel(m.name)
    return genai.GenerativeModel('gemini-pro')

def generar_reporte_html(nombre, edad, curso, condicion, ppm, puntaje, total, diag):
    fecha = datetime.now().strftime("%d/%m/%Y")
    html = f"""
    <html><head><meta charset="utf-8"><style>body{{font-family: Arial; padding: 40px; color: #333; line-height: 1.6; background-color: white;}} .caja{{border: 2px solid #4CAF50; padding: 30px; border-radius: 15px;}} h1{{color: #2E7D32; text-align: center;}}</style></head>
    <body>
        <div class="caja">
            <h1>📄 Reporte Psicopedagógico PIE</h1>
            <p><b>Alumno:</b> {nombre} ({edad} años) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> {fecha}</p>
            <p><b>Curso:</b> {curso} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Condición:</b> {condicion}</p>
            <hr>
            <h3>📊 Resultados de la Evaluación</h3>
            <p><b>Velocidad Lectora:</b> {ppm} Palabras por Minuto (PPM).</p>
            <p><b>Comprensión Lectora:</b> {puntaje} respuestas correctas de {total}.</p>
            <hr>
            <h3>🧠 Análisis PROLEC-R (Adaptado)</h3>
            <p>{diag}</p>
            <br><p><i>Generado automáticamente por Aventura Lectora Premium.</i></p>
        </div>
    </body></html>
    """
    b64 = base64.b64encode(html.encode('utf-8')).decode('utf-8')
    return f'<a href="data:text/html;base64,{b64}" download="Reporte_Lectura_{nombre.replace(" ","_")}.html"><button style="background:#0284C7; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; font-size:18px; cursor:pointer; width:100%;">📥 Descargar Informe Completo (PDF/HTML)</button></a>'

# ==========================================
# BARRA LATERAL (GESTIÓN)
# ==========================================
with st.sidebar:
    st.title("👨‍🏫 Panel Docente")
    
    st.markdown("---")
    st.subheader("👥 Gestión de Alumnos")
    opciones_alumnos = ["➕ Crear Nuevo Perfil..."] + list(st.session_state.bd_alumnos.keys())
    seleccion = st.selectbox("Seleccionar Alumno:", opciones
