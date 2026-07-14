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

# --- DISEÑO VISUAL FLEXIBLE (Compatible con Modo Claro y Oscuro) ---
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

if 'bd_alumnos' not in st.session_state: st.session_state.bd_alumnos = cargar_historial()

# --- MEMORIA DE LA SESIÓN ---
VARIABLES = ['estado', 'tiempo_inicio', 'tiempo_total', 'preguntas', 'evaluado', 'api_key_guardada', 'perfil_activo', 'texto_original', 'texto_lectura', 'ajustes', 'diccionario', 'fragmento_idx', 'aventura_paso', 'aventura_opciones', 'respuestas_usuario']
for v in VARIABLES:
    if v not in st.session_state: st.session_state[v] = None

if st.session_state.estado is None: st.session_state.estado = 'configuracion'
if st.session_state.ajustes is None: st.session_state.ajustes = {}
if st.session_state.api_key_guardada is None:
    try: st.session_state.api_key_guardada = st.secrets.get("GOOGLE_API_KEY", "")
    except: st.session_state.api_key_guardada = ""

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
    st.title("✨ Centro de Misiones Lectoras")
    
    # INSTRUCCIONES CLARAS RESTAURADAS
    st.markdown("""
    <div class="instrucciones-api">
    <b>💡 Bienvenida Profesora: ¿Cómo activar la Inteligencia Artificial?</b><br><br>
    Para que las preguntas y cuentos se generen solos, necesitas una Llave de Google (Gratuita).<br>
    1. Entra a <a href="https://aistudio.google.com/" target="_blank" style="font-weight:bold;">aistudio.google.com</a> e inicia sesión con tu Gmail normal.<br>
    2. Haz clic en el botón azul <b>"Get API key"</b> (arriba a la izquierda) y luego en <b>"Create API key"</b>.<br>
    3. Copia el código largo que te dará y pégalo en la casilla de abajo.
    </div>
    """, unsafe_allow_html=True)

    api_key_input = st.text_input("🔑 Pega aquí tu Clave de IA (Google API):", type="password", value=st.session_state.api_key_guardada)
    if api_key_input: st.session_state.api_key_guardada = api_key_input

    if not st.session_state.perfil_activo:
        st.warning("👈 Por favor, selecciona o crea un perfil de alumno en el panel izquierdo (Panel Docente) para comenzar.")
    else:
        st.markdown("<div class='tarjeta'>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["📖 Texto Libre (Con IA)", "🤖 La IA inventa un Cuento", "🗺️ Elige tu Propia Aventura", "✍️ Modo Manual (Sin IA)"])
        al = st.session_state.perfil_activo
        
        with tab1:
            texto_base = st.text_area("Pega el texto de lectura aquí:", height=150)
            c1, c2 = st.columns(2)
            if c1.button("🔍 Análisis Predictivo"):
                if texto_base and st.session_state.api_key_guardada:
                    with st.spinner("Analizando complejidad..."):
                        ia = obtener_ia()
                        resp = ia.generate_content(f"Analiza si este texto es apto para un niño de {al['edad']} años con {al['condicion']}. Sé breve (2 líneas). Texto: {texto_base}")
                        st.info(f"**Análisis:** {resp.text}")
                else: st.warning("Falta pegar el texto o la Clave IA.")
            if c2.button("🪄 Simplificador Mágico"):
                if texto_base and st.session_state.api_key_guardada:
                    with st.spinner("Adaptando texto (DUA)..."):
                        ia = obtener_ia()
                        resp = ia.generate_content(f"Reescribe este texto usando oraciones cortas y lenguaje extremadamente simple para un niño con {al['condicion']}. Texto: {texto_base}")
                        st.success("Texto Simplificado (cópialo o úsalo directamente):")
                        st.write(resp.text)
                else: st.warning("Falta pegar el texto o la Clave IA.")
            
            if st.button("🚀 Usar este texto", type="primary"):
                st.session_state.texto_original = texto_base
                st.session_state.ajustes['modo'] = "normal"

        with tab2:
            st.write("La IA escribirá un texto desde cero adaptado a la edad y condición del alumno.")
            tema = st.text_input("Tema del cuento (Ej: Un gato detective, Los dinosaurios):")
            if st.button("✨ Crear y Usar Cuento", type="primary"):
                st.session_state.texto_original = tema
                st.session_state.ajustes['modo'] = "generado"
                
        with tab3:
            st.info("La IA creará la introducción. A la mitad, el alumno tomará una decisión y la IA inventará el final en vivo.")
            tema_aventura = st.text_input("¿Sobre qué será la aventura? (Ej: Exploradores en la selva):")
            if st.button("🗺️ Iniciar Aventura Interactiva", type="primary"):
                st.session_state.texto_original = tema_aventura
                st.session_state.ajustes['modo'] = "aventura"
                
        with tab4:
            st.info("💡 Tú escribes las preguntas. No se usará Inteligencia Artificial.")
            texto_manual = st.text_area("Pega el texto de lectura aquí:", height=150, key="txt_manual")
            preguntas_manuales = []
            for i in range(5): 
                with st.expander(f"Pregunta {i+1}", expanded=(i==0)):
                    q = st.text_input("La pregunta:", key=f"q_{i}")
                    c = st.text_input("✅ Opción Correcta:", key=f"c_{i}")
                    f1 = st.text_input("❌ Opción Falsa 1:", key=f"f1_{i}")
                    f2 = st.text_input("❌ Opción Falsa 2 (Opcional):", key=f"f2_{i}")
                    preguntas_manuales.append({"q": q, "c": c, "f1": f1, "f2": f2})
            if st.button("🚀 Iniciar Actividad Manual", type="primary"):
                if texto_manual and preguntas_manuales[0]["q"] and preguntas_manuales[0]["c"]:
                    lista_final = []
                    for p in preguntas_manuales:
                        if p["q"] and p["c"]:
                            opciones = [p["c"].strip(), p["f1"].strip(), p["f2"].strip()]
                            opciones = [op for op in opciones if op] 
                            random.shuffle(opciones) 
                            lista_final.append({
                                "pregunta": p["q"].strip(), 
                                "opciones": opciones, 
                                "respuesta_correcta": p["c"].strip(),
                                "explicacion": "Respuesta correcta ingresada por el profesor."
                            })
                    st.session_state.preguntas = lista_final
                    st.session_state.texto_original = texto_manual
                    st.session_state.ajustes['modo'] = "manual"
                else:
                    st.warning("Completa el texto y al menos la primera pregunta.")

        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='tarjeta'>", unsafe_allow_html=True)
        st.subheader("⚙️ Ajustes de Accesibilidad (Diseño Universal)")
        colA, colB, colC, colD = st.columns(4)
        aj_audio = colA.checkbox("🔊 Audio-Lectura", value=False)
        aj_bionic = colB.checkbox("👁️ Letras en Negrita (TDAH)", value=False)
        aj_frag = colC.checkbox("🧩 Lectura Fragmentada", value=False)
        aj_dicc = colD.checkbox("📖 Diccionario Pre-Lectura", value=True)
        
        # 5 NIVELES DE DIFICULTAD RESTAURADOS
        niveles = [
            "1 - Muy Fácil (Búsqueda de información literal y evidente)",
            "2 - Fácil (Identificar personajes, lugares y acciones directas)",
            "3 - Intermedio (Deducciones sencillas, conectar causa y efecto)",
            "4 - Avanzado (Inferir sentimientos, actitudes y motivaciones)",
            "5 - Desafío (Opinión personal, empatía y el 'por qué' de las cosas)"
        ]
        dificultad = st.selectbox("Nivel de Dificultad para Preguntas con IA:", niveles)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.ajustes.get('modo'):
            modo_elegido = st.session_state.ajustes['modo']
            st.session_state.ajustes.update({'audio': aj_audio, 'bionic': aj_bionic, 'fragmentado': aj_frag, 'diccionario': aj_dicc, 'dificultad': dificultad})
            
            if modo_elegido == "manual":
                st.session_state.texto_lectura = st.session_state.texto_original
                st.session_state.tiempo_inicio = 0
                st.session_state.fragmento_idx = 0
                st.session_state.estado = 'lectura'
                st.rerun()
            else:
                if not st.session_state.api_key_guardada: 
                    st.error("⚠️ Faltó poner la Clave de Google API (Sigue las instrucciones azules de arriba).")
                    st.session_state.ajustes['modo'] = None
                elif not st.session_state.texto_original: 
                    st.warning("⚠️ Falta agregar el texto o tema en la pestaña elegida.")
                    st.session_state.ajustes['modo'] = None
                else:
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
            
        barra.progress(50)
        if st.session_state.ajustes['diccionario'] and modo != "manual":
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
        st.error(f"Error de conexión: Verifica que tu Clave API de Google sea correcta.")
        if st.button("Volver al inicio"): st.session_state.estado = 'configuracion'; st.rerun()

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
    if st.button("🚀 ¡Entendido! A leer", use_container_width=True, type="primary"):
        st.session_state.estado = 'lectura'
        st.rerun()

# ==========================================
# PANTALLA 4: LECTURA ACTIVA
# ==========================================
elif st.session_state.estado == 'lectura':
    st.title("📖 ¡Es hora de tu Aventura!")
    
    if st.session_state.tiempo_inicio == 0:
        st.info("Acomódate, y cuando estés listo, presiona el botón. ¡Tómate todo tu tiempo!")
        if st.button("▶️ Empezar a leer", type="primary"):
            st.session_state.tiempo_inicio = time.time()
            st.rerun()
    else:
        texto_mostrar = st.session_state.texto_lectura
        es_frag = st.session_state.ajustes['fragmentado']
        es_aventura = st.session_state.ajustes['modo'] == 'aventura'
        
        parrafos = [p for p in texto_mostrar.split('\n') if len(p.strip()) > 3]
        if not parrafos: parrafos = [texto_mostrar]
        idx = st.session_state.fragmento_idx
        
        if es_frag and not es_aventura:
            texto_pantalla = parrafos[idx] if idx < len(parrafos) else ""
        else:
            texto_pantalla = "\n\n".join(parrafos)

        if st.session_state.ajustes['audio']:
            reproductor = generar_audio(texto_pantalla)
            if reproductor: st.markdown(reproductor, unsafe_allow_html=True)

        if st.session_state.ajustes['bionic']: texto_html = formato_bionico(texto_pantalla).replace('\n', '<br><br>')
        else: texto_html = texto_pantalla.replace('\n', '<br><br>')
            
        st.markdown(f"<div class='texto-lectura'>{texto_html}</div><br>", unsafe_allow_html=True)
        
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
            if st.button("✅ ¡Terminé de leer!", type="primary", use_container_width=True):
                st.session_state.tiempo_total += round(time.time() - st.session_state.tiempo_inicio)
                if st.session_state.ajustes['modo'] == 'manual':
                    st.session_state.estado = 'preguntas'
                else:
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
            
            if 'respuestas_usuario' not in st.session_state or st.session_state.respuestas_usuario is None: 
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
    
    if 'respuestas_usuario' not in st.session_state or st.session_state.respuestas_usuario is None: 
        st.session_state.respuestas_usuario = {}
        
    todas_listas = True
    
    for i, p in enumerate(st.session_state.preguntas):
        st.markdown("<div class='tarjeta'>", unsafe_allow_html=True)
        st.write(f"### {i+1}. {p['pregunta']}")
        resp = st.radio("Respuesta:", p['opciones'], key=f"q_{i}", index=None, disabled=st.session_state.evaluado, label_visibility="collapsed")
        st.session_state.respuestas_usuario[i] = resp
        if resp is None: todas_listas = False
        
        # Feedback Formativo Integrado
        if st.session_state.evaluado:
            if resp == p['respuesta_correcta']:
                st.markdown(f"<div style='color:#10B981; font-size: 20px; font-weight: bold;'>✨ ¡Correcto!</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:#EF4444; font-size: 20px; font-weight: bold;'>❌ Casi... La respuesta correcta era: {p['respuesta_correcta']}</div>", unsafe_allow_html=True)
            if st.session_state.ajustes['modo'] != 'manual':
                st.markdown(f"<div class='explicacion-ia'>🤖 <b>El Profesor Robot dice:</b> {p.get('explicacion','Revisa el texto de nuevo.')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    if not st.session_state.evaluado:
        if st.button("✅ Enviar mis respuestas", use_container_width=True, type="primary"):
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
        st.subheader("📊 Zona del Docente (Reporte Final)")
        st.write(f"**Velocidad:** {ppm} PPM (Meta perfilada: {meta_ppm} PPM) | **Análisis:** {diag}")
        
        colA, colB = st.columns(2)
        with colA:
            if st.button("💾 Guardar Progreso en el Historial", use_container_width=True, type="primary"):
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                if not any(h['fecha'] == fecha for h in al['historial']):
                    al['historial'].append({"fecha": fecha, "ppm": ppm, "puntaje": puntaje, "total": total})
                    st.session_state.bd_alumnos[al['nombre']] = al
                    guardar_historial(st.session_state.bd_alumnos)
                    st.success("Guardado en la base de datos.")
        with colB:
            html_reporte = generar_reporte_html(al['nombre'], al['edad'], al['curso'], al['condicion'], ppm, puntaje, total, diag)
            st.markdown(html_reporte, unsafe_allow_html=True)
        
        if st.button("🔄 Volver al Inicio y Leer Otro Cuento"):
            mantener = ['api_key_guardada', 'bd_alumnos', 'perfil_activo']
            for v in VARIABLES:
                if v not in mantener: st.session_state[v] = None
            st.session_state.ajustes = {}
            st.session_state.estado = 'configuracion'
            st.rerun()
