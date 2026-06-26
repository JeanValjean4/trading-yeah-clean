# estrategia_maestra.py - WIZARD DE PLAN DE TRADING, CORREGIDO
#
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
# 1. CAPITAL DESACOPLADO: el wizard ya NO pide "capital de trading" como
#    campo propio del plan. El capital SIEMPRE se lee desde perfil_usuario.py
#    (la única fuente de verdad). Antes, el plan guardaba su propio número
#    de capital en el momento de creación, y ese número se quedaba congelado
#    para siempre aunque tu capital real cambiara con cada trade — por eso
#    veías $100 aquí mientras tu capital real era otro número.
#
# 2. SINTAXIS OPENAI CORREGIDA: la versión anterior usaba
#    openai.ChatCompletion.create(...) y respuesta["choices"], que es
#    sintaxis de la librería openai v0.x. Si tienes instalada la v1.x
#    (como en tu journaling.py, que ya usa client.chat.completions.create),
#    esto fallaba silenciosamente y siempre caías al plan por defecto.
#    Ahora usa el mismo cliente que journaling.py.
#
# 3. TODO LO DEMÁS SE PRESERVA: wizard completo, generación con IA,
#    plan por defecto de respaldo, recordatorios diarios, historial
#    de planes, y la estructura de tabs.

import streamlit as st
import pandas as pd
import json
from datetime import datetime, time
from firebase_config import db
import os
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from dotenv import load_dotenv

from perfil_usuario import cargar_perfil_usuario, calcular_capital_actual
from journaling import cargar_operaciones_firebase

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


# ========== ALMACENAMIENTO ==========
def cargar_plan_trading(user_id):
    """Carga el plan de trading del usuario (sin capital — eso viene de perfil_usuario)."""
    try:
        doc_ref = db.collection('users').document(user_id).collection('trading_plan').document('plan_actual')
        doc = doc_ref.get()
        if doc.exists:
            plan = doc.to_dict()
            # Si un plan viejo todavía tiene 'capital' guardado, lo ignoramos al usarlo
            # (no lo borramos del doc viejo para no romper nada, simplemente no se lee)
            return plan
        return None
    except Exception as e:
        st.error(f"Error al cargar plan: {str(e)}")
        return None


def guardar_plan_trading(user_id, plan):
    """Guarda el plan de trading. NUNCA incluye 'capital' — eso vive solo en perfil_usuario."""
    try:
        plan = dict(plan)
        plan.pop('capital', None)  # por si vino de un wizard viejo en memoria
        doc_ref = db.collection('users').document(user_id).collection('trading_plan').document('plan_actual')
        plan['ultima_actualizacion'] = datetime.now().isoformat()
        doc_ref.set(plan)
        return True
    except Exception as e:
        st.error(f"Error al guardar plan: {str(e)}")
        return False


def cargar_historial_planes(user_id):
    try:
        docs = (db.collection('users').document(user_id)
                  .collection('trading_plan_historial')
                  .order_by('fecha_creacion', direction='DESCENDING')
                  .limit(10).stream())
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
def wizard_plan_trading(capital_actual):
    """
    Asistente para crear un plan de trading personalizado.
    capital_actual se recibe como parámetro (ya calculado desde perfil_usuario)
    solo para MOSTRARLO de referencia — el wizard ya no lo pide como input editable.
    """
    st.header("🎯 Wizard de Plan de Trading")
    st.caption(
        f"Tu capital actual es **${capital_actual:,.2f}** (gestionado en ⚙️ Mi Perfil). "
        "El plan que generemos usará este número para calcular tu riesgo — no necesitas ingresarlo aquí."
    )

    with st.form("wizard_plan_trading"):
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

        st.subheader("2. Gestión de Riesgo")
        riesgo_por_operacion = st.slider(
            "Riesgo máximo por operación (% del capital):",
            min_value=0.5, max_value=5.0, value=1.0, step=0.5,
            help="No arriesgues más de este porcentaje por trade"
        )
        max_operaciones_dia = st.slider(
            "Máximo de operaciones por día:",
            min_value=1, max_value=10, value=3,
            help="Límite para evitar overtrading"
        )

        st.subheader("3. Horarios y Mercados Preferidos")
        col3, col4 = st.columns(2)
        with col3:
            hora_inicio = st.time_input("Hora de inicio preferida:", value=time(9, 0))
            hora_fin = st.time_input("Hora de fin preferida:", value=time(16, 0))
        with col4:
            mercados = st.multiselect(
                "Mercados que operas:",
                ["Forex", "Acciones", "Criptomonedas", "Índices", "Futuros", "Opciones"],
                default=["Forex"]
            )
            pares_favoritos = st.text_input(
                "Pares/activos favoritos (separados por coma):",
                "EUR/USD, NZD/USD, GBP/USD",
                help="Ejemplo: EUR/USD, NZD/USD, GBP/USD"
            )

        st.subheader("4. Objetivos y Enfoque Psicológico")
        objetivo_mensual = st.slider(
            "Objetivo de rendimiento mensual (%):",
            min_value=1.0, max_value=20.0, value=5.0, step=0.5,
            help="Objetivo realista de ganancias mensuales"
        )
        desafios_psicologicos = st.multiselect(
            "Desafíos psicológicos a trabajar:",
            ["Miedo a perder", "Ansiedad", "Overtrading", "Falta de disciplina",
             "Revenge trading", "Apego emocional a operaciones", "Entrada prematura por FOMO"],
            default=["Entrada prematura por FOMO"]
        )

        submitted = st.form_submit_button("🚀 Crear Mi Plan de Trading")

        if submitted:
            return {
                'estilo': estilo,
                'experiencia': experiencia,
                'riesgo_por_operacion': riesgo_por_operacion,
                'max_operaciones_dia': max_operaciones_dia,
                'hora_inicio': hora_inicio.strftime("%H:%M"),
                'hora_fin': hora_fin.strftime("%H:%M"),
                'mercados': mercados,
                'pares_favoritos': [p.strip() for p in pares_favoritos.split(",") if p.strip()],
                'objetivo_mensual': objetivo_mensual,
                'desafios_psicologicos': desafios_psicologicos,
                'fecha_creacion': datetime.now().isoformat(),
                'activo': True,
            }

    return None


# ========== GENERACIÓN INTELIGENTE DE PLAN ==========
def generar_plan_inteligente(plan_base, capital_actual):
    """
    Genera un plan de trading detallado usando IA.
    capital_actual se pasa solo para que la IA calcule montos de referencia
    en su texto — no se guarda dentro del plan.
    """
    if client is None:
        st.warning("⚠️ No hay API key de OpenAI configurada. Usando plan por defecto.")
        return crear_plan_por_defecto(plan_base, capital_actual)

    prompt = f"""
    Como mentor experto en trading, crea un plan de trading detallado en español basado en estos parámetros:

    ESTILO: {plan_base['estilo']}
    EXPERIENCIA: {plan_base['experiencia']}
    CAPITAL ACTUAL: ${capital_actual:,.2f}
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

    Responde ÚNICAMENTE con un JSON válido, sin texto adicional, con esta estructura exacta:
    {{
        "reglas_entrada": ["regla1", "regla2"],
        "reglas_salida": ["regla1", "regla2"],
        "gestion_riesgo": ["punto1", "punto2"],
        "checklist_preoperacional": ["item1", "item2"],
        "protocolo_dias_ganadores": "texto descriptivo",
        "protocolo_dias_perdedores": "texto descriptivo",
        "tecnicas_psicologicas": ["tecnica1", "tecnica2"],
        "metricas_seguimiento": ["metrica1", "metrica2"]
    }}
    """

    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un mentor de trading profesional que crea planes personalizados. Respondes solo en JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        contenido = respuesta.choices[0].message.content.strip()
        # Por si el modelo envuelve el JSON en ```json ... ```
        if contenido.startswith("```"):
            contenido = contenido.strip("`")
            if contenido.startswith("json"):
                contenido = contenido[4:].strip()

        plan_detallado = json.loads(contenido)
        plan_base.update(plan_detallado)
        return plan_base

    except Exception as e:
        st.warning(f"No se pudo generar el plan con IA ({str(e)}). Usando plan por defecto.")
        return crear_plan_por_defecto(plan_base, capital_actual)


def crear_plan_por_defecto(plan_base, capital_actual):
    """Plan básico de respaldo si falla la generación con IA."""
    plan_base['reglas_entrada'] = [
        "Solo operar en dirección de la tendencia principal (bias H4/D1)",
        "Esperar a que el precio LLEGUE a la zona de OB, sin adelantarse",
        "Confirmar manipulación / liquidity sweep antes de entrar",
    ]
    plan_base['reglas_salida'] = [
        "TP en la siguiente zona de liquidez real, RR mínimo 2:1",
        "SL basado en estructura, nunca a ojo",
        "Salir si el fundamento (estructura) cambia antes de llegar al TP",
    ]
    plan_base['gestion_riesgo'] = [
        f"Máximo {plan_base['riesgo_por_operacion']}% (${capital_actual * plan_base['riesgo_por_operacion'] / 100:,.2f}) por operación",
        f"Máximo {plan_base['max_operaciones_dia']} operaciones por día",
        "Reducir tamaño en periodos de alta volatilidad o noticias importantes",
    ]
    plan_base['checklist_preoperacional'] = [
        "¿Confirmé el bias en H4/D1?",
        "¿Hubo manipulación o liquidity sweep claro?",
        "¿El precio ya llegó a mi zona, sin adelantarme?",
        "¿Mi SL está en un nivel de estructura?",
        "¿El RR es de al menos 2:1?",
    ]
    plan_base['protocolo_dias_ganadores'] = "Mantén la disciplina. Una racha ganadora no es licencia para aumentar el riesgo o saltarte reglas."
    plan_base['protocolo_dias_perdedores'] = "Detente tras 2 pérdidas consecutivas en el día. Revisa si fue el plan o la ejecución antes de operar de nuevo."
    plan_base['tecnicas_psicologicas'] = ["Mantra antes de cada entrada", "Checklist obligatoria pre-trade", "Journaling inmediato post-trade"]
    plan_base['metricas_seguimiento'] = ["Win rate", "RR promedio", "Adherencia a la checklist", "Rachas de pérdidas consecutivas"]
    return plan_base


# ========== RECORDATORIOS ==========
def generar_recordatorios_diarios(plan, capital_actual):
    recordatorios = []
    riesgo_dolares = capital_actual * plan['riesgo_por_operacion'] / 100
    recordatorios.append(f"💰 Riesgo máximo por operación: {plan['riesgo_por_operacion']}% (${riesgo_dolares:,.2f})")
    recordatorios.append(f"🚫 Máximo {plan['max_operaciones_dia']} operaciones hoy")
    recordatorios.append(f"⏰ Horario de trading: {plan['hora_inicio']} - {plan['hora_fin']}")

    if plan.get('desafios_psicologicos'):
        for desafio in plan['desafios_psicologicos']:
            if desafio == "Overtrading":
                recordatorios.append("⚡ ¿Estás operando por necesidad o por oportunidad?")
            elif desafio == "Falta de disciplina":
                recordatorios.append("🎯 Sigue tu plan, no tus emociones")
            elif desafio == "Miedo a perder":
                recordatorios.append("🛡️ Las pérdidas son parte del juego, gestiónalas bien")
            elif desafio == "Entrada prematura por FOMO":
                recordatorios.append("⏳ Si no llegó a tu zona, el trade no existe todavía")

    return recordatorios


# ========== VISUALIZACIÓN DEL PLAN ==========
def mostrar_plan_visual(plan, capital_actual):
    """
    capital_actual ahora se RECIBE como parámetro, siempre calculado en
    tiempo real desde perfil_usuario.py — nunca leído desde el plan guardado.
    """
    st.header("📊 Dashboard de Tu Plan")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Capital", f"${capital_actual:,.2f}")
    col2.metric("Riesgo/Op", f"{plan['riesgo_por_operacion']}%")
    col3.metric("Límite Diario", f"{plan['max_operaciones_dia']} ops")
    col4.metric("Objetivo Mensual", f"{plan['objetivo_mensual']}%")

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

        riesgo_absoluto = capital_actual * (plan['riesgo_por_operacion'] / 100)
        fig_riesgo = px.bar(
            x=['Capital Total', 'Riesgo por Operación'],
            y=[capital_actual, riesgo_absoluto],
            color=['Capital Total', 'Riesgo por Operación'],
            color_discrete_map={'Capital Total': '#4A5A3D', 'Riesgo por Operación': '#C9A34E'},
            title='Gestión de Capital y Riesgo',
            labels={'x': '', 'y': 'Monto ($)'}
        )
        st.plotly_chart(fig_riesgo, use_container_width=True)

    with tab3:
        st.subheader("Horario de Trading")
        st.write(f"**Horario preferido:** {plan['hora_inicio']} - {plan['hora_fin']}")

        horas = list(range(24))
        h_inicio = int(plan['hora_inicio'].split(':')[0])
        h_fin = int(plan['hora_fin'].split(':')[0])
        actividad = [1 if (h_inicio <= h < h_fin) else 0 for h in horas]

        fig_horario = go.Figure(go.Bar(x=horas, y=actividad, marker_color='#C9A34E'))
        fig_horario.update_layout(title="Horario de Trading Activo",
                                   xaxis_title="Hora del día", yaxis_title="Activo",
                                   showlegend=False)
        st.plotly_chart(fig_horario, use_container_width=True)

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
            st.caption(
                "Esta checklist es la generada por tu plan. Si quieres una checklist editable "
                "que persista entre sesiones, usa la de ⚙️ Mi Perfil."
            )
            for i, item in enumerate(plan['checklist_preoperacional'], 1):
                st.checkbox(f"{i}. {item}", key=f"plan_check_{i}")
        else:
            st.info("Checklist no disponible para este plan")


# ========== INTERFAZ PRINCIPAL ==========
def mostrar_estrategia_maestra():
    st.title("📑 Plan de Trading Maestro")

    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión para acceder al plan de trading")
        return

    user_id = st.session_state.user['uid']

    # Capital real, calculado UNA vez aquí y pasado a todas las funciones
    # que lo necesiten — así nunca hay dos números distintos en pantalla.
    operaciones = cargar_operaciones_firebase(user_id)
    capital_info = calcular_capital_actual(user_id, operaciones)
    capital_actual = capital_info['capital_actual']

    plan_actual = cargar_plan_trading(user_id)
    historial_planes = cargar_historial_planes(user_id)

    tab1, tab2, tab3 = st.tabs(["🎯 Mi Plan Actual", "🔄 Crear Nuevo Plan", "📊 Historial"])

    with tab1:
        if plan_actual:
            mostrar_plan_visual(plan_actual, capital_actual)

            st.header("🔔 Recordatorios para Hoy")
            recordatorios = generar_recordatorios_diarios(plan_actual, capital_actual)
            for recordatorio in recordatorios:
                st.info(recordatorio)

            col7, col8 = st.columns(2)
            if col7.button("🖨️ Exportar Plan a PDF"):
                st.info("Función de exportación próximamente disponible")

            if col8.button("🗑️ Eliminar Plan Actual"):
                st.session_state['confirmar_eliminar_plan'] = True

            if st.session_state.get('confirmar_eliminar_plan'):
                st.warning("¿Confirmas que quieres eliminar tu plan actual?")
                col_si, col_no = st.columns(2)
                if col_si.button("Sí, eliminar"):
                    db.collection('users').document(user_id).collection('trading_plan').document('plan_actual').delete()
                    st.session_state['confirmar_eliminar_plan'] = False
                    st.success("Plan eliminado correctamente")
                    st.rerun()
                if col_no.button("Cancelar"):
                    st.session_state['confirmar_eliminar_plan'] = False
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

        plan_nuevo = wizard_plan_trading(capital_actual)

        if plan_nuevo:
            with st.spinner("Generando plan personalizado con IA..."):
                plan_completo = generar_plan_inteligente(plan_nuevo, capital_actual)

                if guardar_plan_trading(user_id, plan_completo):
                    st.success("🎉 ¡Plan de trading creado exitosamente!")
                    st.balloons()

                    try:
                        historial_ref = db.collection('users').document(user_id).collection('trading_plan_historial').document()
                        historial_ref.set(plan_completo)
                    except Exception as e:
                        st.error(f"Error al guardar en historial: {str(e)}")

                    with st.expander("Ver resumen del plan"):
                        mostrar_plan_visual(plan_completo, capital_actual)
                else:
                    st.error("Error al guardar el plan. Intenta nuevamente.")

    with tab3:
        st.header("Historial de Planes")

        if historial_planes:
            for plan in historial_planes:
                fecha_str = datetime.fromisoformat(plan['fecha_creacion']).strftime('%d/%m/%Y')
                with st.expander(f"Plan del {fecha_str} — {plan.get('estilo', 'N/A')}"):
                    st.write(f"**Estilo:** {plan.get('estilo', 'N/A')}")
                    st.write(f"**Riesgo/Op:** {plan.get('riesgo_por_operacion', 0)}%")
                    st.write(f"**Objetivo mensual:** {plan.get('objetivo_mensual', 0)}%")
                    st.caption("El capital mostrado siempre es tu capital actual, no el histórico de ese momento.")

                    if st.button("Cargar este plan", key=plan['id']):
                        if guardar_plan_trading(user_id, plan):
                            st.success("Plan cargado como actual")
                            st.rerun()
        else:
            st.info("No hay planes históricos guardados")


if __name__ == "__main__":
    mostrar_estrategia_maestra()
