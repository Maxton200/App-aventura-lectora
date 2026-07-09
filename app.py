import streamlit as st
import time
import json
import random

try:
    import google.generativeai as genai
    IA_DISPONIBLE = True
except ImportError:
    IA_DISPONIBLE = False

st.set_page_config(page_title="Aventura Lectora", layout="centered", page_icon="📚")

ESTILO_CSS = (
    "<style>"
    ".texto-lectura { font-size: 24px; line-height: 1.8; font-family: 'Arial', sans-serif; "
    "background-color: #FDF9E3; padding: 25px; border-radius: 15px; color: #222; "
    "box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }"
    "div.stButton > button { font-size: 22px; height: 60px; border-radius: 12px; "
    "background-color: #4CAF50; color: white; transition: all 0.3s ease; }"
    "div.stButton > button:hover { background-color: #45a049; }"
    ".instrucciones-api { background-color: #e8f4f8; padding: 15px; border-radius: 10px; font-size: 15px; margin-bottom: 20px; border-left: 5px solid #2196F3; color: #333;}"
    "</style>"
)
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- VARIABLES DE MEMORIA ---
if 'estado' not in st.session_state: st.session_state.estado = 'configuracion'
if 'tiempo_inicio' not in st.session_state: st.session_state.tiempo_inicio = 0
if 'tiempo_total' not in st.session_state: st.session_state.tiempo_total = 0
if 'preguntas' not in st.session_state: st.session_state.preguntas = []
if 'error_api' not in st.session_state: st.session_state.error_api = ""
if 'evaluado' not in st.session_state: st.session_state.evaluado = False
if 'api_key_guardada' not in st.session_state: st.session_state.api_key_guardada = ""
if 'perfil_guardado' not in st.session_state: st.session_state.perfil_guardado = {}

if st.session_state.estado == 'configuracion':
    st.title("⚙️ Área del Profesor")
    
    # INSTRUCCIONES CLARAS PARA LA PROFESORA
    st.markdown("""
    <div class="instrucciones-api">
    <b>🔑 Instrucciones: ¿Cómo activar la Inteligencia Artificial?</b><br>
    1. Entra a <a href="https://aistudio.google.com/" target="_blank">aistudio.google.com</a> e inicia sesión con tu Gmail.<br>
    2. Haz clic en el botón azul <b>"Get API key"</b> (arriba a la izquierda) y luego en <b>"Create API key"</b>.<br>
    3. Copia el código largo y pégalo en la casilla de abajo. <i>(Solo debes hacerlo una vez al abrir la página)</i>.
    </div>
    """, unsafe_allow_html=True)
    
    modo = st.radio("¿Cómo quieres crear las preguntas hoy?", 
                    ["🤖 Modo Inteligencia Artificial (Automático)", 
                     "✍️ Modo Manual (Yo escribo las preguntas)"])
    
    st.markdown("### 🧑‍🎓 Perfil del Estudiante (Para Diagnóstico de Lectura)")
    col1, col2, col3 = st.columns(3)
    edad_alumno = col1.number_input("Edad:", min_value=4, max_value=25, value=10)
    curso_alumno = col2.selectbox("Curso:", ["1º Básico", "2º Básico", "3º Básico", "4º Básico", "5º Básico", "6º Básico", "7º Básico", "8º Básico", "Educación Media"])
    condicion_alumno = col3.selectbox("Condición:", ["Ninguna", "Discapacidad Intelectual Leve (DIL)", "Trastorno por Déficit Atencional (TDAH)", "DIL + TDAH", "Otra"])

    texto_input = st.text_area("📖 Pega el texto de lectura aquí:", height=150)
    
    if "Inteligencia Artificial" in modo:
        api_key_input = st.text_input("Tu clave de Google API:", type="password", value=st.session_state.api_key_guardada)
            
        niveles = [
            "1 - Muy Fácil (Búsqueda de información literal y evidente)",
            "2 - Fácil (Identificar personajes, lugares y acciones directas)",
            "3 - Intermedio (Deducciones sencillas, conectar causa y efecto)",
            "4 - Avanzado (Inferir sentimientos, actitudes y motivaciones)",
            "5 - Desafío (Opinión personal, empatía y el 'por qué' de las cosas)"
        ]
        dificultad = st.selectbox("Elige el Nivel de Dificultad", niveles)
        
        if st.button("🚀 Iniciar Actividad con IA"):
            if texto_input and api_key_input:
                st.session_state.api_key_guardada = api_key_input
                st.session_state.texto = texto_input
                st.session_state.dificultad = dificultad
                st.session_state.perfil_guardado = {"edad": edad_alumno, "curso": curso_alumno, "condicion": condicion_alumno}
                st.session_state.evaluado = False
                st.session_state.estado = 'lectura'
                st.rerun()
            else:
                st.warning("Falta el texto o la clave API.")

    else:
        st.info("💡 Escribe tus propias preguntas. La aplicación mezclará las alternativas.")
        
        preguntas_manuales = []
        for i in range(5): 
            with st.expander("Pregunta " + str(i+1), expanded=(i==0)):
                q = st.text_input("La pregunta:", key="q_"+str(i))
                c = st.text_input("✅ Opción Correcta:", key="c_"+str(i))
                f1 = st.text_input("❌ Opción Falsa 1:", key="f1_"+str(i))
                f2 = st.text_input("❌ Opción Falsa 2 (Opcional):", key="f2_"+str(i))
                preguntas_manuales.append({"q": q, "c": c, "f1": f1, "f2": f2})
                
        if st.button("🚀 Iniciar Actividad (Manual)"):
            if texto_input and preguntas_manuales[0]["q"] and preguntas_manuales[0]["c"]:
                lista_final = []
                for p in preguntas_manuales:
                    if p["q"] and p["c"]:
                        opciones = [p["c"].strip(), p["f1"].strip(), p["f2"].strip()]
                        opciones = [op for op in opciones if op] 
                        random.shuffle(opciones) 
                        lista_final.append({
                            "pregunta": p["q"].strip(), 
                            "opciones": opciones, 
                            "respuesta_correcta": p["c"].strip()
                        })
                
                st.session_state.preguntas = lista_final
                st.session_state.texto = texto_input
                st.session_state.perfil_guardado = {"edad": edad_alumno, "curso": curso_alumno, "condicion": condicion_alumno}
                st.session_state.evaluado = False
                st.session_state.estado = 'lectura' 
                st.rerun()
            else:
                st.warning("Pega el texto y completa al menos la Pregunta 1 con su respuesta.")

elif st.session_state.estado == 'lectura':
    st.title("📖 ¡Es hora de leer!")
    
    if st.session_state.tiempo_inicio == 0:
        st.write("Tómate todo el tiempo que necesites. Cuando estés listo, presiona el botón.")
        if st.button("▶️ Empezar a Leer (Cronómetro oculto)"):
            st.session_state.tiempo_inicio = time.time()
            st.rerun()
    else:
        texto_html = st.session_state.texto.replace('\n', '<br>')
        st.markdown('<div class="texto-lectura">' + texto_html + '</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("✅ ¡Terminé de leer!"):
            st.session_state.tiempo_total = round(time.time() - st.session_state.tiempo_inicio)
            
            if len(st.session_state.preguntas) > 0:
                st.session_state.estado = 'preguntas'
            else:
                st.session_state.estado = 'generando_ia'
            st.rerun()

elif st.session_state.estado == 'generando_ia':
    st.title("⏳ Fabricando tu misión...")
    st.write("⏱️ Tiempo estimado: 10 segundos.")
    
    barra = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        barra.progress(i + 1)
            
    with st.spinner("Conectando con la Inteligencia Artificial..."):
        try:
            if not IA_DISPONIBLE: 
                raise Exception("Falta instalar la librería de Google.")
                
            genai.configure(api_key=st.session_state.api_key_guardada)
            
            modelo_elegido = None
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name.lower():
                        modelo_elegido = m.name
                        break
            
            if not modelo_elegido:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        modelo_elegido = m.name
                        break
                        
            if not modelo_elegido:
                raise Exception("Tu clave API es correcta, pero Google no detecta modelos disponibles.")
            
            model = genai.GenerativeModel(modelo_elegido)
            
            prompt = (
                "Eres un experto en educación diferencial. Genera EXACTAMENTE 5 preguntas "
                "sobre este texto para un niño con " + str(st.session_state.perfil_guardado['condicion']) + ". Nivel de dificultad: "
                + str(st.session_state.dificultad) + ". Reglas: Lenguaje muy simple. 3 opciones por pregunta. "
                "1 sola correcta. Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta y nada más: "
                '[{"pregunta": "¿Quién...?", "opciones": ["A", "B", "C"], "respuesta_correcta": "A"}]. '
                "MUY IMPORTANTE: El valor de 'respuesta_correcta' debe ser EXACTAMENTE IGUAL a una de las 'opciones'. "
                "Texto: " + str(st.session_state.texto)
            )
            
            respuesta = model.generate_content(prompt)
            texto_limpio = respuesta.text.strip()
            
            texto_limpio = texto_limpio.replace("```json", "").replace("```", "").strip()
                
            inicio = texto_limpio.find('[')
            fin = texto_limpio.rfind(']') + 1
            if inicio != -1 and fin != 0: 
                texto_limpio = texto_limpio[inicio:fin]
                
            datos_ia = json.loads(texto_limpio)
            
            preguntas_limpias = []
            for p in datos_ia:
                opciones_limpias = [str(op).strip() for op in p.get("opciones", [])]
                correcta_limpia = str(p.get("respuesta_correcta", "")).strip()
                
                if correcta_limpia not in opciones_limpias and len(opciones_limpias) > 0:
                    opciones_limpias[0] = correcta_limpia
                    
                random.shuffle(opciones_limpias)
                    
                preguntas_limpias.append({
                    "pregunta": str(p.get("pregunta", "")).strip(),
                    "opciones": opciones_limpias,
                    "respuesta_correcta": correcta_limpia
                })
                
            st.session_state.preguntas = preguntas_limpias
            st.session_state.estado = 'preguntas'
            st.rerun()
            
        except Exception as e:
            st.session_state.error_api = str(e)
            st.session_state.estado = 'error'
            st.rerun()

elif st.session_state.estado == 'error':
    st.error("🚨 La Inteligencia Artificial tuvo un problema.")
    
    st.write("**Detalle técnico del error (Para el profesor):**")
    st.code(st.session_state.error_api) 
    
    if st.button("🔄 Volver a intentar (Con IA)"):
        st.session_state.estado = 'generando_ia'
        st.rerun()
    if st.button("⚙️ Volver al menú inicial"):
        for key in list(st.session_state.keys()): 
            if key != 'api_key_guardada': del st.session_state[key]
        st.rerun()

elif st.session_state.estado == 'preguntas':
    minutos = st.session_state.tiempo_total // 60
    segundos = st.session_state.tiempo_total % 60
    st.success("⏱️ ¡Súper! Leíste durante " + str(minutos) + " min y " + str(segundos) + " seg. Gran trabajo.")
    
    st.title("🕵️‍♂️ Misión de Comprensión")
    
    todas_respondidas = True
    respuestas_usuario = {}
    
    for i, p in enumerate(st.session_state.preguntas):
        st.write("### " + str(i+1) + ". " + str(p.get('pregunta', '')))
        
        radio_key = "q_" + str(i)
        
        respuesta = st.radio("Elige tu respuesta:", p.get('opciones', []), key=radio_key, index=None, disabled=st.session_state.evaluado)
        
        respuestas_usuario[i] = respuesta
        if respuesta is None:
            todas_respondidas = False
            
        if st.session_state.evaluado:
            if respuesta == p.get('respuesta_correcta', ''):
                st.success("✨ ¡Correcto!")
            else:
                st.error("❌ Era casi... La correcta era: **" + str(p.get('respuesta_correcta', '')) + "**")
                
        st.write("---")
        
    if not st.session_state.evaluado:
        if st.button("✅ Revisar mis respuestas"):
            if todas_respondidas:
                st.session_state.evaluado = True
                st.rerun()
            else:
                st.warning("⚠️ ¡Espera! Te falta responder algunas preguntas. Revisa bien hacia arriba antes de entregar.")
    else:
        puntaje = 0
        total_preguntas = len(st.session_state.preguntas)
        
        for i, p in enumerate(st.session_state.preguntas):
            if respuestas_usuario[i] == p.get('respuesta_correcta', ''):
                puntaje += 1
                
        st.header("🏆 Tu Puntaje: " + str(puntaje) + " de " + str(total_preguntas))
        
        if puntaje == total_preguntas:
            st.balloons()
            st.success("¡Completaste todo perfectamente! Eres un genio de la lectura. 🌟")
        elif puntaje >= total_preguntas / 2:
            st.info("¡Muy bien hecho! Sigue así. 👍")
        else:
            st.warning("¡Buen intento! Con un poco más de práctica lo harás excelente, no te rindas. 💪")
            
        # --- REPORTE DE VELOCIDAD LECTORA (PPM) ---
        st.markdown("---")
        st.subheader("📊 Reporte de Fluidez Lectora (Profesor)")
        
        # 1. Calcular Palabras por Minuto (PPM)
        palabras = len(st.session_state.texto.split())
        minutos_totales = st.session_state.tiempo_total / 60.0
        ppm = int(palabras / minutos_totales) if minutos_totales > 0 else 0
        
        # 2. Diccionario base aproximado de PROLEC-R (PPM esperado por curso)
        esperado_base = {
            "1º Básico": 35,
            "2º Básico": 60,
            "3º Básico": 85,
            "4º Básico": 100,
            "5º Básico": 115,
            "6º Básico": 125,
            "7º Básico": 135,
            "8º Básico": 145,
            "Educación Media": 150
        }
        
        curso = st.session_state.perfil_guardado['curso']
        condicion = st.session_state.perfil_guardado['condicion']
        edad = st.session_state.perfil_guardado['edad']
        meta_ppm = esperado_base.get(curso, 85)
        
        # 3. Ajuste de expectativa de velocidad por condición neurológica/cognitiva
        if condicion == "Discapacidad Intelectual Leve (DIL)":
            meta_ppm = int(meta_ppm * 0.6) # Flexibilidad del 40%
        elif condicion == "Trastorno por Déficit Atencional (TDAH)":
            meta_ppm = int(meta_ppm * 0.8) # Flexibilidad del 20%
        elif condicion == "DIL + TDAH":
            meta_ppm = int(meta_ppm * 0.5) # Flexibilidad del 50%
        elif condicion == "Otra":
            meta_ppm = int(meta_ppm * 0.8) # Ajuste moderado por defecto
            
        st.write(f"**Perfil Evaluado:** {edad} años | {curso} | Condición: {condicion}")
        st.write(f"**Métricas:** Leyó {palabras} palabras en {minutos} min y {segundos} seg.")
        st.write(f"**Velocidad Alcanzada:** `{ppm} Palabras por Minuto (PPM)`")
        
        st.markdown("**Análisis según estándares (PROLEC-R adaptado):**")
        if ppm >= meta_ppm:
            st.success(f"🟢 **Velocidad Acorde/Óptima:** La fluidez lectora es adecuada para su curso y perfil (Expectativa mínima adaptada: {meta_ppm} PPM).")
        elif ppm >= meta_ppm * 0.75:
            st.warning(f"🟡 **En Desarrollo:** Velocidad ligeramente por debajo de lo esperado ({meta_ppm} PPM). Requiere estimulación moderada y lectura en conjunto.")
        else:
            st.error(f"🔴 **Lenta / Silábica:** Velocidad significativamente menor a lo esperado ({meta_ppm} PPM). Sugiere focalizar apoyo en decodificación y reconocimiento visual de palabras.")
            
        if st.button("🔄 Leer otro texto"):
            for key in list(st.session_state.keys()):
                if key != 'api_key_guardada':
                    del st.session_state[key]
            st.rerun()
