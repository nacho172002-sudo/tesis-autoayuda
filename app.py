import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai
import os
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="AutoAyuda App", page_icon="🚗", layout="wide")

# --- 2. CONFIGURACIÓN IA (MODO SEGURO) ---
# Este bloque permite que funcione en PC y Web sin escribir la clave aquí
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Error de Configuración: No se encontró la API Key.")
    st.info("👉 En PC: Verificá que exista el archivo .streamlit/secrets.toml")
    st.info("👉 En Web: Verificá los Secrets en el panel de administración.")
    st.stop()

genai.configure(api_key=API_KEY)

# Configuración de Modelo (Prioriza velocidad Flash, usa Pro como respaldo)
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except:
    model = genai.GenerativeModel('gemini-pro')

# --- 3. ARCHIVOS Y PERSISTENCIA ---
FILE_USUARIOS = 'usuarios.csv'
FILE_COMUNIDAD = 'comunidad.csv'
FILE_HISTORIAL = 'historial_global.csv'

# Inicialización segura de archivos (Crea vacíos si no existen)
if not os.path.exists(FILE_USUARIOS):
    pd.DataFrame([{"usuario":"ignacio","clave":"tesis2025"}]).to_csv(FILE_USUARIOS, index=False)

if not os.path.exists(FILE_COMUNIDAD):
    pd.DataFrame(columns=["Fecha", "Usuario", "Titulo", "Contenido", "Etiqueta"]).to_csv(FILE_COMUNIDAD, index=False)

if not os.path.exists(FILE_HISTORIAL):
    pd.DataFrame(columns=["Usuario", "Fecha", "Auto", "Falla", "Diagnostico"]).to_csv(FILE_HISTORIAL, index=False)

# --- 4. FUNCIONES DEL SISTEMA ---

# Gestión de Usuarios
def verificar_login(u, c):
    df = pd.read_csv(FILE_USUARIOS)
    return not df[(df['usuario'] == u) & (df['clave'] == c)].empty

def registrar_usuario(u, c):
    df = pd.read_csv(FILE_USUARIOS)
    if u in df['usuario'].values:
        return False
    nuevo = pd.DataFrame([{"usuario": u, "clave": c}])
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv(FILE_USUARIOS, index=False)
    return True

# Gestión de Historial
def guardar_historial(usuario, auto, falla, diag):
    df = pd.read_csv(FILE_HISTORIAL)
    nuevo = pd.DataFrame([{
        "Usuario": usuario,
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Auto": auto,
        "Falla": falla,
        "Diagnostico": diag
    }])
    df = pd.concat([nuevo, df], ignore_index=True)
    df.to_csv(FILE_HISTORIAL, index=False)

def leer_historial_completo():
    df = pd.read_csv(FILE_HISTORIAL)
    if not df.empty:
        # Conversión de fecha segura para evitar errores en gráficos
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha_DT'])
    return df

# Gestión de Comunidad
def guardar_post_comunidad(usuario, titulo, contenido, etiqueta):
    df = pd.read_csv(FILE_COMUNIDAD)
    nuevo = pd.DataFrame([{
        "Fecha": datetime.datetime.now().strftime("%d/%m %H:%M"),
        "Usuario": usuario,
        "Titulo": titulo,
        "Contenido": contenido,
        "Etiqueta": etiqueta
    }])
    df = pd.concat([nuevo, df], ignore_index=True)
    df.to_csv(FILE_COMUNIDAD, index=False)

def leer_comunidad():
    return pd.read_csv(FILE_COMUNIDAD)

# Motor de IA
def consultar_ia(desc, modelo, sistema):
    try:
        prompt = f"""
        Actúa como mecánico experto. Auto: {modelo}. Falla: {sistema}. Síntoma: "{desc}".
        Responde en formato Markdown breve y estructurado:
        1. **🛠️ Diagnóstico:**
        2. **📊 Gravedad:**
        3. **⚠️ Acción:**
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error de conexión con IA: {str(e)}"

# --- 5. ESTADO DE SESIÓN (MEMORIA) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'ultimo_resultado' not in st.session_state:
    st.session_state.ultimo_resultado = None
if 'temp_post' not in st.session_state:
    st.session_state.temp_post = {}

# --- 6. INTERFAZ GRÁFICA ---

# Barra Lateral (Sidebar)
with st.sidebar:
    st.title("🚗 AutoAyuda")
    if st.session_state.logged_in:
        st.success(f"👤 **{st.session_state.username}**")
        if st.button("Cerrar Sesión"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
        st.error("🚨 **SOS**")
        st.link_button("📞 PEDIR AUXILIO", "https://wa.me/5491100000000")

# Pantalla de Login
if not st.session_state.logged_in:
    st.header("Bienvenido a la Red Colaborativa")
    
    tab_in, tab_up = st.tabs(["Ingresar", "Registrarse"])
    
    with tab_in:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR", type="primary"):
                if verificar_login(u, p):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos.")
    
    with tab_up:
        with st.form("registro"):
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.form_submit_button("CREAR CUENTA"):
                if registrar_usuario(nu, np):
                    st.success("Cuenta creada. Ahora iniciá sesión.")
                else:
                    st.error("El usuario ya existe.")

# Pantalla Principal (App)
else:
    # Menú Principal
    tab_diag, tab_com, tab_hist, tab_mapa = st.tabs([
        "🔧 DIAGNÓSTICO", 
        "👥 COMUNIDAD", 
        "📊 ESTADÍSTICAS", 
        "🗺️ MAPA"
    ])

    # --- TAB 1: DIAGNÓSTICO IA ---
    with tab_diag:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Nueva Consulta")
            # Formulario para evitar recargas accidentales
            mod = st.text_input("Vehículo", "Fiat Cronos 2022")
            sis = st.selectbox("Sistema", ["Motor", "Eléctrico", "Tren Delantero", "Frenos", "Otro"])
            desc = st.text_area("Síntoma", height=100, placeholder="Ej: Ruido metálico al frenar...")
            
            # Botón directo
            if st.button("🔍 ANALIZAR AHORA", type="primary"):
                if not desc:
                    st.warning("⚠️ Por favor describí el problema.")
                else:
                    with st.spinner("La IA está analizando el problema..."):
                        res = consultar_ia(desc, mod, sis)
                        st.session_state.ultimo_resultado = res
                        st.session_state.temp_post = {"mod": mod, "sis": sis, "desc": desc}
                        
                        # Guardar automáticamente en historial personal
                        guardar_historial(st.session_state.username, mod, sis, res)

        with c2:
            st.subheader("Resultado")
            if st.session_state.ultimo_resultado:
                st.success("Diagnóstico Finalizado")
                st.markdown(st.session_state.ultimo_resultado)
                
                st.divider()
                st.info("¿Te sirvió? Compartilo para ayudar a otros:")
                if st.button("📢 Publicar en Comunidad"):
                    d = st.session_state.temp_post
                    guardar_post_comunidad(
                        st.session_state.username, 
                        f"{d['mod']} - {d['sis']}", 
                        st.session_state.ultimo_resultado, 
                        "IA"
                    )
                    st.toast("¡Publicado exitosamente!")

    # --- TAB 2: COMUNIDAD ---
    with tab_com:
        st.subheader("Muro Global de Conocimiento")
        
        # Formulario para aporte manual
        with st.expander("✍️ ¡Aportar un consejo manual!"):
            with st.form("aporte_manual"):
                t = st.text_input("Título (Vehículo y Falla)")
                c = st.text_area("Tu Solución / Consejo")
                if st.form_submit_button("Publicar Aporte"):
                    guardar_post_comunidad(st.session_state.username, t, c, "HUMANO")
                    st.success("Gracias por colaborar!")
                    st.rerun()

        # Mostrar posts
        df_com = leer_comunidad()
        if not df_com.empty:
            # Iteramos al revés para mostrar lo más nuevo arriba
            for i, row in df_com.iloc[::-1].iterrows():
                icon = "🤖" if row['Etiqueta'] == "IA" else "👤"
                with st.container(border=True):
                    c_icon, c_content = st.columns([1, 12])
                    with c_icon:
                        st.header(icon)
                    with c_content:
                        st.markdown(f"**{row['Titulo']}**")
                        st.caption(f"Por @{row['Usuario']} | {row['Fecha']}")
                        st.write(row['Contenido'])
        else:
            st.info("Aún no hay publicaciones en la comunidad.")

    # --- TAB 3: ESTADÍSTICAS ---
    with tab_hist:
        st.subheader("Analytics de la Red")
        
        vista = st.radio("Filtrar datos:", ["Mis Reportes", "Global (Big Data)"], horizontal=True)
        df_hist = leer_historial_completo()
        
        if not df_hist.empty:
            # Filtro de datos
            if vista == "Mis Reportes":
                df_show = df_hist[df_hist['Usuario'] == st.session_state.username]
            else:
                df_show = df_hist

            if not df_show.empty:
                # 1. KPIs (Sin conteo de autos para evitar errores)
                st.markdown("### 📈 Métricas Clave")
                k1, k2, k3 = st.columns(3)
                
                total = len(df_show)
                falla_top = df_show['Falla'].mode()[0] if not df_show.empty else "N/A"
                ultimo_reporte = df_show['Fecha'].iloc[-1].split(" ")[1] if not df_show.empty else "N/A"
                
                k1.metric("Total Reportes", total)
                k2.metric("Sistema más Crítico", falla_top)
                k3.metric("Última Actividad", ultimo_reporte)
                
                st.divider()

                # 2. GRÁFICOS (Solo los seguros)
                g1, g2 = st.columns(2)
                
                with g1:
                    st.markdown("#### Fallas por Sistema")
                    st.bar_chart(df_show['Falla'].value_counts())
                
                with g2:
                    st.markdown("#### Cronología de Reportes")
                    try:
                        if 'Fecha_DT' in df_show.columns:
                            timeline = df_show.set_index('Fecha_DT').resample('h').size()
                            st.line_chart(timeline)
                        else:
                            st.caption("Faltan datos temporales.")
                    except:
                        st.caption("Gráfico no disponible por falta de datos.")

                st.divider()
                st.markdown("#### 📋 Detalle de Registros")
                cols = ['Fecha', 'Usuario', 'Auto', 'Falla', 'Diagnostico']
                st.dataframe(df_show[cols], use_container_width=True)
                st.download_button("📥 Descargar CSV", df_show.to_csv(index=False).encode('utf-8'), "reporte.csv")
            else:
                st.info("No tenés reportes propios todavía.")
        else:
            st.info("La base de datos está vacía.")

    # --- TAB 4: MAPA ---
    with tab_mapa:
        st.subheader("Talleres Verificados")
        
        try:
            # Mapa estático centrado en Buenos Aires
            lat_b, lon_b = -34.6037, -58.3816
            m = folium.Map(location=[lat_b, lon_b], zoom_start=14)
            
            # Marcador Usuario
            folium.Marker(
                [lat_b, lon_b], 
                popup="VOS", 
                tooltip="Tu Ubicación",
                icon=folium.Icon(color="red", icon="user", prefix="fa")
            ).add_to(m)
            
            # Marcadores Talleres
            talleres = [
                [-34.6090, -58.3850, "Taller 'El Pistón'"],
                [-34.5980, -58.3790, "Electricidad Norte"],
                [-34.6050, -58.3900, "Frenos Oeste"]
            ]
            for t in talleres:
                folium.Marker(
                    [t[0], t[1]], 
                    popup=t[2], 
                    icon=folium.Icon(color="blue", icon="wrench", prefix="fa")
                ).add_to(m)
            
            # Renderizado seguro (sin recargas)
            st_folium(m, height=500, width=None, returned_objects=[])
            
        except Exception as e:
            st.error("Error cargando el mapa. Verificá tu conexión.")