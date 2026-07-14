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
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');
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

def limpiar_json(texto):
    texto = texto.strip()
    if "```json" in texto: texto = texto.split("```json")[1]
    if "```" in texto: texto = texto.split("
