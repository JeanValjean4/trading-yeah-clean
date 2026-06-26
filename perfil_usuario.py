# perfil_usuario.py - ÚNICA FUENTE DE VERDAD PARA CAPITAL Y PERFIL DEL TRADER
#
# ARQUITECTURA:
# Este módulo es el ÚNICO lugar del proyecto que escribe en:
#   users/{uid}/perfil/trading_config
#   users/{uid}/movimientos_capital/{movimiento_id}
#
# Ningún otro archivo (journaling.py, estrategia_maestra.py, streamlit_app.py)
# debe escribir directamente en estas rutas. Todos deben IMPORTAR las funciones
# de este archivo para leer o modificar capital.
#
# CONCEPTO CLAVE: separamos dos cosas que antes estaban mezcladas:
#   1. capital_inicial      -> el capital con el que el usuario abrió su cuenta
#   2. movimientos_capital  -> depósitos y retiros (NO son ganancias de trading)
#   3. pnl_trading          -> se calcula SIEMPRE a partir de las operaciones reales
#                              en journaling, nunca se edita a mano
#
# capital_actual = capital_inicial + suma(movimientos_capital) + suma(pnl de operaciones)
#
# Esto evita que un usuario pueda "inventar" ganancias editando un número,
# y evita que un depósito real se confunda con una ganancia de trading
# (lo cual rompería las métricas de rentabilidad).

import streamlit as st
from datetime import datetime
from firebase_config import db
from firebase_admin import firestore

# ─────────────────────────────────────────────────────────────
# LECTURA Y ESCRITURA DEL PERFIL BASE
# ─────────────────────────────────────────────────────────────

PERFIL_DEFAULT = {
    'capital_inicial': 10000.0,
    'riesgo_por_operacion': 1.0,
    'max_operaciones_dia': 5,
    'estrategia_principal': 'Smart Money Concepts',
    'objetivo_mensual': 5.0,
    'drawdown_maximo': 10.0,
    'fecha_creacion': None,
}


def cargar_perfil_usuario(user_id):
    """
    Carga el perfil base del usuario (configuración, NO el capital actual calculado).
    Si no existe, lo crea con valores default.
    """
    try:
        ref = db.collection('users').document(user_id).collection('perfil').document('trading_config')
        doc = ref.get()
        if doc.exists:
            data = doc.to_dict()
            # Aseguramos que todos los campos default existan, por si el doc es viejo
            for key, val in PERFIL_DEFAULT.items():
                if key not in data:
                    data[key] = val
            return data

        nuevo_perfil = dict(PERFIL_DEFAULT)
        nuevo_perfil['fecha_creacion'] = datetime.now().isoformat()
        ref.set(nuevo_perfil)
        return nuevo_perfil

    except Exception as e:
        st.error(f"Error cargando perfil: {str(e)}")
        return dict(PERFIL_DEFAULT)


def guardar_configuracion_perfil(user_id, riesgo_por_operacion, max_operaciones_dia,
                                   estrategia_principal, objetivo_mensual, drawdown_maximo):
    """
    Guarda SOLO la configuración del perfil (no toca capital).
    El capital se modifica exclusivamente vía registrar_movimiento_capital()
    o automáticamente desde journaling.py al guardar una operación.
    """
    try:
        ref = db.collection('users').document(user_id).collection('perfil').document('trading_config')
        ref.set({
            'riesgo_por_operacion': riesgo_por_operacion,
            'max_operaciones_dia': max_operaciones_dia,
            'estrategia_principal': estrategia_principal,
            'objetivo_mensual': objetivo_mensual,
            'drawdown_maximo': drawdown_maximo,
            'ultima_actualizacion': datetime.now().isoformat(),
        }, merge=True)
        return True
    except Exception as e:
        st.error(f"Error guardando configuración: {str(e)}")
        return False


def establecer_capital_inicial(user_id, capital_inicial):
    """
    Establece el capital inicial. Pensado para usarse SOLO la primera vez
    que el usuario configura su cuenta (onboarding). Después de eso, los
    cambios de capital deben pasar por registrar_movimiento_capital().
    """
    try:
        ref = db.collection('users').document(user_id).collection('perfil').document('trading_config')
        ref.set({
            'capital_inicial': float(capital_inicial),
            'ultima_actualizacion': datetime.now().isoformat(),
        }, merge=True)
        return True
    except Exception as e:
        st.error(f"Error estableciendo capital inicial: {str(e)}")
        return False


# ─────────────────────────────────────────────────────────────
# MOVIMIENTOS DE CAPITAL (depósitos / retiros)
# Esto es lo que reemplaza el "capital editable a mano" que pedías antes.
# En vez de sobreescribir un número, queda un registro auditable de cada
# depósito o retiro — igual que en una cuenta de broker real.
# ─────────────────────────────────────────────────────────────

def registrar_movimiento_capital(user_id, tipo, monto, nota=""):
    """
    Registra un depósito o retiro de capital.
    tipo: 'deposito' o 'retiro'
    monto: siempre positivo, el signo se aplica según el tipo
    """
    try:
        if tipo not in ('deposito', 'retiro'):
            raise ValueError("tipo debe ser 'deposito' o 'retiro'")

        monto_firmado = float(monto) if tipo == 'deposito' else -float(monto)

        db.collection('users').document(user_id).collection('movimientos_capital').add({
            'tipo': tipo,
            'monto': monto_firmado,
            'nota': nota,
            'fecha': datetime.now().isoformat(),
            'timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True
    except Exception as e:
        st.error(f"Error registrando movimiento: {str(e)}")
        return False


def cargar_movimientos_capital(user_id):
    """Carga el historial de depósitos y retiros, más reciente primero."""
    try:
        docs = (db.collection('users').document(user_id)
                  .collection('movimientos_capital')
                  .order_by('timestamp', direction=firestore.Query.DESCENDING)
                  .stream())
        movimientos = []
        for doc in docs:
            m = doc.to_dict()
            m['id'] = doc.id
            movimientos.append(m)
        return movimientos
    except Exception as e:
        st.error(f"Error cargando movimientos: {str(e)}")
        return []


def total_movimientos_capital(user_id):
    """Suma neta de todos los depósitos y retiros."""
    movimientos = cargar_movimientos_capital(user_id)
    return sum(m.get('monto', 0.0) for m in movimientos)


# ─────────────────────────────────────────────────────────────
# CÁLCULO DE CAPITAL ACTUAL — LA FUNCIÓN MÁS IMPORTANTE DEL ARCHIVO
# Esta es la función que TODO el resto de la plataforma debe usar
# para mostrar el capital. Nunca se lee un campo "capital_actual"
# guardado — siempre se recalcula desde las tres fuentes reales.
# ─────────────────────────────────────────────────────────────

def calcular_capital_actual(user_id, operaciones=None):
    """
    capital_actual = capital_inicial + movimientos (depósitos/retiros) + pnl_total de trading

    Si 'operaciones' no se pasa, las carga internamente desde journaling.
    Pasarlas como parámetro evita leer Firestore dos veces cuando el
    caller (ej. la barra lateral) ya las tiene cargadas.
    """
    perfil = cargar_perfil_usuario(user_id)
    capital_inicial = perfil.get('capital_inicial', 0.0)

    movimientos_total = total_movimientos_capital(user_id)

    if operaciones is None:
        # Import local para evitar import circular con journaling.py
        from journaling import cargar_operaciones_firebase
        operaciones = cargar_operaciones_firebase(user_id)

    pnl_total = sum(float(op.get('pnl_real', 0.0)) for op in operaciones)

    capital_actual = capital_inicial + movimientos_total + pnl_total

    return {
        'capital_inicial': capital_inicial,
        'movimientos_total': movimientos_total,
        'pnl_total': pnl_total,
        'capital_actual': round(capital_actual, 2),
    }


def calcular_rentabilidad(user_id, operaciones=None):
    """
    Rentabilidad % calculada SOLO sobre el desempeño de trading,
    sin contar depósitos/retiros (que inflarían o desinflarían
    artificialmente el % de rentabilidad real como trader).
    """
    datos = calcular_capital_actual(user_id, operaciones)
    base = datos['capital_inicial'] + datos['movimientos_total']
    if base <= 0:
        return 0.0
    return round((datos['pnl_total'] / base) * 100, 2)


# ─────────────────────────────────────────────────────────────
# CHECKLIST PRE-TRADE — editable por el usuario
# Vive aquí (no en checklist.py separado) porque es parte del
# perfil del trader, junto a su capital y configuración.
# ─────────────────────────────────────────────────────────────

CHECKLIST_DEFAULT = [
    {"id": "1", "texto": "¿Confirmé la estructura de mercado (bias) en H4/D1?", "marcado": False},
    {"id": "2", "texto": "¿Identifiqué una manipulación / liquidity sweep clara?", "marcado": False},
    {"id": "3", "texto": "¿El precio YA llegó a mi zona de OB, sin adelantarme?", "marcado": False},
    {"id": "4", "texto": "¿Mi Stop Loss está en un nivel basado en estructura, no a ojo?", "marcado": False},
    {"id": "5", "texto": "¿El RR es de al menos 2:1?", "marcado": False},
    {"id": "6", "texto": "¿Estoy entrando por mi plan, no por miedo a perderme el movimiento?", "marcado": False},
]


def cargar_checklist(user_id):
    try:
        ref = db.collection('users').document(user_id).collection('perfil').document('checklist')
        doc = ref.get()
        if doc.exists:
            return doc.to_dict().get('items', CHECKLIST_DEFAULT)
        ref.set({'items': CHECKLIST_DEFAULT, 'ultima_actualizacion': datetime.now().isoformat()})
        return list(CHECKLIST_DEFAULT)
    except Exception as e:
        st.error(f"Error cargando checklist: {str(e)}")
        return list(CHECKLIST_DEFAULT)


def guardar_checklist(user_id, items):
    try:
        ref = db.collection('users').document(user_id).collection('perfil').document('checklist')
        ref.set({'items': items, 'ultima_actualizacion': datetime.now().isoformat()})
        return True
    except Exception as e:
        st.error(f"Error guardando checklist: {str(e)}")
        return False


# ─────────────────────────────────────────────────────────────
# NOTAS DE APRENDIZAJE — también centralizadas aquí
# ─────────────────────────────────────────────────────────────

def cargar_notas(user_id):
    try:
        docs = (db.collection('users').document(user_id)
                  .collection('notas')
                  .order_by('timestamp', direction=firestore.Query.DESCENDING)
                  .stream())
        notas = []
        for doc in docs:
            nota = doc.to_dict()
            nota['id'] = doc.id
            notas.append(nota)
        return notas
    except Exception as e:
        st.error(f"Error cargando notas: {str(e)}")
        return []


def guardar_nota(user_id, titulo, contenido):
    try:
        db.collection('users').document(user_id).collection('notas').add({
            'titulo': titulo,
            'contenido': contenido,
            'fecha': datetime.now().isoformat(),
            'timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True
    except Exception as e:
        st.error(f"Error guardando nota: {str(e)}")
        return False


def eliminar_nota(user_id, nota_id):
    try:
        db.collection('users').document(user_id).collection('notas').document(nota_id).delete()
        return True
    except Exception as e:
        st.error(f"Error eliminando nota: {str(e)}")
        return False


# ─────────────────────────────────────────────────────────────
# SISTEMA DE NIVEL / EXPERIENCIA
# Se calcula siempre a partir de operaciones reales, nunca se
# guarda como número fijo (para que no se desincronice).
# ─────────────────────────────────────────────────────────────

def calcular_progreso(operaciones):
    """
    Calcula experiencia, nivel, rachas a partir de las operaciones reales.
    No se guarda en Firestore como número — se recalcula cada vez,
    así nunca puede desincronizarse del historial real.
    """
    if not operaciones:
        return {
            'experiencia': 0, 'nivel': 1, 'rango': '🥉 Aprendiz',
            'mejor_racha': 0, 'peor_racha': 0,
            'experiencia_en_nivel': 0, 'porcentaje_siguiente_nivel': 0,
        }

    ganadoras = sum(1 for op in operaciones if op.get('resultado') == 'Ganadora')
    perdedoras = sum(1 for op in operaciones if op.get('resultado') == 'Perdedora')
    total = len(operaciones)

    experiencia = max(0, total * 10 + ganadoras * 5 - perdedoras * 2)
    nivel = max(1, int(experiencia / 100) + 1)
    experiencia_en_nivel = experiencia % 100

    # Rachas: recorremos en orden cronológico (las operaciones vienen DESC, las invertimos)
    ops_cronologico = list(reversed(operaciones))
    racha_actual = 0
    mejor_racha = 0
    peor_racha = 0
    racha_perdidas_actual = 0

    for op in ops_cronologico:
        if op.get('resultado') == 'Ganadora':
            racha_actual += 1
            racha_perdidas_actual = 0
            mejor_racha = max(mejor_racha, racha_actual)
        elif op.get('resultado') == 'Perdedora':
            racha_perdidas_actual += 1
            racha_actual = 0
            peor_racha = max(peor_racha, racha_perdidas_actual)

    if nivel <= 3:
        rango = "🥉 Aprendiz"
    elif nivel <= 6:
        rango = "🥈 Trader Consistente"
    elif nivel <= 10:
        rango = "🥇 Trader Experto"
    elif nivel <= 15:
        rango = "🏆 Trader Elite"
    else:
        rango = "👑 Leyenda del Trading"

    return {
        'experiencia': experiencia,
        'nivel': nivel,
        'rango': rango,
        'mejor_racha': mejor_racha,
        'peor_racha': peor_racha,
        'experiencia_en_nivel': experiencia_en_nivel,
        'porcentaje_siguiente_nivel': experiencia_en_nivel,
    }
