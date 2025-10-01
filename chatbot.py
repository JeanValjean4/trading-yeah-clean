# chatbot.py - VERSIÓN MEJORADA Y CORREGIDA
import streamlit as st
import openai
import json
from datetime import datetime
import random
import time
from firebase_config import db
import os
import pandas as pd
import plotly.express as px


# Configuración segura de API key
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))

# ========== SISTEMA DE MEMORIA Y CONTEXTO ==========
def cargar_historial_chat(user_id):
    """Carga el historial de conversación del usuario"""
    try:
        doc_ref = db.collection('users').document(user_id).collection('chatbot').document('historial')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('conversaciones', [])
        return []
    except Exception as e:
        st.error(f"Error al cargar historial: {str(e)}")
        return []

def guardar_historial_chat(user_id, conversaciones):
    """Guarda el historial de conversación"""
    try:
        doc_ref = db.collection('users').document(user_id).collection('chatbot').document('historial')
        doc_ref.set({
            'conversaciones': conversaciones[-20:],  # Mantener sólo las últimas 20 interacciones
            'ultima_actualizacion': datetime.now().isoformat()
        })
    except Exception as e:
        st.error(f"Error al guardar historial: {str(e)}")

def cargar_perfil_emocional(user_id):
    """Carga el perfil emocional del usuario"""
    try:
        doc_ref = db.collection('users').document(user_id).collection('chatbot').document('perfil_emocional')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {'estado_actual': 'neutral', 'patrones': [], 'mantras_personalizados': []}
    except Exception as e:
        st.error(f"Error al cargar perfil emocional: {str(e)}")
        return {'estado_actual': 'neutral', 'patrones': [], 'mantras_personalizados': []}

def guardar_perfil_emocional(user_id, perfil):
    """Guarda el perfil emocional del usuario"""
    try:
        doc_ref = db.collection('users').document(user_id).collection('chatbot').document('perfil_emocional')
        doc_ref.set(perfil)
    except Exception as e:
        st.error(f"Error al guardar perfil emocional: {str(e)}")

# ========== MANTRAS Y RECORDATORIOS ==========
MANTRAS_PREDETERMINADOS = [
    "El mercado siempre tendrá otra oportunidad, no te cases con una operación",
    "La consistencia es más importante que la ganancia ocasional",
    "Gestiona el riesgo primero, las ganancias vendrán después",
    "Las pérdidas son parte del juego, acéptalas y aprende",
    "Opera el plan, planifica la operación",
    "La paciencia es la virtud más valiosa del trader",
    "No confundas suerte con estrategia",
    "El control emocional es el 90% del trading exitoso",
    "Pequeñas ganancias consistentes > grandes ganancias esporádicas",
    "El análisis es importante, pero la ejecución lo es más"
]

RECORDATORIOS_TEMPORALES = {
    'mañana': [
        "¿Has revisado tu plan de trading para hoy?",
        "Recuerda: solo operaciones de alta probabilidad hoy",
        "Mantén tu riesgo por operación bajo control",
        "Visualiza tu sesión de trading exitosa"
    ],
    'tarde': [
        "¿Estás siguiendo tu plan o operando por impulso?",
        "Revisa tu gestión de riesgo en las operaciones actuales",
        "Mantén la calma, el mercado estará ahí mañana",
        "No forces operaciones si el mercado no da setups claros"
    ],
    'noche': [
        "Haz tu journaling de hoy, ¿qué aprendiste?",
        "Analiza tus operaciones sin juicio, solo aprendizaje",
        "Desconecta del mercado, tu mente necesita descanso",
        "Prepárate mentalmente para el día de mañana"
    ]
}

# ========== DETECCIÓN EMOCIONAL MEJORADA ==========
def analizar_estado_emocional(texto):
    """Analiza el estado emocional del texto usando IA - Versión mejorada"""
    try:
        prompt = f"""
        Como psicólogo especializado en traders, analiza este mensaje y responde SOLO con JSON válido:
        {{
            "emocion_principal": "ansiedad|confianza|frustracion|euforia|calma|neutral|miedo|culpa|impulsividad",
            "intensidad": 1-10,
            "necesita_ayuda_urgente": true/false,
            "palabras_clave": ["lista", "de", "palabras"],
            "tipo_problema": "riesgo|disciplina|perdida|ganancia|overtrading|ansiedad"
        }}

        Texto del trader: "{texto}"

        Sé preciso y analítico. El trader necesita ayuda real.
        """

        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un analista emocional experto en trading. Responde solo con JSON válido y preciso."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Menor temperatura para más precisión
            max_tokens=200
        )
        
        return json.loads(respuesta["choices"][0]["message"]["content"])
    except Exception as e:
        return {
            "emocion_principal": "neutral",
            "intensidad": 5,
            "necesita_ayuda_urgente": False,
            "palabras_clave": [],
            "tipo_problema": "general"
        }

# ========== RESPUESTAS INTELIGENTES MEJORADAS ==========
def generar_respuesta_emocional(user_input, estado_emocional, historial, perfil_emocional):
    """Genera una respuesta psicológica apropiada - Versión mejorada"""
    
    # Actualizar perfil emocional
    perfil_emocional['estado_actual'] = estado_emocional['emocion_principal']
    perfil_emocional['ultima_actualizacion'] = datetime.now().isoformat()
    
    # Construir contexto detallado para la IA
    contexto = f"""
    Eres Dr. Trading, un coach psicológico especializado EXCLUSIVAMENTE en traders profesionales. 
    
    CONTEXTO ACTUAL:
    - Estado emocional: {estado_emocional['emocion_principal']} (Intensidad: {estado_emocional['intensidad']}/10)
    - Tipo de problema: {estado_emocional.get('tipo_problema', 'general')}
    - Palabras clave detectadas: {', '.join(estado_emocional.get('palabras_clave', []))}
    
    HISTORIAL RECIENTE:
    {json.dumps(historial[-3:] if historial else 'Sin historial reciente', ensure_ascii=False)}
    
    RESPONDE CON:
    - Análisis psicológico PROFESIONAL del problema
    - 2-3 acciones CONCRETAS y prácticas para resolverlo
    - Un framework específico para manejar esta situación
    - Referencia a técnicas de psicología trading comprobadas
    - Máximo 2 párrafos, extremadamente conciso pero útil
    - Lenguaje profesional pero accesible
    - Incluye un mantra relevante si aplica
    
    EJEMPLO DE RESPUESTA PROFESIONAL:
    "Entiendo tu frustración por la operación perdedora. Esto es classic revenge trading. 
    Paso 1: Detente inmediatamente y cierra todas las plataformas. 
    Paso 2: Revisa tu plan de trading y identifica QUÉ regla rompiste. 
    Paso 3: Mañana solo operarás con tamaño reducido al 50%. 
    Recuerda: 'Las pérdidas son tuition fees, no failures'."
    
    El usuario dijo: "{user_input}"
    """

    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": contexto},
                {"role": "user", "content": user_input}
            ],
            temperature=0.8,
            max_tokens=400
        )
        return respuesta["choices"][0]["message"]["content"]
    except Exception as e:
        # Respuesta de fallback MUCHO más útil
        return f"""🔍 **Análisis de tu situación:** Detecto {estado_emocional['emocion_principal']} de intensidad {estado_emocional['intensidad']}/10.

🚀 **Acciones inmediatas:**
1. Detén toda operación por hoy
2. Revisa tu journaling de las últimas 3 operaciones
3. Programa una revisión de tu plan de trading

💡 **Recordatorio clave:** '{random.choice(MANTRAS_PREDETERMINADOS)}'

¿Qué regla específica de tu plan crees que se vio comprometida?"""

# ========== SISTEMA DE RECORDATORIOS MEJORADO ==========
def obtener_recordatorio_contextual(user_id):
    """Devuelve recordatorios basados en la hora y contexto - Versión mejorada"""
    try:
        # Cargar recordatorios personalizados
        perfil = cargar_perfil_emocional(user_id)
        recordatorios_personalizados = perfil.get('recordatorios_personalizados', [])
        
        # Filtrar recordatorios activos
        recordatorios_activos = [
            r for r in recordatorios_personalizados 
            if r.get('activo', True) and (
                r.get('frecuencia') == 'Siempre visible' or
                (r.get('frecuencia') == 'Diario' and 
                 datetime.now().timestamp() - datetime.fromisoformat(r.get('creado', '2023-01-01')).timestamp() < 86400) or
                (r.get('frecuencia') == 'Semanal' and 
                 datetime.now().timestamp() - datetime.fromisoformat(r.get('creado', '2023-01-01')).timestamp() < 604800)
            )
        ]
        
        if recordatorios_activos:
            return random.choice(recordatorios_activos)['texto']
        
        # Si no hay recordatorios personalizados, usar los predeterminados
        hora_actual = datetime.now().hour
        
        if 5 <= hora_actual < 12:
            return random.choice(RECORDATORIOS_TEMPORALES['mañana'])
        elif 12 <= hora_actual < 18:
            return random.choice(RECORDATORIOS_TEMPORALES['tarde'])
        else:
            return random.choice(RECORDATORIOS_TEMPORALES['noche'])
            
    except Exception as e:
        return "Revisa tu plan de trading antes de operar hoy"

def obtener_mantra_personalizado(perfil_emocional):
    """Selecciona un mantra apropiado para el estado actual"""
    try:
        if perfil_emocional.get('mantras_personalizados'):
            return random.choice(perfil_emocional['mantras_personalizados'])
        return random.choice(MANTRAS_PREDETERMINADOS)
    except:
        return "Opera el plan, planifica la operación"

# ========== INTERFAZ PRINCIPAL MEJORADA ==========
def mostrar_chatbot_trading():
    st.title("🧠 Apoyo Psicológico en Tiempo Real")
    
    # Aplicar estilos CSS para mejorar la visualización
    st.markdown("""
    <style>
    .stMetric {
        background-color: #2E2E2E;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #C9A34E;
    }
    .stMetric label {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    .stMetric div {
        color: #C9A34E !important;
        font-size: 16px !important;
    }
    .mantra-box {
        background-color: #3A3A3A !important;
        color: #FFFFFF !important;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #4A5A3D;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificar autenticación
    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión para acceder al apoyo psicológico")
        return
    
    user_id = st.session_state.user['uid']
    
    # Cargar datos del usuario
    historial = cargar_historial_chat(user_id)
    perfil_emocional = cargar_perfil_emocional(user_id)
    
    # ========== SECCIÓN 1: ESTADO ACTUAL MEJORADO ==========
    st.header("📋 Tu Estado Actual")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Estado emocional con mejor visualización
        emocion_actual = perfil_emocional.get('estado_actual', 'neutral').capitalize()
        st.metric("Estado Emocional", emocion_actual)
    
    with col2:
        # Mantra completo y visible
        mantra_completo = obtener_mantra_personalizado(perfil_emocional)
        st.metric("Mantra del Día", mantra_completo)
    
    with col3:
        # Recordatorio completo
        recordatorio = obtener_recordatorio_contextual(user_id)
        st.metric("Recordatorio", recordatorio)
    
    # ========== SECCIÓN 2: CHAT INTERACTIVO MEJORADO ==========
    st.header("💬 Chat de Apoyo Psicológico")
    
    # Mostrar historial de conversación
    for msg in historial[-8:]:  # Mostrar últimas 8 interacciones
        with st.chat_message("user" if msg['tipo'] == 'usuario' else "assistant"):
            st.write(msg['mensaje'])
            if msg.get('emocion'):
                st.caption(f"⌚ {msg['timestamp']} • 🎭 {msg['emocion'].capitalize()}")
    
    # Input de chat
    user_input = st.chat_input("¿Cómo te sientes o en qué necesitas apoyo?")
    
    if user_input:
        # Analizar estado emocional
        with st.spinner("🔍 Analizando tu estado emocional..."):
            estado_emocional = analizar_estado_emocional(user_input)
            time.sleep(1)  # Pequeña pausa para mejor UX
        
        # Guardar mensaje del usuario
        mensaje_usuario = {
            'tipo': 'usuario',
            'mensaje': user_input,
            'timestamp': datetime.now().strftime("%H:%M"),
            'emocion': estado_emocional['emocion_principal']
        }
        historial.append(mensaje_usuario)
        
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.write(user_input)
            st.caption(f"⌚ {mensaje_usuario['timestamp']} • 🎭 {estado_emocional['emocion_principal'].capitalize()}")
        
        # Generar y mostrar respuesta MEJORADA
        with st.spinner("💭 Analizando la mejor estrategia para ayudarte..."):
            respuesta = generar_respuesta_emocional(user_input, estado_emocional, historial, perfil_emocional)
            time.sleep(1)  # Pequeña pausa para mejor UX
        
        mensaje_asistente = {
            'tipo': 'asistente',
            'mensaje': respuesta,
            'timestamp': datetime.now().strftime("%H:%M"),
            'emocion_detectada': estado_emocional['emocion_principal']
        }
        historial.append(mensaje_asistente)
        
        with st.chat_message("assistant"):
            st.write(respuesta)
            st.caption(f"⌚ {mensaje_asistente['timestamp']} • 🎯 Basado en tu estado emocional")
        
        # Guardar historial y perfil actualizado
        guardar_historial_chat(user_id, historial)
        guardar_perfil_emocional(user_id, perfil_emocional)
        st.rerun()  # Forzar actualización para mostrar nuevos mensajes
    
    # ========== SECCIÓN 3: HERRAMIENTAS RÁPIDAS MEJORADAS ==========
    st.header("⚡ Herramientas Rápidas")
    
    tab1, tab2, tab3 = st.tabs(["🧘 Mantras", "📋 Recordatorios", "🎯 Acciones Rápidas"])
    
    with tab1:
        st.subheader("Mantras Personalizados")
        selected_mantra = st.selectbox("Elige un mantra para hoy:", MANTRAS_PREDETERMINADOS)
        
        if st.button("💾 Guardar como favorito", key="guardar_mantra"):
            if 'mantras_personalizados' not in perfil_emocional:
                perfil_emocional['mantras_personalizados'] = []
            if selected_mantra not in perfil_emocional['mantras_personalizados']:
                perfil_emocional['mantras_personalizados'].append(selected_mantra)
                if guardar_perfil_emocional(user_id, perfil_emocional):
                    st.success("✅ Mantra guardado en tus favoritos!")
        
        st.subheader("Tus mantras favoritos")
        if perfil_emocional.get('mantras_personalizados'):
            for mantra in perfil_emocional['mantras_personalizados']:
                st.markdown(f'<div class="mantra-box">• {mantra}</div>', unsafe_allow_html=True)
        else:
            st.info("📝 Aún no tienes mantras favoritos. Guarda algunos arriba!")
    
    with tab2:
        st.subheader("📋 Recordatorios Contextuales")
        recordatorio_actual = obtener_recordatorio_contextual(user_id)
        st.info(f"🔔 {recordatorio_actual}")
        
        st.subheader("⏰ Programar Recordatorio Personalizado")
        
        with st.form("nuevo_recordatorio"):
            recordatorio_personalizado = st.text_input("Tu recordatorio personalizado:", 
                                                     placeholder="Ej: Revisar el RSI antes de cada entrada")
            frecuencia = st.selectbox("Frecuencia:", ["Diario", "Semanal", "Siempre visible"])
            
            if st.form_submit_button("💾 Programar Recordatorio"):
                if recordatorio_personalizado:
                    if 'recordatorios_personalizados' not in perfil_emocional:
                        perfil_emocional['recordatorios_personalizados'] = []
                    
                    perfil_emocional['recordatorios_personalizados'].append({
                        'texto': recordatorio_personalizado,
                        'frecuencia': frecuencia,
                        'creado': datetime.now().isoformat(),
                        'activo': True
                    })
                    
                    if guardar_perfil_emocional(user_id, perfil_emocional):
                        st.success("✅ Recordatorio programado correctamente!")
                        st.rerun()
    
    with tab3:
        st.subheader("🎯 Acciones Rápidas para Estados Emocionales")
        
        emocion = st.selectbox("Selecciona tu estado emocional actual:", 
                              ["Ansiedad", "Frustración", "Euforia", "Miedo", "Aburrimiento", "Impulsividad"])
        
        if st.button("🚀 Obtener Acción Recomendada", key="accion_rapida"):
            acciones = {
                "Ansiedad": """🔍 **Diagnóstico:** Ansiedad pre-operacional
🚀 **Acción:** Haz 5 minutos de respiración 4-7-8 (4s inhalar, 7s retener, 8s exhalar)
📋 **Checklist:** Revisa tu plan 3 veces antes de entrar""",
                
                "Frustración": """🔍 **Diagnóstico:** Frustración por operaciones perdedoras
🚀 **Acción:** Revisa 3 operaciones pasadas EXITOSAS
📋 **Checklist:** Anota 3 cosas que hiciste bien esta semana""",
                
                "Euforia": """🔍 **Diagnóstico:** Exceso de confianza (peligroso)
🚀 **Acción:** Reduce tamaño de posición al 50% hoy
📋 **Checklist:** Revisa tu máximo drawdown permitido""",
                
                "Miedo": """🔍 **Diagnóstico:** Parálisis por análisis
🚀 **Acción:** Opera con tamaño 25% más pequeño
📋 **Checklist:** Enfócate en 1 solo setup confiable""",
                
                "Aburrimiento": """🔍 **Diagnóstico:** Buscando acción en mercados planos
🚀 **Acción:** Lee un libro de trading, NO operes
📋 **Checklist:** Backtesta tu estrategia en vez de operar""",
                
                "Impulsividad": """🔍 **Diagnóstico:** Trading por impulso emocional
🚀 **Acción:** Cierra TODAS las plataformas 1 hora
📋 **Checklist:** Revisa qué desencadenó el impulso"""
            }
            
            st.success(acciones[emocion])
    
    # ========== SECCIÓN 4: PANEL DE ESTADÍSTICAS EMOCIONALES ==========
    with st.expander("📊 Estadísticas Emocionales (Haz clic para ver)"):
        if historial:
            # Analizar patrones emocionales
            emociones = [msg.get('emocion', 'neutral') for msg in historial if msg['tipo'] == 'usuario']
            if emociones:
                from collections import Counter
                conteo_emociones = Counter(emociones)
                
                st.subheader("📈 Tu Perfil Emocional en Trading")
                
                col_graf, col_stats = st.columns([2, 1])
                
                with col_graf:
                    # Gráfico de emociones
                    df_emociones = pd.DataFrame.from_dict(conteo_emociones, orient='index').reset_index()
                    df_emociones.columns = ['Emoción', 'Frecuencia']
                    fig = px.bar(df_emociones, x='Emoción', y='Frecuencia', 
                                title='Distribución de Estados Emocionales',
                                color='Emoción')
                    st.plotly_chart(fig)
                
                with col_stats:
                    st.write("**📊 Estadísticas:**")
                    for emocion, count in conteo_emociones.most_common():
                        st.write(f"• {emocion.capitalize()}: {count} veces")
                
                # Recomendación basada en patrones
                emocion_comun = conteo_emociones.most_common(1)[0][0]
                recomendaciones = {
                    "ansiedad": "🧘 Considera practicar meditación 10 min antes de trading",
                    "frustración": "📝 Establece expectativas más realistas sobre drawdowns",
                    "euforia": "⚠️ Cuidado con overconfidence - mantén tu risk management",
                    "miedo": "🛡️ Trabaja en tamaño de posición gradual (scaling in)",
                    "neutral": "✅ Buen equilibrio emocional - mantén tu disciplina",
                    "impulsividad": "⏰ Implementa reglas de 'cooling off' antes de operar"
                }
                
                st.info(f"**🎯 Recomendación personalizada:** {recomendaciones.get(emocion_comun, 'Mantén tu enfoque actual')}")
            else:
                st.info("📊 Aún no hay suficientes datos para análisis emocional. ¡Interactúa más con el chatbot!")
        else:
            st.info("💬 Interactúa con el chatbot para generar estadísticas emocionales útiles")

# Ejecutar si se corre directamente
if __name__ == "__main__":
    mostrar_chatbot_trading()