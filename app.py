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

# Memoria permanente para la clave de Google API
if 'api_key_guardada' not in st.session_state: st.session_state.api_key_guardada = ""

if st.session_state.estado == 'configuracion':
    st.title("⚙️ Área del Profesor")
    
    modo = st.radio("¿Cómo quieres crear las preguntas hoy?", 
                    ["🤖 Modo Inteligencia Artificial (Automático)", 
                     "✍️ Modo Manual (Yo escribo las preguntas)"])
    
    texto_input = st.text_area("📖 Pega el texto de lectura aquí:", height=150)
    
    if "Inteligencia Artificial" in modo:
        # Carga la clave automáticamente si ya la habías puesto
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
                st.session_state.api_key_guardada = api_key_input # Guardamos la clave
                st.session_state.texto = texto_input
                st.session_state.dificultad = dificultad
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
                "sobre este texto para un niño con discapacidad intelectual leve. Nivel de dificultad: "
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
            
            # Limpiar espacios invisibles para que la corrección sea perfecta
            preguntas_limpias = []
            for p in datos_ia:
                opciones_limpias = [str(op).strip() for op in p.get("opciones", [])]
                correcta_limpia = str(p.get("respuesta_correcta", "")).strip()
                
                # Nos aseguramos al 100% que la correcta esté en la lista
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
        
        # El estudiante marca, pero si ya se evaluó, los botones se bloquean.
        respuesta = st.radio("Elige tu respuesta:", p.get('opciones', []), key=radio_key, index=None, disabled=st.session_state.evaluado)
        
        respuestas_usuario[i] = respuesta
        if respuesta is None:
            todas_respondidas = False
            
        # Solo muestra la corrección SI ya presionó evaluar al final de la página
        if st.session_state.evaluado:
            if respuesta == p.get('respuesta_correcta', ''):
                st.success("✨ ¡Correcto!")
            else:
                st.error("❌ Casi... La correcta era: **" + str(p.get('respuesta_correcta', '')) + "**")
                
        st.write("---")
        
    # --- BOTÓN DE EVALUACIÓN FINAL ---
    if not st.session_state.evaluado:
        if st.button("✅ Revisar mis respuestas"):
            if todas_respondidas:
                st.session_state.evaluado = True
                st.rerun()
            else:
                st.warning("⚠️ ¡Espera! Te falta responder algunas preguntas. Revisa bien hacia arriba antes de entregar.")
    else:
        # Calcular y mostrar el puntaje final
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
            
        if st.button("🔄 Leer otro texto"):
            # Limpiamos todas las memorias MENOS la clave de la API
            for key in list(st.session_state.keys()):
                if key != 'api_key_guardada':
                    del st.session_state[key]
            st.rerun()