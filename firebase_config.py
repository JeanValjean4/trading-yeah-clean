# firebase_config.py - VERSIÓN PRODUCCIÓN (SIN DEMO MODE)
import streamlit as st
import os

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    
    if not firebase_admin._apps:
        # FORZAR inicialización incluso con configuración mínima
        if 'FIREBASE_PRIVATE_KEY' in st.secrets:
            cred_dict = {
                "type": "service_account",
                "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            st.success("🔥 Firebase CONECTADO - MODO PRODUCCIÓN")
        
        else:
            # SI FALTA CONFIGURACIÓN: ERROR CLARO, NO DEMO MODE
            st.error("🚨 CONFIGURACIÓN FIREBASE REQUERIDA")
            st.info("""
            **Para lanzar al público necesitas:**
            1. Ve a Firebase Console → Configuración → Cuentas de servicio
            2. Genera nueva clave privada (JSON)
            3. En Streamlit Cloud Secrets, agrega:
               - FIREBASE_PROJECT_ID
               - FIREBASE_PRIVATE_KEY  
               - FIREBASE_CLIENT_EMAIL
            """)
    
    # Instancias globales
    db = firestore.client()
    auth_instance = auth

except Exception as e:
    st.error(f"🚨 ERROR CRÍTICO: {str(e)}")
    st.stop()  # ⛔ DETENER LA APP SI FIREBASE FALLA