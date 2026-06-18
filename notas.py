# notas.py - Módulo de notas de aprendizaje
import streamlit as st
from datetime import datetime
from firebase_config import db

def cargar_notas(user_id):
    try:
        docs = db.collection('users').document(user_id).collection('notas').order_by('fecha', direction='DESCENDING').stream()
        notas = []
        for doc in docs:
            nota = doc.to_dict()
            nota['id'] = doc.id
            notas.append(nota)
        return notas
    except:
        return []

def guardar_nota(user_id, titulo, contenido):
    try:
        db.collection('users').document(user_id).collection('notas').add({
            'titulo': titulo,
            'contenido': contenido,
            'fecha': datetime.now().isoformat()
        })
        return True
    except:
        return False

def eliminar_nota(user_id, nota_id):
    try:
        db.collection('users').document(user_id).collection('notas').document(nota_id).delete()
        return True
    except:
        return False

def mostrar_notas():
    st.title("📝 Mis Notas de Trading")
    
    if 'user' not in st.session_state:
        st.warning("🔒 Inicia sesión")
        return
    
    user_id = st.session_state.user['uid']
    
    tab1, tab2 = st.tabs(["➕ Nueva Nota", "📚 Mis Notas"])
    
    with tab1:
        titulo = st.text_input("Título de la nota")
        contenido = st.text_area("Contenido (aprendizajes, ideas, reflexiones)", height=200)
        if st.button("Guardar Nota"):
            if titulo and contenido:
                if guardar_nota(user_id, titulo, contenido):
                    st.success("Nota guardada")
                    st.rerun()
            else:
                st.warning("Completa título y contenido")
    
    with tab2:
        notas = cargar_notas(user_id)
        if not notas:
            st.info("Aún no tienes notas. ¡Guarda tus aprendizajes!")
        else:
            for nota in notas:
                with st.expander(f"{nota.get('titulo', 'Sin título')} - {nota.get('fecha', '')[:10]}"):
                    st.write(nota.get('contenido', ''))
                    if st.button("🗑️ Eliminar", key=f"del_{nota['id']}"):
                        if eliminar_nota(user_id, nota['id']):
                            st.rerun()
