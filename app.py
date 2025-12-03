import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="AutoAyuda IA", page_icon="🚗", layout="wide")

# --- CONFIGURACIÓN DIRECTA DE LA IA ---
# ACÁ ESTÁ TU CLAVE YA PUESTA PARA QUE FUNCIONE DIRECTO
API_KEY = "AIzaSyCxlwQO6cpQVHeWX_rF8osULqa1d3reRsc"
genai.configure(api_key=API_KEY)

# Usamos el modelo más nuevo y rápido
model = genai.GenerativeModel('gemini-2.0-flash')

# --- FUNCIONES ---
def consultar_gemini(sintoma, auto_modelo):
    prompt = f"""
    Actúa como un mecánico experto con 30 años de experiencia.
    Vehículo: {auto_modelo}
    Síntoma del usuario: "{sintoma}"
    
    Tu tarea:
    1. Identificar la falla más probable.
    2. Dar un porcentaje de confianza estimado.
    3. Explicar brevemente qué revisar (máximo 2 items).
    4. Indicar si es peligroso seguir manejando.
    
    Responde en formato corto, directo y sin saludos.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error de conexión con IA: {str(e)}"

# --- BASE DE DATOS TEMPORAL (SESIÓN) ---
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

# --- INTERFAZ GRÁFICA ---
st.title("🚗 AutoAyuda: Red Colaborativa con IA")
st.markdown("---")

# Usamos pestañas para separar la App del Conductor y el Dashboard
tab1, tab2 = st.tabs(["📱 MODO CONDUCTOR", "📊 DASHBOARD TALLER"])

# --- PESTAÑA 1: LA APP ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Ingresá los datos del vehículo")
        modelo = st.text_input("Modelo y Año", "Chevrolet Corsa 2010")
        tipo = st.selectbox("Categoría Sospechosa", ["Motor", "Eléctrico", "Tren Delantero", "Frenos", "Desconocido"])
    
    with col2:
        st.warning("Describí el síntoma")
        descripcion = st.text_area("¿Qué sentís, escuchás o ves?", height=100, placeholder="Ej: Hace un ruido clac-clac al doblar...")

    if st.button("🔍 ANALIZAR FALLA CON IA", type="primary"):
        if not descripcion:
            st.error("Por favor describí el problema primero.")
        else:
            with st.spinner("La IA está analizando patrones mecánicos..."):
                # Simular un poco de "pensamiento" para efecto visual
                time.sleep(1)
                
                # Llamada real a Google Gemini
                resultado = consultar_gemini(descripcion, modelo)
                
                # Guardar
                guardar_registro(modelo, tipo, descripcion, resultado)
                
                # Mostrar resultados
                st.success("Diagnóstico Completado")
                st.markdown(f"### 🤖 Resultado:\n{resultado}")
                
                st.markdown("---")
                st.write("📍 **Talleres Cercanos Sugeridos:**")
                st.map(pd.DataFrame({'lat': [-34.6037], 'lon': [-58.3816]}))

# --- PESTAÑA 2: EL DASHBOARD ---
with tab2:
    st.header("Tablero de Control Operativo")
    
    if len(st.session_state.historial) > 0:
        df = pd.DataFrame(st.session_state.historial)
        
        # Métricas
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Total Diagnósticos", len(df))
        kpi2.metric("Última Actividad", df.iloc[-1]['Fecha'].split(" ")[1])
        
        # Gráficos
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Fallas por Categoría")
            st.bar_chart(df['Tipo'].value_counts())
        with c2:
            st.subheader("Historial Reciente")
            st.dataframe(df[['Modelo', 'Problema', 'Diagnostico_IA']])
    else:
        st.info("Aún no hay datos. Usá la pestaña 'Modo Conductor' para generar reportes.")