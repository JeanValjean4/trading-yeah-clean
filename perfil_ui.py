# perfil_ui.py - INTERFAZ DE "MI PERFIL"
#
# Este archivo SOLO contiene interfaz (Streamlit). Toda la lógica de datos
# vive en perfil_usuario.py. Así, si después cambias de Firebase a otra
# base de datos, solo tocas perfil_usuario.py y esta UI sigue funcionando igual.

import streamlit as st
from datetime import datetime

from perfil_usuario import (
    cargar_perfil_usuario, guardar_configuracion_perfil, establecer_capital_inicial,
    registrar_movimiento_capital, cargar_movimientos_capital,
    calcular_capital_actual, calcular_rentabilidad,
    cargar_checklist, guardar_checklist,
    cargar_notas, guardar_nota, eliminar_nota,
)
from journaling import cargar_operaciones_firebase


def mostrar_perfil_usuario():
    st.title("⚙️ Mi Perfil de Trading")

    if 'user' not in st.session_state:
        st.warning("🔒 Debes iniciar sesión")
        return

    user_id = st.session_state.user['uid']
    perfil = cargar_perfil_usuario(user_id)
    operaciones = cargar_operaciones_firebase(user_id)
    capital_info = calcular_capital_actual(user_id, operaciones)
    rentabilidad = calcular_rentabilidad(user_id, operaciones)

    tab_capital, tab_config, tab_checklist, tab_notas = st.tabs(
        ["💰 Capital", "🎯 Configuración", "✅ Checklist", "📝 Notas"]
    )

    # ═══════════════════════════════════════════════════
    # TAB: CAPITAL
    # ═══════════════════════════════════════════════════
    with tab_capital:
        st.subheader("Resumen de capital")

        col1, col2, col3 = st.columns(3)
        col1.metric("Capital actual", f"${capital_info['capital_actual']:,.2f}")
        col2.metric("P&L de trading", f"${capital_info['pnl_total']:,.2f}",
                     delta=f"{rentabilidad:+.1f}%")
        col3.metric("Depósitos/Retiros netos", f"${capital_info['movimientos_total']:,.2f}")

        st.caption(
            f"Capital inicial: ${capital_info['capital_inicial']:,.2f} · "
            "El capital actual se calcula automáticamente: capital inicial + depósitos/retiros + "
            "ganancias o pérdidas reales registradas en tu Journaling. No se edita directamente."
        )

        st.divider()

        # Si el usuario nunca ha configurado capital inicial real (sigue en default),
        # se lo dejamos claro y fácil de ajustar UNA vez.
        st.subheader("¿Necesitas corregir tu capital inicial?")
        st.caption(
            "Usa esto solo si tu capital inicial no refleja con qué abriste tu cuenta realmente. "
            "Para depósitos o retiros nuevos, usa la sección de abajo."
        )
        with st.form("form_capital_inicial"):
            nuevo_capital_inicial = st.number_input(
                "Capital inicial correcto ($)",
                value=float(capital_info['capital_inicial']),
                step=100.0, format="%.2f"
            )
            if st.form_submit_button("Corregir capital inicial"):
                if establecer_capital_inicial(user_id, nuevo_capital_inicial):
                    st.success("✅ Capital inicial actualizado")
                    st.rerun()

        st.divider()

        st.subheader("Registrar depósito o retiro")
        col_a, col_b = st.columns(2)
        with col_a:
            with st.form("form_deposito"):
                monto_dep = st.number_input("Monto a depositar ($)", min_value=0.0, step=50.0, format="%.2f")
                nota_dep = st.text_input("Nota (opcional)", key="nota_dep")
                if st.form_submit_button("💵 Registrar depósito"):
                    if monto_dep > 0:
                        if registrar_movimiento_capital(user_id, 'deposito', monto_dep, nota_dep):
                            st.success("✅ Depósito registrado")
                            st.rerun()
                    else:
                        st.warning("El monto debe ser mayor a 0")

        with col_b:
            with st.form("form_retiro"):
                monto_ret = st.number_input("Monto a retirar ($)", min_value=0.0, step=50.0, format="%.2f")
                nota_ret = st.text_input("Nota (opcional)", key="nota_ret")
                if st.form_submit_button("💸 Registrar retiro"):
                    if monto_ret > 0:
                        if monto_ret > capital_info['capital_actual']:
                            st.error("No puedes retirar más de tu capital actual")
                        elif registrar_movimiento_capital(user_id, 'retiro', monto_ret, nota_ret):
                            st.success("✅ Retiro registrado")
                            st.rerun()
                    else:
                        st.warning("El monto debe ser mayor a 0")

        st.divider()

        st.subheader("Historial de movimientos")
        movimientos = cargar_movimientos_capital(user_id)
        if not movimientos:
            st.caption("Sin depósitos o retiros registrados todavía.")
        else:
            for m in movimientos[:15]:
                signo = "🟢" if m['monto'] >= 0 else "🔴"
                fecha_corta = m.get('fecha', '')[:10]
                etiqueta = "Depósito" if m['tipo'] == 'deposito' else "Retiro"
                nota_txt = f" — {m['nota']}" if m.get('nota') else ""
                st.write(f"{signo} **{etiqueta}** ${abs(m['monto']):,.2f} · {fecha_corta}{nota_txt}")

    # ═══════════════════════════════════════════════════
    # TAB: CONFIGURACIÓN
    # ═══════════════════════════════════════════════════
    with tab_config:
        st.subheader("Configuración de tu estrategia y riesgo")

        with st.form("form_config_perfil"):
            col1, col2 = st.columns(2)
            with col1:
                riesgo = st.slider("Riesgo por operación (%)", 0.5, 5.0,
                                    value=float(perfil.get('riesgo_por_operacion', 1.0)), step=0.5)
                drawdown_max = st.slider("Drawdown máximo permitido (%)", 5.0, 30.0,
                                          value=float(perfil.get('drawdown_maximo', 10.0)), step=1.0)
            with col2:
                opciones_estrategia = ["Smart Money Concepts", "Price Action", "Soporte/Resistencia",
                                        "Breakout", "Medias Móviles", "RSI/MACD", "Scalping", "Swing Trading"]
                estrategia_actual = perfil.get('estrategia_principal', 'Smart Money Concepts')
                if estrategia_actual not in opciones_estrategia:
                    opciones_estrategia.append(estrategia_actual)
                estrategia = st.selectbox("Estrategia principal", opciones_estrategia,
                                           index=opciones_estrategia.index(estrategia_actual))
                max_ops = st.number_input("Máximo operaciones por día", 1, 20,
                                           value=int(perfil.get('max_operaciones_dia', 5)))
                objetivo = st.number_input("Objetivo mensual (%)", 1.0, 50.0,
                                            value=float(perfil.get('objetivo_mensual', 5.0)), step=0.5)

            if st.form_submit_button("💾 Guardar configuración", type="primary"):
                if guardar_configuracion_perfil(user_id, riesgo, max_ops, estrategia, objetivo, drawdown_max):
                    st.success("✅ Configuración guardada")
                    st.rerun()

        st.divider()
        st.subheader("Lo que esto significa para tu día a día")
        col1, col2, col3 = st.columns(3)
        col1.metric("Riesgo en $ por operación",
                    f"${capital_info['capital_actual'] * perfil.get('riesgo_por_operacion', 1.0) / 100:,.2f}")
        col2.metric("Drawdown máximo en $",
                    f"${capital_info['capital_actual'] * perfil.get('drawdown_maximo', 10.0) / 100:,.2f}")
        col3.metric("Objetivo mensual en $",
                    f"${capital_info['capital_actual'] * perfil.get('objetivo_mensual', 5.0) / 100:,.2f}")

    # ═══════════════════════════════════════════════════
    # TAB: CHECKLIST
    # ═══════════════════════════════════════════════════
    with tab_checklist:
        st.subheader("✅ Checklist Pre-Trade")
        st.caption(
            "Tu lista personal de verificación. Edítala según tu estilo — la idea es que "
            "te tome 30 segundos confirmar que no estás entrando por miedo o impulso."
        )

        items = cargar_checklist(user_id)

        items_actualizados = []
        for item in items:
            marcado = st.checkbox(item['texto'], value=item.get('marcado', False), key=f"check_{item['id']}")
            items_actualizados.append({'id': item['id'], 'texto': item['texto'], 'marcado': marcado})

        total = len(items_actualizados)
        marcados = sum(1 for i in items_actualizados if i['marcado'])
        if total > 0:
            st.progress(marcados / total, text=f"Cumplimiento: {marcados}/{total}")
            if marcados == total:
                st.success("🎉 Checklist completa. Tienes luz verde según tus propias reglas.")
            elif marcados >= total * 0.7:
                st.info("Buen avance — revisa los puntos pendientes antes de entrar.")
            else:
                st.warning("⚠️ Te faltan varios puntos. Vale la pena esperar antes de operar.")

        if items_actualizados != items:
            guardar_checklist(user_id, items_actualizados)

        with st.expander("✏️ Editar items de la checklist"):
            nuevo_texto = st.text_input("Nuevo punto a verificar:", key="nuevo_check_item")
            if st.button("➕ Añadir punto"):
                if nuevo_texto.strip():
                    nuevo_id = str(int(items_actualizados[-1]['id']) + 1) if items_actualizados else "1"
                    items_actualizados.append({'id': nuevo_id, 'texto': nuevo_texto.strip(), 'marcado': False})
                    guardar_checklist(user_id, items_actualizados)
                    st.rerun()

            if items_actualizados:
                st.write("Eliminar puntos:")
                ids_a_eliminar = []
                for item in items_actualizados:
                    if st.checkbox(f"🗑️ {item['texto']}", key=f"del_check_{item['id']}"):
                        ids_a_eliminar.append(item['id'])
                if ids_a_eliminar and st.button("Eliminar seleccionados"):
                    restantes = [i for i in items_actualizados if i['id'] not in ids_a_eliminar]
                    guardar_checklist(user_id, restantes)
                    st.rerun()

    # ═══════════════════════════════════════════════════
    # TAB: NOTAS
    # ═══════════════════════════════════════════════════
    with tab_notas:
        st.subheader("📝 Notas de Aprendizaje")

        with st.form("form_nueva_nota", clear_on_submit=True):
            titulo = st.text_input("Título")
            contenido = st.text_area("Contenido — lección, idea, reflexión", height=120)
            if st.form_submit_button("💾 Guardar nota"):
                if titulo.strip() and contenido.strip():
                    if guardar_nota(user_id, titulo.strip(), contenido.strip()):
                        st.success("✅ Nota guardada")
                        st.rerun()
                else:
                    st.warning("Completa título y contenido")

        st.divider()

        notas = cargar_notas(user_id)
        if not notas:
            st.caption("Aún no tienes notas guardadas.")
        else:
            for nota in notas:
                fecha_corta = nota.get('fecha', '')[:10]
                with st.expander(f"{nota.get('titulo', 'Sin título')} — {fecha_corta}"):
                    st.write(nota.get('contenido', ''))
                    if st.button("🗑️ Eliminar", key=f"del_nota_{nota['id']}"):
                        if eliminar_nota(user_id, nota['id']):
                            st.rerun()
