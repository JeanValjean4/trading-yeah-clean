# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from firebase_config import db
import openai
import os
from openai import OpenAI
client = OpenAI()

# Configuración de API (usa variables de entorno)
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))

# ========== FUNCIONES DE DATOS ==========
def cargar_operaciones_usuario(user_id):
    """Carga las operaciones del usuario desde Firebase"""
    try:
        operaciones = []
        docs = db.collection('users').document(user_id).collection('operaciones').stream()
        
        for doc in docs:
            op_data = doc.to_dict()
            op_data['id'] = doc.id
            operaciones.append(op_data)
            
        return operaciones
    except Exception as e:
        st.error(f"Error al cargar operaciones: {str(e)}")
        return []

def procesar_datos_operaciones(operaciones):
    """Convierte las operaciones en DataFrame y calcula métricas"""
    if not operaciones:
        return None
    
    df = pd.DataFrame(operaciones)
    
    # Convertir y limpiar datos
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.sort_values('fecha')
    
    # Calcular métricas de rendimiento
    if all(col in df.columns for col in ['resultado', 'precio_entrada', 'stop_loss', 'take_profit']):
        # Calcular P&L simulado (si no hay campo real)
        df['resultado_num'] = df['resultado'].apply(lambda x: 1 if x == 'Ganadora' else -1)
        df['risk_reward_ratio'] = (df['take_profit'] - df['precio_entrada']) / (df['precio_entrada'] - df['stop_loss'])
        
        # Calcular equity curve (simulada)
        df['profit_loss'] = df['resultado_num'] * df['risk_reward_ratio'] * 100  # Simulación
        df['equity_curve'] = df['profit_loss'].cumsum()
    
    return df

# ========== MÉTRICAS Y KPIs ==========
def calcular_metricas_avanzadas(df):
    """Calcula métricas avanzadas de trading"""
    if df is None or df.empty:
        return {}
    
    metricas = {}
    
    # =====================
    # MÉTRICAS BÁSICAS
    # =====================
    total_ops = len(df)
    ganadoras = 0
    perdedoras = 0
    win_rate = 0

    if 'resultado' in df.columns:
        ganadoras = len(df[df['resultado'] == 'Ganadora'])
        perdedoras = total_ops - ganadoras
        win_rate = (ganadoras / total_ops * 100) if total_ops > 0 else 0

    metricas['total_operaciones'] = total_ops
    metricas['operaciones_ganadoras'] = ganadoras
    metricas['operaciones_perdedoras'] = perdedoras
    metricas['win_rate'] = round(win_rate, 2)

    # =====================
    # MÉTRICAS AVANZADAS
    # =====================
    if 'profit_loss' in df.columns and not df['profit_loss'].isnull().all():
        metricas['profit_total'] = round(df['profit_loss'].sum(), 2)
        metricas['profit_promedio'] = round(df['profit_loss'].mean(), 2) if total_ops > 0 else 0
        metricas['profit_maximo'] = round(df['profit_loss'].max(), 2) if total_ops > 0 else 0
        metricas['profit_minimo'] = round(df['profit_loss'].min(), 2) if total_ops > 0 else 0

        # Drawdown calculation
        equity_curve = df['equity_curve'].values if 'equity_curve' in df.columns else df['profit_loss'].cumsum().values
        roll_max = np.maximum.accumulate(equity_curve)
        drawdowns = equity_curve - roll_max
        metricas['max_drawdown'] = round(np.min(drawdowns), 2) if len(drawdowns) > 0 else 0
        metricas['drawdown_actual'] = round(drawdowns[-1], 2) if len(drawdowns) > 0 else 0

    # =====================
    # MÉTRICAS POR ACTIVO
    # =====================
    if 'activo' in df.columns and 'profit_loss' in df.columns:
        metricas_activo = df.groupby('activo').agg({
            'resultado': (lambda x: (x == 'Ganadora').mean() * 100) if 'resultado' in df.columns else (lambda x: 0),
            'profit_loss': 'sum'
        }).rename(columns={'resultado': 'win_rate_activo', 'profit_loss': 'profit_activo'})

        metricas['mejor_activo'] = metricas_activo['profit_activo'].idxmax() if not metricas_activo.empty else "N/A"
        metricas['peor_activo'] = metricas_activo['profit_activo'].idxmin() if not metricas_activo.empty else "N/A"

    # =====================
    # MÉTRICAS EMOCIONALES
    # =====================
    emociones_campos = ['emocion_antes', 'emocion_durante', 'emocion_despues']
    for campo in emociones_campos:
        if campo in df.columns and 'resultado_num' in df.columns:
            emociones_stats = df.groupby(campo)['resultado_num'].mean() * 100
            if not emociones_stats.empty:
                metricas[f'mejor_emocion_{campo}'] = emociones_stats.idxmax()
                metricas[f'peor_emocion_{campo}'] = emociones_stats.idxmin()

    return metricas


# ========== VISUALIZACIONES ==========
def crear_grafico_equity_curve(df):
    """Crea gráfico de curva de equity con drawdown"""
    if df is None or 'equity_curve' not in df.columns:
        return None
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.1, subplot_titles=('Curva de Equity', 'Drawdown'))
    
    # Equity curve
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['equity_curve'], 
                           mode='lines', name='Equity', line=dict(color='#4A5A3D')),
                 row=1, col=1)
    
    # Drawdown calculation
    roll_max = np.maximum.accumulate(df['equity_curve'])
    drawdown = df['equity_curve'] - roll_max
    
    fig.add_trace(go.Scatter(x=df['fecha'], y=drawdown, 
                           mode='lines', name='Drawdown', fill='tozeroy', 
                           line=dict(color='#FF6B6B')),
                 row=2, col=1)
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown ($)", row=2, col=1)
    
    return fig

def crear_grafico_distribucion_resultados(df):
    """Gráfico de distribución de resultados por diferentes dimensiones"""
    if df is None:
        return None
    
    fig = make_subplots(rows=2, cols=2, 
                       subplot_titles=('Por Activo', 'Por Timeframe', 
                                      'Por Resultado', 'Por Emoción Inicial'),
                       specs=[[{"type": "pie"}, {"type": "pie"}],
                             [{"type": "bar"}, {"type": "bar"}]])
    
    # Por activo
    if 'activo' in df.columns:
        activo_counts = df['activo'].value_counts()
        fig.add_trace(go.Pie(labels=activo_counts.index, values=activo_counts.values,
                           name="Por Activo"), row=1, col=1)
    
    # Por timeframe
    if 'timeframe' in df.columns:
        tf_counts = df['timeframe'].value_counts()
        fig.add_trace(go.Pie(labels=tf_counts.index, values=tf_counts.values,
                           name="Por Timeframe"), row=1, col=2)
    
    # Por resultado
    if 'resultado' in df.columns:
        resultado_counts = df['resultado'].value_counts()
        fig.add_trace(go.Bar(x=resultado_counts.index, y=resultado_counts.values,
                           name="Por Resultado", marker_color=['#4A5A3D', '#C9A34E']), 
                     row=2, col=1)
    
    # Por emoción inicial
    if 'emocion_antes' in df.columns:
        emocion_counts = df['emocion_antes'].value_counts()
        fig.add_trace(go.Bar(x=emocion_counts.index, y=emocion_counts.values,
                           name="Por Emoción", marker_color='#6A0DAD'), 
                     row=2, col=2)
    
    fig.update_layout(height=700, showlegend=False)
    return fig

def crear_grafico_rendimiento_temporal(df):
    """Gráfico de rendimiento por tiempo"""
    if df is None or 'fecha' not in df.columns:
        return None
    
    # Agrupar por día
    df_daily = df.groupby(df['fecha'].dt.date).agg({
        'resultado_num': ['count', 'mean'],
        'profit_loss': 'sum'
    }).round(2)
    
    df_daily.columns = ['operaciones_dia', 'win_rate_dia', 'profit_dia']
    df_daily = df_daily.reset_index()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Barras para operaciones por día
    fig.add_trace(go.Bar(x=df_daily['fecha'], y=df_daily['operaciones_dia'],
                       name="Operaciones/Día", marker_color='#C9A34E'),
                 secondary_y=False)
    
    # Línea para win rate
    fig.add_trace(go.Scatter(x=df_daily['fecha'], y=df_daily['win_rate_dia']*100,
                          mode='lines+markers', name="Win Rate %", line=dict(color='#4A5A3D')),
                 secondary_y=True)
    
    fig.update_layout(title="Rendimiento Diario",
                     xaxis_title="Fecha",
                     height=400)
    
    fig.update_yaxes(title_text="Operaciones por Día", secondary_y=False)
    fig.update_yaxes(title_text="Win Rate (%)", secondary_y=True, range=[0, 100])
    
    return fig

# ========== ANÁLISIS CON IA ==========
def generar_analisis_ia(metricas, df):
    """Genera análisis inteligente con IA"""
    if not metricas or df is None:
        return "No hay suficientes datos para generar análisis."
    
    try:
        resumen_metricas = "\n".join([f"{k}: {v}" for k, v in metricas.items()])
        
        emociones_analysis = ""
        emociones_campos = ['emocion_antes', 'emocion_durante', 'emocion_despues']
        for campo in emociones_campos:
            if campo in df.columns:
                emoc_stats = df.groupby(campo)['resultado_num'].mean() * 100
                emociones_analysis += f"\nEmociones {campo}:\n" + "\n".join([f"  {emoc}: {rate:.1f}% win rate" 
                                                                           for emoc, rate in emoc_stats.items()])
        
        prompt = f"""
        Como analista experto en trading, analiza estas métricas y proporciona insights accionables:

        MÉTRICAS PRINCIPALES:
        {resumen_metricas}

        ANÁLISIS EMOCIONAL:
        {emociones_analysis}

        Proporciona:
        1. 3 fortalezas clave del trader
        2. 3 áreas de mejora críticas
        3. Recomendaciones específicas basadas en los patrones detectados
        4. Análisis de consistencia y disciplina
        5. Advertencias sobre posibles riesgos

        Sé conciso, profesional y enfocado en insights accionables. Responde en español.
        """
        
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un analista cuantitativo experto en psicología del trading"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        return respuesta.choices[0].message.content
    
    except Exception as e:
        return f"Error en análisis IA: {str(e)}"

# ========== INTERFAZ PRINCIPAL ==========
def mostrar_dashboard_personalizado():
    st.title("📊 Dashboard Personalizado")
    
    # Verificar autenticación
    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión para acceder al dashboard")
        return
    
    user_id = st.session_state.user['uid']
    
    # Cargar datos
    with st.spinner("Cargando y analizando tus operaciones..."):
        operaciones = cargar_operaciones_usuario(user_id)
        df = procesar_datos_operaciones(operaciones)
        metricas = calcular_metricas_avanzadas(df)
    
    if not operaciones:
        st.info("""
        ## 🚀 Bienvenido a tu Dashboard Personalizado
        
        Una vez que comiences a registrar operaciones en el Journaling Inteligente, 
        aquí verás:
        
        - 📈 **Métricas de rendimiento** en tiempo real
        - 📊 **Gráficos interactivos** de tu evolución
        - 🧠 **Análisis inteligente** con IA
        - 💡 **Recomendaciones personalizadas** para mejorar
        
        ¡Ve al Journaling y registra tu primera operación!
        """)
        return
    
    # ========== SECCIÓN 1: MÉTRICAS PRINCIPALES ==========
    st.header("📈 Métricas Clave de Desempeño")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Operaciones Totales", metricas.get('total_operaciones', 0))
        st.metric("Win Rate", f"{metricas.get('win_rate', 0)}%")
    
    with col2:
        st.metric("Ganadoras", metricas.get('operaciones_ganadoras', 0))
        st.metric("Perdedoras", metricas.get('operaciones_perdedoras', 0))
    
    with col3:
        profit_total = metricas.get('profit_total', 0)
        st.metric("Profit Total", f"${profit_total:,.2f}", 
                 delta_color="normal" if profit_total >= 0 else "inverse")
        st.metric("Profit Promedio", f"${metricas.get('profit_promedio', 0):,.2f}")
    
    with col4:
        st.metric("Max Drawdown", f"${metricas.get('max_drawdown', 0):,.2f}",
                 delta_color="inverse")
        st.metric("Mejor Activo", metricas.get('mejor_activo', 'N/A'))
    
    # ========== SECCIÓN 2: GRÁFICOS INTERACTIVOS ==========
    st.header("📊 Visualización de Datos")
    
    tab1, tab2, tab3 = st.tabs(["Curva de Equity", "Distribución", "Rendimiento Temporal"])
    
    with tab1:
        fig_equity = crear_grafico_equity_curve(df)
        if fig_equity:
            st.plotly_chart(fig_equity, use_container_width=True)
        else:
            st.info("Agrega más operaciones para ver la curva de equity")
    
    with tab2:
        fig_dist = crear_grafico_distribucion_resultados(df)
        if fig_dist:
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Datos insuficientes para gráficos de distribución")
    
    with tab3:
        fig_temp = crear_grafico_rendimiento_temporal(df)
        if fig_temp:
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("Datos insuficientes para análisis temporal")
    
    # ========== SECCIÓN 3: ANÁLISIS DETALLADO ==========
    st.header("🧠 Análisis Inteligente con IA")
    
    with st.expander("🔍 Insights Detallados", expanded=True):
        analisis_ia = generar_analisis_ia(metricas, df)
        st.markdown(f"""
        <div style='background-color: #2E2E2E; padding: 20px; border-radius: 10px; border-left: 4px solid #C9A34E;'>
        {analisis_ia}
        </div>
        """, unsafe_allow_html=True)
    
    # ========== SECCIÓN 4: RECOMENDACIONES ACCIONABLES ==========
    st.header("💡 Recomendaciones Personalizadas")
    
    # Recomendaciones basadas en métricas
    rec_col1, rec_col2 = st.columns(2)
    
    with rec_col1:
        st.subheader("🎯 Para Mejorar")
        if metricas.get('win_rate', 0) < 50:
            st.warning("**Focus en calidad:** Tu win rate sugiere que necesitas mejorar la selección de operaciones")
        if metricas.get('max_drawdown', 0) < -500:
            st.error("**Gestión de riesgo:** El drawdown es elevado, considera reducir el tamaño de posición")
        if 'emocion_antes' in df.columns:
            emocion_peor = metricas.get('peor_emocion_emocion_antes', '')
            if emocion_peor:
                st.info(f"**Estado emocional:** Evita operar cuando te sientes {emocion_peor.lower()}")
    
    with rec_col2:
        st.subheader("✅ Para Mantener")
        if metricas.get('win_rate', 0) > 60:
            st.success("**Excelente consistencia:** Mantén tu estrategia actual")
        if metricas.get('profit_total', 0) > 0:
            st.success("**Rentabilidad positiva:** Sigue con tu enfoque actual")
        if len(df) > 20 and metricas.get('win_rate', 0) > 55:
            st.success("**Consistencia demostrada:** Tu método está funcionando")
    
    # ========== SECCIÓN 5: DATOS CRUDOS ==========
    with st.expander("📋 Ver Datos Detallados"):
        if df is not None:
            columnas_necesarias = ['fecha', 'activo', 'timeframe', 'resultado', 'profit_loss']
            columnas_presentes = [c for c in columnas_necesarias if c in df.columns]
        
            if columnas_presentes:
                st.dataframe(df[columnas_presentes].sort_values('fecha', ascending=False))
            else:
                st.info("⚠️ Aún no tienes datos suficientes para mostrar columnas detalladas.")
        
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Datos CSV",
                data=csv,
                file_name="mis_operaciones_trading.csv",
                mime="text/csv"
            )


# Ejecutar dashboard si se corre directamente
if __name__ == "__main__":
    mostrar_dashboard_personalizado()