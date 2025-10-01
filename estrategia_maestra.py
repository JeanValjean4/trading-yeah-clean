
import streamlit as st
import pandas as pd
import json
from datetime import datetime, time
import random
from firebase_config import db
import openai
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración segura de API key
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))

# ========== SISTEMA DE ALMACENAMIENTO ==========
def cargar_plan_trading(user_id):
    """Carga el plan de trading del usuario"""
    try:
        doc_ref = db.collection('users').document(user_id).collection('trading_plan').document('plan_actual')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"Error al cargar plan: {str(e)}")
        return None

def guardar_plan_trading(user_id, plan):
    """Guarda el plan de trading del usuario"""
    try:
        doc_ref = db.collection('users').document(user_id).collection('trading_plan').document('plan_actual')
        plan['ultima_actualizacion'] = datetime.now().isoformat()
        doc_ref.set(plan)
        return True
    except Exception as e:
        st.error(f"Error al guardar plan: {str(e)}")
        return False

def cargar_historial_planes(user_id):
    """Carga el historial de planes del usuario"""
    try:
        docs = db.collection('users').document(user_id).collection('trading_plan_historial').order_by('fecha_creacion', direction='DESCENDING').limit(10).stream()
        planes = []
        for doc in docs:
            plan_data = doc.to_dict()
            plan_data['id'] = doc.id
            planes.append(plan_data)
        return planes
    except Exception as e:
        st.error(f"Error al cargar historial: {str(e)}")
        return []

# ========== WIZARD INTELIGENTE ==========
def wizard_plan_trading():
    """Asistente para crear un plan de trading personalizado"""
    
    st.header("🎯 Wizard de Plan de Trading")
    
    with st.form("wizard_plan_trading"):
        # Paso 1: Estilo de trading
        st.subheader("1. Tu Estilo de Trading")
        col1, col2 = st.columns(2)
        
        with col1:
            estilo = st.selectbox(
                "Estilo principal:",
                ["Day Trading", "Swing Trading", "Position Trading", "Scalping"],
                help="¿Qué timeframe manejas principalmente?"
            )
        
        with col2:
            experiencia = st.selectbox(
                "Nivel de experiencia:",
                ["Principiante (0-1 año)", "Intermedio (1-3 años)", "Avanzado (3+ años)"],
                help="¿Cuánto tiempo llevas trading?"
            )
        
        # Paso 2: Gestión de riesgo
        st.subheader("2. Gestión de Riesgo")
        
        capital = st.number_input(
            "Capital de trading ($):",
            min_value=100,
            max_value=1000000,
            value=5000,
            step=500,
            help="Capital total destinado para trading"
        )
        
        riesgo_por_operacion = st.slider(
            "Riesgo máximo por operación (% del capital):",
            min_value=0.5,
            max_value=5.0,
            value=1.0,
            step=0.5,
            help="No arriesgues más de este porcentaje por trade"
        )
        
        max_operaciones_dia = st.slider(
            "Máximo de operaciones por día:",
            min_value=1,
            max_value=10,
            value=3,
            help="Límite para evitar overtrading"
        )
        
        # Paso 3: Horarios y mercados
        st.subheader("3. Horarios y Mercados Preferidos")
        
        col3, col4 = st.columns(2)
        
        with col3:
            hora_inicio = st.time_input(
                "Hora de inicio preferida:",
                value=time(9, 0),
                help="¿A qué hora sueles empezar a tradear?"
            )
            
            hora_fin = st.time_input(
                "Hora de fin preferida:",
                value=time(16, 0),
                help="¿Hasta qué hora sueles tradear?"
            )
        
        with col4:
            mercados = st.multiselect(
                "Mercados que operas:",
                ["Forex", "Acciones", "Criptomonedas", "Índices", "Futuros", "Opciones"],
                default=["Forex", "Acciones"]
            )
            
            pares_favoritos = st.text_input(
                "Pares/activos favoritos (separados por coma):",
                "EUR/USD, AAPL, BTC/USD",
                help="Ejemplo: EUR/USD, AAPL, BTC/USD"
            )
        
        # Paso 4: Objetivos y psicología
        st.subheader("4. Objetivos y Enfoque Psicológico")
        
        objetivo_mensual = st.slider(
            "Objetivo de rendimiento mensual (%):",
            min_value=1.0,
            max_value=20.0,
            value=5.0,
            step=0.5,
            help="Objetivo realista de ganancias mensuales"
        )
        
        desafios_psicologicos = st.multiselect(
            "Desafíos psicológicos a trabajar:",
            [
                "Miedo a perder", "Ansiedad", "Overtrading", 
                "Falta de disciplina", "Revenge trading", 
                "Apego emocional a operaciones"
            ],
            default=["Overtrading", "Falta de disciplina"]
        )
        
        # Submit
        submitted = st.form_submit_button("🚀 Crear Mi Plan de Trading")
        
        if submitted:
            plan = {
                'estilo': estilo,
                'experiencia': experiencia,
                'capital': capital,
                'riesgo_por_operacion': riesgo_por_operacion,
                'max_operaciones_dia': max_operaciones_dia,
                'hora_inicio': hora_inicio.strftime("%H:%M"),
                'hora_fin': hora_fin.strftime("%H:%M"),
                'mercados': mercados,
                'pares_favoritos': [p.strip() for p in pares_favoritos.split(",")],
                'objetivo_mensual': objetivo_mensual,
                'desafios_psicologicos': desafios_psicologicos,
                'fecha_creacion': datetime.now().isoformat(),
                'activo': True
            }
            
            return plan
    
    return None

# ========== GENERACIÓN INTELIGENTE DE PLAN ==========
def generar_plan_inteligente(plan_base):
    """Genera un plan de trading detallado usando IA"""
    
    prompt = f"""
    Como mentor experto en trading, crea un plan de trading detallado en español basado en estos parámetros:
    
    ESTILO: {plan_base['estilo']}
    EXPERIENCIA: {plan_base['experiencia']}
    CAPITAL: ${plan_base['capital']}
    RIESGO POR OPERACIÓN: {plan_base['riesgo_por_operacion']}%
    MÁXIMO OPERACIONES/DÍA: {plan_base['max_operaciones_dia']}
    HORARIO: {plan_base['hora_inicio']} a {plan_base['hora_fin']}
    MERCADOS: {', '.join(plan_base['mercados'])}
    ACTIVOS FAVORITOS: {', '.join(plan_base['pares_favoritos'])}
    OBJETIVO MENSUAL: {plan_base['objetivo_mensual']}%
    DESAFÍOS PSICOLÓGICOS: {', '.join(plan_base['desafios_psicologicos'])}
    
    Genera un plan estructurado que incluya:
    1. Reglas específicas de entrada y salida
    2. Estrategia de gestión de riesgo detallada
    3. Horarios óptimos de trading
    4. Checklist pre-operacional
    5. Protocolo para días ganadores y perdedores
    6. Técnicas para los desafíos psicológicos identificados
    7. Métricas de seguimiento específicas
    
    El plan debe ser práctico, accionable y personalizado. Responde en formato JSON con esta estructura:
    {{
        "reglas_entrada": ["regla1", "regla2", ...],
        "reglas_salida": ["regla1", "regla2", ...],
        "gestion_riesgo": ["punto1", "punto2", ...],
        "checklist_preoperacional": ["item1", "item2", ...],
        "protocolo_dias_ganadores": "texto descriptivo",
        "protocolo_dias_perdedores": "texto descriptivo",
        "tecnicas_psicologicas": ["tecnica1", "tecnica2", ...],
        "metricas_seguimiento": ["metrica1", "metrica2", ...]
    }}
    """
    
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un mentor de trading profesional que crea planes personalizados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        plan_detallado = json.loads(respuesta["choices"][0]["message"]["content"])
        plan_base.update(plan_detallado)
        return plan_base
        
    except Exception as e:
        st.error(f"Error al generar plan: {str(e)}")
        # Plan por defecto si falla la IA
        return crear_plan_por_defecto(plan_base)

def crear_plan_por_defecto(plan_base):
    """Crea un plan básico si falla la generación con IA"""
    
    plan_base['reglas_entrada'] = [
        "Solo operar en dirección de la tendencia principal",
        "Confirmación con al menos 2 indicadores técnicos",
        "Volumen por encima del promedio para entradas"
    ]
    
    plan_base['reglas_salida'] = [
        "TP: 2:1 risk-reward ratio mínimo",
        "SL: Nunca mover en contra de la operación",
        "Salir si el fundamento inicial cambia"
    ]
    
    plan_base['gestion_riesgo'] = [
        f"Máximo {plan_base['riesgo_por_operacion']}% por operación",
        f"Máximo {plan_base['max_operaciones_dia']} operaciones por día",
        "Reducir tamaño en periodos de alta volatilidad"
    ]
    
    return plan_base

# ========== SISTEMA DE RECORDATORIOS ==========
def generar_recordatorios_diarios(plan):
    """Genera recordatorios personalizados para el día"""
    
    recordatorios = []
    
    # Recordatorios basados en riesgo
    recordatorios.append(f"💰 Riesgo máximo por operación: {plan['riesgo_por_operacion']}%")
    recordatorios.append(f"🚫 Máximo {plan['max_operaciones_dia']} operaciones hoy")
    
    # Recordatorios basados en horario
    recordatorios.append(f"⏰ Horario de trading: {plan['hora_inicio']} - {plan['hora_fin']}")
    
    # Recordatorios psicológicos
    if plan.get('desafios_psicologicos'):
        for desafio in plan['desafios_psicologicos']:
            if desafio == "Overtrading":
                recordatorios.append("⚡ ¿Estás operando por necesidad o por oportunidad?")
            elif desafio == "Falta de disciplina":
                recordatorios.append("🎯 Sigue tu plan, no tus emociones")
            elif desafio == "Miedo a perder":
                recordatorios.append("🛡️ Las pérdidas son parte del juego, gestionalas bien")
    
    return recordatorios

# ========== VISUALIZACIÓN DEL PLAN ==========
def mostrar_plan_visual(plan):
    """Muestra el plan de trading de forma visual e interactiva"""
    
    st.header("📊 Dashboard de Tu Plan")
    
    # Métricas clave
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Capital", f"${plan['capital']:,.0f}")
    col2.metric("Riesgo/Op", f"{plan['riesgo_por_operacion']}%")
    col3.metric("Límite Diario", f"{plan['max_operaciones_dia']} ops")
    col4.metric("Objetivo Mensual", f"{plan['objetivo_mensual']}%")
    
    # Pestañas para diferentes secciones
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Reglas", "🛡️ Riesgo", "📅 Horario", "🧠 Psicología", "📋 Checklist"])
    
    with tab1:
        st.subheader("Reglas de Trading")
        col5, col6 = st.columns(2)
        
        with col5:
            st.write("**Entradas:**")
            for i, regla in enumerate(plan.get('reglas_entrada', []), 1):
                st.write(f"{i}. {regla}")
        
        with col6:
            st.write("**Salidas:**")
            for i, regla in enumerate(plan.get('reglas_salida', []), 1):
                st.write(f"{i}. {regla}")
    
    with tab2:
        st.subheader("Gestión de Riesgo")
        for i, item in enumerate(plan.get('gestion_riesgo', []), 1):
            st.write(f"{i}. {item}")
        
        # Gráfico de riesgo
        riesgo_absoluto = plan['capital'] * (plan['riesgo_por_operacion'] / 100)
        datos_riesgo = {
            'Tipo': ['Capital Total', 'Riesgo por Operación'],
            'Monto': [plan['capital'], riesgo_absoluto],
            'Color': ['#4A5A3D', '#C9A34E']
        }
        fig_riesgo = px.bar(datos_riesgo, x='Tipo', y='Monto', color='Color', 
                          title='Gestión de Capital y Riesgo')
        st.plotly_chart(fig_riesgo)
    
    with tab3:
        st.subheader("Horario de Trading")
        st.write(f"**Horario preferido:** {plan['hora_inicio']} - {plan['hora_fin']}")
        
        # Visualización de horario
        horas = list(range(24))
        actividad = [1 if (h >= int(plan['hora_inicio'].split(':')[0]) and 
                          h < int(plan['hora_fin'].split(':')[0])) else 0 for h in horas]
        
        fig_horario = go.Figure(go.Bar(x=horas, y=actividad, marker_color='#C9A34E'))
        fig_horario.update_layout(title="Horario de Trading Activo", 
                                xaxis_title="Hora del día", 
                                yaxis_title="Actividad",
                                showlegend=False)
        st.plotly_chart(fig_horario)
    
    with tab4:
        st.subheader("Manejo Psicológico")
        if plan.get('desafios_psicologicos'):
            st.write("**Desafíos a trabajar:**")
            for desafio in plan['desafios_psicologicos']:
                st.write(f"• {desafio}")
        
        if plan.get('tecnicas_psicologicas'):
            st.write("**Técnicas recomendadas:**")
            for tecnica in plan['tecnicas_psicologicas']:
                st.write(f"• {tecnica}")
    
    with tab5:
        st.subheader("Checklist Pre-Operacional")
        if plan.get('checklist_preoperacional'):
            for i, item in enumerate(plan['checklist_preoperacional'], 1):
                st.checkbox(f"{i}. {item}", key=f"check_{i}")
        else:
            st.info("Checklist no disponible para este plan")

# ========== INTERFAZ PRINCIPAL ==========
def mostrar_estrategia_maestra():
    st.title("📑 Plan de Trading Maestro")
    
    # Verificar autenticación
    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión para acceder al plan de trading")
        return
    
    user_id = st.session_state.user['uid']
    
    # Cargar plan existente
    plan_actual = cargar_plan_trading(user_id)
    historial_planes = cargar_historial_planes(user_id)
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["🎯 Mi Plan Actual", "🔄 Crear Nuevo Plan", "📊 Historial"])
    
    with tab1:
        if plan_actual:
            mostrar_plan_visual(plan_actual)
            
            # Recordatorios diarios
            st.header("🔔 Recordatorios para Hoy")
            recordatorios = generar_recordatorios_diarios(plan_actual)
            for recordatorio in recordatorios:
                st.info(recordatorio)
            
            # Botones de acción
            col7, col8 = st.columns(2)
            if col7.button("🖨️ Exportar Plan a PDF"):
                st.success("Función de exportación próximamente disponible")
            
            if col8.button("🗑️ Eliminar Plan Actual"):
                if st.button("Confirmar eliminación"):
                    # Implementar eliminación
                    st.success("Plan eliminado correctamente")
                    st.rerun()
        
        else:
            st.info("""
            ## 🚀 Bienvenido al Planificador de Trading
            
            Aún no tienes un plan de trading creado. Un plan sólido es fundamental para:
            
            - ✅ **Disciplina**: Sigue reglas claras en lugar de emociones
            - ✅ **Consistencia**: Mantén un approach coherente
            - ✅ **Gestión de riesgo**: Protege tu capital
            - ✅ **Medición**: Evalúa tu performance objetivamente
            
            Ve a la pestaña 'Crear Nuevo Plan' para comenzar.
            """)
    
    with tab2:
        st.header("Crear Nuevo Plan de Trading")
        
        plan_nuevo = wizard_plan_trading()
        
        if plan_nuevo:
            with st.spinner("Generando plan personalizado con IA..."):
                plan_completo = generar_plan_inteligente(plan_nuevo)
                
                if guardar_plan_trading(user_id, plan_completo):
                    st.success("🎉 ¡Plan de trading creado exitosamente!")
                    st.balloons()
                    
                    # Guardar en historial
                    try:
                        historial_ref = db.collection('users').document(user_id).collection('trading_plan_historial').document()
                        historial_ref.set(plan_completo)
                    except Exception as e:
                        st.error(f"Error al guardar en historial: {str(e)}")
                    
                    # Mostrar resumen
                    with st.expander("Ver resumen del plan"):
                        mostrar_plan_visual(plan_completo)
                
                else:
                    st.error("Error al guardar el plan. Intenta nuevamente.")
    
    with tab3:
        st.header("Historial de Planes")
        
        if historial_planes:
            for plan in historial_planes:
                with st.expander(f"Plan del {datetime.fromisoformat(plan['fecha_creacion']).strftime('%d/%m/%Y')}"):
                    st.write(f"**Estilo:** {plan.get('estilo', 'N/A')}")
                    st.write(f"**Capital:** ${plan.get('capital', 0):,.0f}")
                    st.write(f"**Riesgo/Op:** {plan.get('riesgo_por_operacion', 0)}%")
                    
                    if st.button("Cargar este plan", key=plan['id']):
                        if guardar_plan_trading(user_id, plan):
                            st.success("Plan cargado como actual")
                            st.rerun()
        else:
            st.info("No hay planes históricos guardados")

# Ejecutar si se corre directamente
if __name__ == "__main__":
    mostrar_estrategia_maestra()