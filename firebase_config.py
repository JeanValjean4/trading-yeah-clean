# firebase_config.py - VERSIÓN DEFINITIVA
import streamlit as st

# Valores por defecto
db = None
auth_instance = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    
    if not firebase_admin._apps:
        # Verificar secrets mínimos
        if all(key in st.secrets for key in ['FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL']):
            
            cred_dict = {
                "type": "service_account",
                "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
            db = firestore.client()
            auth_instance = auth
            st.success("✅ Firebase conectado")
        else:
            st.info("🔧 Modo demo - Firebase disponible al configurar secrets")
    
except ImportError:
    st.error("📦 Ejecuta: pip install firebase-admin")
except Exception as e:
    st.error(f"❌ Error Firebase: {str(e)}")