# firebase_config.py - VERSIÓN CORREGIDA PARA PRODUCCIÓN
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Inicializar Firebase de forma segura
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Verificar si tenemos las secrets necesarias
            required_secrets = ['FIREBASE_PRIVATE_KEY', 'FIREBASE_PROJECT_ID', 'FIREBASE_CLIENT_EMAIL']
            
            if all(secret in st.secrets for secret in required_secrets):
                firebase_creds = {
                    "type": st.secrets.get("FIREBASE_TYPE", "service_account"),
                    "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                    "private_key_id": st.secrets.get("FIREBASE_PRIVATE_KEY_ID", ""),
                    "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                    "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
                    "client_id": st.secrets.get("FIREBASE_CLIENT_ID", ""),
                    "auth_uri": st.secrets.get("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                    "token_uri": st.secrets.get("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                    "auth_provider_x509_cert_url": st.secrets.get("FIREBASE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                }
                
                cred = credentials.Certificate(firebase_creds)
                firebase_admin.initialize_app(cred)
                return True
            else:
                st.warning("⚠️ Firebase no configurado - Modo demo activado")
                return False
                
        except Exception as e:
            st.error(f"❌ Error configurando Firebase: {str(e)}")
            return False
    return True

# Inicializar Firebase al importar el módulo
firebase_initialized = initialize_firebase()

# Exportar instancias de Firebase (solo si se inicializó correctamente)
if firebase_initialized:
    try:
        db = firestore.client()
        auth_instance = auth
    except Exception as e:
        st.error(f"❌ Error obteniendo instancias de Firebase: {str(e)}")
        db = None
        auth_instance = None
else:
    db = None
    auth_instance = None
