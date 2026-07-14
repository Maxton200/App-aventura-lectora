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

if 'bd_alumnos' not in st.session_state: st.session_state.bd_alumnos = cargar_historial()

# --- MEMORIA DE LA SESIÓN BLINDADA ---
DEFAULTS = {
    'estado': 'configuracion',
    'tiempo_inicio': 0.0,
    'tiempo_total': 0.0,
    'preguntas': [],
    'evaluado': False,
    'perfil_activo': None,
    'texto_original': "",
    'texto_lectura': "",
    'texto_libre': "",
    'texto_manual': "",
    'tema_generado': "",
    'tema_aventura': "",
    'ajustes': {},
    'diccionario': [],
    'fragmento_idx': 0,
    'aventura_paso': 0,
    'aventura_opciones': [],
    'respuestas_usuario': {},
    'eleccion': "",
    'modo_demo': False
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if 'api_key_guardada' not in st.session_state:
    try: st.session_state.api_key_guardada = st.secrets.get("GOOGLE_API_KEY", "")
    except: st.session_state.api_key_guardada = ""

# --- FUNCIONES DE APOYO Y MOCKING ---
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
    texto = str(texto).strip()
    inicio = texto.find('[')
    fin = texto.rfind(']') + 1
    if inicio != -1 and fin > inicio:
        return texto[inicio:fin]
    raise ValueError("Formato JSON no encontrado en la respuesta.")

def obtener_respuesta_mock(tipo):
    time.sleep(1.5) # Simula el tiempo de carga realista
    if tipo == "analisis": 
        return "El texto tiene un nivel de complejidad adecuado. Usa oraciones cortas y vocabulario concreto, ideal para el perfil del estudiante."
    if tipo == "simplificador": 
        return "Había una vez un perrito muy feliz. El perrito corría por el parque verde. Le gustaba jugar con su pelota roja todo el día."
    if tipo == "cuento": 
        tema = st.session_state.texto_original if st.session_state.texto_original else "aventura"
        return f"Había una vez un gran héroe que quería descubrir los secretos de '{tema}'. Viajó por muchos lugares fantásticos hasta que por fin encontró lo que tanto buscaba. Fue muy feliz."
    if tipo == "aventura_inicio": 
        tema = st.session_state.texto_original if st.session_state.texto_original else "el misterio"
        return json.dumps([{"texto": f"Empieza la gran historia sobre '{tema}'. Vas caminando por el bosque y llegas a una encrucijada. ¿Qué decides hacer ahora?", "opcion_a": "Ir por el camino oscuro", "opcion_b": "Cruzar el puente de madera"}])
    if tipo == "diccionario": 
        return json.dumps([
            {"palabra": "Encrucijada", "definicion": "Cruce de caminos donde debes elegir por dónde ir.", "emoji": "🔀"},
            {"palabra": "Descubrir", "definicion": "Encontrar algo que estaba escondido o que no conocías.", "emoji": "🔍"},
            {"palabra": "Misterio", "definicion": "Algo difícil de entender o explicar.", "emoji": "🕵️‍♂️"}
        ])
    if tipo == "aventura_final": 
        return "Tomaste una decisión muy valiente. Caminaste por un rato, encontraste un tesoro brillante y regresaste a casa a salvo. Fin de la aventura."
    if tipo == "preguntas": 
        return json.dumps([
            {"pregunta": "¿Qué encontró el personaje al final de su aventura?", "opciones": ["Un tesoro brillante", "Un castillo oscuro", "Una cueva vacía"], "respuesta_correcta": "Un tesoro brillante", "explicacion": "El texto dice claramente que después de tomar la decisión, encontró un tesoro brillante."},
            {"pregunta": "¿Cómo se sintió el héroe al terminar su viaje?", "opciones": ["Muy feliz", "Triste", "Enojado"], "respuesta_correcta": "Muy feliz", "explicacion": "La historia menciona que el personaje fue muy feliz tras lograr su objetivo."},
            {"pregunta": "¿A dónde llegó el personaje al caminar por el bosque?", "opciones": ["A una encrucijada", "A un río profundo", "A una montaña"], "respuesta_correcta": "A una encrucijada", "explicacion": "El cuento relata que caminando por el bosque se topó con una encrucijada y tuvo que elegir un camino."},
            {"pregunta": "¿Qué debió hacer el personaje en la encrucijada?", "opciones": ["Tomar una decisión", "Dormir", "Comer"], "respuesta_correcta": "Tomar una decisión", "explicacion": "El texto dice '¿Qué decides hacer ahora?', indicando que debía elegir."},
            {"pregunta": "¿Qué opinas de la decisión del personaje?", "opciones": ["Fue muy valiente", "Fue aburrida", "Fue mala"], "respuesta_correcta": "Fue muy valiente", "explicacion": "El texto final señala que tomaste una decisión muy valiente."}
        ])

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

def reiniciar_app(mantener_perfil=True):
    mantener = ['api_key_guardada', 'bd_alumnos', 'modo_demo']
    if mantener_perfil: mantener.append('perfil_activo')
    for k in list(st.session_state.keys()):
        if k not in mantener:
            del st.session_state[k]
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    st.rerun()

def solicitar_ia(prompt, JSON=False):
    """Busca dinámicamente qué modelos de IA funcionan en tu cuenta para saltarse los bloqueos o límites (Fallback)"""
    if st.session_state.modo_demo: return "" 
    
    genai.configure(api_key=st.session_state.api_key_guardada)
    modelos_disponibles = []
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponibles.append(m.name)
    except Exception as e:
        raise Exception(f"Error al conectar con Google: {e}")
        
    modelos_disponibles.sort(key=lambda x: 'flash' not in x.lower())
    
    ultimo_error = None
    for nombre_modelo in modelos_disponibles:
        try:
            model = genai.GenerativeModel(nombre_modelo)
            if JSON:
                try: 
                    respuesta = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    return respuesta.text
                except: 
                    pass 
            
            respuesta = model.generate_content(prompt)
            return respuesta.text
            
        except Exception as e:
            ultimo_error = str(e).lower()
            if "429" in ultimo_error or "quota" in ultimo_error or "404" in ultimo_error or "503" in ultimo_error:
                time.sleep(0.5)
                continue
            else:
                raise e
                
    raise Exception(f"Se ha agotado el saldo gratuito de todos los modelos de IA en tu cuenta. Intenta mañana o activa el Modo Demo. (Error: {ultimo_error})")

# ==========================================
# BARRA LATERAL (GESTIÓN)
# ==========================================
with st.sidebar:
    st.title("👨‍🏫 Panel Docente")
    st.markdown("---")
    
    st.session_state.modo_demo = st.toggle("🛠️ Modo Demostración (Sin IA)", value=st.session_state.modo_demo)
    if st.session_state.modo_demo:
        st.success("Modo Demo Activo: Respuestas y funciones automáticas pre-cargadas sin consumir saldo de Google.")
        
    st.markdown("---")
    st.subheader("👥 Gestión de Alumnos")
    opciones_alumnos = ["➕ Crear Nuevo Perfil..."] + list(st.session_state.bd_alumnos.keys())
    
    idx_seleccion = 0
    if st.session_state.perfil_activo and st.session_state.perfil_activo['nombre'] in opciones_alumnos:
        idx_seleccion = opciones_alumnos.index(st.session_state.perfil_activo['nombre'])
        
    seleccion = st.selectbox("Seleccionar Alumno:", opciones_alumnos, index=idx_seleccion)
    
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
            if len(al.get('historial', [])) > 0:
                for h in reversed(al['historial']):
                    st.write(f"📅 {h['fecha']}: **{h['ppm']} PPM** | Aciertos: {h['puntaje']}/{h['total']}")
            else: st.caption("No hay actividades registradas aún.")
            
    st.markdown("---")
    if st.button("🔄 Reiniciar Sesión General"):
        reiniciar_app(mantener_perfil=False)

# ==========================================
# PANTALLA 1: CONFIGURACIÓN DOCENTE
# ==========================================
if st.session_state.estado == 'configuracion':
    st.title("✨ Centro de Misiones Lectoras")
    
    st.markdown("""
    <div class="instrucciones-api">
    <b>💡 Bienvenida Profesora: ¿Cómo activar la Inteligencia Artificial?</b><br><br>
    Para que las preguntas y cuentos se generen solos, necesitas una Llave de Google (Gratuita).<br>
    1. Entra a <a href="https://aistudio.google.com/" target="_blank" style="font-weight:bold;">aistudio.google.com</a> e inicia sesión con tu Gmail normal.<br>
    2. Haz clic en el botón azul <b>"Get API key"</b> (arriba a la izquierda) y luego en <b>"Create API key"</b>.<br>
    3. Copia el código largo que te dará y pégalo en la casilla de abajo. <i>(O activa el Modo Demo en el panel izquierdo para probar la app).</i>
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
            texto_base = st.text_area("Pega el texto de lectura original aquí:", value=st.session_state.texto_libre, height=150)
            st.session_state.texto_libre = texto_base
            
            c1, c2 = st.columns(2)
            if c1.button("🔍 Análisis Predictivo"):
                if texto_base.strip() and (st.session_state.api_key_guardada or st.session_state.modo_demo):
                    with st.spinner("Analizando complejidad..."):
                        if st.session_state.modo_demo:
                            resp_text = obtener_respuesta_mock("analisis")
                        else:
                            try: resp_text = solicitar_ia(f"Analiza si este texto es apto para un niño de {al['edad']} años con {al['condicion']}. Sé breve (2 líneas). Texto: {texto_base}")
                            except Exception as e: resp_text = f"Error de IA: {e}"
                        st.info(f"**Análisis:** {resp_text}")
                else: st.warning("Falta pegar el texto o la Clave IA.")
                
            if c2.button("🪄 Simplificador Mágico (Diseño Universal)"):
                if texto_base.strip() and (st.session_state.api_key_guardada or st.session_state.modo_demo):
                    with st.spinner("Adaptando texto para el estudiante..."):
                        if st.session_state.modo_demo:
                            st.session_state.texto_libre = obtener_respuesta_mock("simplificador")
                            st.rerun() 
                        else:
                            try:
                                respuesta = solicitar_ia(f"Reescribe este texto usando oraciones cortas y lenguaje extremadamente simple para un niño con {al['condicion']}. Texto: {texto_base}")
                                st.session_state.texto_libre = respuesta.strip()
                                st.rerun() 
                            except Exception as e: st.error(f"Error de IA: {e}")
                else: st.warning("Falta pegar el texto o la Clave IA.")
            
            if st.button("🚀 Usar este texto", type="primary"):
                if st.session_state.texto_libre.strip():
                    st.session_state.texto_original = st.session_state.texto_libre
                    st.session_state.ajustes['modo'] = "normal"
                else: st.warning("Pega un texto en la caja primero.")

        with tab2:
            st.write("La IA escribirá un texto desde cero adaptado a la edad y condición del alumno.")
            tema_gen = st.text_input("Tema del cuento (Ej: Un gato detective, Los dinosaurios):", value=st.session_state.tema_generado)
            st.session_state.tema_generado = tema_gen
            if st.button("✨ Crear y Usar Cuento", type="primary"):
                if tema_gen.strip():
                    st.session_state.texto_original = tema_gen
                    st.session_state.ajustes['modo'] = "generado"
                else: st.warning("Escribe un tema primero.")
                
        with tab3:
            st.info("La IA creará la introducción. A la mitad, el alumno tomará una decisión y la IA inventará el final en vivo.")
            tema_av = st.text_input("¿Sobre qué será la aventura? (Ej: Exploradores en la selva):", value=st.session_state.tema_aventura)
            st.session_state.tema_aventura = tema_av
            if st.button("🗺️ Iniciar Aventura Interactiva", type="primary"):
                if tema_av.strip():
                    st.session_state.texto_original = tema_av
                    st.session_state.ajustes['modo'] = "aventura"
                else: st.warning("Escribe un tema primero.")
                
        with tab4:
            st.info("💡 Tú escribes las preguntas. No se usará Inteligencia Artificial.")
            texto_man = st.text_area("Pega el texto de lectura aquí (Modo Manual):", value=st.session_state.texto_manual, height=150)
            st.session_state.texto_manual = texto_man
            preguntas_manuales = []
            for i in range(5): 
                with st.expander(f"Pregunta {i+1}", expanded=(i==0)):
                    q = st.text_input("La pregunta:", key=f"qm_{i}")
                    c = st.text_input("✅ Opción Correcta:", key=f"cm_{i}")
                    f1 = st.text_input("❌ Opción Falsa 1:", key=f"f1m_{i}")
                    f2 = st.text_input("❌ Opción Falsa 2 (Opcional):", key=f"f2m_{i}")
                    preguntas_manuales.append({"q": q, "c": c, "f1": f1, "f2": f2})
                    
            if st.button("🚀 Iniciar Actividad Manual", type="primary"):
                if texto_man.strip() and preguntas_manuales[0]["q"] and preguntas_manuales[0]["c"]:
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
                    if len(lista_final) > 0:
                        st.session_state.preguntas = lista_final
                        st.session_state.texto_original = texto_man
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
            
            st.session_state.tiempo_inicio = 0.0
            st.session_state.tiempo_total = 0.0
            st.session_state.fragmento_idx = 0
            st.session_state.aventura_paso = 0
            
            if modo_elegido == "manual":
                st.session_state.texto_lectura = st.session_state.texto_original
                st.session_state.estado = 'lectura'
                st.rerun()
            else:
                if not st.session_state.api_key_guardada and not st.session_state.modo_demo: 
                    st.error("⚠️ Faltó poner la Clave de Google API o activar el Modo Demo (Panel izquierdo).")
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
    al = st.session_state.perfil_activo
    modo = st.session_state.ajustes['modo']
    
    try:
        barra.progress(25)
        if modo == "generado":
            st.write("Escribiendo cuento personalizado...")
            if st.session_state.modo_demo:
                st.session_state.texto_lectura = obtener_respuesta_mock("cuento")
            else:
                prompt_t = f"Escribe un cuento corto (max 150 palabras) sobre '{st.session_state.texto_original}' para un niño de {al['edad']} años con {al['condicion']}. Súper simple."
                st.session_state.texto_lectura = solicitar_ia(prompt_t).strip()
            
        elif modo == "aventura":
            st.write("Creando el universo de la aventura...")
            if st.session_state.modo_demo:
                respuesta = obtener_respuesta_mock("aventura_inicio")
            else:
                prompt_a = f"Inicia un cuento sobre '{st.session_state.texto_original}' para un niño. Escribe 2 párrafos y termina dando 2 opciones (A y B) sobre qué hacer. Devuelve estrictamente un JSON válido: [{{\"texto\": \"...\", \"opcion_a\": \"...\", \"opcion_b\": \"...\"}}]"
                respuesta = solicitar_ia(prompt_a, JSON=True)
                
            resp = json.loads(limpiar_json(respuesta))[0]
            st.session_state.texto_lectura = resp['texto']
            st.session_state.aventura_opciones = [resp['opcion_a'], resp['opcion_b']]
        else:
            st.session_state.texto_lectura = st.session_state.texto_original
            
        barra.progress(50)
        if st.session_state.ajustes['diccionario'] and modo != "manual":
            st.write("Buscando las palabras más difíciles...")
            if st.session_state.modo_demo:
                st.session_state.diccionario = json.loads(obtener_respuesta_mock("diccionario"))
            else:
                prompt_d = f"Extrae las 3 palabras más difíciles de este texto. Devuelve estrictamente un JSON válido: [{{\"palabra\":\"x\", \"definicion\":\"y\", \"emoji\":\"😎\"}}]. Texto: {st.session_state.texto_lectura}"
                try: st.session_state.diccionario = json.loads(limpiar_json(solicitar_ia(prompt_d, JSON=True)))
                except: st.session_state.diccionario = []
            
        barra.progress(100)
        
        if st.session_state.ajustes['diccionario'] and st.session_state.diccionario:
            st.session_state.estado = 'pre_lectura'
        else: st.session_state.estado = 'lectura'
        st.rerun()
        
    except Exception as e:
        st.error(f"Error de conexión con la IA. Es posible que tu cuota gratuita se haya agotado.")
        with st.expander("Ver detalle técnico (Para el profesor)"): st.code(str(e))
        if st.button("Volver al inicio", type="primary"): reiniciar_app(mantener_perfil=True)

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
    
    if st.session_state.tiempo_inicio == 0.0:
        st.info("Acomódate, y cuando estés listo, presiona el botón. ¡Tómate todo tu tiempo!")
        if st.button("▶️ Empezar a leer", type="primary"):
            st.session_state.tiempo_inicio = float(time.time())
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
                if st.session_state.tiempo_inicio > 0.0:
                    st.session_state.tiempo_total += float(time.time() - st.session_state.tiempo_inicio)
                    st.session_state.tiempo_inicio = 0.0
                st.rerun()
            if col2.button("🅱️ " + st.session_state.aventura_opciones[1], use_container_width=True):
                st.session_state.eleccion = st.session_state.aventura_opciones[1]
                st.session_state.estado = 'resolviendo_aventura'
                if st.session_state.tiempo_inicio > 0.0:
                    st.session_state.tiempo_total += float(time.time() - st.session_state.tiempo_inicio)
                    st.session_state.tiempo_inicio = 0.0
                st.rerun()
        else:
            if st.button("✅ ¡Terminé de leer!", type="primary", use_container_width=True):
                if st.session_state.tiempo_inicio > 0.0:
                    st.session_state.tiempo_total += float(time.time() - st.session_state.tiempo_inicio)
                    st.session_state.tiempo_inicio = 0.0
                
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
        try:
            if st.session_state.modo_demo: 
                respuesta_av = obtener_respuesta_mock("aventura_final")
            else:
                respuesta_av = solicitar_ia(f"Continuación del cuento: {st.session_state.texto_lectura}. El niño eligió: '{st.session_state.eleccion}'. Escribe el final de la historia. Corto y simple.")
                
            final = respuesta_av.strip()
            st.session_state.texto_lectura += "\n\n***\n\n**TÚ DECIDISTE:** " + st.session_state.eleccion + "\n\n" + final
            st.session_state.aventura_paso = 1
            st.session_state.tiempo_inicio = float(time.time())
            st.session_state.estado = 'lectura'
            st.rerun()
        except Exception as e:
            st.error("Error al conectar con la IA para continuar la aventura.")
            with st.expander("Ver detalle técnico"): st.code(str(e))
            if st.button("Volver al inicio"): reiniciar_app(mantener_perfil=True)

# ==========================================
# PANTALLA 5: CREANDO PREGUNTAS
# ==========================================
elif st.session_state.estado == 'creando_preguntas':
    st.title("⏳ Preparando tu desafío...")
    barra = st.progress(0)
    for i in range(100): time.sleep(0.01); barra.progress(i + 1)
    
    with st.spinner("Analizando texto para generar retroalimentación educativa..."):
        al = st.session_state.perfil_activo
        prompt = f"""
        Eres un sistema estricto. Genera EXACTAMENTE 5 preguntas de comprensión lectora sobre el texto para un estudiante con {al['condicion']}. Nivel: {st.session_state.ajustes['dificultad']}.
        
        INSTRUCCIONES OBLIGATORIAS:
        1. Devuelve ÚNICAMENTE un arreglo JSON válido. NO escribas saludos, comentarios ni nada extra.
        2. Formato exacto a respetar:
        [
            {{"pregunta": "¿...?", "opciones": ["A", "B", "C"], "respuesta_correcta": "A", "explicacion": "Breve explicación."}}
        ]
        
        Texto: {st.session_state.texto_lectura}
        """
        try:
            if st.session_state.modo_demo: 
                respuesta_cruda = obtener_respuesta_mock("preguntas")
            else:
                respuesta_cruda = solicitar_ia(prompt, JSON=True)
                
            texto_limpio = limpiar_json(respuesta_cruda)
            preguntas = json.loads(texto_limpio)
            
            for p in preguntas:
                opc = [str(o).strip() for o in p.get("opciones", [])]
                corr = str(p.get("respuesta_correcta", "")).strip()
                if corr not in opc and len(opc) > 0: opc[0] = corr
                random.shuffle(opc)
                p["opciones"] = opc
                p["respuesta_correcta"] = corr
                
            st.session_state.preguntas = preguntas
            st.session_state.respuestas_usuario = {}
            st.session_state.evaluado = False
            st.session_state.estado = 'preguntas'
            st.rerun()
            
        except Exception as e:
            st.error("🚨 Hubo un problema al crear las preguntas o se agotó el saldo de IA.")
            st.info("¡No te preocupes! El progreso del estudiante y el tiempo medido están a salvo. Puedes intentar generarlas de nuevo o encender el Modo Demo.")
            
            with st.expander("Ver detalle técnico (Para el profesor)"):
                st.code(str(e))
                if 'respuesta_cruda' in locals():
                    st.write("Respuesta cruda:")
                    st.text(respuesta_cruda)
                    
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Volver a intentar generar preguntas", type="primary"): st.rerun()
            with col2:
                if st.button("🏠 Cancelar y volver al inicio"): reiniciar_app(mantener_perfil=True)

# ==========================================
# PANTALLA 6: PREGUNTAS Y REPORTE
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
        
        palabras = len(st.session_state.texto_lectura.split())
        mins = float(st.session_state.tiempo_total) / 60.0
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
        
        minutos_mostrar = int(float(st.session_state.tiempo_total) // 60)
        segundos_mostrar = int(float(st.session_state.tiempo_total) % 60)
        st.write(f"**Tiempo de lectura:** {minutos_mostrar} min y {segundos_mostrar} seg. | **Velocidad:** {ppm} PPM (Meta perfilada: {meta_ppm} PPM)")
        st.write(f"**Análisis:** {diag}")
        
        colA, colB = st.columns(2)
        with colA:
            if st.button("💾 Guardar Progreso en el Historial", use_container_width=True, type="primary"):
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                if not any(h['fecha'] == fecha for h in al.get('historial', [])):
                    al['historial'].append({"fecha": fecha, "ppm": ppm, "puntaje": puntaje, "total": total})
                    st.session_state.bd_alumnos[al['nombre']] = al
                    guardar_historial(st.session_state.bd_alumnos)
                    st.success("Guardado en la base de datos.")
        with colB:
            html_reporte = generar_reporte_html(al['nombre'], al['edad'], al['curso'], al['condicion'], ppm, puntaje, total, diag)
            st.markdown(html_reporte, unsafe_allow_html=True)
        
        if st.button("🔄 Volver al Inicio y Leer Otro Cuento"):
            reiniciar_app(mantener_perfil=True)
