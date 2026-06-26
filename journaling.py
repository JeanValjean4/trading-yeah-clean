# journaling.py - VERSIÓN CORREGIDA: dashboard interno conectado a capital real
import streamlit as st
import pandas as pd
import plotly.express as px
import openai
from datetime import datetime
import base64
import binascii
from firebase_config import db
import os
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai.api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

if not api_key:
    raise ValueError("⚠️ No se encontró la API key. Define OPENAI_API_KEY en tu .env o en secrets.toml")

client = OpenAI(api_key=api_key)

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)


# ========== FIREBASE: OPERACIONES ==========
def guardar_operacion_firebase(user_id, operacion):
    """Guarda operación en Firestore. pnl_real es el único campo que afecta el capital global."""
    try:
        if "imagen" in operacion and operacion["imagen"]:
            if hasattr(operacion["imagen"], 'read'):
                operacion["imagen"] = base64.b64encode(operacion["imagen"].read()).decode('utf-8')
            elif isinstance(operacion["imagen"], bytes):
                operacion["imagen"] = base64.b64encode(operacion["imagen"]).decode('utf-8')

        for field in ["precio_entrada", "stop_loss", "take_profit", "pnl_real"]:
            if field in operacion:
                operacion[field] = float(operacion[field])

        operacion["timestamp"] = firestore.SERVER_TIMESTAMP

        doc_ref = db.collection('users').document(user_id).collection('operaciones').document()
        doc_ref.set(operacion)
        st.success("Operación guardada en la nube ✅ — tu capital se actualizó automáticamente")
        return True
    except Exception as e:
        st.error(f"Error al guardar: {str(e)}")
        return False


def cargar_operaciones_firebase(user_id):
    try:
        operaciones = []
        docs = (db.collection('users').document(user_id)
                  .collection('operaciones')
                  .order_by('timestamp', direction='DESCENDING')
                  .stream())

        for doc in docs:
            operacion = doc.to_dict()
            operacion["id"] = doc.id
            for field in ["precio_entrada", "stop_loss", "take_profit", "pnl_real"]:
                if field in operacion:
                    operacion[field] = float(operacion[field])
                else:
                    operacion[field] = 0.0
            operaciones.append(operacion)

        return operaciones
    except Exception as e:
        st.error(f"Error al cargar operaciones: {str(e)}")
        return []


def eliminar_operacion_firebase(user_id, operacion_id):
    try:
        doc_ref = db.collection('users').document(user_id).collection('operaciones').document(operacion_id)
        doc_ref.delete()
        return True
    except Exception:
        return False


# ========== ANÁLISIS ==========
def analizar_operaciones_avanzado(operaciones):
    if not operaciones:
        return None

    try:
        df = pd.DataFrame(operaciones)
        total_ops = len(df)
        ganadoras = len(df[df["resultado"] == "Ganadora"])
        perdedoras = total_ops - ganadoras
        win_rate = (ganadoras / total_ops * 100) if total_ops > 0 else 0

        if "resultado_num" not in df.columns:
            df["resultado_num"] = df["resultado"].apply(lambda x: 1 if x == "Ganadora" else -1)

        analisis = {
            "operaciones_totales": total_ops,
            "operaciones_ganadoras": ganadoras,
            "operaciones_perdedoras": perdedoras,
            "win_rate": round(win_rate, 2),
            "ratio_ganancia_perdida": ganadoras / perdedoras if perdedoras > 0 else float('inf'),
            "mejor_activo": df.groupby("activo")["resultado_num"].sum().idxmax() if not df.empty else "N/A",
            "peor_activo": df.groupby("activo")["resultado_num"].sum().idxmin() if not df.empty else "N/A",
            "mejor_timeframe": df.groupby("timeframe")["resultado_num"].sum().idxmax() if not df.empty else "N/A",
        }
        return analisis
    except Exception as e:
        st.error(f"Error en análisis avanzado: {str(e)}")
        return None


def generar_retroalimentacion_avanzada(operaciones, analisis):
    if not operaciones or not analisis:
        return "No hay suficientes datos para análisis."

    try:
        resumen_ops = "\n".join([
            f"{op.get('fecha', '')} - {op.get('activo', '')} - {op.get('resultado', '')} - {op.get('resumen', '')}"
            for op in operaciones[:10]
        ])

        prompt = f"""
        Como mentor experto en trading, analiza estas operaciones y métricas:

        MÉTRICAS:
        - Total operaciones: {analisis['operaciones_totales']}
        - Operaciones ganadoras: {analisis['operaciones_ganadoras']}
        - Operaciones perdedoras: {analisis['operaciones_perdedoras']}
        - Win Rate: {analisis['win_rate']}%
        - Mejor activo: {analisis['mejor_activo']}
        - Peor activo: {analisis['peor_activo']}
        - Mejor timeframe: {analisis['mejor_timeframe']}

        ÚLTIMAS OPERACIONES:
        {resumen_ops}

        Proporciona un análisis con:
        1. Patrones detectados (buenos y malos)
        2. Recomendaciones específicas de mejora
        3. Análisis psicológico basado en las notas
        4. Sugerencias para mantener la disciplina
        5. Advertencias sobre posibles sesgos cognitivos

        Responde en español con un tono profesional pero cercano.
        """

        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un mentor de trading profesional con expertise en psicología del trading"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"Error al generar retroalimentación: {str(e)}"


# ========== FORMULARIO ==========
def formulario_operacion_mejorado(operacion=None):
    valores_default = {
        "activo": "", "timeframe": "15m", "zona_interes": "",
        "precio_entrada": 0.0, "stop_loss": 0.0, "take_profit": 0.0,
        "resultado": "Ganadora", "resumen": "", "tipo": "Largo", "pnl_real": 0.0,
        "emocion_antes": "Neutral", "emocion_durante": "Neutral",
        "emocion_despues": "Neutral", "leccion_aprendida": ""
    }

    if operacion:
        for key in valores_default:
            if key in operacion:
                valores_default[key] = operacion[key]

    with st.form("op_form_mejorado", clear_on_submit=True):
        st.subheader("📝 Registro de Operación")

        col1, col2 = st.columns(2)
        activo = col1.text_input("Par (Ej: EUR/USD)", value=valores_default["activo"]).upper()
        timeframe = col2.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1H", "4H", "1D"],
                                    index=["1m", "5m", "15m", "30m", "1H", "4H", "1D"].index(valores_default["timeframe"]))

        col3, col4, col5 = st.columns(3)
        precio_entrada = col3.number_input("Precio Entrada", value=valores_default["precio_entrada"], format="%.5f")
        sl = col4.number_input("Stop Loss", value=valores_default["stop_loss"], format="%.5f")
        tp = col5.number_input("Take Profit", value=valores_default["take_profit"], format="%.5f")

        col6, col7, col8 = st.columns(3)
        resultado = col6.selectbox("Resultado", ["Ganadora", "Perdedora"],
                                    index=["Ganadora", "Perdedora"].index(valores_default["resultado"]))
        tipo = col7.selectbox("Dirección", ["Largo", "Corto"],
                               index=["Largo", "Corto"].index(valores_default["tipo"]))
        pnl_real = col8.number_input(
            "Ganancia/Pérdida Real ($)",
            value=float(valores_default.get("pnl_real", 0.0)),
            format="%.2f",
            help="Este valor es el ÚNICO que mueve tu capital global. Si fue pérdida, ingresa un número negativo."
        )

        st.subheader("🧠 Estado Emocional")
        emocion_cols = st.columns(3)
        emocion_antes = emocion_cols[0].selectbox(
            "Antes", ["Confianza", "Ansiedad", "Miedo", "Euforia", "Neutral", "Indecisión"],
            index=["Confianza", "Ansiedad", "Miedo", "Euforia", "Neutral", "Indecisión"].index(valores_default["emocion_antes"]))
        emocion_durante = emocion_cols[1].selectbox(
            "Durante", ["Calma", "Ansiedad", "Miedo", "Euforia", "Frustración", "Neutral"],
            index=["Calma", "Ansiedad", "Miedo", "Euforia", "Frustración", "Neutral"].index(valores_default["emocion_durante"]))
        emocion_despues = emocion_cols[2].selectbox(
            "Después", ["Satisfacción", "Arrepentimiento", "Alivio", "Frustración", "Neutral", "Confianza"],
            index=["Satisfacción", "Arrepentimiento", "Alivio", "Frustración", "Neutral", "Confianza"].index(valores_default["emocion_despues"]))

        leccion_aprendida = st.text_area("Lección aprendida", value=valores_default["leccion_aprendida"],
                                          placeholder="¿Qué aprendiste de esta operación?")
        resumen = st.text_area("Resumen detallado", value=valores_default["resumen"],
                                placeholder="Describe tu análisis, entrada, gestión y salida")

        imagen = st.file_uploader("Captura del gráfico (opcional)", type=["png", "jpg", "jpeg"])

        submit = st.form_submit_button("💾 Guardar Operación")

        if submit:
            if not activo:
                st.error("Debes especificar un par de trading")
                return None

            return {
                "fecha": datetime.now().isoformat(),
                "activo": activo,
                "timeframe": timeframe,
                "precio_entrada": precio_entrada,
                "stop_loss": sl,
                "take_profit": tp,
                "resultado": resultado,
                "tipo": tipo,
                "pnl_real": pnl_real,
                "resumen": resumen,
                "leccion_aprendida": leccion_aprendida,
                "emocion_antes": emocion_antes,
                "emocion_durante": emocion_durante,
                "emocion_despues": emocion_despues,
                "imagen": imagen
            }

    return None


# ========== DASHBOARD INTERNO DEL JOURNALING ==========
def mostrar_dashboard(operaciones, user_id):
    """
    NOTA: recibe user_id ahora, para poder mostrar capital real consistente
    con el resto de la plataforma (antes este dashboard no sabía nada de capital).
    """
    if not operaciones:
        st.info("Agrega operaciones para ver tu dashboard")
        return

    from perfil_usuario import calcular_capital_actual, calcular_rentabilidad

    st.header("📊 Dashboard de Rendimiento")

    capital_info = calcular_capital_actual(user_id, operaciones)
    rentabilidad = calcular_rentabilidad(user_id, operaciones)

    analisis = analizar_operaciones_avanzado(operaciones)
    if not analisis:
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Capital actual", f"${capital_info['capital_actual']:,.2f}", delta=f"{rentabilidad:+.1f}%")
    col2.metric("Operaciones Totales", analisis["operaciones_totales"])
    col3.metric("Win Rate", f"{analisis['win_rate']}%")
    col4.metric("Ganadoras", analisis["operaciones_ganadoras"])
    col5.metric("Perdedoras", analisis["operaciones_perdedoras"])

    try:
        df = pd.DataFrame(operaciones)

        if not df.empty and 'activo' in df.columns and 'resultado' in df.columns:
            fig_activos = px.bar(df, x='activo', color='resultado',
                                  title='Resultados por Activo', barmode='group')
            st.plotly_chart(fig_activos, use_container_width=True)

        # Curva de equity real, basada en pnl_real acumulado en orden cronológico
        if not df.empty and 'fecha' in df.columns and 'pnl_real' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'])
            df_cronologico = df.sort_values('fecha_dt')
            df_cronologico['pnl_acumulado'] = (
                capital_info['capital_inicial'] + capital_info['movimientos_total']
                + df_cronologico['pnl_real'].cumsum()
            )
            fig_equity = px.line(df_cronologico, x='fecha_dt', y='pnl_acumulado',
                                  title='Curva de Equity', markers=True)
            fig_equity.update_layout(yaxis_title="Capital ($)", xaxis_title="Fecha")
            st.plotly_chart(fig_equity, use_container_width=True)

    except Exception as e:
        st.error(f"Error al generar gráficos: {str(e)}")

    st.subheader("🧠 Retroalimentación Inteligente")
    retro = generar_retroalimentacion_avanzada(operaciones, analisis)
    st.markdown(f"<div style='background-color:#2E2E2E; padding:15px; border-radius:10px;'>{retro}</div>",
                unsafe_allow_html=True)


# ========== INTERFAZ PRINCIPAL ==========
def mostrar_journaling_inteligente():
    st.title("📈 Journaling Inteligente")

    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión para acceder al journaling")
        return

    user_id = st.session_state.user['uid']

    if 'editar_operacion' not in st.session_state:
        st.session_state.editar_operacion = None

    with st.spinner("Cargando operaciones..."):
        operaciones = cargar_operaciones_firebase(user_id)

    tab1, tab2, tab3 = st.tabs(["➕ Nueva Operación", "📋 Historial", "📊 Dashboard"])

    with tab1:
        st.header("Registrar Nueva Operación")
        nueva_op = formulario_operacion_mejorado(st.session_state.editar_operacion)
        if nueva_op:
            if guardar_operacion_firebase(user_id, nueva_op):
                st.session_state.editar_operacion = None
                st.rerun()

    with tab2:
        st.header("Historial de Operaciones")
        if not operaciones:
            st.info("No hay operaciones registradas aún")
        else:
            for operacion in operaciones:
                with st.expander(
                    f"{operacion.get('activo', 'N/A')} - {operacion.get('timeframe', 'N/A')} "
                    f"({operacion.get('resultado', 'N/A')}) — ${operacion.get('pnl_real', 0.0):,.2f}"
                ):
                    mostrar_operacion(operacion)
                    col1, col2 = st.columns(2)
                    if col1.button("✏️ Editar", key=f"edit_{operacion['id']}"):
                        st.session_state.editar_operacion = operacion
                        st.rerun()
                    if col2.button("🗑️ Eliminar", key=f"del_{operacion['id']}"):
                        if eliminar_operacion_firebase(user_id, operacion['id']):
                            st.rerun()

    with tab3:
        mostrar_dashboard(operaciones, user_id)


def mostrar_operacion(operacion):
    st.subheader(f"{operacion.get('activo', '')} - {operacion.get('timeframe', '')}")

    if "imagen" in operacion and operacion["imagen"]:
        try:
            if isinstance(operacion["imagen"], str):
                imagen_bytes = base64.b64decode(operacion["imagen"])
                st.image(imagen_bytes, caption="Gráfico del Trade", use_container_width=True)
        except (binascii.Error, TypeError):
            st.warning("Formato de imagen inválido")

    cols = st.columns(5)
    cols[0].metric("Entrada", f"{operacion.get('precio_entrada', 'N/A')}")
    cols[1].metric("SL", f"{operacion.get('stop_loss', 'N/A')}")
    cols[2].metric("TP", f"{operacion.get('take_profit', 'N/A')}")
    cols[3].metric("Resultado", operacion.get('resultado', 'N/A'))
    cols[4].metric("P&L", f"${operacion.get('pnl_real', 0.0):,.2f}")

    if any(key in operacion for key in ["emocion_antes", "emocion_durante", "emocion_despues"]):
        st.write("**Estado Emocional:**")
        emoc_cols = st.columns(3)
        emoc_cols[0].write(f"Antes: {operacion.get('emocion_antes', 'N/A')}")
        emoc_cols[1].write(f"Durante: {operacion.get('emocion_durante', 'N/A')}")
        emoc_cols[2].write(f"Después: {operacion.get('emocion_despues', 'N/A')}")

    if operacion.get('leccion_aprendida'):
        st.write(f"**Lección:** {operacion['leccion_aprendida']}")
    if operacion.get('resumen'):
        st.write(f"**Resumen:** {operacion['resumen']}")
