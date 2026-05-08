import streamlit as st
import pandas as pd
import os
import zipfile
import yagmail
from io import BytesIO

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Sistema de Validación Nacional", layout="centered")

# --- FUNCIÓN PARA ENVIAR CORREO ---
def enviar_correo(archivo_adjunto, entidad):
    try:
        # Configuración de cuentas
        usuario_envio = "g.aisawork@gmail.com"  # Tu cuenta de las capturas
        destinatario = "g.aisawork@gmail.com"   # Puedes enviártelo a ti mismo o a otro
        
        # Obtener la contraseña desde los Secrets de Streamlit
        password_envio = st.secrets["ueyh gaqo homm bykp"] 

        # Inicializar el cliente de correo
        yag = yagmail.SMTP(usuario_envio, password_envio)
        
        asunto = f"✅ Nueva Validación: {entidad}"
        cuerpo = f"Se ha recibido la validación de insumos de la entidad: {entidad}.\nSe adjunta el archivo Parquet generado."
        
        yag.send(
            to=destinatario,
            subject=asunto,
            contents=cuerpo,
            attachments=archivo_adjunto
        )
        return True
    except Exception as e:
        st.error(f"Error técnico al enviar correo: {e}")
        return False

# 2. CARGA DE DATOS
@st.cache_data
def load_data():
    # Nombre exacto de tu archivo en GitHub
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
    
    # Reestructurar datos para el editor
    datos_verticales = []
    columnas = df.columns.tolist()
    
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

    # Editor de datos
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

    # Botón de envío
    if st.button("Enviar Validación Final"):
        nombre_archivo = f"validado_{entidad.replace(' ', '_')}.parquet"
        df_editado['Entidad_Validante'] = entidad
        
        # Guardar archivo temporalmente en el servidor
        df_editado.to_parquet(nombre_archivo)
        
        # Enviar por correo
        with st.spinner("Procesando y enviando respaldo por correo..."):
            exito = enviar_correo(nombre_archivo, entidad)
            
            if exito:
                st.success(f"✅ ¡Éxito! La validación de {entidad} ha sido enviada y respaldada.")
                st.balloons()
            else:
                st.warning("⚠️ Los datos se guardaron en el servidor, pero hubo un problema con el envío del correo.")

# 4. PANEL DE ADMINISTRACIÓN (BARRA LATERAL)
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Acceso Administrativo")

if st.sidebar.checkbox("Modo Administrador"):
    clave = st.sidebar.text_input("Contraseña:", type="password")
    
    if clave == "VIRIDIANA":
        st.sidebar.success("Acceso Autorizado")
        
        # Buscar archivos parquet que aún existan en el servidor
        archivos = [f for f in os.listdir('.') if f.endswith('.parquet')]
        
        if archivos:
            st.sidebar.write(f"Archivos temporales: {len(archivos)}")
            
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for f in archivos:
                    z.write(f)
            
            st.sidebar.download_button(
                label="📥 Descargar respaldo local (.zip)",
                data=buf.getvalue(),
                file_name="consolidado_nacional.zip",
                mime="application/zip"
            )
        else:
            st.sidebar.info("No hay archivos temporales en el servidor. Revise su correo para ver los respaldos permanentes.")
    elif clave != "":
        st.sidebar.error("Clave incorrecta")