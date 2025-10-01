
# analisis_mercado.py - VERSIÓN CORREGIDA
import streamlit as st
from datetime import datetime
try:
    from firebase_config import db
except Exception:
    db = None

def _save_waitlist_entry(email: str, source: str = "proximamente", uid: str = None):
    """Guarda una entrada en la lista de espera"""
    entry = {
        "email": email,
        "source": source,
        "uid": uid,
        "created_at": datetime.utcnow().isoformat()
    }
    try:
        if db:
            db.collection("waitlist").add(entry)
            return True, "🎉 ¡Te has unido a la lista de espera exclusiva!"
        else:
            st.session_state.setdefault("local_waitlist", [])
            st.session_state["local_waitlist"].append(entry)
            return True, "🎉 ¡Lista de espera local - funcionalidad en desarrollo!"
    except Exception as e:
        return False, f"❌ Error: {e}"

def mostrar_proximamente():
    """Página 'Próximamente' - El futuro del trading está aquí"""
    
    # Hero Section
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #C9A34E; font-size: 3.5rem; margin-bottom: 1rem;'>🚀 EL FUTURO DEL TRADING</h1>
        <h2 style='color: #FFFFFF; font-size: 1.8rem; margin-bottom: 2rem;'>
            Donde los traders encuentran su edge y los mentores construyen su legado
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Introducción épica
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### 🌟 **La Revolución que la Industria Trading Necesita**
        
        Imagina un ecosistema donde **cada trader** tiene las herramientas para alcanzar su máximo potencial 
        y **cada mentor** puede impactar vidas mientras construye un negocio sostenible.
        
        **Eso es Trading Yeah.**
        """)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4A5A3D, #2E2E2E); padding: 2rem; border-radius: 15px; border: 1px solid #C9A34E; text-align: center;'>
            <h3 style='color: #C9A34E; margin: 0;'>🚀 COMING SOON</h3>
            <p style='color: #FFFFFF; margin: 0.5rem 0 0 0;'>Q4 2024</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Features Grid - Mejorado
    st.markdown("""
    ## 🎯 **Funcionalidades que Cambiarán el Juego**
    """)
    
    # Grid de características
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: #2E2E2E; padding: 1.5rem; border-radius: 12px; border: 1px solid #4A5A3D; height: 100%;'>
            <h4 style='color: #C9A34E;'>🧠 Asistente IA de Mercado</h4>
            <p style='color: #FFFFFF; font-size: 0.9rem;'>
            <strong>Tu segundo cerebro para análisis:</strong> Combina SMC, análisis técnico y TU plan personal 
            para darte segundas opiniones accionables, no señales genéricas.
            </p>
            <div style='background: #4A5A3D; color: white; padding: 0.5rem; border-radius: 6px; margin-top: 1rem; text-align: center;'>
            🤝 Respetamos tu estrategia
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #2E2E2E; padding: 1.5rem; border-radius: 12px; border: 1px solid #4A5A3D; height: 100%;'>
            <h4 style='color: #C9A34E;'>👥 Comunidades Skool-Style</h4>
            <p style='color: #FFFFFF; font-size: 0.9rem;'>
            <strong>Donde los mentores construyen imperios:</strong> Crea tu comunidad, monetiza tu conocimiento 
            y conecta con traders que realmente valoran tu expertise.
            </p>
            <div style='background: #4A5A3D; color: white; padding: 0.5rem; border-radius: 6px; margin-top: 1rem; text-align: center;'>
            💰 Monetización real
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: #2E2E2E; padding: 1.5rem; border-radius: 12px; border: 1px solid #4A5A3D; height: 100%;'>
            <h4 style='color: #C9A34E;'>🎓 Marketplace Educativo</h4>
            <p style='color: #FFFFFF; font-size: 0.9rem;'>
            <strong>El Netflix del trading educativo:</strong> Cursos estructurados, mentores verificados 
            y un sistema que premia la calidad sobre la cantidad.
            </p>
            <div style='background: #4A5A3D; color: white; padding: 0.5rem; border-radius: 6px; margin-top: 1rem; text-align: center;'>
            🏆 Calidad garantizada
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sección de Problema/Solución
    st.markdown("""
    ## 💡 **El Problema que Resolvemos**
    """)
    
    prob_col1, prob_col2 = st.columns(2)
    
    with prob_col1:
        st.markdown("""
        ### ❌ **El Status Quo**
        - **Traders solitarios** sin apoyo real
        - **Mentores sobresaturados** en redes sociales
        - **Contenido de baja calidad** que confunde más que ayuda
        - **Falta de estructura** en el aprendizaje
        - **Cero personalización** en las herramientas
        """)
    
    with prob_col2:
        st.markdown("""
        ### ✅ **Nuestra Solución**
        - **Comunidad activa** de apoyo mutuo
        - **Plataforma dedicada** para mentores serios
        - **Contenido verificado** y estructurado
        - **Roadmap de aprendizaje** personalizado
        - **Herramientas que se adaptan** a TU estilo
        """)
    
    st.markdown("---")
    
    # Sección Específica para Mentores - CORREGIDA
    st.markdown("""
    ## 👑 **Para Mentores: Construye Tu Legado**
    """)
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #4A5A3D, #2E2E2E); padding: 2rem; border-radius: 15px; border: 2px solid #C9A34E;'>
        <h3 style='color: #C9A34E; text-align: center;'>🏆 ¿Eres un Mentor con Experiencia Real?</h3>
        <p style='color: #FFFFFF; text-align: center; font-size: 1.1rem;'>
        <strong>Deja de competir en redes sociales y únete a una plataforma donde tu expertise es valorado.</strong>
        </p>
        
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem;'>
            <div style='text-align: center;'>
                <h4 style='color: #C9A34E;'>🎯</h4>
                <p style='color: #FFFFFF;'>Audiencia segmentada que busca aprender</p>
            </div>
            <div style='text-align: center;'>
                <h4 style='color: #C9A34E;'>💸</h4>
                <p style='color: #FFFFFF;'>Múltiples flujos de ingresos</p>
            </div>
            <div style='text-align: center;'>
                <h4 style='color: #C9A34E;'>📈</h4>
                <p style='color: #FFFFFF;'>Herramientas profesionales incluidas</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)  # ¡ESTA ERA LA LÍNEA QUE FALTABA!
    
    st.markdown("---")
    
    # Sección Mi Zen
    st.markdown("""
    ## 🧘 **Mi Zen: Tu Estrategia, Tu Legado**
    """)
    
    zen_col1, zen_col2 = st.columns([1, 1])
    
    with zen_col1:
        st.markdown("""
        ### 📊 **Compila tu Edge**
        - Historial de operaciones verificado
        - Reglas de trading documentadas
        - Métricas de performance reales
        - Psicología y gestión de riesgo
        """)
    
    with zen_col2:
        st.markdown("""
        ### 💰 **Monetiza tu Conocimiento**
        - Crea tu "Zen Pack" verificable
        - Comparte con alumnos selectos
        - Genera ingresos pasivos
        - Construye tu marca personal
        """)
    
    st.markdown("""
    <div style='background: #2E2E2E; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #C9A34E; margin: 1rem 0;'>
        <p style='color: #FFFFFF; margin: 0;'>
        <strong>💡 Innovación:</strong> Por primera vez, los traders pueden <strong>empaquetar y monetizar</strong> 
        su metodología completa de manera profesional y transparente.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # CTA Principal
    st.markdown("""
    ## 🎪 **Sé Parte de la Revolución**
    """)
    
    # Lista de espera
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E2E2E, #4A5A3D); padding: 2rem; border-radius: 15px; text-align: center; border: 1px solid #C9A34E;'>
        <h3 style='color: #C9A34E;'>🚀 Acceso Anticipado Exclusivo</h3>
        <p style='color: #FFFFFF;'>
        Únete a la lista de espera y sé de los primeros en acceder a estas funcionalidades revolucionarias.
        <strong>Posiciones limitadas para testers beta.</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de lista de espera
    user_email = None
    user_uid = None
    
    try:
        if 'user' in st.session_state and isinstance(st.session_state.user, dict):
            user_email = st.session_state.user.get('email')
            user_uid = st.session_state.user.get('uid')
    except Exception:
        user_email = None
    
    col1, col2 = st.columns([2, 1])
    with col1:
        email_input = st.text_input(
            "📧 Tu correo para acceso prioritario:",
            value=user_email or "",
            placeholder="tunombre@ejemplo.com"
        )
    with col2:
        if st.button("🎯 UNIRME A LA LISTA", use_container_width=True):
            if not email_input or "@" not in email_input:
                st.error("❌ Ingresa un correo válido para unirte a la lista exclusiva.")
            else:
                ok, msg = _save_waitlist_entry(email_input, source="proximamente_hype", uid=user_uid)
                if ok:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)
    
    # Formulario para mentores
    st.markdown("---")
    st.markdown("""
    ## 👑 **Formulario para Mentores (Aplicación Exclusiva)**
    """)
    
    st.markdown("""
    <div style='background: #2E2E2E; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;'>
        <p style='color: #FFFFFF; margin: 0;'>
        <strong>Para mentores serios:</strong> Estamos seleccionando un grupo exclusivo de mentores para nuestro lanzamiento. 
        Si tienes experiencia real y quieres construir tu legado en nuestra plataforma, aplica aquí.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("mentor_application"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Nombre / Alias profesional")
            expertise = st.selectbox(
                "🎯 Tu especialidad principal",
                ["Smart Money Concepts", "Price Action", "Swing Trading", "Day Trading", 
                 "Opciones", "Futuros", "Análisis Técnico", "Psicología del Trading"]
            )
        
        with col2:
            years_exp = st.selectbox(
                "📅 Años de experiencia trading",
                ["1-2 años", "3-5 años", "5+ años", "10+ años"]
            )
            contact_email = st.text_input(
                "📧 Correo de contacto",
                value=user_email or ""
            )
        
        teaching_style = st.text_area(
            "💡 Describe tu estilo de enseñanza",
            placeholder="¿Cómo ayudas a tus estudiantes? ¿Qué hace único tu approach?...",
            height=100
        )
        
        submitted = st.form_submit_button("🎓 ENVIAR SOLICITUD DE MENTOR")
        
        if submitted:
            if not contact_email:
                st.error("❌ Proporciona un email de contacto válido.")
            else:
                try:
                    doc = {
                        "name": name or "Sin nombre",
                        "expertise": expertise,
                        "years_exp": years_exp,
                        "email": contact_email,
                        "teaching_style": teaching_style,
                        "uid": user_uid,
                        "status": "pending",
                        "submitted_at": datetime.utcnow().isoformat()
                    }
                    
                    if db:
                        db.collection("mentor_applications").add(doc)
                        st.success("""
                        🎉 ¡Solicitud enviada con éxito!
                        
                        **Próximos pasos:**
                        1. Revisaremos tu aplicación en 48-72 horas
                        2. Te contactaremos para una breve entrevista
                        3. Acceso anticipado a la plataforma para mentores
                        """)
                    else:
                        st.session_state.setdefault("local_mentor_apps", [])
                        st.session_state["local_mentor_apps"].append(doc)
                        st.success("📝 Solicitud guardada (modo demo - base de datos no disponible)")
                        
                except Exception as e:
                    st.error(f"❌ Error al enviar solicitud: {e}")
    
    # Footer épico
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h3 style='color: #C9A34E;'>🚀 EL FUTURO DEL TRADING ESTÁ MÁS CERCA DE LO QUE CREES</h3>
        <p style='color: #FFFFFF;'>
        <strong>Trading Yeah</strong> - Donde los traders se convierten en leyendas y los mentores construyen imperios.
        </p>
       </div>
    """, unsafe_allow_html=True)

# Alias para compatibilidad
def mostrar_analisis_mercado():
    mostrar_proximamente()