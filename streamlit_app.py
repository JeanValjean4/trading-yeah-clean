# streamlit_app.py - VERSIÓN CORREGIDA: SINCRONÍA TOTAL DE CAPITAL
import streamlit as st
from datetime import datetime

try:
    from firebase_config import db, auth_instance as auth
except Exception as e:
    db = None
    auth = None
    print(f"Firebase import error: {e}")

try:
    from dashboard import mostrar_dashboard_personalizado
    from journaling import mostrar_journaling_inteligente, cargar_operaciones_firebase
    from chatbot import mostrar_chatbot_trading
    from estrategia_maestra import mostrar_estrategia_maestra
    from analisis_mercado import mostrar_proximamente
    from perfil_usuario import cargar_perfil_usuario, calcular_capital_actual, calcular_rentabilidad, calcular_progreso
    from perfil_ui import mostrar_perfil_usuario
    from translations import get_translation
except ImportError as e:
    st.error(f"Error importing modules: {e}")

# ========== CONFIGURACIÓN VISUAL ==========
COLOR_PRIMARY = "#4A5A3D"
COLOR_SECONDARY = "#C9A34E"
COLOR_BACKGROUND = "#1E1E1E"
COLOR_TEXT = "#FFFFFF"

st.markdown(f"""
<style>
    .stApp {{ background-color: {COLOR_BACKGROUND}; color: {COLOR_TEXT}; }}
    h1, h2, h3, h4, h5, h6 {{ color: {COLOR_SECONDARY}; }}
    .stMarkdown, .stText, .stSubheader, label, .stCaption, .stDataFrame {{ color: {COLOR_TEXT} !important; }}
    .stButton>button {{ background-color: {COLOR_PRIMARY}; color: {COLOR_TEXT}; border-radius: 8px; }}
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
        background-color: #2E2E2E !important; border: 1px solid #4A5A3D !important; border-radius: 8px !important;
    }}
    .stAlert p, .stInfo p, .stSuccess p, .stWarning p, .stError p {{ color: #FFFFFF !important; }}
    .stAlert svg, .stInfo svg, .stSuccess svg, .stWarning svg, .stError svg {{ fill: #C9A34E !important; }}
    .stMetric {{
        background-color: #2E2E2E !important; border: 1px solid #4A5A3D !important;
        border-radius: 8px !important; padding: 15px !important;
    }}
    .stMetric label {{ color: #C9A34E !important; font-weight: bold !important; }}
    .stMetric div {{ color: #FFFFFF !important; font-size: 18px !important; font-weight: normal !important; }}
    .stTextInput input, .stTextArea textarea {{
        background-color: #2E2E2E !important; color: #FFFFFF !important; border: 1px solid #4A5A3D !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px !important; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #2E2E2E !important; color: #C9A34E !important;
        border-radius: 8px 8px 0px 0px !important; padding: 10px 16px !important; border: 1px solid #4A5A3D !important;
    }}
    .stTabs [aria-selected="true"] {{ background-color: #4A5A3D !important; color: #FFFFFF !important; }}
    .streamlit-expanderHeader {{
        background-color: #2E2E2E !important; color: #C9A34E !important; border: 1px solid #4A5A3D !important;
        border-radius: 8px !important; padding: 10px !important; margin-bottom: 10px !important;
    }}
    .streamlit-expanderContent {{
        background-color: #2E2E2E !important; border: 1px solid #4A5A3D !important;
        border-radius: 0px 0px 8px 8px !important; padding: 15px !important;
    }}
    .stDataFrame {{ background-color: #2E2E2E !important; color: #FFFFFF !important; }}
    .progress-card {{
        background-color: #2E2E2E; border-radius: 10px; padding: 14px;
        margin: 10px 0; border-left: 4px solid #C9A34E;
    }}
    .level-badge {{
        background-color: #4A5A3D; color: white; padding: 4px 14px;
        border-radius: 20px; font-weight: bold; font-size: 13px; display: inline-block;
    }}
    .progress-track {{ background-color: #444; border-radius: 10px; height: 16px; overflow: hidden; margin-top: 8px; }}
    .progress-fill {{ background: linear-gradient(90deg, #4A5A3D, #C9A34E); height: 100%; transition: width 0.4s; }}
</style>
""", unsafe_allow_html=True)


# ========== TARJETA DE PROGRESO (barra lateral) ==========
def mostrar_tarjeta_progreso(user_id):
    """
    Calcula TODO en tiempo real desde la única fuente de verdad
    (perfil_usuario.py). No lee ningún número guardado de 'capital_actual'
    o 'nivel' — todo se recalcula aquí mismo cada vez.
    """
    operaciones = cargar_operaciones_firebase(user_id)
    capital_info = calcular_capital_actual(user_id, operaciones)
    rentabilidad = calcular_rentabilidad(user_id, operaciones)
    progreso = calcular_progreso(operaciones)

    color_rent = "#4CAF50" if rentabilidad >= 0 else "#FF6B6B"

    st.sidebar.markdown(f"""
    <div class="progress-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="level-badge">Nivel {progreso['nivel']}</span>
            <span style="color:#C9A34E; font-size:13px;">{progreso['rango']}</span>
        </div>
        <div style="margin-top:10px; font-size:20px; color:#FFFFFF; font-weight:600;">
            ${capital_info['capital_actual']:,.2f}
            <span style="color:{color_rent}; font-size:14px; margin-left:6px;">
                ({rentabilidad:+.1f}%)
            </span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{progreso['porcentaje_siguiente_nivel']}%;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; color:#AAAAAA; font-size:11px; margin-top:4px;">
            <span>{progreso['experiencia']} pts</span>
            <span>{progreso['porcentaje_siguiente_nivel']}% a Nivel {progreso['nivel']+1}</span>
        </div>
        <div style="display:flex; justify-content:space-around; margin-top:12px; color:#FFFFFF; font-size:12px;">
            <span>🔥 {progreso['mejor_racha']}</span>
            <span>💔 {progreso['peor_racha']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if rentabilidad > 10:
        st.sidebar.success("🚀 Superando tus objetivos.")
    elif rentabilidad > 5:
        st.sidebar.info("📈 Buen camino hacia tus metas.")
    elif rentabilidad < -5:
        st.sidebar.warning("⚠️ En drawdown — revisa tu gestión de riesgo.")
    else:
        st.sidebar.caption("💪 Construyendo consistencia.")


# ========== FEEDBACK ==========
def guardar_feedback(texto, correo, pagina, idioma):
    if texto.strip():
        try:
            if db:
                feedback_data = {
                    "texto": texto, "correo": correo, "pagina": pagina,
                    "idioma": idioma, "fecha": datetime.now().isoformat(),
                }
                db.collection("feedback").add(feedback_data)
                success_messages = {
                    "en": "✅ Thank you! Your feedback is gold 🏆",
                    "es": "✅ ¡Gracias! Tu opinión vale oro 🏆",
                    "ru": "✅ Спасибо! Ваш отзыв - это золото 🏆",
                }
                st.success(success_messages.get(idioma, success_messages["en"]))
            else:
                st.info("📝 Feedback guardado localmente (Firebase no conectado)")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("Por favor escribe algo antes de enviar")


def seccion_feedback():
    st.sidebar.markdown("---")
    with st.sidebar.expander("💬 Enviar Comentarios"):
        pagina_actual = st.session_state.get('opcion', 'Unknown')
        lang = st.session_state.get("language", "en")
        feedback_text = st.text_area("Tu opinión:", key="feedback_input")
        user_email = st.text_input(
            "Tu correo (opcional)",
            value=st.session_state.user.get('email', '') if 'user' in st.session_state else "",
            key="feedback_email"
        )
        if st.button("📤 Enviar"):
            guardar_feedback(feedback_text, user_email, pagina_actual, lang)


# ========== AUTH ==========
def get_user_role(uid):
    try:
        if db:
            doc = db.collection('user_roles').document(uid).get()
            return doc.to_dict().get('role', 'mentee') if doc.exists else 'mentee'
        return 'mentee'
    except Exception:
        return 'mentee'


def auth_ui():
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
                        st.session_state.user = {'uid': user.uid, 'email': email, 'role': get_user_role(user.uid)}
                        st.rerun()
                    else:
                        st.session_state.user = {'uid': f"demo-user-{hash(email)}", 'email': email, 'role': 'mentee'}
                        st.success(get_translation(lang, "demo_login_success"))
                        st.rerun()
                except Exception as e:
                    if "USER_NOT_FOUND" in str(e):
                        st.error("Usuario no encontrado. Por favor regístrate primero." if lang != "en"
                                  else "User not found. Please register first.")
                    else:
                        st.error(f"Error: {str(e)}")

    with tab2:
        with st.form("Registro"):
            email = st.text_input(get_translation(lang, "login_email"), key="reg_email")
            password = st.text_input(get_translation(lang, "login_password"), type="password", key="reg_pass")
            role_options = get_translation(lang, "roles")
            role = st.selectbox(get_translation(lang, "role_select"), role_options)
            if st.form_submit_button(get_translation(lang, "register_button")):
                try:
                    if auth and db:
                        user = auth.create_user(email=email, password=password)
                        db.collection('user_roles').document(user.uid).set(
                            {'role': 'mentor' if role == role_options[1] else 'mentee'}
                        )
                        # Inicializamos el perfil del nuevo usuario usando la fuente única
                        from perfil_usuario import cargar_perfil_usuario as _init_perfil
                        _init_perfil(user.uid)
                        st.success("¡Cuenta creada! Inicia sesión." if lang != "en" else "Account created! Please login.")
                    else:
                        st.info("🔧 Modo demo - Registro simulado")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


# ========== BARRA LATERAL ==========
def sidebar():
    if 'user' not in st.session_state:
        st.sidebar.markdown("### 🌐 Idioma")
        lang = st.sidebar.radio("Elegir idioma:", ["English", "Español", "Русский"],
                                  horizontal=True, label_visibility="collapsed")
        lang_map = {"English": "en", "Español": "es", "Русский": "ru"}
        st.session_state.language = lang_map[lang]

    st.sidebar.title("🚀 Trading Yeah")

    if 'user' not in st.session_state:
        auth_ui()
        st.stop()

    lang = st.session_state.get("language", "en")
    user_id = st.session_state.user['uid']

    st.sidebar.write(f"👤 {st.session_state.user['email']}")
    st.sidebar.write(f"🎖️ Rol: {st.session_state.user['role'].capitalize()}")

    if db is None:
        st.sidebar.warning("Modo demo (Firebase no conectado)")
    else:
        mostrar_tarjeta_progreso(user_id)

    # ===== MENÚ — "Mi Perfil" agregado como funcionalidad de primer nivel =====
    opciones_traducidas = list(get_translation(lang, "menu_items"))
    etiqueta_perfil = {"es": "⚙️ Mi Perfil", "en": "⚙️ My Profile", "ru": "⚙️ Мой профиль"}.get(lang, "⚙️ Mi Perfil")
    if etiqueta_perfil not in opciones_traducidas:
        opciones_traducidas.append(etiqueta_perfil)

    opcion_seleccionada = st.sidebar.radio(get_translation(lang, "sidebar_menu"), opciones_traducidas)
    st.session_state.opcion = opcion_seleccionada

    seccion_feedback()

    return opcion_seleccionada


# ========== MAIN ==========
def main():
    opcion = sidebar()
    lang = st.session_state.get("language", "en")

    mapa_opciones = {
        "Dashboard": "Dashboard",
        "Intelligent Journaling": "Journaling Inteligente",
        "Journaling Inteligente": "Journaling Inteligente",
        "Psychological Support": "Apoyo Psicológico",
        "Apoyo Psicológico": "Apoyo Psicológico",
        "Trading Planner": "Planificador de Trading",
        "Planificador de Trading": "Planificador de Trading",
        "🚀 Coming Soon": "🚀 Próximamente",
        "🚀 Próximamente": "🚀 Próximamente",
        "⚙️ Mi Perfil": "Mi Perfil",
        "⚙️ My Profile": "Mi Perfil",
        "⚙️ Мой профиль": "Mi Perfil",
    }

    opcion_base = mapa_opciones.get(opcion, opcion)

    if opcion_base == "Dashboard":
        mostrar_dashboard_personalizado()
    elif opcion_base == "Journaling Inteligente":
        mostrar_journaling_inteligente()
    elif opcion_base == "Apoyo Psicológico":
        mostrar_chatbot_trading()
    elif opcion_base == "Planificador de Trading":
        mostrar_estrategia_maestra()
    elif opcion_base == "Mi Perfil":
        mostrar_perfil_usuario()
    elif opcion_base == "🚀 Próximamente":
        mostrar_proximamente()


if __name__ == "__main__":
    main()
