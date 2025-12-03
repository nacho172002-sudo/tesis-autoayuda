import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai
import time

# CONFIGURACIÓN
st.set_page_config(page_title="AutoAyuda IA", page_icon="🚗", layout="wide")

# CLAVE Y MODELO (Directo en el código)
API_KEY = "AIzaSyCxlwQO6cpQVHeWX_rF8osULqa1d3reRsc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- FUNCIONES ---
def consultar_gemini(sintoma, auto_modelo):
    prompt = f"""
    Actúa como un mecánico experto. Vehículo: {auto_modelo}. Síntoma: "{sintoma}".
    1. Identificar falla probable.
    2. Porcentaje de confianza.
    3. Qué revisar (breve).
    4. ¿Es peligroso manejar?
    Responde corto y directo.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error IA: {str(e)}"

if 'historial' not in st.session_state:
    st.session_state.historial = []

def guardar_registro(modelo, tipo, descripcion, diagnostico):
    nuevo = {
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Modelo": modelo, "Tipo": tipo, "Problema": descripcion, "Diagnostico_IA": diagnostico
    }
    st.session_state.historial.append(nuevo)

# --- INTERFAZ ---
st.title("🚗 AutoAyuda: Diagnóstico IA")

tab1, tab2 = st.tabs(["📱 DIAGNÓSTICO", "📊 DASHBOARD"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        modelo = st.text_input("Modelo", "Fiat Cronos 2020")
        tipo = st.selectbox("Categoría", ["Motor", "Eléctrico", "Tren Delantero", "Frenos", "Otro"])
    with col2:
        descripcion = st.text_area("Síntoma", height=100)

    if st.button("ANALIZAR"):
        if not descripcion:
            st.error("Describí el problema.")
        else:
            with st.spinner("Analizando..."):
                resultado = consultar_gemini(descripcion, modelo)
                guardar_registro(modelo, tipo, descripcion, resultado)
                st.success("Diagnóstico:")
                st.info(resultado)
                st.map(pd.DataFrame({'lat': [-34.6037], 'lon': [-58.3816]}))

with tab2:
    if len(st.session_state.historial) > 0:
        df = pd.DataFrame(st.session_state.historial)
        st.dataframe(df)
        st.bar_chart(df['Tipo'].value_counts())
    else:
        st.info("Sin datos aún.")