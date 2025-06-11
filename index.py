import pandas as pd
import streamlit as st
from io import StringIO, BytesIO
import chardet
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Explorador Avanzado de Videojuegos",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para detectar encoding y delimitador
def detect_file_properties(file_path):
    # Detectar encoding
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read(10000))
    encoding = result['encoding']
    
    # Detectar delimitador
    with open(file_path, 'r', encoding=encoding) as f:
        primera_linea = f.readline()
        delimitador = "," if primera_linea.count(",") > primera_linea.count(";") else ";"
    
    return encoding, delimitador

# Función para cargar archivos subidos
def load_uploaded_file(uploaded_file):
    # Leer como bytes para detectar encoding
    raw_data = uploaded_file.getvalue()
    
    # Detectar encoding
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    
    try:
        # Intentar decodificar con el encoding detectado
        string_data = raw_data.decode(encoding)
        stringio = StringIO(string_data)
        
        # Detectar delimitador
        primera_linea = stringio.readline()
        delimitador = "," if primera_linea.count(",") > primera_linea.count(";") else ";"
        stringio.seek(0)  # Rebobinar para leer desde el inicio
        
        # Leer el DataFrame
        df = pd.read_csv(stringio, delimiter=delimitador, on_bad_lines='warn')
        return df
    except UnicodeDecodeError:
        # Fallback a latin1 si falla
        try:
            string_data = raw_data.decode('latin1')
            stringio = StringIO(string_data)
            primera_linea = stringio.readline()
            delimitador = "," if primera_linea.count(",") > primera_linea.count(";") else ";"
            stringio.seek(0)
            df = pd.read_csv(stringio, delimiter=delimitador, on_bad_lines='warn')
            return df
        except Exception as e:
            st.error(f"No se pudo decodificar el archivo: {e}")
            return None

# Función para limpiar datos
def clean_data(df):
    # Eliminar duplicados
    df = df.drop_duplicates()
    
    # Convertir columnas numéricas
    numeric_cols = ['AÑO', 'PRECIO', 'MEDIA', 'PUNTUACIÓN']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Limpiar texto
    text_cols = ['TÍTULO', 'GÉNERO', 'PLATAFORMA', 'DESARROLLADOR']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].str.strip().str.upper()
    
    return df

# Interfaz de usuario
st.title("🎮 Explorador Avanzado de Base de Datos de Videojuegos")
st.markdown("""
<style>
.big-font {
    font-size:18px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">Explora, analiza y visualiza datos de videojuegos de manera interactiva</p>', unsafe_allow_html=True)
st.markdown("---")

# Cargar datos
uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])
if uploaded_file is not None:
    df = load_uploaded_file(uploaded_file)
    if df is not None:
        st.success("✅ Archivo cargado correctamente")
else:
    # Cargar archivo por defecto si no se sube uno
    try:
        archivo = "base_productos.csv"
        encoding, delimitador = detect_file_properties(archivo)
        df = pd.read_csv(archivo, encoding=encoding, delimiter=delimitador, on_bad_lines='warn')
        st.success(f"✅ Archivo por defecto cargado correctamente (Encoding: {encoding}, Delimitador: '{delimitador}')")
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo por defecto: {e}")
        st.stop()

# Limpieza de datos
df = clean_data(df)

# Sidebar con análisis rápido
st.sidebar.title("🔍 Análisis Rápido")
st.sidebar.metric("Total de Juegos", len(df))
if 'AÑO' in df.columns:
    st.sidebar.metric("Año más reciente", int(df['AÑO'].max()))
if 'PRECIO' in df.columns:
    st.sidebar.metric("Precio promedio", f"${df['PRECIO'].mean():.2f}")

# Pestañas principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "🔍 Explorar", "📈 Visualización", "💾 Exportar"])

with tab1:
    st.subheader("Resumen General")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filas", df.shape[0])
    with col2:
        st.metric("Columnas", df.shape[1])
    with col3:
        st.metric("Valores faltantes", df.isnull().sum().sum())
    
    st.subheader("Estructura de Datos")
    st.dataframe(df.head(10), use_container_width=True)
    
    expander = st.expander("📝 Detalles Técnicos")
    with expander:
        st.write("**Tipos de datos:**")
        st.write(df.dtypes)
        st.write("**Valores nulos por columna:**")
        st.write(df.isnull().sum())

with tab2:
    st.subheader("Exploración Interactiva")
    
    # Filtros dinámicos
    cols = st.columns(3)
    filter_params = {}
    
    with cols[0]:
        if 'GÉNERO' in df.columns:
            generos = ['Todos'] + sorted(df['GÉNERO'].dropna().unique().tolist())
            filter_params['genero'] = st.selectbox("Filtrar por género:", generos)
    
    with cols[1]:
        if 'PLATAFORMA' in df.columns:
            plataformas = ['Todas'] + sorted(df['PLATAFORMA'].dropna().unique().tolist())
            filter_params['plataforma'] = st.selectbox("Filtrar por plataforma:", plataformas)
    
    with cols[2]:
        if 'AÑO' in df.columns:
            año_min, año_max = int(df['AÑO'].min()), int(df['AÑO'].max())
            filter_params['rango_años'] = st.slider("Rango de años:", año_min, año_max, (año_min, año_max))
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if 'GÉNERO' in df.columns and filter_params.get('genero', 'Todos') != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['GÉNERO'] == filter_params['genero']]
    if 'PLATAFORMA' in df.columns and filter_params.get('plataforma', 'Todas') != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['PLATAFORMA'] == filter_params['plataforma']]
    if 'AÑO' in df.columns:
        rango = filter_params.get('rango_años', (df['AÑO'].min(), df['AÑO'].max()))
        df_filtrado = df_filtrado[(df_filtrado['AÑO'] >= rango[0]) & (df_filtrado['AÑO'] <= rango[1])]
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    if st.checkbox("Mostrar estadísticas descriptivas"):
        st.write(df_filtrado.describe(include='all'))

with tab3:
    st.subheader("Visualización de Datos")
    
    col1, col2 = st.columns(2)
    with col1:
        if 'GÉNERO' in df.columns:
            fig = px.pie(df, names='GÉNERO', title='Distribución por Género')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if 'AÑO' in df.columns:
            fig = px.histogram(df, x='AÑO', title='Juegos por Año')
            st.plotly_chart(fig, use_container_width=True)
    
    col3, col4 = st.columns(2)
    with col3:
        if 'PLATAFORMA' in df.columns:
            fig = px.bar(df['PLATAFORMA'].value_counts().head(10), 
                        title='Top 10 Plataformas')
            st.plotly_chart(fig, use_container_width=True)
    with col4:
        if all(col in df.columns for col in ['PRECIO', 'MEDIA']):
            fig = px.scatter(df, x='PRECIO', y='MEDIA', 
                            hover_data=['TÍTULO'], title='Precio vs Puntuación')
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Exportar Datos")
    
    # Opciones de exportación
    export_format = st.radio("Formato de exportación:", ["CSV", "Excel", "JSON"])
    
    if export_format == "CSV":
        st.download_button(
            label="Descargar como CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='videojuegos_limpio.csv',
            mime='text/csv'
        )
    elif export_format == "Excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="Descargar como Excel",
            data=output.getvalue(),
            file_name='videojuegos_limpio.xlsx',
            mime='application/vnd.ms-excel'
        )
    elif export_format == "JSON":
        st.download_button(
            label="Descargar como JSON",
            data=df.to_json(orient='records').encode('utf-8'),
            file_name='videojuegos_limpio.json',
            mime='application/json'
        )
    
    st.markdown("---")
    st.write("**Filtros aplicados actualmente:**")
    st.code(f"""
    Género: {filter_params.get('genero', 'N/A')}
    Plataforma: {filter_params.get('plataforma', 'N/A')}
    Años: {filter_params.get('rango_años', 'N/A')}
    """)

# Notas finales
st.markdown("---")
st.markdown("""
**Notas:**
- Los gráficos son interactivos (puedes hacer zoom, hover, etc.)
- Usa los filtros para explorar datos específicos
- Exporta los datos en el formato que prefieras
""")