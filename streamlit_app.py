# streamlit_app.py - VERSIÓN CORREGIDA Y LIMPIA
import streamlit as st
from firebase_config import db, auth_instance as auth
from dashboard import mostrar_dashboard_personalizado
from journaling import mostrar_journaling_inteligente
from chatbot import mostrar_chatbot_trading
from estrategia_maestra import mostrar_estrategia_maestra
from analisis_mercado import mostrar_proximamente

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
    """Interfaz de autenticación con manejo de modos"""
    st.title("🔐 Trading Yeah")
    
    # Mostrar modo actual
    if db is None:
        st.warning("🔧 Modo Demo - Firebase no configurado")
    
    tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
    
    with tab1:
        with st.form("Login"):
            email = st.text_input("📧 Correo")
            password = st.text_input("🔒 Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
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
                        # Modo demo - simular login
                        st.session_state.user = {
                            'uid': 'demo-user-123',
                            'email': email,
                            'role': 'mentee'
                        }
                        st.success("✅ Modo demo - Sesión iniciada")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        with st.form("Registro"):
            email = st.text_input("📧 Correo (registro)")
            password = st.text_input("🔒 Nueva contraseña", type="password")
            role = st.selectbox("👤 Rol", ["Mentorado", "Mentor"])
            if st.form_submit_button("Crear cuenta"):
                try:
                    if auth and db:
                        user = auth.create_user(email=email, password=password)
                        db.collection('user_roles').document(user.uid).set({
                            'role': 'mentor' if role == "Mentor" else 'mentee'
                        })
                        st.success("¡Cuenta creada! Inicia sesión.")
                    else:
                        st.info("🔧 Modo demo - Registro simulado")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ========== BARRA LATERAL MEJORADA ==========
def sidebar():
    st.sidebar.title("🚀 Trading Yeah")
    
    if 'user' not in st.session_state:
        auth_ui()
        st.stop()
        
    st.sidebar.write(f"👤 {st.session_state.user['email']}")
    st.sidebar.write(f"🎖️ Rol: {st.session_state.user['role'].capitalize()}")
    
    if db is None:
        st.sidebar.warning("🔧 Modo Demo Activado")

    # SOLO FUNCIONALIDADES MVP
    opciones = [
        "Dashboard", 
        "Journaling Inteligente",
        "Apoyo Psicológico",
        "Planificador de Trading",
        "🚀 Próximamente"
    ]
    
    return st.sidebar.radio("Menú", opciones)

# ========== MAIN CORREGIDO ==========
def main():
    opcion = sidebar()
    
    if opcion == "Dashboard":
        mostrar_dashboard_personalizado()
    elif opcion == "Journaling Inteligente":
        mostrar_journaling_inteligente()
    elif opcion == "Apoyo Psicológico":
        mostrar_chatbot_trading()
    elif opcion == "Planificador de Trading":
        mostrar_estrategia_maestra()
    elif opcion == "🚀 Próximamente":
        mostrar_proximamente()

if __name__ == "__main__":
    main()