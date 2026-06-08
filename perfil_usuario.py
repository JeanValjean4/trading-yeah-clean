# perfil_usuario.py - Configuración del perfil de trading
import streamlit as st
from datetime import datetime
from firebase_config import db

def cargar_perfil_usuario(user_id):
    """Carga el perfil del usuario desde Firebase"""
    try:
        doc = db.collection('users').document(user_id).collection('perfil').document('trading_config').get()
        if doc.exists:
            return doc.to_dict()
        return {
            'capital_inicial': 10000.0,
            'riesgo_por_operacion': 1.0,
            'max_operaciones_dia': 5,
            'estrategia_principal': 'Price Action',
            'objetivo_mensual': 5.0,
            'drawdown_maximo': 10.0
        }
    except:
        return {
            'capital_inicial': 10000.0,
            'riesgo_por_operacion': 1.0,
            'max_operaciones_dia': 5,
            'estrategia_principal': 'Price Action',
            'objetivo_mensual': 5.0,
            'drawdown_maximo': 10.0
        }

def guardar_perfil_usuario(user_id, perfil):
    """Guarda el perfil del usuario en Firebase"""
    try:
        perfil['ultima_actualizacion'] = datetime.now().isoformat()
        db.collection('users').document(user_id).collection('perfil').document('trading_config').set(perfil)
        return True
    except:
        return False

def mostrar_perfil_usuario():
    st.title("⚙️ Mi Perfil de Trading")
    
    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión")
        return
    
    user_id = st.session_state.user['uid']
    perfil = cargar_perfil_usuario(user_id)
    
    st.info("📊 Configura estos datos para obtener análisis más precisos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Gestión de Capital")
        capital = st.number_input("Capital inicial ($)", 
                                 value=float(perfil.get('capital_inicial', 10000)),
                                 step=1000.0, format="%.2f")
        riesgo = st.slider("Riesgo por operación (%)", 
                          min_value=0.5, max_value=5.0, 
                          value=float(perfil.get('riesgo_por_operacion', 1.0)),
                          step=0.5)
        drawdown_max = st.slider("Drawdown máximo permitido (%)",
                                min_value=5.0, max_value=30.0,
                                value=float(perfil.get('drawdown_maximo', 10.0)),
                                step=1.0)
    
    with col2:
        st.subheader("🎯 Estrategia y Objetivos")
        estrategia = st.selectbox("Estrategia principal",
                                 ["Price Action", "Soporte/Resistencia", "Breakout", 
                                  "Medias Móviles", "RSI/MACD", "Scalping", "Swing Trading"],
                                 index=["Price Action", "Soporte/Resistencia", "Breakout", 
                                        "Medias Móviles", "RSI/MACD", "Scalping", "Swing Trading"].index(
                                            perfil.get('estrategia_principal', 'Price Action')))
        max_ops = st.number_input("Máximo operaciones por día",
                                 min_value=1, max_value=20,
                                 value=int(perfil.get('max_operaciones_dia', 5)))
        objetivo = st.number_input("Objetivo mensual (%)",
                                  min_value=1.0, max_value=20.0,
                                  value=float(perfil.get('objetivo_mensual', 5.0)),
                                  step=0.5)
    
    if st.button("💾 Guardar Configuración", type="primary"):
        nuevo_perfil = {
            'capital_inicial': capital,
            'riesgo_por_operacion': riesgo,
            'drawdown_maximo': drawdown_max,
            'estrategia_principal': estrategia,
            'max_operaciones_dia': max_ops,
            'objetivo_mensual': objetivo
        }
        
        if guardar_perfil_usuario(user_id, nuevo_perfil):
            st.success("✅ Perfil actualizado correctamente")
            st.balloons()
        else:
            st.error("❌ Error al guardar")
    
    # Mostrar recomendaciones basadas en perfil
    st.divider()
    st.subheader("📊 Recomendaciones Personalizadas")
    
    st.info(f"""
    **Basado en tu configuración:**
    - 💰 Capital: ${capital:,.0f}
    - 🛡️ Riesgo por operación: ${capital * riesgo / 100:.0f} USD
    - ⚠️ Debes parar cuando pierdas: ${capital * drawdown_max / 100:.0f} USD
    - 🎯 Objetivo mensual: ${capital * objetivo / 100:.0f} USD
    """)
