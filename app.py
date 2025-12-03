import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai
import os
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AutoAyuda App", page_icon="🚗", layout="wide")

# --- 2. CONFIGURACIÓN IA (MODELO 2.0 FLASH) ---
# Usamos tu clave directa para evitar errores
API_KEY = "AIzaSyCxlwQO6cpQVHeWX_rF8osULqa1d3reRsc"
genai.configure(api_key=API_KEY)

# Configuramos explícitamente el modelo 2.0 que es el más rápido
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except:
    # Fallback por seguridad
    model = genai.GenerativeModel('gemini-pro')

# --- 3. ESTADO Y ARCHIVOS ---
FILE_USUARIOS = 'usuarios.csv'

# Inicializar memoria de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'ultimo_resultado' not in st.session_state:
    st.session_state.ultimo_resultado = None

# --- 4. FUNCIONES ---
def verificar_login(u, c):
    if not os.path.exists(FILE_USUARIOS):
        pd.DataFrame([{"usuario":"ignacio","clave":"tesis2025"}]).to_csv(FILE_USUARIOS, index=False)
    df = pd.read_csv(FILE_USUARIOS)
    return not df[(df['usuario'] == u) & (df['clave'] == c)].empty

def registrar_usuario(u, c):
    if not os.path.exists(FILE_USUARIOS):
        pd.DataFrame([{"usuario":"ignacio","clave":"tesis2025"}]).to_csv(FILE_USUARIOS, index=False)
    df = pd.read_csv(FILE_USUARIOS)
    if u in df['usuario'].values:
        return False
    nuevo = pd.DataFrame([{"usuario": u, "clave": c}])
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv(FILE_USUARIOS, index=False)
    return True

def consultar_ia(desc, modelo, sistema):
    try:
        prompt = f"""
        Actúa como mecánico experto. Auto: {modelo}. Sistema: {sistema}. Síntoma: "{desc}".
        Responde en formato Markdown estructurado:
        1. **🛠️ Diagnóstico Probable:**
        2. **📊 Nivel de Confianza:**
        3. **⚠️ Acción Inmediata:**
        4. **🚦 ¿Es peligroso manejar?:**
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error de conexión IA: {str(e)}"

# --- 5. INTERFAZ GRÁFICA ---

# PANTALLA DE LOGIN
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🚗 AutoAyuda</h1>", unsafe_allow_html=True)
    
    tab_in, tab_up = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab_in:
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR", type="primary", use_container_width=True):
                if verificar_login(u, p):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("❌ Datos incorrectos (Probá: ignacio / tesis2025)")
    
    with tab_up:
        with st.form("registro_form"):
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Contraseña", type="password")
            if st.form_submit_button("CREAR CUENTA", use_container_width=True):
                if registrar_usuario(nu, np):
                    st.success("✅ Cuenta creada. Ahora iniciá sesión.")
                else:
                    st.error("⚠️ El usuario ya existe.")

# PANTALLA PRINCIPAL (APP)
else:
    # Header
    c1, c2 = st.columns([8, 1])
    c1.title(f"Bienvenido, {st.session_state.username.capitalize()} 👋")
    if c2.button("Salir"):
        st.session_state.logged_in = False
        st.rerun()
    
    st.markdown("---")
    tabs = st.tabs(["🔧 DIAGNÓSTICO IA", "🗺️ MAPA INTERACTIVO", "📊 HISTORIAL"])

    # --- PESTAÑA 1: DIAGNÓSTICO ---
    with tabs[0]:
        col_form, col_res = st.columns(2)
        
        with col_form:
            st.subheader("Reportar Incidente")
            with st.form("diag_form"):
                mod = st.text_input("Vehículo", "Volkswagen Gol Trend 2017")
                sis = st.selectbox("Sistema", ["Motor", "Eléctrico", "Tren Delantero", "Frenos", "Otro"])
                desc = st.text_area("Descripción del Problema", height=120, placeholder="Ej: Ruido metálico al pasar lomas de burro...")
                
                # Botón de envío
                enviado = st.form_submit_button("🔍 ANALIZAR CON GEMINI 2.0", type="primary")
            
            if enviado:
                if not desc:
                    st.warning("⚠️ Por favor describí el problema.")
                else:
                    with st.spinner("Conectando con el motor de IA..."):
                        # Llamada a la IA
                        res = consultar_ia(desc, mod, sis)
                        st.session_state.ultimo_resultado = res
                        
                        # Guardar historial
                        st.session_state.historial.append({
                            "Fecha": datetime.datetime.now().strftime("%d/%m %H:%M"),
                            "Auto": mod,
                            "Falla": sis,
                            "Resultado": res
                        })

        with col_res:
            st.subheader("Resultado del Análisis")
            if st.session_state.ultimo_resultado:
                st.success("Diagnóstico Recibido")
                st.markdown(st.session_state.ultimo_resultado)
            else:
                st.info("Esperando consulta...")

    # --- PESTAÑA 2: MAPA INTERACTIVO (FOLIUM) ---
    with tabs[1]:
        st.subheader("Red de Talleres Verificados")
        
        # Coordenadas base (Obelisco)
        lat_b, lon_b = -34.6037, -58.3816
        
        # Creamos el mapa
        m = folium.Map(location=[lat_b, lon_b], zoom_start=14)
        
        # 1. Marcador TU UBICACIÓN (Rojo)
        folium.Marker(
            [lat_b, lon_b], 
            popup="<b>VOS</b>", 
            tooltip="Tu Ubicación",
            icon=folium.Icon(color="red", icon="user", prefix="fa")
        ).add_to(m)
        
        # 2. Talleres (Azules)
        talleres = [
            [-34.6090, -58.3850, "Taller 'El Pistón'"],
            [-34.5980, -58.3790, "Electricidad Norte"],
            [-34.6100, -58.3700, "Gomería Sur"],
            [-34.6050, -58.3900, "Frenos Oeste"]
        ]
        
        for t in talleres:
            folium.Marker(
                [t[0], t[1]], 
                popup=f"<b>{t[2]}</b><br>⭐⭐⭐⭐", 
                tooltip=t[2],
                icon=folium.Icon(color="blue", icon="wrench", prefix="fa")
            ).add_to(m)

        # EL SECRETO PARA QUE NO TITILE: returned_objects=[]
        st_folium(m, height=500, width=None, returned_objects=[])

    # --- PESTAÑA 3: HISTORIAL ---
    with tabs[2]:
        st.subheader("Tus Reportes")
        if st.session_state.historial:
            df = pd.DataFrame(st.session_state.historial)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Descargar CSV", df.to_csv(index=False).encode('utf-8'), "historial.csv")
        else:
            st.info("No hay datos aún.")
            