import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="AutoAyuda IA Real", page_icon="🚗", layout="wide")

# --- CONFIGURACIÓN DE LA IA (GEMINI) ---
# Intentamos obtener la clave de los secretos de Streamlit (Nube) o local
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Si lo corrés local sin configurar secretos, pedirá la clave en la pantalla
    api_key = None

def consultar_gemini(sintoma, auto_modelo):
    if not api_key:
        return "⚠️ Error: Falta configurar la API Key."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Actúa como un mecánico experto con 30 años de experiencia.
    Vehículo: {auto_modelo}
    Síntoma del usuario: "{sintoma}"
    
    Tu tarea:
    1. Identificar la falla más probable.
    2. Dar un porcentaje de confianza estimado.
    3. Explicar brevemente qué revisar.
    4. Indicar si es peligroso seguir manejando.
    
    Responde en formato corto y directo, máximo 3 líneas.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error de conexión con IA: {str(e)}"

# --- BASE DE DATOS (CSV) ---
# Nota: En Streamlit Cloud, el CSV se reinicia si la app se "duerme". 
# Para persistencia real se necesita Google Sheets o Firebase, pero para el MVP esto sirve.
if 'historial' not in st.session_state:
    st.session_state.historial = []

def guardar_registro(modelo, tipo, descripcion, diagnostico):
    nuevo = {
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Modelo": modelo,
        "Tipo": tipo,
        "Problema": descripcion,
        "Diagnostico_IA": diagnostico
    }
    st.session_state.historial.append(nuevo)

# --- INTERFAZ ---
st.title("🚗 AutoAyuda: Diagnóstico con IA Generativa")

tab1, tab2 = st.tabs(["📱 Diagnóstico", "📊 Dashboard"])

with tab1:
    # Si no hay API Key configurada (caso local primera vez), mostrar input
    if not api_key:
        st.warning("Para usar la IA Real, ingresá tu API Key de Google:")
        temp_key = st.text_input("Pegá tu API Key acá (AIza...)", type="password")
        if temp_key:
            api_key = temp_key
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        modelo = st.text_input("Tu Auto (Modelo y Año)", "Ford Fiesta 2015")
        tipo = st.selectbox("Categoría", ["Motor", "Eléctrico", "Tren Delantero", "Frenos", "Otro"])
    with col2:
        descripcion = st.text_area("Describí el problema (sé detallado)", height=100)

    if st.button("Analizar con IA"):
        if not descripcion:
            st.error("Escribí un problema primero.")
        else:
            with st.spinner("Consultando al experto artificial..."):
                resultado = consultar_gemini(descripcion, modelo)
                guardar_registro(modelo, tipo, descripcion, resultado)
                st.success("Diagnóstico Generado")
                st.info(resultado)
                st.map(pd.DataFrame({'lat': [-34.6037], 'lon': [-58.3816]})) # Mapa ejemplo

with tab2:
    st.header("Panel de Control en Tiempo Real")
    if len(st.session_state.historial) > 0:
        df = pd.DataFrame(st.session_state.historial)
        st.dataframe(df)
        st.bar_chart(df['Tipo'].value_counts())
    else:
        st.info("Aún no hay diagnósticos realizados en esta sesión.")

