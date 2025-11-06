# streamlit_app.py - VERSIÓN COMPLETA CON FEEDBACK + IDIOMAS
import streamlit as st
from datetime import datetime

# Importaciones con manejo de errores
try:
    from firebase_config import db, auth_instance as auth
    from firebase_admin import firestore
except Exception as e:
    db = None
    auth = None
    firestore = None
    print(f"Firebase import error: {e}")

try:
    from dashboard import mostrar_dashboard_personalizado
    from journaling import mostrar_journaling_inteligente
    from chatbot import mostrar_chatbot_trading
    from estrategia_maestra import mostrar_estrategia_maestra
    from analisis_mercado import mostrar_proximamente
    from translations import get_translation
except ImportError as e:
    st.error(f"Error importing modules: {e}")

# ========== CONFIGURACIÓN INICIAL ==========
COLOR_PRIMARY = "#4A5A3D"
COLOR_SECONDARY = "#C9A34E"
COLOR_BACKGROUND = "#1E1E1E"
COLOR_TEXT = "#FFFFFF"

st.markdown(f"""
<style>
    .stApp {{
        background-color: {COLOR_BACKGROUND};
        color: {COLOR_TEXT};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOR_SECONDARY};
    }}
    .stMarkdown, .stText, .stSubheader, label, .stCaption, .stDataFrame {{
        color: {COLOR_TEXT} !important;
    }}
    .stButton>button {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT};
        border-radius: 8px;
    }}
    
    /* ========== ESTILOS PARA ELEMENTOS DE STREAMLIT ========== */
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
        background-color: #2E2E2E !important;
        border: 1px solid #4A5A3D !important;
        border-radius: 8px !important;
    }}
    
    /* Texto dentro de alertas */
    .stAlert p, .stInfo p, .stSuccess p, .stWarning p, .stError p {{
        color: #FFFFFF !important;
    }}
    
    /* Iconos dentro de alertas */
    .stAlert svg, .stInfo svg, .stSuccess svg, .stWarning svg, .stError svg {{
        fill: #C9A34E !important;
    }}
    
    /* Métricas de Streamlit */
    .stMetric {{
        background-color: #2E2E2E !important;
        border: 1px solid #4A5A3D !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }}
    
    .stMetric label {{
        color: #C9A34E !important;
        font-weight: bold !important;
    }}
    
    .stMetric div {{
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: normal !important;
    }}
    
    /* Checkboxes y selects */
    .stCheckbox label, .stRadio label, .stSelectbox label {{
        color: #FFFFFF !important;
    }}
    
    /* Inputs de texto */
    .stTextInput input, .stTextArea textarea {{
        background-color: #2E2E2E !important;
        color: #FFFFFF !important;
        border: 1px solid #4A5A3D !important;
    }}
    
    /* Sliders */
    .stSlider label {{
        color: #FFFFFF !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: #2E2E2E !important;
        color: #C9A34E !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 10px 16px !important;
        border: 1px solid #4A5A3D !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: #4A5A3D !important;
        color: #FFFFFF !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: #2E2E2E !important;
        color: #C9A34E !important;
        border: 1px solid #4A5A3D !important;
        border-radius: 8px !important;
        padding: 10px !important;
        margin-bottom: 10px !important;
    }}
    
    .streamlit-expanderContent {{
        background-color: #2E2E2E !important;
        border: 1px solid #4A5A3D !important;
        border-radius: 0px 0px 8px 8px !important;
        padding: 15px !important;
    }}
    
    /* Dataframes y tablas */
    .stDataFrame {{
        background-color: #2E2E2E !important;
        color: #FFFFFF !important;
    }}
    
    /* Tooltips */
    .stTooltip {{
        background-color: #4A5A3D !important;
        color: #FFFFFF !important;
    }}
</style>
""", unsafe_allow_html=True)

# ========== SISTEMA DE FEEDBACK MEJORADO ==========
def guardar_feedback(texto, correo, pagina, idioma):
    """Guarda feedback en Firebase y trigger de email"""
    if texto.strip():
        try:
            if db:
                feedback_data = {
                    "texto": texto,
                    "correo": correo,
                    "pagina": pagina,
                    "idioma": idioma,
                    "fecha": datetime.now().isoformat(),
                    "user_agent": "Streamlit App",
                }
                
                # Guardar en Firebase
                db.collection("feedback").add(feedback_data)
                
                # Trigger para email
                trigger_email_notification(feedback_data)
                
                # Mensaje de éxito
                if idioma == "en":
                    st.success("✅ Thank you! Your feedback is gold 🏆")
                else:
                    st.success("✅ ¡Gracias! Tu opinión vale oro 🏆")
                    
                # Limpiar el campo
                if 'feedback_input' in st.session_state:
                    st.session_state.feedback_input = ""
            else:
                if idioma == "en":
                    st.info("📝 Feedback saved locally (Firebase not connected)")
                else:
                    st.info("📝 Feedback guardado localmente (Firebase no conectado)")
                
        except Exception as e:
            st.error(f"❌ Error saving feedback: {str(e)}")
    else:
        if idioma == "en":
            st.warning("Please write something before sending")
        else:
            st.warning("Por favor, escribe algo antes de enviar")

def trigger_email_notification(feedback_data):
    """Placeholder para integración con EmailJS/Zapier"""
    # Por ahora solo log
    print(f"📧 New feedback from {feedback_data['correo']} on {feedback_data['pagina']}")

def seccion_feedback():
    """Sistema de feedback con tracking de página"""
    st.sidebar.markdown("---")
    with st.sidebar.expander("💬 Send Feedback / Enviar Comentarios"):
        
        # Detectar página actual
        pagina_actual = st.session_state.get('opcion', 'Unknown')
        
        feedback_text = st.text_area(
            "Your feedback or suggestion / Tu opinión o sugerencia:",
            placeholder="What do you like? What can be improved? / ¿Qué te gusta? ¿Qué podemos mejorar?",
            key="feedback_input"
        )
        
        user_email = st.text_input(
            "Your email (optional) / Tu correo (opcional):",
            value=st.session_state.user.get('email', '') if 'user' in st.session_state else "",
            key="feedback_email"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📤 Send Feedback", key="enviar_feedback_en"):
                guardar_feedback(feedback_text, user_email, pagina_actual, "en")
        with col2:
            if st.button("📤 Enviar Comentario", key="enviar_feedback_es"):
                guardar_feedback(feedback_text, user_email, pagina_actual, "es")

# ========== AUTH MEJORADA CON MANEJO DE ERRORES ==========
def get_user_role(uid):
    """Obtener rol del usuario con manejo de errores"""
    try:
        if db:
            doc = db.collection('user_roles').document(uid).get()
            return doc.to_dict().get('role', 'mentee') if doc.exists else 'mentee'
        return 'mentee'
    except Exception as e:
        st.error(f"Error obteniendo rol: {str(e)}")
        return 'mentee'

def auth_ui():
    """Interfaz de autenticación con soporte para idiomas"""
    lang = st.session_state.get("language", "en")
    
    st.title(get_translation(lang, "login_title"))

    if db is None:
        st.warning(get_translation(lang, "demo_warning"))
    
    tab1, tab2 = st.tabs(["Login", "Register"] if lang == "en" else ["Ingresar", "Registrarse"])
    
    with tab1:
        with st.form("Login"):
            email = st.text_input(get_translation(lang, "login_email"))
            password = st.text_input(get_translation(lang, "login_password"), type="password")
            if st.form_submit_button(get_translation(lang, "login_button")):
                try:
                    if auth:
                        user = auth.get_user_by_email(email)
                        st.session_state.user = {
                            'uid': user.uid,
                            'email': email,
                            'role': get_user_role(user.uid)
                        }
                        st.rerun()
                    else:
                        st.session_state.user = {
                            'uid': f"demo-user-{hash(email)}",
                            'email': email,
                            'role': 'mentee'
                        }
                        st.success(get_translation(lang, "demo_login_success"))
                        st.rerun()
                except Exception as e:
                    if "USER_NOT_FOUND" in str(e):
                        if lang == "en":
                            st.error("User not found. Please register first.")
                        else:
                            st.error("Usuario no encontrado. Por favor regístrate primero.")
                    else:
                        st.error(f"Error: {str(e)}")
    
    with tab2:
        with st.form("Registro"):
            email = st.text_input(get_translation(lang, "login_email"))
            password = st.text_input(get_translation(lang, "login_password"), type="password")
            role_options = get_translation(lang, "roles")
            role = st.selectbox(get_translation(lang, "role_select"), role_options)
            if st.form_submit_button(get_translation(lang, "register_button")):
                try:
                    if auth and db:
                        user = auth.create_user(email=email, password=password)
                        db.collection('user_roles').document(user.uid).set({
                            'role': 'mentor' if role == role_options[1] else 'mentee'
                        })
                        if lang == "en":
                            st.success("Account created! Please login.")
                        else:
                            st.success("¡Cuenta creada! Inicia sesión.")
                    else:
                        if lang == "en":
                            st.info("🔧 Demo mode - Registration simulated")
                        else:
                            st.info("🔧 Modo demo - Registro simulado")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ========== BARRA LATERAL MEJORADA ==========
def sidebar():
    # Selector de idioma (solo mostrar si no hay usuario)
    if 'user' not in st.session_state:
        st.sidebar.markdown("### 🌐 Language / Idioma")
        lang = st.sidebar.radio("Choose your language / Elige tu idioma:", ["English", "Español"], horizontal=True)
        st.session_state.language = "en" if lang == "English" else "es"
    
    st.sidebar.title("🚀 Trading Yeah")
    
    if 'user' not in st.session_state:
        auth_ui()
        st.stop()
        
    lang = st.session_state.get("language", "en")
    
    st.sidebar.write(f"👤 {st.session_state.user['email']}")
    st.sidebar.write(f"🎖️ {get_translation(lang, 'sidebar_role')}: {st.session_state.user['role'].capitalize()}")
    
    if db is None:
        st.sidebar.warning(get_translation(lang, "sidebar_demo"))

    # Menú con traducciones
    opciones = get_translation(lang, "menu_items")
    
    # Guardar opción actual para tracking
    opcion_seleccionada = st.sidebar.radio(get_translation(lang, "sidebar_menu"), opciones)
    st.session_state.opcion = opcion_seleccionada
    
    # Agregar feedback
    seccion_feedback()
    
    # Sección de onboarding/beta testing
    st.sidebar.markdown("---")
    if st.sidebar.button("🧪 Beta Testing Guide" if lang == "en" else "🧪 Guía Beta"):
        st.session_state.show_onboarding = True
    
    return opcion_seleccionada

# ========== SECCIÓN ONBOARDING ==========
def mostrar_guia_onboarding():
    """Muestra la guía de onboarding para testers"""
    lang = st.session_state.get("language", "en")
    
    if lang == "en":
        st.title("🧪 Trading Yeah - Beta Testing Guide")
        st.success("🚀 **Welcome to Trading Yeah Beta!**\n\nThank you for helping us improve. Your feedback is crucial to build the best trading platform possible.")
        
        with st.expander("🎯 What to Test", expanded=True):
            st.markdown("""
            **Please focus on:**
            - 🧠 **Intelligent Journaling**: Does it help you analyze your trades better?
            - 📊 **Dashboard**: Are the metrics useful and understandable?  
            - 💬 **Psychological Support**: Are the AI responses helpful?
            - 📝 **Trading Planner**: Is the planning process intuitive?
            - 🎨 **UI/UX**: Is the interface easy to use?
            """)
        
        with st.expander("📝 How to Give Feedback"):
            st.markdown("""
            **Be specific and constructive:**
            - ❌ **Not helpful**: "I don't like it"
            - ✅ **Helpful**: "The journaling form is confusing because [...]"
            
            **Use the feedback section in the sidebar** to report:
            - Bugs or errors
            - Confusing interfaces  
            - Missing features
            - Things you love! ❤️
            """)
            
        st.info("💡 **Pro tip**: Use the platform as you would normally trade. The most valuable feedback comes from real usage!")
    else:
        st.title("🧪 Trading Yeah - Guía Beta")
        st.success("🚀 **¡Bienvenido a Trading Yeah Beta!**\n\nGracias por ayudarnos a mejorar. Tu feedback es crucial para construir la mejor plataforma de trading posible.")
        
        with st.expander("🎯 Qué Probar", expanded=True):
            st.markdown("""
            **Por favor enfócate en:**
            - 🧠 **Journaling Inteligente**: ¿Te ayuda a analizar mejor tus operaciones?
            - 📊 **Dashboard**: ¿Son útiles y entendibles las métricas?  
            - 💬 **Apoyo Psicológico**: ¿Son útiles las respuestas de IA?
            - 📝 **Planificador de Trading**: ¿Es intuitivo el proceso de planificación?
            - 🎨 **UI/UX**: ¿Es fácil de usar la interfaz?
            """)
        
        with st.expander("📝 Cómo Dar Feedback"):
            st.markdown("""
            **Sé específico y constructivo:**
            - ❌ **No útil**: "No me gusta"
            - ✅ **Útil**: "El formulario de journaling es confuso porque [...]"
            
            **Usa la sección de feedback en la barra lateral** para reportar:
            - Errores o bugs
            - Interfaces confusas  
            - Funcionalidades faltantes
            - ¡Cosas que amas! ❤️
            """)
            
        st.info("💡 **Consejo profesional**: Usa la plataforma como lo harías normalmente al tradear. ¡El feedback más valioso viene del uso real!")

# ========== MAIN CORREGIDO ==========
def main():
    # Mostrar onboarding si se solicita
    if st.session_state.get('show_onboarding'):
        mostrar_guia_onboarding()
        lang = st.session_state.get("language", "en")
        if st.button("← Back to Platform" if lang == "en" else "← Volver a la Plataforma"):
            st.session_state.show_onboarding = False
            st.rerun()
        return
    
    opcion = sidebar()
    
    # Mapear opciones traducidas a las funciones originales
    opciones_base = {
        "Dashboard": "Dashboard",
        "Intelligent Journaling": "Journaling Inteligente", 
        "Psychological Support": "Apoyo Psicológico",
        "Trading Planner": "Planificador de Trading",
        "🚀 Coming Soon": "🚀 Próximamente",
        "Journaling Inteligente": "Journaling Inteligente",
        "Apoyo Psicológico": "Apoyo Psicológico",
        "Planificador de Trading": "Planificador de Trading",
        "🚀 Próximamente": "🚀 Próximamente"
    }
    
    opcion_base = opciones_base.get(opcion, opcion)
    
    if opcion_base == "Dashboard":
        mostrar_dashboard_personalizado()
    elif opcion_base == "Journaling Inteligente":
        mostrar_journaling_inteligente()
    elif opcion_base == "Apoyo Psicológico":
        mostrar_chatbot_trading()
    elif opcion_base == "Planificador de Trading":
        mostrar_estrategia_maestra()
    elif opcion_base == "🚀 Próximamente":
        mostrar_proximamente()

if __name__ == "__main__":
    main()