import streamlit as st
import time
import json
import random
import os
import base64
from datetime import datetime

# Nuevas librerías
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

st.set_page_config(page_title="Aventura Lectora Premium", layout="wide", page_icon="🚀")

# --- DISEÑO VISUAL AVANZADO (UI/UX) ---
ESTILO_CSS = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');
    html, body, [class*="css"]  { font-family: 'Nunito', sans-serif; }
    
    .stApp { background-color: #F8F9FA; }
    
    .tarjeta {
        background: white; border-radius: 20px; padding: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 25px;
        border-top: 5px solid #4CAF50;
    }
    .texto-lectura {
        font-size: 26px; line-height: 1.9; color: #2C3E50;
        background-color: #FFFDE7; padding: 40px; border-radius: 20px;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.02); border: 2px solid #FFF59D;
    }
    
    .stButton > button {
        font-size: 20px !important; font-weight: 800; border-radius: 15px;
        height: auto; padding: 15px 30px; transition: all 0.3s cubic-bezier(.25,.8,.25,1);
        border: none; width: 100%;
    }
    .stButton > button:hover { transform: translateY(-3px); box-shadow: 0 7px 14px rgba(0,0,0,0.1); }
    
    .cofre-palabras { background: #E3F2FD; padding: 20px; border-radius: 15px; margin-bottom: 15px; border-left: 5px solid #2196F3;}
    .explicacion-ia { background: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-top: 10px; font-size: 18px;}
    </style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- SISTEMA DE GESTIÓN DE PERFILES (HISTORIAL) ---
def cargar_historial():
    if os.path.exists("historial_alumnos.json"):
        try:
            with open("historial_alumnos.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def guardar_historial(data):
    with open("historial_alumnos.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

if 'bd_alumnos' not in st.session_state: st.session_state.bd_alumnos = cargar_historial()

# --- MEMORIA DE LA SESIÓN ---
VARIABLES = ['estado', 'tiempo_inicio', 'tiempo_total', 'preguntas', 'evaluado', 'api_key_guardada', 'perfil_activo', 'texto_original', 'texto_lectura', 'ajustes', 'diccionario', 'fragmento_idx', 'aventura_paso', 'aventura_opciones']
for v in VARIABLES:
    if v not in st.session_state: st.session_state[v] = None

if st.session_state.estado is None: st.session_state.estado = 'configuracion'
if st.session_state.ajustes is None: st.session_state.ajustes = {}
if st.session_state.api_key_guardada is None:
    try: st.session_state.api_key_guardada = st.secrets.get("GOOGLE_API_KEY", "")
    except: st.session_state.api_key_guardada = ""

# --- FUNCIONES DE APOYO COGNITIVO ---
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
    if "```" in texto: texto = texto.split("```")[0]
    inicio = texto.find('[')
    fin = texto.rfind(']') + 1
    return texto[inicio:fin] if inicio != -1 else texto

def obtener_ia():
    genai.configure(api_key=st.session_state.api_key_guardada)
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower():
            return genai.GenerativeModel(m.name)
    return genai.GenerativeModel('gemini-pro')

# --- GENERADOR DE REPORTES (HTML Descargable / Imprimible) ---
def generar_reporte_html(nombre, edad, curso, condicion, ppm, puntaje, total, diag):
    fecha = datetime.now().strftime("%d/%m/%Y")
    html = f"""
    <html><head><meta charset="utf-8"><style>body{{font-family: Arial; padding: 40px; color: #333; line-height: 1.6;}} .caja{{border: 2px solid #4CAF50; padding: 30px; border-radius: 15px;}} h1{{color: #2E7D32; text-align: center;}}</style></head>
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
    return f'<a href="data:text/html;base64,{b64}" download="Reporte_Lectura_{nombre.replace(" ","_")}.html"><button style="background:#2196F3; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; font-size:18px; cursor:pointer; width:100%;">📥 Descargar Informe Completo (PDF/HTML)</button></a>'

# ==========================================
# BARRA LATERAL: GESTIÓN DE PERFILES E IA
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3253/3253200.png", width=100)
    st.title("Panel Docente")
    
    if not st.session_state.api_key_guardada:
        api_input = st.text_input("🔑 Clave de IA (Google API):", type="password", value=st.session_state.api_key_guardada)
        if api_input: st.session_state.api_key_guardada = api_input
    
    st.markdown("---")
    st.subheader("👥 Gestión de Alumnos")
    opciones_alumnos = ["➕ Crear Nuevo Perfil..."] + list(st.session_state.bd_alumnos.keys())
    seleccion = st.selectbox("Seleccionar Alumno:", opciones_alumnos)
    
    if seleccion == "➕ Crear Nuevo Perfil...":
        with st.form("nuevo_perfil"):
            n_nombre = st.text_input("Nombre del Alumno")
            n_edad = st.number_input("Edad", 4, 25, 10)
            n_curso = st.selectbox("Curso", ["1º Básico", "2º Básico", "3º Básico", "4º Básico", "5º Básico", "6º Básico", "7º Básico", "8º Básico", "Media"])
            n_cond = st.selectbox("Condición", ["Ninguna", "Discapacidad Intelectual Leve (DIL)", "Trastorno por Déficit Atencional (TDAH)", "DIL + TDAH", "Otra"])
            if st.form_submit_button("Guardar Perfil"):
                if n_nombre:
                    st.session_state.bd_alumnos[n_nombre] = {"nombre": n_nombre, "edad": n_edad, "curso": n_curso, "condicion": n_cond, "historial": []}
                    guardar_historial(st.session_state.bd_alumnos)
                    st.success("¡Perfil Creado!")
                    st.rerun()
        st.session_state.perfil_activo = None
    else:
        st.session_state.perfil_activo = st.session_state.bd_alumnos[seleccion]
        al = st.session_state.perfil_activo
        st.info(f"**Activo:** {al['nombre']} | {al['edad']} años | {al['condicion']}")
        
        # Historial de Aprendizaje
        with st.expander("📈 Historial de Aprendizaje"):
            if len(al['historial']) > 0:
                for h in reversed(al['historial']):
                    st.write(f"📅 {h['fecha']}: **{h['ppm']} PPM** | Aciertos: {h['puntaje']}/{h['total']}")
            else: st.caption("No hay actividades registradas aún.")
            
    st.markdown("---")
    if st.button("🔄 Reiniciar Sesión General"):
        mantener = ['api_key_guardada', 'bd_alumnos']
        for v in VARIABLES:
            if v not in mantener: st.session_state[v] = None
        st.rerun()

# ==========================================
# PANTALLA 1: CONFIGURACIÓN DOCENTE
# ==========================================
if st.session_state.estado == 'configuracion':
    if not st.session_state.perfil_activo:
        st.warning("👈 Por favor, selecciona o crea un perfil de alumno en el panel izquierdo para comenzar.")
    else:
        st.title("✨ Centro de Misiones Lectoras")
        st.markdown("<div class='tarjeta'>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📖 Texto Libre", "🤖 Generar Cuento Personalizado", "🗺️ Elige tu Propia Aventura"])
        
        # TAB 1: Texto Propio y Analítica
        with tab1:
            texto_base = st.text_area("Pega el texto de lectura aquí:", height=150)
            
            c1, c2 = st.columns(2)
            if c1.button("🔍 Análisis Predictivo"):
                if texto_base and st.session_state.api_key_guardada:
                    with st.spinner("Analizando complejidad..."):
                        ia = obtener_ia()
                        resp = ia.generate_content(f"Analiza si este texto es apto para un niño de {al['edad']} años con {al['condicion']}. Sé breve (2 líneas). Texto: {texto_base}")
                        st.info(f"**Análisis:** {resp.text}")
            if c2.button("🪄 Simplificador Mágico"):
                if texto_base and st.session_state.api_key_guardada:
                    with st.spinner("Adaptando texto (DUA)..."):
                        ia = obtener_ia()
                        resp = ia.generate_content(f"Reescribe este texto usando oraciones cortas y lenguaje extremadamente simple para un niño con {al['condicion']}. Texto: {texto_base}")
                        st.success("Texto Simplificado (cópialo o úsalo directamente):")
                        st.write(resp.text)
            
            if st.button("🚀 Usar este texto"):
                st.session_state.texto_original = texto_base
                st.session_state.ajustes['modo'] = "normal"

        # TAB 2: Generar Cuento
        with tab2:
            st.write("La Inteligencia artificial escribirá un texto desde cero adaptado a la edad del alumno.")
            tema = st.text_input("Tema del cuento (Ej: Un gato detective):")
            if st.button("✨ Crear y Usar Cuento"):
                st.session_state.texto_original = tema
                st.session_state.ajustes['modo'] = "generado"
                
        # TAB 3: CYOA (Aventura)
        with tab3:
            st.info("La IA creará la introducción de un cuento. A la mitad, el alumno tomará una decisión y la IA inventará el final en vivo.")
            tema_aventura = st.text_input("¿Sobre qué será la aventura? (Ej: Exploradores en la selva):")
            if st.button("🗺️ Iniciar Aventura Interactiva"):
                st.session_state.texto_original = tema_aventura
                st.session_state.ajustes['modo'] = "aventura"

        st.markdown("---")
        st.subheader("⚙️ Ajustes de Accesibilidad (Diseño Universal)")
        colA, colB, colC, colD = st.columns(4)
        aj_audio = colA.checkbox("🔊 Audio-Lectura", value=False)
        aj_bionic = colB.checkbox("👁️ Letras en Negrita (TDAH)", value=False)
        aj_frag = colC.checkbox("🧩 Lectura Fragmentada", value=False)
        aj_dicc = colD.checkbox("📖 Diccionario Pre-Lectura", value=True)
        
        dificultad = st.selectbox("Dificultad de la Evaluación:", ["Fácil (Literal)", "Intermedio (Deducción)", "Desafío (Opinión)"])
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Guardar ajustes y avanzar si se presionó algún botón de inicio
        if st.session_state.ajustes.get('modo'):
            if not st.session_state.api_key_guardada: st.error("⚠️ Falta tu Clave de IA en el panel izquierdo.")
            elif not st.session_state.texto_original: st.warning("⚠️ Falta agregar el texto o tema.")
            else:
                st.session_state.ajustes.update({'audio': aj_audio, 'bionic': aj_bionic, 'fragmentado': aj_frag, 'diccionario': aj_dicc, 'dificultad': dificultad})
                st.session_state.estado = 'procesando_ia'
                st.rerun()

# ==========================================
# PANTALLA 2: MOTOR DE PREPARACIÓN IA
# ==========================================
elif st.session_state.estado == 'procesando_ia':
    st.title("⏳ El Robot Profesor está preparando la magia...")
    barra = st.progress(0)
    ia = obtener_ia()
    al = st.session_state.perfil_activo
    modo = st.session_state.ajustes['modo']
    
    try:
        # 1. Generación de Textos
        barra.progress(25)
        if modo == "generado":
            st.write("Escribiendo cuento personalizado...")
            prompt_t = f"Escribe un cuento corto (max 150 palabras) sobre '{st.session_state.texto_original}' para un niño de {al['edad']} años con {al['condicion']}. Súper simple."
            st.session_state.texto_lectura = ia.generate_content(prompt_t).text.strip()
            
        elif modo == "aventura":
            st.write("Creando el universo de la aventura...")
            prompt_a = f"Inicia un cuento sobre '{st.session_state.texto_original}' para un niño. Escribe 2 párrafos y termina dando 2 opciones (A y B) sobre qué hacer. Devuelve JSON: [{{\"texto\": \"...\", \"opcion_a\": \"...\", \"opcion_b\": \"...\"}}]"
            resp = json.loads(limpiar_json(ia.generate_content(prompt_a).text))[0]
            st.session_state.texto_lectura = resp['texto']
            st.session_state.aventura_opciones = [resp['opcion_a'], resp['opcion_b']]
        else:
            st.session_state.texto_lectura = st.session_state.texto_original
            
        # 2. Diccionario
        barra.progress(50)
        if st.session_state.ajustes['diccionario']:
            st.write("Buscando las palabras más difíciles...")
            prompt_d = f"Extrae las 3 palabras más difíciles de este texto. Devuelve JSON: [{{\"palabra\":\"x\", \"definicion\":\"y\", \"emoji\":\"😎\"}}]. Texto: {st.session_state.texto_lectura}"
            try: st.session_state.diccionario = json.loads(limpiar_json(ia.generate_content(prompt_d).text))
            except: st.session_state.diccionario = []
            
        barra.progress(100)
        st.session_state.tiempo_inicio = 0
        st.session_state.fragmento_idx = 0
        st.session_state.aventura_paso = 0
        
        if st.session_state.ajustes['diccionario'] and st.session_state.diccionario:
            st.session_state.estado = 'pre_lectura'
        else: st.session_state.estado = 'lectura'
        st.rerun()
        
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        if st.button("Volver"): st.session_state.estado = 'configuracion'; st.rerun()

# ==========================================
# PANTALLA 3: DICCIONARIO PRE-LECTURA
# ==========================================
elif st.session_state.estado == 'pre_lectura':
    st.title("🎒 Tu Cofre de Palabras Mágicas")
    st.markdown("<div class='tarjeta'>", unsafe_allow_html=True)
    st.write("Antes de leer, mira estas palabras que aparecerán en la historia para que seas todo un experto:")
    
    for d in st.session_state.diccionario:
        st.markdown(f"<div class='cofre-palabras'><b>{d.get('emoji','')} {d.get('palabra','').upper()}</b>: {d.get('definicion','')}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("🚀 ¡Entendido! A leer", use_container_width=True):
        st.session_state.estado = 'lectura'
        st.rerun()

# ==========================================
# PANTALLA 4: LECTURA ACTIVA
# ==========================================
elif st.session_state.estado == 'lectura':
    st.title("📖 ¡Es hora de tu Aventura!")
    
    if st.session_state.tiempo_inicio == 0:
        st.info("Acomódate, y cuando estés listo, presiona el botón. ¡Tómate todo tu tiempo!")
        if st.button("▶️ Empezar a leer"):
            st.session_state.tiempo_inicio = time.time()
            st.rerun()
    else:
        texto_mostrar = st.session_state.texto_lectura
        es_frag = st.session_state.ajustes['fragmentado']
        es_aventura = st.session_state.ajustes['modo'] == 'aventura'
        
        # Configurar fragmentos
        parrafos = [p for p in texto_mostrar.split('\n') if len(p.strip()) > 3]
        idx = st.session_state.fragmento_idx
        
        if es_frag and not es_aventura:
            texto_pantalla = parrafos[idx] if idx < len(parrafos) else ""
        else:
            texto_pantalla = "\n\n".join(parrafos)

        # Generar Audio Dinámico
        if st.session_state.ajustes['audio']:
            reproductor = generar_audio(texto_pantalla)
            if reproductor: st.markdown(reproductor, unsafe_allow_html=True)

        # Formatear Texto (Biónico)
        if st.session_state.ajustes['bionic']: texto_html = formato_bionico(texto_pantalla).replace('\n', '<br><br>')
        else: texto_html = texto_pantalla.replace('\n', '<br><br>')
            
        st.markdown(f"<div class='texto-lectura'>{texto_html}</div><br>", unsafe_allow_html=True)
        
        # Botones de Avance
        if es_frag and not es_aventura and idx < len(parrafos) - 1:
            if st.button("⬇️ Siguiente Párrafo", use_container_width=True):
                st.session_state.fragmento_idx += 1
                st.rerun()
        elif es_aventura and st.session_state.aventura_paso == 0:
            st.write("### 🤔 ¿Qué decides hacer ahora?")
            col1, col2 = st.columns(2)
            if col1.button("🅰️ " + st.session_state.aventura_opciones[0], use_container_width=True):
                st.session_state.eleccion = st.session_state.aventura_opciones[0]
                st.session_state.estado = 'resolviendo_aventura'
                st.session_state.tiempo_total += round(time.time() - st.session_state.tiempo_inicio)
                st.rerun()
            if col2.button("🅱️ " + st.session_state.aventura_opciones[1], use_container_width=True):
                st.session_state.eleccion = st.session_state.aventura_opciones[1]
                st.session_state.estado = 'resolviendo_aventura'
                st.session_state.tiempo_total += round(time.time() - st.session_state.tiempo_inicio)
                st.rerun()
        else:
            if st.button("✅ ¡Terminé de leer!", use_container_width=True):
                st.session_state.tiempo_total += round(time.time() - st.session_state.tiempo_inicio)
                st.session_state.estado = 'creando_preguntas'
                st.rerun()

# ==========================================
# ESTADO: RESOLVIENDO AVENTURA
# ==========================================
elif st.session_state.estado == 'resolviendo_aventura':
    st.title("✨ Escribiendo tu destino...")
    with st.spinner("La IA está inventando el final basado en tu decisión..."):
        ia = obtener_ia()
        final = ia.generate_content(f"Continuación del cuento: {st.session_state.texto_lectura}. El niño eligió: '{st.session_state.eleccion}'. Escribe el final de la historia. Corto y simple.").text.strip()
        st.session_state.texto_lectura += "\n\n***\n\n**TÚ DECIDISTE:** " + st.session_state.eleccion + "\n\n" + final
        st.session_state.aventura_paso = 1
        st.session_state.tiempo_inicio = time.time()
        st.session_state.estado = 'lectura'
        st.rerun()

# ==========================================
# PANTALLA 5: CREANDO PREGUNTAS (Feedback Formativo)
# ==========================================
elif st.session_state.estado == 'creando_preguntas':
    st.title("⏳ Preparando tu desafío...")
    barra = st.progress(0)
    for i in range(100): time.sleep(0.01); barra.progress(i + 1)
    
    with st.spinner("Analizando texto para generar retroalimentación educativa..."):
        ia = obtener_ia()
        al = st.session_state.perfil_activo
        
        prompt = f"""
        Genera 5 preguntas de comprensión lectora sobre este texto para un niño con {al['condicion']}. Nivel: {st.session_state.ajustes['dificultad']}.
        Devuelve SOLO un JSON exacto:
        [
            {{"pregunta": "¿?", "opciones": ["A", "B", "C"], "respuesta_correcta": "A", "explicacion": "Explicación muy amable del porqué esa es la respuesta correcta."}}
        ]
        El valor 'respuesta_correcta' debe ser idéntico a una de las 'opciones'.
        Texto: {st.session_state.texto_lectura}
        """
        try:
            preguntas = json.loads(limpiar_json(ia.generate_content(prompt).text))
            for p in preguntas:
                opc = [str(o).strip() for o in p["opciones"]]
                corr = str(p["respuesta_correcta"]).strip()
                if corr not in opc: opc[0] = corr
                random.shuffle(opc)
                p["opciones"] = opc
                p["respuesta_correcta"] = corr
            st.session_state.preguntas = preguntas
            st.session_state.respuestas_usuario = {}
            st.session_state.evaluado = False
            st.session_state.estado = 'preguntas'
            st.rerun()
        except:
            st.error("Error al crear preguntas. Volviendo al inicio...")
            time.sleep(2)
            st.session_state.estado = 'configuracion'
            st.rerun()

# ==========================================
# PANTALLA 6: PREGUNTAS, FEEDBACK Y REPORTE
# ==========================================
elif st.session_state.estado == 'preguntas':
    st.title("🕵️‍♂️ Misión de Comprensión")
    
    if 'respuestas_usuario' not in st.session_state: st.session_state.respuestas_usuario = {}
    todas_listas = True
    
    for i, p in enumerate(st.session_state.preguntas):
        st.markdown("<div class='tarjeta'>", unsafe_allow_html=True)
        st.write(f"### {i+1}. {p['pregunta']}")
        resp = st.radio("Respuesta:", p['opciones'], key=f"q_{i}", index=None, disabled=st.session_state.evaluado, label_visibility="collapsed")
        st.session_state.respuestas_usuario[i] = resp
        if resp is None: todas_listas = False
        
        # El secreto del aprendizaje: Feedback Formativo Integrado
        if st.session_state.evaluado:
            if resp == p['respuesta_correcta']:
                st.markdown(f"<div class='feedback-bien'>✨ <b>¡Correcto!</b></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='feedback-mal'>❌ <b>Casi...</b> La respuesta correcta era: <b>{p['respuesta_correcta']}</b></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='explicacion-ia'>🤖 <b>El Profesor Robot dice:</b> {p.get('explicacion','Revisa el texto de nuevo.')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    if not st.session_state.evaluado:
        if st.button("✅ Enviar mis respuestas", use_container_width=True):
            if todas_listas: st.session_state.evaluado = True; st.rerun()
            else: st.warning("⚠️ Faltan preguntas por responder.")
    else:
        puntaje = sum(1 for i, p in enumerate(st.session_state.preguntas) if st.session_state.respuestas_usuario.get(i) == p['respuesta_correcta'])
        total = len(st.session_state.preguntas)
        st.balloons() if puntaje == total else None
        
        st.markdown(f"<div class='tarjeta' style='text-align:center;'><h2>🏆 Puntaje Final: {puntaje} / {total}</h2></div>", unsafe_allow_html=True)
        
        # --- GENERADOR DE INFORME Y ANALÍTICA ---
        palabras = len(st.session_state.texto_lectura.split())
        mins = st.session_state.tiempo_total / 60.0
        ppm = int(palabras / mins) if mins > 0 else 0
        
        al = st.session_state.perfil_activo
        meta_ppm = {"1º Básico": 35, "2º Básico": 60, "3º Básico": 85, "4º Básico": 100, "5º Básico": 115, "6º Básico": 125, "7º Básico": 135}.get(al['curso'], 100)
        if "DIL" in al['condicion']: meta_ppm = int(meta_ppm * 0.6)
        if "TDAH" in al['condicion']: meta_ppm = int(meta_ppm * 0.8)
        
        if ppm >= meta_ppm: diag = "🟢 Óptima / Adecuada para su perfil."
        elif ppm >= meta_ppm * 0.75: diag = "🟡 En Desarrollo. Requiere estimulación moderada."
        else: diag = "🔴 Lenta / Silábica. Requiere apoyo en decodificación."
        
        st.markdown("---")
        st.subheader("📊 Zona del Docente")
        st.write(f"**Velocidad:** {ppm} PPM (Meta perfilada: {meta_ppm} PPM) | **Análisis:** {diag}")
        
        colA, colB = st.columns(2)
        with colA:
            if st.button("💾 Guardar Progreso en el Historial del Alumno", use_container_width=True):
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                if not any(h['fecha'] == fecha for h in al['historial']):
                    al['historial'].append({"fecha": fecha, "ppm": ppm, "puntaje": puntaje, "total": total})
                    st.session_state.bd_alumnos[al['nombre']] = al
                    guardar_historial(st.session_state.bd_alumnos)
                    st.success("Guardado en la base de datos.")
        with colB:
            # Botón de Reporte en HTML imprimible
            html_reporte = generar_reporte_html(al['nombre'], al['edad'], al['curso'], al['condicion'], ppm, puntaje, total, diag)
            st.markdown(html_reporte, unsafe_allow_html=True)
        
        if st.button("🔄 Volver al Inicio y Leer Otro Cuento"):
            mantener = ['api_key_guardada', 'bd_alumnos', 'perfil_activo']
            for v in VARIABLES:
                if v not in mantener: st.session_state[v] = None
            st.session_state.estado = 'configuracion'
            st.rerun()
