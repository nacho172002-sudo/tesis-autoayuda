import streamlit as st
import pandas as pd
import datetime
import os
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="AutoAyuda MVP", page_icon="🚗", layout="wide")

# --- SIMULACIÓN DE BASE DE DATOS (ARCHIVO CSV LOCAL) ---
FILE_DB = 'historial_fallas.csv'

def cargar_datos():
    if not os.path.exists(FILE_DB):
        return pd.DataFrame(columns=["Fecha", "Modelo", "Tipo_Falla", "Descripcion", "Diagnostico_IA"])
    return pd.read_csv(FILE_DB)

def guardar_registro(modelo, tipo, descripcion, diagnostico):
    df = cargar_datos()
    nuevo_registro = {
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Modelo": modelo,
        "Tipo_Falla": tipo,
        "Descripcion": descripcion,
        "Diagnostico_IA": diagnostico
    }
    # Usamos pd.concat para agregar el nuevo registro
    df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
    df.to_csv(FILE_DB, index=False)
    return df

# --- MOTOR DE INTELIGENCIA ARTIFICIAL (SIMULADO PARA MVP) ---
def motor_ia_diagnostico(descripcion, tipo):
    descripcion = descripcion.lower()
    
    # Lógica de reglas simple para simular la IA
    if "arranca" in descripcion or "bateria" in descripcion or "luces" in descripcion or "muerta" in descripcion:
        return "⚠️ Falla Eléctrica / Batería (Confianza: 92%) - Acción: Revisar bornes y alternador."
    elif "ruido" in descripcion or "golpe" in descripcion or "vibra" in descripcion or "pozo" in descripcion:
        return "⚠️ Tren Delantero / Suspensión (Confianza: 85%) - Acción: Revisar bujes y amortiguadores."
    elif "calienta" in descripcion or "temperatura" in descripcion or "humo" in descripcion or "agua" in descripcion:
        return "🛑 Refrigeración / Motor (Confianza: 98%) - Acción: DETENER MOTOR INMEDIATAMENTE."
    elif "freno" in descripcion or "chillido" in descripcion:
        return "⚠️ Sistema de Frenos (Confianza: 90%) - Acción: Revisar pastillas y líquido."
    else:
        return "ℹ️ Diagnóstico General - Se requiere inspección física con escáner en taller."

# --- INTERFAZ GRÁFICA ---

# Barra lateral
st.sidebar.title("Navegación")
perfil = st.sidebar.radio("Seleccionar Vista:", ["📱 App Conductor (Usuario)", "📊 Dashboard (Administrador)"])

st.sidebar.divider()
st.sidebar.info("Prototipo funcional v1.0 - Tesis Ingeniería")

# ---------------- PANTALLA 1: LA APP DEL CONDUCTOR ----------------
if perfil == "📱 App Conductor (Usuario)":
    
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.write("🚗") # Acá podés poner una imagen real con st.image
    with col_titulo:
        st.title("AutoAyuda")
        st.caption("Red Colaborativa de Diagnóstico Automotriz")

    st.markdown("---")
    st.subheader("Reportar Nueva Falla")
    
    with st.form("form_reporte", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            modelo = st.text_input("Modelo del vehículo", "Chevrolet Corsa 2010")
        with col2:
            km = st.number_input("Kilometraje actual", value=120000, step=1000)
            
        tipo_falla = st.selectbox("Categoría del problema", 
                                  ["Eléctrico/Batería", "Motor/Temperatura", "Suspensión/Ruedas", "Frenos", "Otro"])
        
        descripcion = st.text_area("Describí el problema (Ej: 'Hace ruido al doblar', 'No arranca')", height=100)
        
        # Botón de envío
        enviado = st.form_submit_button("🔍 DIAGNOSTICAR CON IA")
        
    if enviado:
        if not descripcion:
            st.error("Por favor, describí el problema para que la IA pueda analizarlo.")
        else:
            with st.spinner('Conectando con Motor de IA... Analizando patrones...'):
                time.sleep(1.5) # Simula tiempo de procesamiento de red
                
                # 1. Ejecutar IA
                resultado = motor_ia_diagnostico(descripcion, tipo_falla)
                
                # 2. Guardar en Base de Datos
                guardar_registro(modelo, tipo_falla, descripcion, resultado)
                
                # 3. Mostrar Resultado
                st.success("✅ Diagnóstico Finalizado")
                
                c_res1, c_res2 = st.columns([2, 1])
                
                with c_res1:
                    st.info(f"**Resultado del Análisis:**\n\n{resultado}")
                    st.write("Este diagnóstico se basa en 14,500 casos similares en la base de datos.")
                
                with c_res2:
                    st.warning("📍 **Talleres Cercanos:**")
                    # Mapa simulado (Coordenadas de Buenos Aires por defecto)
                    df_mapa = pd.DataFrame({
                        'lat': [-34.6037, -34.6100, -34.5900], 
                        'lon': [-58.3816, -58.3900, -58.4000]
                    })
                    st.map(df_mapa, zoom=12)

# ---------------- PANTALLA 2: EL DASHBOARD (EVIDENCIA) ----------------
else:
    st.title("Tablero de Control Operativo")
    st.markdown("Monitoreo en tiempo real de fallas reportadas y performance de la IA.")
    
    df = cargar_datos()
    
    if not df.empty:
        # Métricas (KPIs)
        total_reportes = len(df)
        falla_mas_comun = df['Tipo_Falla'].mode()[0] if not df.empty else "N/A"
        ult_falla = df.iloc[-1]['Fecha']
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Reportes", total_reportes, "+1 hoy")
        kpi2.metric("Falla Frecuente", falla_mas_comun)
        kpi3.metric("Último Reporte", ult_falla.split(" ")[1]) # Solo hora
        kpi4.metric("Precisión IA Estimada", "91%", "+2%")
        
        st.divider()
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("Distribución por Tipo de Falla")
            conteo_fallas = df['Tipo_Falla'].value_counts()
            st.bar_chart(conteo_fallas, color="#FF4B4B")
            
        with col_graf2:
            st.subheader("Últimos Diagnósticos Generados")
            st.dataframe(
                df[["Modelo", "Tipo_Falla", "Diagnostico_IA"]].sort_index(ascending=False), 
                height=300, 
                use_container_width=True
            )
            
        st.success("Base de datos sincronizada con Firebase (Simulación).")
        
    else:
        st.info("⚠️ Aún no hay datos. Andá al modo 'App Conductor' y cargá reportes para ver el tablero.")
        