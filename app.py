
import streamlit as st
import pandas as pd

import os
import zipfile
from io import BytesIO

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Sistema de Validación Nacional", layout="centered")

# 2. CARGA DE DATOS
@st.cache_data
def load_data():
    # Asegúrate de que el nombre del archivo coincida exactamente con el que subiste a GitHub
    archivo = "cuadro de distribución para oficio con ajustes 31 03 26.xlsx"
    return pd.read_excel(archivo, sheet_name='VAL 30 04 26')

try:
    df = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo Excel: {e}")
    st.stop()

# 3. INTERFAZ DE USUARIO
st.title("📋 Formulario de Validación de Insumos")
st.markdown("---")

entidad = st.selectbox("Seleccione su Entidad:", ["-- Seleccione --"] + list(df['Entidad'].unique()))

if entidad != "-- Seleccione --":
    # Filtrar datos de la entidad
    fila_entidad = df[df['Entidad'] == entidad].iloc[0]
    
    # Transformar datos a formato vertical para facilitar la lectura
    datos_verticales = []
    columnas = df.columns.tolist()
    
    # Lógica para emparejar Medicamento con su Celda de Validación
    for i in range(1, len(columnas), 2):
        nombre_med = columnas[i]
        nombre_val = columnas[i+1]
        datos_verticales.append({
            "Medicamento": nombre_med,
            "Cantidad Asignada": fila_entidad[nombre_med],
            "CANTIDAD VALIDADA": fila_entidad[nombre_val] if pd.notnull(fila_entidad[nombre_val]) else 0
        })

    df_vertical = pd.DataFrame(datos_verticales)

    st.info(f"Usted está validando los insumos para: **{entidad}**")

    # Editor de datos vertical
    df_editado = st.data_editor(
        df_vertical,
        column_config={
            "Medicamento": st.column_config.Column(width="medium", disabled=True),
            "Cantidad Asignada": st.column_config.NumberColumn(disabled=True),
            "CANTIDAD VALIDADA": st.column_config.NumberColumn("Cantidad Real Recibida", min_value=0)
        },
        hide_index=True,
        use_container_width=True
    )

    # Botón de Guardado para los Estados
    if st.button("Enviar Validación Final"):
        nombre_archivo = f"validado_{entidad.replace(' ', '_')}.parquet"
        df_editado['Entidad_Validante'] = entidad
        df_editado.to_parquet(nombre_archivo)
        st.success(f"✅ Validación de {entidad} guardada exitosamente en el servidor.")

# 4. PANEL DE ADMINISTRACIÓN (BARRA LATERAL)
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Acceso Administrativo")

if st.sidebar.checkbox("Modo Administrador"):
    clave = st.sidebar.text_input("Contraseña:", type="password")
    
    if clave == "VIRIDIANA":
        st.sidebar.success("Acceso Autorizado")
        
        # Buscar archivos parquet generados
        archivos = [f for f in os.listdir('.') if f.endswith('.parquet')]
        
        if archivos:
            st.sidebar.write(f"Validaciones recibidas: {len(archivos)}")
            
            # Crear ZIP para descarga
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for f in archivos:
                    z.write(f)
            
            st.sidebar.download_button(
                label="📥 Descargar todas las validaciones (.zip)",
                data=buf.getvalue(),
                file_name="consolidado_nacional.zip",
                mime="application/zip"
            )
        else:
            st.sidebar.warning("Aún no hay datos enviados por los estados.")
    elif clave != "VIRIDIANA":
        st.sidebar.error("Clave incorrecta")