# checklist.py - Checklist personalizada para traders
import streamlit as st
from datetime import datetime
from firebase_config import db

def cargar_checklist(user_id):
    try:
        doc = db.collection('users').document(user_id).collection('checklist').document('items').get()
        if doc.exists:
            return doc.to_dict().get('items', [])
        # Items por defecto
        return [
            {"texto": "¿He confirmado la dirección de la tendencia?", "marcado": False},
            {"texto": "¿Mi stop loss está en un nivel lógico?", "marcado": False},
            {"texto": "¿El riesgo/recompensa es al menos 1:2?", "marcado": False},
            {"texto": "¿Estoy operando según mi plan, no por impulso?", "marcado": False},
            {"texto": "¿He esperado la confirmación de mi entrada?", "marcado": False}
        ]
    except:
        return []

def guardar_checklist(user_id, items):
    try:
        db.collection('users').document(user_id).collection('checklist').document('items').set({
            'items': items,
            'ultima_actualizacion': datetime.now().isoformat()
        })
        return True
    except:
        return False

def mostrar_checklist():
    st.title("📋 Checklist Antes de Operar")
    
    if 'user' not in st.session_state:
        st.warning("🔒 Inicia sesión para usar tu checklist")
        return
    
    user_id = st.session_state.user['uid']
    items = cargar_checklist(user_id)
    
    st.info("Marca cada punto antes de entrar a una operación. Esto te ayudará a evitar decisiones impulsivas.")
    
    # Mostrar items con checkbox
    nuevos_items = []
    for idx, item in enumerate(items):
        marcado = st.checkbox(item['texto'], value=item.get('marcado', False), key=f"check_{idx}")
        nuevos_items.append({"texto": item['texto'], "marcado": marcado})
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar progreso"):
            if guardar_checklist(user_id, nuevos_items):
                st.success("✅ Checklist guardada")
            else:
                st.error("Error al guardar")
    with col2:
        if st.button("➕ Añadir nuevo ítem"):
            # Usar session_state para agregar
            st.session_state.nuevo_item = ""
    
    # Input para nuevo item
    if 'nuevo_item' in st.session_state:
        nuevo_texto = st.text_input("Escribe tu nuevo ítem:", key="input_nuevo")
        if st.button("Agregar ítem"):
            if nuevo_texto:
                items.append({"texto": nuevo_texto, "marcado": False})
                guardar_checklist(user_id, items)
                st.rerun()
    
    # Estadísticas de cumplimiento
    total = len(items)
    marcados = sum(1 for i in items if i.get('marcado', False))
    if total > 0:
        st.progress(marcados/total, text=f"Cumplimiento: {marcados}/{total}")
        if marcados == total:
            st.success("🎉 ¡Todos los puntos verificados! Puedes operar con confianza.")
        elif marcados >= total*0.7:
            st.info("✅ Buen progreso, revisa los puntos faltantes.")
        else:
            st.warning("⚠️ Te faltan varios puntos. Reflexiona antes de operar.")
