import streamlit as st
import pandas as pd

st.set_page_config(page_title="Validación Vertical de Insumos", layout="centered")

@st.cache_data
def load_data():
    # Cargamos el archivo que nos compartiste
    return pd.read_excel("cuadro de distribución para oficio con ajustes 31 03 26.xlsx", sheet_name='VAL 30 04 26')

df = load_data()

st.title("📋 Formulario de Validación de Insumos")
st.markdown("---")

entidad = st.selectbox("Seleccione su Entidad:", ["-- Seleccione --"] + list(df['Entidad'].unique()))

if entidad != "-- Seleccione --":
    # 1. Obtener la fila de la entidad y transponerla para que sea vertical
    fila_entidad = df[df['Entidad'] == entidad].iloc[0]
    
    # Creamos una lista de diccionarios para armar una tabla vertical
    datos_verticales = []
    
    # Iteramos por las columnas para emparejar Medicamento con su Celda de Validación
    # Según tu archivo, los medicamentos están en las columnas pares y validaciones en las impares
    columnas = df.columns.tolist()
    
    for i in range(1, len(columnas), 2):
        nombre_medicamento = columnas[i]
        nombre_validacion = columnas[i+1]
        
        datos_verticales.append({
            "Medicamento": nombre_medicamento,
            "Cantidad Asignada": fila_entidad[nombre_medicamento],
            "CANTIDAD VALIDADA": fila_entidad[nombre_validacion] if pd.notnull(fila_entidad[nombre_validacion]) else 0
        })

    df_vertical = pd.DataFrame(datos_verticales)

    st.info(f"Validando insumos para: **{entidad}**")

    # 2. Editor en formato vertical
    df_editado_vertical = st.data_editor(
        df_vertical,
        column_config={
            "Medicamento": st.column_config.Column(width="medium", disabled=True),
            "Cantidad Asignada": st.column_config.NumberColumn(disabled=True),
            "CANTIDAD VALIDADA": st.column_config.NumberColumn(
                "Cantidad Validada",
                help="Ingrese la cantidad real recibida",
                min_value=0,
                required=True
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # 3. Guardado en Parquet
    if st.button("Enviar Validación Final"):
        nombre_archivo = f"validado_{entidad.replace(' ', '_')}.parquet"
        # Guardamos el formato vertical (más fácil de procesar después)
        df_editado_vertical['Entidad'] = entidad
        df_editado_vertical.to_parquet(nombre_archivo)
        st.success(f"✅ La validación de {entidad} se ha guardado correctamente.")