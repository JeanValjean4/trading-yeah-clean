# firebase_config.py - VERSIÓN CORREGIDA (ELIMINANDO DEMO MODE)
import streamlit as st
import os

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    
    # FORZAR RECONFIGURACIÓN COMPLETA
    if firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin.get_app())
    
    # VERIFICACIÓN ESTRICTA DE SECRETS
    required_secrets = ["FIREBASE_PROJECT_ID", "FIREBASE_PRIVATE_KEY", "FIREBASE_CLIENT_EMAIL"]
    missing_secrets = [secret for secret in required_secrets if secret not in st.secrets]
    
    if missing_secrets:
        st.error(f"🚨 CONFIGURACIÓN FIREBASE INCOMPLETA")
        st.error(f"Faltan los siguientes secrets: {', '.join(missing_secrets)}")
        st.info("""
        **Para configurar Firebase correctamente:**
        
        1. Ve a [Firebase Console](https://console.firebase.google.com)
        2. Tu proyecto → Configuración → Cuentas de servicio  
        3. Haz click en 'Generar nueva clave privada'
        4. En Streamlit Cloud Secrets, agrega EXACTAMENTE:
           - FIREBASE_PROJECT_ID
           - FIREBASE_PRIVATE_KEY (incluyendo '-----BEGIN PRIVATE KEY-----')
           - FIREBASE_CLIENT_EMAIL
        """)
        st.stop()
    
    # CONFIGURACIÓN CON VALIDACIÓN EXTRA
    cred_dict = {
        "type": "service_account",
        "project_id": st.secrets["FIREBASE_PROJECT_ID"],
        "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
        "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # VALIDAR FORMATO DE PRIVATE KEY
    private_key = cred_dict["private_key"]
    if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
        st.error("🚨 FORMATO DE PRIVATE KEY INCORRECTO")
        st.error("La FIREBASE_PRIVATE_KEY debe incluir los headers completos:")
        st.code("-----BEGIN PRIVATE KEY-----\nMII...\n-----END PRIVATE KEY-----")
        st.stop()
    
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    
    # VERIFICAR CONEXIÓN
    db = firestore.client()
    auth_instance = auth
    
    # TEST DE CONEXIÓN
    test_doc = db.collection("connection_test").document("test")
    test_doc.set({"timestamp": firestore.SERVER_TIMESTAMP}, merge=True)
    test_doc.delete()
    
    st.success("🔥 Firebase CONECTADO - MODO PRODUCCIÓN ACTIVO")
    st.balloons()

except Exception as e:
    st.error(f"🚨 ERROR CRÍTICO DE FIREBASE: {str(e)}")
    st.error("""
    **Posibles soluciones:**
    1. Verifica que el proyecto Firebase esté activo
    2. Asegúrate de que la clave privada sea la correcta
    3. Verifica que el client_email tenga permisos de administrador
    """)
    # FORZAR DETENCIÓN COMPLETA
    import sys
    sys.exit(1)