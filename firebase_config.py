# firebase_config.py - VERSIÓN CORREGIDA Y COMPLETA
import streamlit as st

# Valores por defecto
db = None
auth_instance = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    
    if not firebase_admin._apps:
        # Verificar secrets mínimos
        required_secrets = ['FIREBASE_TYPE', 'FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY_ID', 
                          'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL', 'FIREBASE_CLIENT_ID',
                          'FIREBASE_AUTH_URI', 'FIREBASE_TOKEN_URI', 'FIREBASE_AUTH_PROVIDER_CERT_URL']
        
        if all(key in st.secrets for key in ['FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL']):
            
            # Crear credenciales COMPLETAS
            cred_dict = {
                "type": st.secrets.get("FIREBASE_TYPE", "service_account"),
                "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                "private_key_id": st.secrets.get("FIREBASE_PRIVATE_KEY_ID", "default_key_id"),
                "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
                "client_id": st.secrets.get("FIREBASE_CLIENT_ID", "default_client_id"),
                "auth_uri": st.secrets.get("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": st.secrets.get("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": st.secrets.get("FIREBASE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": st.secrets.get("FIREBASE_CLIENT_CERT_URL", "")
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
            db = firestore.client()
            auth_instance = auth
            st.success("✅ Firebase conectado correctamente")
        else:
            st.info("🔧 Modo demo - Configura las credenciales de Firebase en Secrets")
    
except ImportError:
    st.error("📦 Error: firebase-admin no instalado. Ejecuta: pip install firebase-admin")
except Exception as e:
    st.error(f"❌ Error Firebase: {str(e)}")
    # Modo demo como fallback
    db = None
    auth_instance = None