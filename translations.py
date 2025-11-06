# translations.py - Sistema de internacionalización
translations = {
    "en": {
        "login_title": "🔐 Trading Yeah",
        "login_email": "📧 Email",
        "login_password": "🔒 Password", 
        "login_button": "Login",
        "register_button": "Create Account",
        "role_select": "👤 Role",
        "roles": ["Mentee", "Mentor"],
        "demo_warning": "🔧 Demo Mode - Firebase not configured",
        "demo_login_success": "✅ Demo mode - Session started",
        "sidebar_title": "🚀 Trading Yeah",
        "sidebar_role": "Role",
        "sidebar_demo": "🔧 Demo Mode Activated",
        "menu_items": [
            "Dashboard", 
            "Intelligent Journaling",
            "Psychological Support", 
            "Trading Planner",
            "🚀 Coming Soon"
        ],
        "feedback_title": "💬 Send Feedback",
        "feedback_placeholder": "What do you like? What can be improved?",
        "feedback_email": "Your email (optional)",
        "feedback_button": "📤 Send Feedback",
        "feedback_success": "✅ Thank you! Your feedback is gold 🏆",
        "feedback_warning": "Please write something before sending"
    },
    "es": {
        "login_title": "🔐 Trading Yeah", 
        "login_email": "📧 Correo",
        "login_password": "🔒 Contraseña",
        "login_button": "Ingresar",
        "register_button": "Crear cuenta", 
        "role_select": "👤 Rol",
        "roles": ["Mentorado", "Mentor"],
        "demo_warning": "🔧 Modo Demo - Firebase no configurado",
        "demo_login_success": "✅ Modo demo - Sesión iniciada",
        "sidebar_title": "🚀 Trading Yeah",
        "sidebar_role": "Rol", 
        "sidebar_demo": "🔧 Modo Demo Activado",
        "menu_items": [
            "Dashboard",
            "Journaling Inteligente",
            "Apoyo Psicológico",
            "Planificador de Trading", 
            "🚀 Próximamente"
        ],
        "feedback_title": "💬 Enviar Comentarios",
        "feedback_placeholder": "¿Qué te gusta? ¿Qué podemos mejorar?",
        "feedback_email": "Tu correo (opcional)",
        "feedback_button": "📤 Enviar Comentario",
        "feedback_success": "✅ ¡Gracias! Tu opinión vale oro 🏆",
        "feedback_warning": "Por favor, escribe algo antes de enviar"
    }
}

def get_translation(lang, key):
    """Obtiene traducción segura"""
    return translations.get(lang, translations["en"]).get(key, key)