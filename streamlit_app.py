# streamlit_app.py - VERSIÓN PRODUCCIÓN COMPLETA
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import hashlib
import json

# ========== IMPORTACIONES CON MANEJO DE ERRORES ==========
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
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
        background-color: #2E2E2E !important;
        border: 1px solid #4A5A3D !important;
        border-radius: 8px !important;
    }}
    .stAlert p, .stInfo p, .stSuccess p, .stWarning p, .stError p {{
        color: #FFFFFF !important;
    }}
    .stAlert svg, .stInfo svg, .stSuccess svg, .stWarning svg, .stError svg {{
        fill: #C9A34E !important;
    }}
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
    .stTextInput input, .stTextArea textarea {{
        background-color: #2E2E2E !important;
        color: #FFFFFF !important;
        border: 1px solid #4A5A3D !important;
    }}
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
    .stDataFrame {{
        background-color: #2E2E2E !important;
        color: #FFFFFF !important;
    }}
    .progress-bar {{
        background-color: #2E2E2E;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        border-left: 4px solid #C9A34E;
    }}
    .level-badge {{
        background-color: #4A5A3D;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }}
</style>
""", unsafe_allow_html=True)

# ========== FUNCIONES DE PERFIL DE USUARIO ==========
def cargar_perfil_usuario(user_id):
    """Carga el perfil del usuario desde Firebase"""
    try:
        doc = db.collection('users').document(user_id).collection('perfil').document('trading_config').get()
        if doc.exists:
            return doc.to_dict()
        # Perfil por defecto
        return {
            'capital_inicial': 10000.0,
            'riesgo_por_operacion': 1.0,
            'max_operaciones_dia': 5,
            'estrategia_principal': 'Price Action',
            'objetivo_mensual': 5.0,
            'drawdown_maximo': 10.0,
            'capital_actual': 10000.0,
            'mejor_racha': 0,
            'peor_racha': 0,
            'nivel_progreso': 1,
            'experiencia_acumulada': 0
        }
    except:
        return {
            'capital_inicial': 10000.0,
            'riesgo_por_operacion': 1.0,
            'max_operaciones_dia': 5,
            'estrategia_principal': 'Price Action',
            'objetivo_mensual': 5.0,
            'drawdown_maximo': 10.0,
            'capital_actual': 10000.0,
            'mejor_racha': 0,
            'peor_racha': 0,
            'nivel_progreso': 1,
            'experiencia_acumulada': 0
        }

def guardar_perfil_usuario(user_id, perfil):
    """Guarda el perfil del usuario en Firebase"""
    try:
        perfil['ultima_actualizacion'] = datetime.now().isoformat()
        db.collection('users').document(user_id).collection('perfil').document('trading_config').set(perfil)
        return True
    except:
        return False

def actualizar_capital_desde_operaciones(user_id, operaciones):
    """Actualiza el capital actual basado en las operaciones registradas"""
    perfil = cargar_perfil_usuario(user_id)
    capital_base = perfil.get('capital_inicial', 10000.0)
    
    # Calcular P&L total de operaciones
    if operaciones:
        df = pd.DataFrame(operaciones)
        if 'pnl_real' in df.columns:
            pnl_total = df['pnl_real'].astype(float).sum()
            capital_actual = capital_base + pnl_total
            perfil['capital_actual'] = round(capital_actual, 2)
            
            # Actualizar rachas
            if 'resultado' in df.columns:
                resultados = df['resultado'].tolist()
                racha_actual = 0
                mejor_racha = 0
                peor_racha = 0
                for res in resultados:
                    if res == 'Ganadora':
                        racha_actual += 1
                        mejor_racha = max(mejor_racha, racha_actual)
                    else:
                        racha_actual = -1 if res == 'Perdedora' else 0
                        peor_racha = min(peor_racha, racha_actual)
                perfil['mejor_racha'] = mejor_racha
                perfil['peor_racha'] = abs(peor_racha)
            
            # Calcular nivel de progreso y experiencia
            total_ops = len(operaciones)
            win_rate = perfil.get('win_rate', 0)
            # Experiencia acumulada: cada operación +10, cada win +5, cada loss -2
            experiencia = total_ops * 10 + (df['resultado'] == 'Ganadora').sum() * 5 - (df['resultado'] == 'Perdedora').sum() * 2
            perfil['experiencia_acumulada'] = max(0, experiencia)
            
            # Nivel: cada 100 puntos de experiencia sube 1 nivel
            perfil['nivel_progreso'] = max(1, int(perfil['experiencia_acumulada'] / 100) + 1)
            
            guardar_perfil_usuario(user_id, perfil)
    
    return perfil

def cargar_operaciones_usuario(user_id):
    """Carga operaciones del usuario"""
    try:
        operaciones = []
        docs = db.collection('users').document(user_id).collection('operaciones').stream()
        for doc in docs:
            op = doc.to_dict()
            op['id'] = doc.id
            operaciones.append(op)
        return operaciones
    except:
        return []

# ========== FUNCIONES DE NOTAS PERSONALES ==========
def cargar_notas_usuario(user_id):
    """Carga notas del usuario"""
    try:
        doc = db.collection('users').document(user_id).collection('notas').document('notas_personales').get()
        if doc.exists:
            return doc.to_dict().get('notas', [])
        return []
    except:
        return []

def guardar_notas_usuario(user_id, notas):
    """Guarda notas del usuario"""
    try:
        db.collection('users').document(user_id).collection('notas').document('notas_personales').set({
            'notas': notas,
            'ultima_actualizacion': datetime.now().isoformat()
        })
        return True
    except:
        return False

# ========== FUNCIONES DE CHECKLIST PERSONALIZADA ==========
def cargar_checklist_usuario(user_id):
    """Carga checklist personalizada del usuario"""
    try:
        doc = db.collection('users').document(user_id).collection('checklist').document('checklist_personal').get()
        if doc.exists:
            return doc.to_dict().get('items', [])
        # Checklist por defecto (el usuario puede modificarla)
        return [
            {'id': '1', 'texto': '¿He verificado mi plan de trading?', 'completado': False},
            {'id': '2', 'texto': '¿El setup cumple con mis reglas de entrada?', 'completado': False},
            {'id': '3', 'texto': '¿He calculado el tamaño de posición según mi riesgo?', 'completado': False},
            {'id': '4', 'texto': '¿He establecido stop-loss y take-profit claros?', 'completado': False},
            {'id': '5', 'texto': '¿Estoy operando sin sesgos emocionales?', 'completado': False}
        ]
    except:
        return [
            {'id': '1', 'texto': '¿He verificado mi plan de trading?', 'completado': False},
            {'id': '2', 'texto': '¿El setup cumple con mis reglas de entrada?', 'completado': False},
            {'id': '3', 'texto': '¿He calculado el tamaño de posición según mi riesgo?', 'completado': False},
            {'id': '4', 'texto': '¿He establecido stop-loss y take-profit claros?', 'completado': False},
            {'id': '5', 'texto': '¿Estoy operando sin sesgos emocionales?', 'completado': False}
        ]

def guardar_checklist_usuario(user_id, items):
    """Guarda checklist personalizada del usuario"""
    try:
        db.collection('users').document(user_id).collection('checklist').document('checklist_personal').set({
            'items': items,
            'ultima_actualizacion': datetime.now().isoformat()
        })
        return True
    except:
        return False

# ========== SISTEMA DE PROGRESO Y RECOMPENSAS ==========
def mostrar_sistema_progreso(perfil):
    """Muestra el sistema de progreso del trader"""
    nivel = perfil.get('nivel_progreso', 1)
    experiencia = perfil.get('experiencia_acumulada', 0)
    capital_actual = perfil.get('capital_actual', 0)
    capital_inicial = perfil.get('capital_inicial', 10000)
    mejor_racha = perfil.get('mejor_racha', 0)
    peor_racha = perfil.get('peor_racha', 0)
    
    # Calcular progreso hacia siguiente nivel (100 puntos por nivel)
    experiencia_nivel = experiencia % 100
    porcentaje_nivel = min(100, (experiencia_nivel / 100) * 100)
    
    # Determinar rango según nivel
    if nivel <= 3:
        rango = "🥉 Aprendiz"
    elif nivel <= 6:
        rango = "🥈 Trader Consistente"
    elif nivel <= 10:
        rango = "🥇 Trader Experto"
    elif nivel <= 15:
        rango = "🏆 Trader Elite"
    else:
        rango = "👑 Leyenda del Trading"
    
    # Calcular rentabilidad
    if capital_inicial > 0:
        rentabilidad = ((capital_actual - capital_inicial) / capital_inicial) * 100
    else:
        rentabilidad = 0
    
    st.markdown(f"""
    <div class="progress-bar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="level-badge">Nivel {nivel}</span>
                <span style="margin-left: 10px; color: #C9A34E;">{rango}</span>
            </div>
            <div style="color: #FFFFFF;">
                💰 ${capital_actual:,.2f}
                <span style="color: {'#4CAF50' if rentabilidad >= 0 else '#FF6B6B'}; margin-left: 10px;">
                    ({rentabilidad:+.1f}%)
                </span>
            </div>
        </div>
        <div style="margin-top: 10px;">
            <div style="background-color: #444; border-radius: 10px; height: 20px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #4A5A3D, #C9A34E); width: {porcentaje_nivel}%; height: 100%; transition: width 0.5s;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; color: #AAAAAA; font-size: 12px; margin-top: 5px;">
                <span>Experiencia: {experiencia} pts</span>
                <span>{int(porcentaje_nivel)}% para Nivel {nivel+1}</span>
            </div>
        </div>
        <div style="display: flex; justify-content: space-around; margin-top: 15px; color: #FFFFFF;">
            <div>🔥 Mejor racha: {mejor_racha}</div>
            <div>💔 Peor racha: {peor_racha}</div>
            <div>📊 Rentabilidad: {rentabilidad:+.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mensaje motivacional según nivel
    if rentabilidad > 10:
        st.success("🚀 ¡Excelente! Estás superando tus objetivos.")
    elif rentabilidad > 5:
        st.info("📈 Buen trabajo. Sigue así y alcanzarás tus metas.")
    elif rentabilidad < -5:
        st.warning("⚠️ Estás en drawdown. Revisa tu gestión de riesgo.")
    else:
        st.info("💪 Construyendo consistencia. Cada operación te acerca al éxito.")

# ========== SECCIÓN DE NOTAS EN BARRA LATERAL ==========
def seccion_notas(user_id):
    """Sección de notas personales en la barra lateral"""
    with st.sidebar.expander("📝 Notas Personales", expanded=False):
        notas = cargar_notas_usuario(user_id)
        
        # Mostrar notas existentes
        if notas:
            for i, nota in enumerate(notas):
                st.markdown(f"• {nota}")
                if st.button("🗑️ Eliminar", key=f"del_nota_{i}"):
                    notas.pop(i)
                    guardar_notas_usuario(user_id, notas)
                    st.rerun()
        else:
            st.caption("No tienes notas guardadas")
        
        # Agregar nueva nota
        nueva_nota = st.text_area("Nueva nota:", placeholder="Escribe tu aprendizaje...", key="nueva_nota_input")
        if st.button("💾 Guardar Nota") and nueva_nota.strip():
            notas.append(nueva_nota.strip())
            guardar_notas_usuario(user_id, notas)
            st.success("✅ Nota guardada")
            st.rerun()

# ========== SECCIÓN DE CHECKLIST PERSONALIZADA ==========
def seccion_checklist(user_id):
    """Sección de checklist personalizada en la barra lateral"""
    with st.sidebar.expander("✅ Checklist Pre-Trade", expanded=False):
        items = cargar_checklist_usuario(user_id)
        
        # Mostrar y permitir tachar
        items_actualizados = []
        for item in items:
            completado = st.checkbox(
                item['texto'], 
                value=item.get('completado', False),
                key=f"check_{item['id']}"
            )
            items_actualizados.append({
                'id': item['id'],
                'texto': item['texto'],
                'completado': completado
            })
        
        # Guardar cambios automáticamente
        if items_actualizados != items:
            guardar_checklist_usuario(user_id, items_actualizados)
        
        # Opciones de edición (añadir/eliminar items)
        with st.expander("✏️ Editar Checklist"):
            # Agregar nuevo item
            nuevo_texto = st.text_input("Nuevo item:", key="nuevo_check_item")
            if st.button("➕ Añadir") and nuevo_texto.strip():
                nuevo_id = str(len(items_actualizados) + 1)
                items_actualizados.append({
                    'id': nuevo_id,
                    'texto': nuevo_texto.strip(),
                    'completado': False
                })
                guardar_checklist_usuario(user_id, items_actualizados)
                st.rerun()
            
            # Eliminar items (mostrar con checkboxes para seleccionar)
            st.write("Selecciona items para eliminar:")
            items_a_eliminar = []
            for item in items_actualizados:
                if st.checkbox(f"🗑️ {item['texto']}", key=f"del_check_{item['id']}"):
                    items_a_eliminar.append(item['id'])
            
            if st.button("🗑️ Eliminar Seleccionados") and items_a_eliminar:
                items_actualizados = [i for i in items_actualizados if i['id'] not in items_a_eliminar]
                guardar_checklist_usuario(user_id, items_actualizados)
                st.rerun()
        
        # Estadísticas de checklist
        total = len(items_actualizados)
        completados = sum(1 for i in items_actualizados if i.get('completado', False))
        if total > 0:
            st.caption(f"✅ {completados}/{total} completados ({int(completados/total*100)}%)")

# ========== SISTEMA DE FEEDBACK MEJORADO ==========
def guardar_feedback(texto, correo, pagina, idioma):
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
                db.collection("feedback").add(feedback_data)
                trigger_email_notification(feedback_data)
                success_messages = {
                    "en": "✅ Thank you! Your feedback is gold 🏆",
                    "es": "✅ ¡Gracias! Tu opinión vale oro 🏆", 
                    "ru": "✅ Спасибо! Ваш отзыв - это золото 🏆"
                }
                st.success(success_messages.get(idioma, success_messages["en"]))
                if 'feedback_input' in st.session_state:
                    st.session_state.feedback_input = ""
            else:
                demo_messages = {
                    "en": "📝 Feedback saved locally",
                    "es": "📝 Feedback guardado localmente",
                    "ru": "📝 Отзыв сохранен локально"
                }
                st.info(demo_messages.get(idioma, demo_messages["en"]))
        except Exception as e:
            st.error(f"❌ Error saving feedback: {str(e)}")
    else:
        warning_messages = {
            "en": "Please write something before sending",
            "es": "Por favor, escribe algo antes de enviar",
            "ru": "Пожалуйста, напишите что-нибудь перед отправкой"
        }
        st.warning(warning_messages.get(idioma, warning_messages["en"]))

def trigger_email_notification(feedback_data):
    print(f"📧 New feedback from {feedback_data['correo']} on {feedback_data['pagina']}")

def seccion_feedback():
    st.sidebar.markdown("---")
    with st.sidebar.expander("💬 Send Feedback / Enviar Comentarios / Отправить отзыв"):
        pagina_actual = st.session_state.get('opcion', 'Unknown')
        lang = st.session_state.get("language", "en")
        
        placeholder_text = {
            "en": "What do you like? What can be improved?",
            "es": "¿Qué te gusta? ¿Qué podemos mejorar?",
            "ru": "Что вам нравится? Что можно улучшить?"
        }
        email_text = {
            "en": "Your email (optional)",
            "es": "Tu correo (opcional)", 
            "ru": "Ваша почта (необязательно)"
        }
        
        feedback_text = st.text_area(
            "Your feedback / Tu opinión / Ваш отзыв:",
            placeholder=placeholder_text.get(lang, "What do you like? What can be improved?"),
            key="feedback_input"
        )
        user_email = st.text_input(
            email_text.get(lang, "Your email (optional)"),
            value=st.session_state.user.get('email', '') if 'user' in st.session_state else "",
            key="feedback_email"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 English", key="enviar_feedback_en"):
                guardar_feedback(feedback_text, user_email, pagina_actual, "en")
        with col2:
            if st.button("📤 Español", key="enviar_feedback_es"):
                guardar_feedback(feedback_text, user_email, pagina_actual, "es")
        with col3:
            if st.button("📤 Русский", key="enviar_feedback_ru"):
                guardar_feedback(feedback_text, user_email, pagina_actual, "ru")

# ========== AUTH MEJORADA ==========
def get_user_role(uid):
    try:
        if db:
            doc = db.collection('user_roles').document(uid).get()
            return doc.to_dict().get('role', 'mentee') if doc.exists else 'mentee'
        return 'mentee'
    except:
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

# ========== BARRA LATERAL COMPLETA ==========
def sidebar():
    if 'user' not in st.session_state:
        st.sidebar.markdown("### 🌐 Language / Idioma / Язык")
        lang = st.sidebar.radio("Choose language / Elegir idioma / Выберите язык:", 
                               ["English", "Español", "Русский"], 
                               horizontal=True,
                               label_visibility="collapsed")
        lang_map = {"English": "en", "Español": "es", "Русский": "ru"}
        st.session_state.language = lang_map[lang]
    
    st.sidebar.title("🚀 Trading Yeah")
    
    if 'user' not in st.session_state:
        auth_ui()
        st.stop()
    
    lang = st.session_state.get("language", "en")
    user_id = st.session_state.user['uid']
    
    st.sidebar.write(f"👤 {st.session_state.user['email']}")
    st.sidebar.write(f"🎖️ {get_translation(lang, 'sidebar_role')}: {st.session_state.user['role'].capitalize()}")
    
    if db is None:
        st.sidebar.warning(get_translation(lang, "sidebar_demo"))
    
    # ===== SECCIÓN DE PROGRESO =====
    if db is not None:
        operaciones = cargar_operaciones_usuario(user_id)
        perfil = actualizar_capital_desde_operaciones(user_id, operaciones)
        mostrar_sistema_progreso(perfil)
    
    # ===== MENÚ PRINCIPAL =====
    opciones = get_translation(lang, "menu_items")
    opcion_seleccionada = st.sidebar.radio(get_translation(lang, "sidebar_menu"), opciones)
    st.session_state.opcion = opcion_seleccionada
    
    # ===== SECCIÓN DE NOTAS =====
    if db is not None:
        seccion_notas(user_id)
    
    # ===== SECCIÓN DE CHECKLIST =====
    if db is not None:
        seccion_checklist(user_id)
    
    # ===== SECCIÓN DE FEEDBACK =====
    seccion_feedback()
    
    # ===== SECCIÓN DE ONBOARDING =====
    st.sidebar.markdown("---")
    if st.sidebar.button("🧪 Beta Testing Guide" if lang == "en" else "🧪 Guía Beta"):
        st.session_state.show_onboarding = True
    
    return opcion_seleccionada

# ========== ONBOARDING ==========
def mostrar_guia_onboarding():
    lang = st.session_state.get("language", "en")
    if lang == "en":
        st.title("🧪 Trading Yeah - Beta Testing Guide")
        st.success("🚀 **Welcome to Trading Yeah Beta!**\n\nThank you for helping us improve.")
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
            **Use the feedback section in the sidebar** to report bugs, confusing interfaces, missing features, or things you love!
            """)
        st.info("💡 **Pro tip**: Use the platform as you would normally trade.")
    else:
        st.title("🧪 Trading Yeah - Guía Beta")
        st.success("🚀 **¡Bienvenido a Trading Yeah Beta!**\n\nGracias por ayudarnos a mejorar.")
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
            **Usa la sección de feedback en la barra lateral** para reportar errores, interfaces confusas, funcionalidades faltantes o cosas que amas.
            """)
        st.info("💡 **Consejo profesional**: Usa la plataforma como lo harías normalmente al tradear.")

# ========== MAIN ==========
def main():
    try:
        from firebase_config import db
        if db:
            st.sidebar.success("✅ Firebase Conectado")
        else:
            st.sidebar.error("❌ Firebase No Conectado")
    except:
        st.sidebar.error("❌ Error Importando Firebase")
    
    if st.session_state.get('show_onboarding'):
        mostrar_guia_onboarding()
        lang = st.session_state.get("language", "en")
        if st.button("← Back to Platform" if lang == "en" else "← Volver a la Plataforma"):
            st.session_state.show_onboarding = False
            st.rerun()
        return
    
    opcion = sidebar()
    
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
