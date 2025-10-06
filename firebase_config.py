# firebase_config.py - VERSIÓN SEGURA Y REVISADA PARA PRODUCCIÓN

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth # AÑADIDO: Importamos firestore aquí

# Definir variables inicialmente como None o importadas globalmente
db = None
auth_app = None # Cambiamos el nombre de la variable local para evitar conflictos

# Inicializar Firebase solo una vez
if not firebase_admin._apps:
    try:
        # En producción, usar secrets de Streamlit
        if 'FIREBASE_PRIVATE_KEY' in st.secrets:
            firebase_creds = {
                "type": st.secrets["FIREBASE_TYPE"],
                "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
                "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
                "client_id": st.secrets["FIREBASE_CLIENT_ID"],
                "auth_uri": st.secrets["FIREBASE_AUTH_URI"],
                "token_uri": st.secrets["FIREBASE_TOKEN_URI"],
                "auth_provider_x509_cert_url": st.secrets["FIREBASE_AUTH_PROVIDER_CERT_URL"],
            }
            cred = credentials.Certificate(firebase_creds)
            firebase_app = firebase_admin.initialize_app(cred)
            
            # Obtener instancias SÓLO si la app se inicializa
            db = firestore.client(firebase_app)
            auth_app = auth.get_auth(firebase_app)
        else:
            # Para desarrollo local sin credenciales (solo UI)
            st.warning("⚠️ Firebase no configurado - Modo demo activado")
    except Exception as e:
        st.error(f"❌ Error configurando Firebase: {str(e)}")

# Exportar las instancias
# NOTA: Exportamos firestore para que streamlit_app.py pueda importarlo (si es necesario)
firestore = firestore
db = db
auth = auth_app
